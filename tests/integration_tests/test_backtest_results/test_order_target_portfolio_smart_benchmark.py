from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import pytest
from pandas import Series, read_csv

from rqalpha import run_func
from rqalpha.mod.rqalpha_mod_sys_accounts.api.order_target_portfolio import order_target_portfolio_smart

DATES = (
    '2025-06-16',
    '2025-06-17',
    '2025-06-18',
    '2025-06-19',
    '2025-06-20',
    '2025-06-23',
    '2025-06-24',
    '2025-06-25',
    '2025-06-26',
    '2025-06-27',
    '2025-06-30',
    '2025-07-01',
    '2025-07-02',
    '2025-07-03',
    '2025-07-04',
    '2025-07-07',
    '2025-07-08',
    '2025-07-09',
    '2025-07-10',
    '2025-07-11',
    '2025-07-14',
    '2025-07-15',
)
SCALES = (100, 500, 1000, 1500)
INITIAL_CASH = 100_000_000
BASE_DIR = Path(__file__).parent / 'resources' / 'benchmark_order_target_portfolio_smart'
RESULTS_DIR = BASE_DIR / 'results'


@dataclass(frozen=True)
class BenchmarkCase:
    """封装单个规模样本的 benchmark 基线读写与比较。"""

    scale: int

    @property
    def name(self) -> str:
        """返回规模样本名。"""
        return f'{self.scale}持仓20%换手率'

    def sample_name(self, trade_date: str) -> str:
        """返回单日样本名。"""
        return f'{self.name}_{trade_date.replace("-", "")}'

    def weights_path(self, trade_date: str) -> Path:
        """返回目标权重文件路径。"""
        return BASE_DIR / str(self.scale) / f'{self.sample_name(trade_date)}.csv'

    def result_path(self, trade_date: str) -> Path:
        """返回单日订单结果快照路径。"""
        return BASE_DIR / str(self.scale) / f'{self.sample_name(trade_date)}.json'

    @property
    def metrics_path(self) -> Path:
        """返回聚合后的总权重误差指标路径。"""
        return RESULTS_DIR / f'{self.name}.metrics.json'

    def new_result_path(self, trade_date: str) -> Path:
        """返回单日候选订单结果快照路径。"""
        return BASE_DIR / str(self.scale) / f'{self.sample_name(trade_date)}.new.json'

    @property
    def new_metrics_path(self) -> Path:
        """返回候选总权重误差指标路径。"""
        return RESULTS_DIR / f'{self.name}.metrics.new.json'

    def load_target_weights(self, trade_date: str) -> Series:
        """读取某个交易日的目标权重。"""
        weights_path = self.weights_path(trade_date)
        frame = read_csv(weights_path)
        missing_columns = {'order_book_id', 'weight'} - set(frame.columns)
        if missing_columns:
            raise AssertionError(f'权重文件缺少字段 {sorted(missing_columns)}: {weights_path}')
        return cast(Series, frame.set_index('order_book_id')['weight'])

    def serialize_results(self, raw_results: dict[str, Any]) -> list[dict[str, Any]]:
        """把订单结果序列化为稳定 JSON 结构。"""
        return sorted(
            (self._serialize_result(order_book_id, result) for order_book_id, result in raw_results.items()),
            key=lambda item: item['order_book_id'],
        )

    @staticmethod
    def calculate_total_weight_diff(context, target_weights: Series) -> float:
        """计算单日总权重误差。"""
        total_value = float(context.portfolio.total_value)
        actual_weights = Series(
            {
                position.order_book_id: position.market_value / total_value
                for position in context.portfolio.stock_account.get_positions()
            }
        )
        return round(abs(float(actual_weights.sum()) - float(target_weights.sum())), 12)

    def build_metrics_payload(self, daily_total_weight_diff: dict[str, float]) -> dict[str, Any]:
        """构造聚合后的多日指标与平均值。"""
        expected_dates = set(DATES)
        actual_dates = set(daily_total_weight_diff)
        missing_dates = sorted(expected_dates - actual_dates)
        extra_dates = sorted(actual_dates - expected_dates)
        if missing_dates or extra_dates:
            raise AssertionError(f'{self.name} 指标日期不完整: missing={missing_dates}, extra={extra_dates}')

        normalized_daily = {trade_date: round(float(daily_total_weight_diff[trade_date]), 12) for trade_date in DATES}
        average_total_weight_diff = round(sum(normalized_daily.values()) / len(normalized_daily), 12)
        return {
            'daily_total_weight_diff': normalized_daily,
            'average_total_weight_diff': average_total_weight_diff,
        }

    def persist_and_assert(
        self,
        results_by_date: dict[str, list[dict[str, Any]]],
        daily_total_weight_diff: dict[str, float],
    ) -> None:
        """按月均总权重误差决定初始化、更新基线或生成候选结果。"""
        metrics = self.build_metrics_payload(daily_total_weight_diff)
        if (not self._has_all_daily_results()) or (not self.metrics_path.exists()):
            self._write_daily_results(results_by_date)
            self._write_json(self.metrics_path, metrics)
            self._remove_daily_new_results()
            self._remove_if_exists(self.new_metrics_path)
            return

        baseline_metrics = self._load_metrics()
        baseline_average = baseline_metrics['average_total_weight_diff']
        candidate_average = metrics['average_total_weight_diff']

        if candidate_average < baseline_average:
            self._write_daily_results(results_by_date)
            self._write_json(self.metrics_path, metrics)
            self._remove_daily_new_results()
            self._remove_if_exists(self.new_metrics_path)
            return

        if candidate_average > baseline_average:
            self._write_daily_new_results(results_by_date)
            self._write_json(self.new_metrics_path, metrics)
            raise AssertionError(
                f'{self.name} 月均总权重误差退化: {baseline_average} -> {candidate_average}; '
                f'candidate_metrics={self.new_metrics_path.name}'
            )

        self._remove_daily_new_results()
        self._remove_if_exists(self.new_metrics_path)

    def _load_metrics(self) -> dict[str, Any]:
        """读取并校验聚合后的总权重误差指标。"""
        with self.metrics_path.open('rt', encoding='utf-8') as file:
            payload = json.load(file)
        if not isinstance(payload, dict):
            raise AssertionError(f'指标文件必须是字典结构: {self.metrics_path}')
        if 'daily_total_weight_diff' not in payload or 'average_total_weight_diff' not in payload:
            raise AssertionError(f'指标文件缺少字段: {self.metrics_path}')
        daily_total_weight_diff = payload['daily_total_weight_diff']
        if not isinstance(daily_total_weight_diff, dict):
            raise AssertionError(f'daily_total_weight_diff 必须是字典结构: {self.metrics_path}')
        return {
            'daily_total_weight_diff': {
                str(trade_date): round(float(value), 12) for trade_date, value in daily_total_weight_diff.items()
            },
            'average_total_weight_diff': round(float(payload['average_total_weight_diff']), 12),
        }

    def _has_all_daily_results(self) -> bool:
        """检查所有交易日基线结果文件是否存在。"""
        return all(self.result_path(trade_date).exists() for trade_date in DATES)

    def _write_daily_results(self, results_by_date: dict[str, list[dict[str, Any]]]) -> None:
        """写入全部交易日基线结果文件。"""
        for trade_date in DATES:
            self._write_json(self.result_path(trade_date), results_by_date[trade_date])

    def _write_daily_new_results(self, results_by_date: dict[str, list[dict[str, Any]]]) -> None:
        """写入全部交易日候选结果文件。"""
        for trade_date in DATES:
            self._write_json(self.new_result_path(trade_date), results_by_date[trade_date])

    def _remove_daily_new_results(self) -> None:
        """删除全部交易日候选结果文件。"""
        for trade_date in DATES:
            self._remove_if_exists(self.new_result_path(trade_date))

    @staticmethod
    def _write_json(path: Path, payload: Any) -> None:
        """写入 JSON 文件。"""
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('wt', encoding='utf-8') as file:
            json.dump(payload, file, ensure_ascii=False, indent=2, sort_keys=True)

    @staticmethod
    def _remove_if_exists(path: Path) -> None:
        """删除已存在的文件。"""
        if path.exists():
            path.unlink()

    @staticmethod
    def _serialize_result(order_book_id: str, result: Any) -> dict[str, Any]:
        """序列化单笔订单结果。"""
        if isinstance(result, str):
            return {
                'order_book_id': str(order_book_id),
                'status': 'rejected',
                'rejection_reason': result,
            }

        trading_datetime = getattr(result, 'trading_datetime', None)
        if trading_datetime is not None and hasattr(trading_datetime, 'strftime'):
            trading_datetime_value = trading_datetime.strftime('%Y-%m-%d %H:%M:%S')
        else:
            trading_datetime_value = str(trading_datetime or '')

        return {
            'order_book_id': str(order_book_id),
            'status': str(getattr(getattr(result, 'status', ''), 'name', getattr(result, 'status', ''))),
            'side': str(getattr(getattr(result, 'side', ''), 'name', getattr(result, 'side', ''))),
            'position_effect': str(
                getattr(
                    getattr(result, 'position_effect', ''),
                    'name',
                    getattr(result, 'position_effect', ''),
                )
            ),
            'quantity': int(getattr(result, 'quantity', 0) or 0),
            'filled_quantity': int(getattr(result, 'filled_quantity', 0) or 0),
            'unfilled_quantity': int(getattr(result, 'unfilled_quantity', 0) or 0),
            'avg_price': round(float(getattr(result, 'avg_price', 0.0) or 0.0), 10),
            'transaction_cost': round(float(getattr(result, 'transaction_cost', 0.0) or 0.0), 10),
            'trading_datetime': trading_datetime_value,
            'message': str(getattr(result, 'message', '') or ''),
        }


@pytest.mark.parametrize('scale', SCALES)
def test_order_target_portfolio_smart_benchmark_json(scale):
    """只比较月均总权重误差，每日结果按规模落在对应目录，metrics 按规模汇总到 results。"""
    case = BenchmarkCase(scale=scale)
    results_by_date: dict[str, list[dict[str, Any]]] = {}
    daily_total_weight_diff: dict[str, float] = {}

    def open_auction(context, bar_dict) -> None:
        trade_date = context.now.strftime('%Y-%m-%d')
        weights_path = case.weights_path(trade_date)
        if not weights_path.exists():
            raise AssertionError(f'缺少权重文件: {weights_path}')

        target_weights = case.load_target_weights(trade_date)
        raw_results = order_target_portfolio_smart(target_weights) or {}
        results_by_date[trade_date] = case.serialize_results(raw_results)
        daily_total_weight_diff[trade_date] = case.calculate_total_weight_diff(context, target_weights)

    config = {
        'base': {
            'start_date': DATES[0],
            'end_date': DATES[-1],
            'frequency': '1d',
            'matching_type': 'current_bar',
            'benchmark': None,
            'accounts': {'stock': INITIAL_CASH},
        },
        'extra': {
            'log_level': 'error',
        },
    }
    run_func(config=config, open_auction=open_auction)
    # 由于每台机器运行耗时不一样，这里就不记录耗时了
    case.persist_and_assert(results_by_date=results_by_date, daily_total_weight_diff=daily_total_weight_diff)
