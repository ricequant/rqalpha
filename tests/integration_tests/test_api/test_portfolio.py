from datetime import date
from math import isclose

from rqalpha import run_func
from rqalpha.apis import order_shares, get_position, order_value, buy_open, buy_close, sell_open, sell_close, withdraw
from rqalpha.environment import Environment
from rqalpha.const import DEFAULT_ACCOUNT_TYPE


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
        context.monthly_realized_pnl = 0
        context.annual_deductible_balance = 0

    def handle_bar(context, bar_dict):
        today = context.now.date()
        if today == date(2025, 10, 9):
            order_shares(context.s1, 1000)
        elif today == date(2025, 10, 23):
            # 股票涨价后卖出，获得盈利
            cost_price = get_position(context.s1).avg_price
            order = order_shares(context.s1, -1000)
            context.monthly_realized_pnl += (order.avg_price - cost_price) * 1000
            assert context.portfolio._monthly_realized_pnl == context.monthly_realized_pnl
        elif today == date(2025, 11, 3):
            # 月底进行了税款结算
            assert context.stock_account.cash == context.cash - context.monthly_realized_pnl * 0.0318
            context.monthly_realized_pnl = 0
            assert context.portfolio._monthly_realized_pnl == 0
        elif today == date(2025, 11, 20):
            order_shares(context.s1, 1000)
        elif today == date(2025, 11, 24):
            cost_price = get_position(context.s1).avg_price
            order = order_shares(context.s1, -1000)
            context.monthly_realized_pnl += (order.avg_price - cost_price) * 1000
            assert context.portfolio._monthly_realized_pnl == context.monthly_realized_pnl
        elif today == date(2025, 12, 1):
            # 月底进行了税款结算，但是因为 tax_basis 是负的，所以不需要扣税
            assert context.portfolio._monthly_realized_pnl == 0
            context.annual_deductible_balance = context.annual_deductible_balance + context.monthly_realized_pnl
            context.monthly_realized_pnl = 0
            assert context.portfolio._annual_deductible_balance == context.annual_deductible_balance
            assert context.stock_account.cash == context.cash
        elif today == date(2026, 1, 5):
            # 跨年，K 重置为 0
            assert context.portfolio._annual_deductible_balance == 0
            context.annual_deductible_balance = 0
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
        context.monthly_realized_pnl = 0

    def handle_bar(context, bar_dict):
        today = context.now.date()
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
            context.monthly_realized_pnl += (order_1.avg_price - cost_price_1) * 2000 + (order_2.avg_price - cost_price_2) * 1000
            assert context.portfolio._monthly_realized_pnl == context.monthly_realized_pnl

        elif today == date(2025, 12, 1):
            # 增值税结算
            assert context.portfolio._monthly_realized_pnl == 0
            assert context.portfolio._annual_deductible_balance == 0
            assert context.stock_account.cash == context.cash - context.monthly_realized_pnl * 0.0318
            context.monthly_realized_pnl = 0
        
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
        context.monthly_realized_pnl = 0
        context.annual_deductible_balance = 0

    def handle_bar(context, bar_dict):
        today = context.now.date()
        ins = Environment.get_instance().data_proxy.get_active_instrument(context.f1, context.now)
        if today == date(2025, 10, 17):
            buy_open(context.f1, 2)  # 开仓价为 6805
        elif today == date(2025, 10, 29):
            # 多仓低开高平，盈利
            order = sell_close(context.f1, 2)
            context.monthly_realized_pnl += (order.avg_price - 6805) * 2 * ins.contract_multiplier
            assert context.portfolio._monthly_realized_pnl == context.monthly_realized_pnl
        elif today == date(2025, 11, 3):
            # 税款结算
            assert context.portfolio._monthly_realized_pnl == 0
            assert context.future_account.cash == context.cash - context.monthly_realized_pnl * 0.0318
            context.monthly_realized_pnl = 0
        
        elif today == date(2025, 11, 10):
            buy_open(context.f1, 2)  # 开仓价格为 7199.2
        elif today == date(2025, 11, 21):
            # 多仓高开低平，亏损
            order = sell_close(context.f1, 2)
            context.monthly_realized_pnl += (order.avg_price - 7199.2) * 2 * ins.contract_multiplier
            assert context.portfolio._monthly_realized_pnl == context.monthly_realized_pnl
        elif today == date(2025, 12, 1):
            # 税款结算，但是因为 tax_basis 是负的，所以不需要扣税
            assert context.portfolio._monthly_realized_pnl == 0
            context.annual_deductible_balance = context.annual_deductible_balance + context.monthly_realized_pnl
            context.monthly_realized_pnl = 0
            assert context.portfolio._annual_deductible_balance == context.annual_deductible_balance
            assert context.future_account.cash == context.cash
        elif today == date(2026, 1, 5):
            # 跨年，annual_deductible_balance 重置为 0
            assert context.portfolio._annual_deductible_balance == 0
            context.annual_deductible_balance = 0

        context.cash = context.future_account.cash
    
    run_func(config=config, init=init, handle_bar=handle_bar)


def test_capital_gains_tax_with_futures_2():
    """
    测试期货空头仓位的增值税计算
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
        context.monthly_realized_pnl = 0
        context.annual_deductible_balance = 0

    def handle_bar(context, bar_dict):
        today = context.now.date()
        ins = Environment.get_instance().data_proxy.get_active_instrument(context.f1, context.now)
        if today == date(2025, 10, 9):
            sell_open(context.f1, 2)  # 开空仓价格为 7229
        elif today == date(2025, 10, 17):
            # 空仓高开低平，盈利
            order = buy_close(context.f1, 2)
            context.monthly_realized_pnl += (order.avg_price - 7229) * 2 * ins.contract_multiplier * (-1)
            assert context.portfolio._monthly_realized_pnl == context.monthly_realized_pnl
        elif today == date(2025, 11, 3):
            # 税款结算
            assert context.portfolio._monthly_realized_pnl == 0
            assert context.future_account.cash == context.cash - context.monthly_realized_pnl * 0.0318
            context.monthly_realized_pnl = 0

        elif today == date(2025, 11, 21):
            sell_open(context.f1, 2)  # 开空仓价格为 6802.8
        elif today == date(2025, 11, 27):
            # 空仓低开高平，亏损
            order = buy_close(context.f1, 2)
            context.monthly_realized_pnl += (order.avg_price - 6802.8) * 2 * ins.contract_multiplier * (-1)
            assert context.portfolio._monthly_realized_pnl == context.monthly_realized_pnl
        elif today == date(2025, 12, 1):
            # 税款结算，但是因为 tax_basis 是负的，所以不需要扣税
            assert context.portfolio._monthly_realized_pnl == 0
            context.annual_deductible_balance = context.annual_deductible_balance + context.monthly_realized_pnl
            context.monthly_realized_pnl = 0
            assert context.portfolio._annual_deductible_balance == context.annual_deductible_balance
            assert context.future_account.cash == context.cash
        elif today == date(2026, 1, 5):
            # 跨年，annual_deductible_balance 重置为 0
            assert context.portfolio._annual_deductible_balance == 0
            context.annual_deductible_balance = 0

        context.cash = context.future_account.cash

    run_func(config=config, init=init, handle_bar=handle_bar)


def test_capital_gains_tax_with_mul_type_1():
    """
    测试股票期货混合仓位的增值税计算，股票账户资金不够完全扣除时，会将剩余部分在期货账户中扣除
    """
    config = {
        "base": {
            "start_date": "2025-10-09",
            "end_date": "2026-01-31",
            "accounts": {
                "stock": 100000,
                "future": 200000,
            },
            "capital_gain_tax_rate": 0.0318
        }
    }

    def init(context):
        context.s1 = "000001.XSHE"
        context.f1 = "IM2603"
        context.monthly_realized_pnl = 0
        context.annual_deductible_balance = 0

    def handle_bar(context, bar_dict):
        today = context.now.date()

        if today == date(2025, 10, 13):
            order_value(context.s1, 100000)
            buy_open(context.f1, 1)  # 开仓价为 7077.6 元
        elif today == date(2025, 11, 13):
            pos = get_position(context.s1)
            s_quantity, cost_price = pos.quantity, pos.avg_price
            order = order_shares(context.s1, -s_quantity)
            context.monthly_realized_pnl += (order.avg_price - cost_price) * s_quantity
            assert context.portfolio._monthly_realized_pnl == context.monthly_realized_pnl
            
            order = sell_close(context.f1, 1)
            ins = Environment.get_instance().data_proxy.get_active_instrument(context.f1, context.now)
            context.monthly_realized_pnl += (order.avg_price - 7077.6) * 1 * ins.contract_multiplier
            assert context.portfolio._monthly_realized_pnl == context.monthly_realized_pnl
        elif today == date(2025, 11, 14):
            # 将股票账户的资金用完，测试增值税在两个账户之间的扣除
            order_value(context.s1, context.stock_account.cash)
        elif today == date(2025, 12, 1):
            # 税款结算
            assert context.portfolio._monthly_realized_pnl == 0
            # 股票账户剩余现金 960+ 元，需缴纳税款 1210+ 元，优先扣除股票账户，剩余的从期货账户扣除
            assert context.stock_account.cash == 0
            futures_account_deduction = context.monthly_realized_pnl * 0.0318 - context.stock_cash
            assert context.future_account.cash == context.futures_cash - futures_account_deduction

        context.stock_cash = context.stock_account.cash
        context.futures_cash = context.future_account.cash

    run_func(config=config, init=init, handle_bar=handle_bar)


def test_capital_gains_tax_with_mul_type_2():
    """
    测试股票期货混合仓位的增值税计算，股票和期货账户资金加总不够完全扣除时，会将剩余部分在股票账户中扣除，允许股票账户最终为负数
    """
    config = {
        "base": {
            "start_date": "2025-10-09",
            "end_date": "2026-01-31",
            "accounts": {
                "stock": 100000,
                "future": 200000,
            },
            "capital_gain_tax_rate": 0.0318
        }
    }

    def init(context):
        context.s1 = "000001.XSHE"
        context.f1 = "IM2603"
        context.monthly_realized_pnl = 0
        context.annual_deductible_balance = 0

    def handle_bar(context, bar_dict):
        today = context.now.date()

        if today == date(2025, 10, 13):
            order_value(context.s1, 100000)
            buy_open(context.f1, 1)  # 开仓价为 7077.6 元
        elif today == date(2025, 11, 13):
            pos = get_position(context.s1)
            s_quantity, cost_price = pos.quantity, pos.avg_price
            order = order_shares(context.s1, -s_quantity)
            context.monthly_realized_pnl += (order.avg_price - cost_price) * s_quantity
            assert context.portfolio._monthly_realized_pnl == context.monthly_realized_pnl
            
            order = sell_close(context.f1, 1)
            ins = Environment.get_instance().data_proxy.get_active_instrument(context.f1, context.now)
            context.monthly_realized_pnl += (order.avg_price - 7077.6) * 1 * ins.contract_multiplier
            assert context.portfolio._monthly_realized_pnl == context.monthly_realized_pnl
        elif today == date(2025, 11, 14):
            # 将两个账户的资金都出金至只剩下 100 元
            withdraw(DEFAULT_ACCOUNT_TYPE.STOCK, context.stock_account.cash - 100)
            withdraw(DEFAULT_ACCOUNT_TYPE.FUTURE, context.future_account.cash - 100)
        elif today == date(2025, 12, 1):
            # 税款结算
            assert context.portfolio._monthly_realized_pnl == 0
            # 两个账户剩余总资金 200 元，需缴纳税款 1210+ 元，结果应为期货账户为 0，股票账户 -1010+
            assert context.future_account.cash == 0
            assert context.stock_account.cash == (context.stock_cash + context.futures_cash) - context.monthly_realized_pnl * 0.0318

        context.stock_cash = context.stock_account.cash
        context.futures_cash = context.future_account.cash

    run_func(config=config, init=init, handle_bar=handle_bar)