from datetime import date
from math import isclose

from rqalpha import run_func
from rqalpha.apis import order_shares, get_position, buy_open, buy_close, sell_open, sell_close
from rqalpha.environment import Environment
from rqalpha.const import POSITION_DIRECTION


def test_capital_gains_tax_with_stock_1():
    """
    测试单支股票的增值税计算，以及跨年时的重置机制
    """

    config = {
        "base": {
            "start_date": "2025-10-09",
            "end_date": "2026-01-31",
            "accounts": {
                "stock": 1000000,
            },
            "capital_gain_tax_rate": 0.0318
        }
    }

    def init(context):
        context.s1 = "000001.XSHE"
        context.R = 0
        context.K = 0
        context.capital_gains_tax_calculator = context.portfolio._capital_gains_tax_calculator

    def handle_bar(context, bar_dict):
        today = context.now.date()
        if today == date(2025, 10, 9):
            order_shares(context.s1, 1000)
        elif today == date(2025, 10, 23):
            # 股票涨价后卖出，获得盈利
            cost_price = get_position(context.s1).avg_price
            order = order_shares(context.s1, -1000)
            context.R += (order.avg_price - cost_price) * 1000
            assert context.capital_gains_tax_calculator._R == context.R
        elif today == date(2025, 11, 3):
            # 月底进行了税款结算
            assert context.stock_account.cash == context.cash - context.R * 0.0318
            context.R = 0
            assert context.capital_gains_tax_calculator._R == 0
        elif today == date(2025, 11, 20):
            order_shares(context.s1, 1000)
        elif today == date(2025, 11, 24):
            cost_price = get_position(context.s1).avg_price
            order = order_shares(context.s1, -1000)
            context.R += (order.avg_price - cost_price) * 1000
            assert context.capital_gains_tax_calculator._R == context.R
        elif today == date(2025, 12, 1):
            # 月底进行了税款结算，但是因为 R+K 是负的，所以不需要扣税
            assert context.capital_gains_tax_calculator._R == 0
            context.K = context.K + context.R
            context.R = 0
            assert context.capital_gains_tax_calculator._K == context.K
            assert context.stock_account.cash == context.cash
        elif today == date(2026, 1, 5):
            # 跨年，K 重置为 0
            assert context.capital_gains_tax_calculator._K == 0
            context.K = 0
        context.cash = context.stock_account.cash

    run_func(config=config, init=init, handle_bar=handle_bar)


def test_capital_gains_tax_with_stock_2():
    """
    测试多支股票仓位的增值税计算逻辑
    """
    config = {
        "base": {
            "start_date": "2025-11-03",
            "end_date": "2026-01-31",
            "accounts": {
                "stock": 1000000,
            },
            "capital_gain_tax_rate": 0.0318
        }
    }

    def init(context):
        context.s1 = "000001.XSHE"
        context.s2 = "600000.XSHG"
        context.R = 0

    def handle_bar(context, bar_dict):
        today = context.now.date()
        capital_gains_tax_calculator = context.portfolio._capital_gains_tax_calculator
        if today == date(2025, 11, 3):
            order_shares(context.s1, 2000)
        elif today == date(2025, 11, 5):
            order_shares(context.s2, 1000)
        elif today == date(2025, 11, 13):
            cost_price_1 = get_position(context.s1).avg_price
            cost_price_2 = get_position(context.s2).avg_price
            order_1 = order_shares(context.s1, -2000)
            order_2 = order_shares(context.s2, -1000)
            # 两个仓位的收益一正一负，最后的增值税计算以两者的加和为准
            context.R += (order_1.avg_price - cost_price_1) * 2000 + (order_2.avg_price - cost_price_2) * 1000
            assert capital_gains_tax_calculator._R == context.R

        elif today == date(2025, 12, 1):
            # 增值税结算
            assert capital_gains_tax_calculator._R == 0
            assert capital_gains_tax_calculator._K == 0
            assert context.stock_account.cash == context.cash - context.R * 0.0318
            context.R = 0
        
        context.cash = context.stock_account.cash

    run_func(config=config, init=init, handle_bar=handle_bar)


def test_capital_gains_tax_with_futures_1():
    """
    测试期货多头仓位的增值税计算
    """
    config = {
        "base": {
            "start_date": "2025-10-09",
            "end_date": "2026-01-10",
            "accounts": {
                "future": 1000000
            },
            "capital_gain_tax_rate": 0.0318
        }
    }

    def init(context):
        context.f1 = "IM2603"
        context.R = 0
        context.K = 0
        context.capital_gains_tax_calculator = context.portfolio._capital_gains_tax_calculator

    def handle_bar(context, bar_dict):
        today = context.now.date()
        ins = Environment.get_instance().data_proxy.get_active_instrument(context.f1, context.now)
        if today == date(2025, 10, 17):
            buy_open(context.f1, 2)
        elif today == date(2025, 10, 29):
            # 多仓低开高平，盈利
            cost_price = get_position(context.f1).avg_price
            order = sell_close(context.f1, 2)
            context.R += (order.avg_price - cost_price) * 2 * ins.contract_multiplier
            assert context.capital_gains_tax_calculator._R == context.R
        elif today == date(2025, 11, 3):
            # 税款结算
            assert context.capital_gains_tax_calculator._R == 0
            assert context.future_account.cash == context.cash - context.R * 0.0318
            context.R = 0
        
        elif today == date(2025, 11, 10):
            buy_open(context.f1, 2)
        elif today == date(2025, 11, 21):
            # 多仓高开低平，亏损
            cost_price = get_position(context.f1).avg_price
            order = sell_close(context.f1, 2)
            context.R += (order.avg_price - cost_price) * 2 * ins.contract_multiplier
            assert context.capital_gains_tax_calculator._R == context.R
        elif today == date(2025, 12, 1):
            # 税款结算，但是因为 R+K 是负的，所以不需要扣税
            assert context.capital_gains_tax_calculator._R == 0
            context.K = context.K + context.R
            context.R = 0
            assert context.capital_gains_tax_calculator._K == context.K
            assert context.future_account.cash == context.cash
        elif today == date(2026, 1, 5):
            # 跨年，K 重置为 0
            assert context.capital_gains_tax_calculator._K == 0
            context.K = 0

        context.cash = context.future_account.cash
    
    run_func(config=config, init=init, handle_bar=handle_bar)


def test_capital_gains_tax_with_futures_2():
    """
    测试期货多头仓位的增值税计算
    """
    config = {
        "base": {
            "start_date": "2025-10-09",
            "end_date": "2026-01-10",
            "accounts": {
                "future": 1000000
            },
            "capital_gain_tax_rate": 0.0318
        }
    }

    def init(context):
        context.f1 = "IM2603"
        context.R = 0
        context.K = 0
        context.capital_gains_tax_calculator = context.portfolio._capital_gains_tax_calculator

    def handle_bar(context, bar_dict):
        today = context.now.date()
        ins = Environment.get_instance().data_proxy.get_active_instrument(context.f1, context.now)
        if today == date(2025, 10, 9):
            sell_open(context.f1, 2)
        elif today == date(2025, 10, 17):
            # 空仓高开低平，盈利
            cost_price = get_position(context.f1, POSITION_DIRECTION.SHORT).avg_price
            order = buy_close(context.f1, 2)
            context.R += (order.avg_price - cost_price) * 2 * ins.contract_multiplier * (-1)
            assert context.capital_gains_tax_calculator._R == context.R
        elif today == date(2025, 11, 3):
            # 税款结算
            assert context.capital_gains_tax_calculator._R == 0
            assert context.future_account.cash == context.cash - context.R * 0.0318
            context.R = 0

        elif today == date(2025, 11, 21):
            sell_open(context.f1, 2)
        elif today == date(2025, 11, 27):
            # 空仓低开高平，亏损
            cost_price = get_position(context.f1, POSITION_DIRECTION.SHORT).avg_price
            order = buy_close(context.f1, 2)
            context.R += (order.avg_price - cost_price) * 2 * ins.contract_multiplier * (-1)
            assert context.capital_gains_tax_calculator._R == context.R
        elif today == date(2025, 12, 1):
            # 税款结算，但是因为 R+K 是负的，所以不需要扣税
            assert context.capital_gains_tax_calculator._R == 0
            context.K = context.K + context.R
            context.R = 0
            assert context.capital_gains_tax_calculator._K == context.K
            assert context.future_account.cash == context.cash
        elif today == date(2026, 1, 5):
            # 跨年，K 重置为 0
            assert context.capital_gains_tax_calculator._K == 0
            context.K = 0

        context.cash = context.future_account.cash

    run_func(config=config, init=init, handle_bar=handle_bar)


def test_capital_gains_tax_with_mul_type():
    pass