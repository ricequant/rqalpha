from copy import deepcopy
from datetime import datetime, time
from typing import Optional, List, Callable, Iterable, Dict

from pandas import DataFrame

import rqdatac

from rqalpha.core.strategy_context import StrategyContext
from rqalpha.utils.dict_func import deep_update
from rqalpha.mod.rqalpha_mod_sys_accounts.api.api_stock import order_target_portfolio


class Strategy:
    DEFAULTG_CONFIG = {
        "base": {
            "accounts": {
                "STOCK": 20000000
            }
        },
        "mod": {
            "sys_transaction_cost": {
                "cn_stock_min_commission": 2,
                "commission_multiplier": 0.25,
            },
        }
    }

    def __init__(
        self,
        factor: DataFrame,
        rebalance_frequency: str,
        start_date,
        end_date,
        universe: Optional[str] = None,
        factor_threshold: float = 0.1,
        filter_suspended: bool = True,
        config: Optional[Dict] = None,
    ):
        self.config = deepcopy(self.DEFAULTG_CONFIG)
        deep_update(config, self.config)
        deep_update({
            "base": {
                "start_date": start_date,
                "end_date": end_date,
            }
        }, self.config)

        self._factor = factor
        self._factor_threshold = factor_threshold
        self._filters: List[Callable[[StrategyContext, Iterable[str]], List[str]]] = []
        self._rebalance_frequency = rebalance_frequency

        all_cs = rqdatac.all_instruments("CS").order_book_id
        if filter_suspended:
            suspended = rqdatac.is_suspended(all_cs, start_date, end_date)

            def _filter_suspended(context, order_book_ids):
                _suspended = suspended.loc[str(context.now.date())]
                _suspended = set(_suspended[_suspended].keys())
                return [o for o in order_book_ids if o not in _suspended]

            self._filters.append(_filter_suspended)

        if universe:
            index_components = {k.date(): v for k, v in rqdatac.index_components(
                universe, start_date=start_date, end_date=end_date
            ).items()}
            self._get_universe = lambda today: index_components[today]
        else:
            self._get_universe = lambda today: all_cs

    def _rebalance(self, context, _):
        if context.target is None:
            return
        target = context.target
        for f in self._filters:
            target = f(context, target)
        order_target_portfolio(dict.fromkeys(target, 0.99 / len(target)))

    def init(self, _):
        if self._rebalance_frequency == "1w":
            scheduler.run_weekly(self._rebalance, tradingday=1)  # noqa
        else:
            raise NotImplementedError(f"unsuported rebalance frequency {self._rebalance_frequency}")

    def after_trading(self, context):
        obids = self._get_universe(context.now.date())
        factor = self._factor.loc[str(context.now.date())][obids]
        context.target = set(factor.sort_values()[:int(len(factor) * self._factor_threshold)].keys())


def run(
        factor: DataFrame,
        rebalance_frequency: str,
        start_date,
        end_date,
        universe: Optional[str] = None,
        factor_threshold: float = 0.1,
        filter_suspended: bool = True,
        config: Optional[Dict] = None,
):
    strategy = Strategy(
        factor, rebalance_frequency, start_date, end_date, universe, factor_threshold, filter_suspended, config
    )
    from rqalpha import run_func
    run_func(init=strategy.init, after_trading=strategy.after_trading, config=strategy.config)
