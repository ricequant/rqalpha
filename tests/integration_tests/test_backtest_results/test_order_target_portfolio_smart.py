import os
from typing import cast

from numpy import isinf

from rqalpha.mod.rqalpha_mod_sys_accounts.api.api_stock import order_target_portfolio_smart

from pandas import read_csv, Series


def test_order_target_portfolio_smart(resources_path, run_and_assert_result):
    def open_auction(context, bar_dict):
        if context.now.strftime("%Y%m%d") in [
            "20241104", "20241108", "20241111", "20241118"
        ]:
            # 调仓日
            target_weights: Series = cast(Series, read_csv(os.path.join(
                resources_path, context.now.strftime("%Y-%m-%d.csv")
            )).set_index("order_book_id")["weight"])
            order_target_portfolio_smart(target_weights, None)
        
            # 检查成交情况
            total_value = context.portfolio.total_value
            account = context.portfolio.stock_account
            actual_weights = Series({
                p.order_book_id: p.market_value / total_value for p in account.get_positions()
            })

            total_weights_diff = abs(actual_weights.sum() - target_weights.sum())
            assert total_weights_diff <= 0.001

            weights_diff = (actual_weights.div(target_weights, fill_value=0) - 1).abs()
            
            open_close_failed = (isinf(weights_diff) | (weights_diff >= 1))
            assert open_close_failed.sum() <= 3  # 开平仓失败

            assert weights_diff.median() < 0.005  # 0.6%
            assert weights_diff.quantile(0.75) < 0.01  # 1%



    config = {
        "base": {
            "start_date": "2024-11-04",
            "end_date": "2024-11-22",
            "frequency": "1d",
            "matching_type": "current_bar",
            "benchmark": None,
            "accounts": {
                "stock": 50000000,  # 1e
            }
        },
        "extra": {
            "log_level": "error",
        },
        "mod": {
            "sys_analyser": {
                "plot": True
            }
        }
    }

    return run_and_assert_result(config=config, open_auction=open_auction)