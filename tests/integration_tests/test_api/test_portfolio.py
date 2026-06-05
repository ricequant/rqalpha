from datetime import date
from math import isclose

from rqalpha import run_func
from rqalpha.apis import order_shares, get_position, order_value, buy_open, buy_close, sell_open, sell_close, withdraw
from rqalpha.const import DEFAULT_ACCOUNT_TYPE


def _capital_gains_tax_config(start_date, end_date, accounts):
    return {
        "base": {
            "start_date": start_date,
            "end_date": end_date,
            "accounts": accounts,
            "capital_gain_tax_rate": 0.0318,
        }
    }


def _run_sys_analyser(config, init, handle_bar):
    return run_func(config=config, init=init, handle_bar=handle_bar)["sys_analyser"]


def _assert_capital_gains_tax_events(result, expected_events):
    events = result.get("portfolio_event")
    if not expected_events:
        assert events is None or events.empty
        return
    assert events is not None
    assert len(events) == len(expected_events)
    assert list(events["event_category"]) == ["taxes_paid"] * len(expected_events)
    assert list(events["remark"]) == ["capital_gains"] * len(expected_events)
    assert list(events["delta_quantity"]) == [0] * len(expected_events)
    for (_, event), (trading_date, delta_amount) in zip(events.iterrows(), expected_events):
        assert event["trading_date"] == trading_date
        assert isclose(event["delta_amount"], delta_amount, rel_tol=0, abs_tol=1e-6)


def _cash(result, account_type, trading_date):
    return float(result[f"{account_type}_account"].loc[trading_date, "cash"])


def _assert_cash_delta(result, account_type, before_date, after_date, delta_amount):
    actual_delta = _cash(result, account_type, before_date) - _cash(result, account_type, after_date)
    assert isclose(actual_delta, delta_amount, rel_tol=0, abs_tol=1e-4)


def _assert_cash_unchanged(result, account_type, before_date, after_date):
    assert isclose(
        _cash(result, account_type, before_date),
        _cash(result, account_type, after_date),
        rel_tol=0,
        abs_tol=1e-4,
    )


def test_capital_gains_tax_with_stocks():
    """
    测试多支股票仓位的增值税计算，以及跨年时的重置机制
    """

    config = _capital_gains_tax_config("2025-10-09", "2026-01-31", {"stock": 1000000})

    def init(context):
        context.s1 = "000001.XSHE"
        context.s2 = "600000.XSHG"

    def handle_bar(context, bar_dict):
        today = context.now.date()
        if today == date(2025, 10, 9):
            order_shares(context.s1, 1000)
        elif today == date(2025, 10, 10):
            order_shares(context.s2, 1000)
        elif today == date(2025, 10, 23):
            # 两个仓位的收益最后以加和为准计算增值税
            order_shares(context.s1, -1000)
            order_shares(context.s2, -1000)
        elif today == date(2025, 11, 20):
            order_shares(context.s1, 1000)
            order_shares(context.s2, 1000)
        elif today == date(2025, 11, 24):
            order_shares(context.s1, -1000)
            order_shares(context.s2, -1000)
        elif today == date(2026, 1, 5):
            order_shares(context.s1, 1000)
            order_shares(context.s2, 1000)
        elif today == date(2026, 1, 15):
            order_shares(context.s1, -1000)
            order_shares(context.s2, -1000)

    result = _run_sys_analyser(config, init, handle_bar)
    _assert_capital_gains_tax_events(result, [("2025-10-31", 50.7528)])
    _assert_cash_delta(result, "stock", "2025-10-30", "2025-10-31", 50.7528)
    _assert_cash_unchanged(result, "stock", "2025-11-27", "2025-11-28")
    _assert_cash_unchanged(result, "stock", "2026-01-29", "2026-01-30")


def test_capital_gains_tax_with_futures():
    """
    测试期货多头和空头仓位的增值税计算
    """
    config = _capital_gains_tax_config("2025-10-09", "2026-01-10", {"future": 1000000})

    def init(context):
        context.f1 = "IM2603"

    def handle_bar(context, bar_dict):
        today = context.now.date()
        if today == date(2025, 10, 9):
            sell_open(context.f1, 2)  # 开空仓价格为 7229
        elif today == date(2025, 10, 17):
            # 空仓高开低平，盈利
            buy_close(context.f1, 2)
            buy_open(context.f1, 2)  # 开仓价为 6805
        elif today == date(2025, 10, 29):
            # 多仓低开高平，盈利
            sell_close(context.f1, 2)
        elif today == date(2025, 11, 10):
            buy_open(context.f1, 2)  # 开仓价格为 7199.2
        elif today == date(2025, 11, 21):
            # 多仓高开低平，亏损
            sell_close(context.f1, 2)
            sell_open(context.f1, 2)  # 开空仓价格为 6802.8
        elif today == date(2025, 11, 27):
            # 空仓低开高平，亏损
            buy_close(context.f1, 2)

    result = _run_sys_analyser(config, init, handle_bar)
    _assert_capital_gains_tax_events(result, [("2025-10-31", 10888.32)])
    _assert_cash_delta(result, "future", "2025-10-30", "2025-10-31", 10888.32)
    _assert_cash_unchanged(result, "future", "2025-11-28", "2025-12-01")


def test_capital_gains_tax_with_mul_type_1():
    """
    测试股票期货混合仓位的增值税计算，股票账户资金不够完全扣除时，会将剩余部分在期货账户中扣除
    """
    config = _capital_gains_tax_config("2025-10-09", "2026-01-31", {"stock": 100000, "future": 200000})

    def init(context):
        context.s1 = "000001.XSHE"
        context.f1 = "IM2603"

    def handle_bar(context, bar_dict):
        today = context.now.date()

        if today == date(2025, 10, 13):
            order_value(context.s1, 100000)
            buy_open(context.f1, 1)  # 开仓价为 7077.6 元
        elif today == date(2025, 11, 13):
            pos = get_position(context.s1)
            order_shares(context.s1, -pos.quantity)
            sell_close(context.f1, 1)
        elif today == date(2025, 11, 14):
            # 将股票账户的资金用完，测试增值税在两个账户之间的扣除
            order_value(context.s1, context.stock_account.cash)

    result = _run_sys_analyser(config, init, handle_bar)
    tax_amount = 1219.31376
    _assert_capital_gains_tax_events(result, [("2025-11-28", tax_amount)])
    assert isclose(_cash(result, "stock", "2025-11-28"), 0, rel_tol=0, abs_tol=1e-4)
    _assert_cash_delta(result, "future", "2025-11-27", "2025-11-28", tax_amount - _cash(result, "stock", "2025-11-27"))


def test_capital_gains_tax_with_mul_type_2():
    """
    测试股票期货混合仓位的增值税计算，股票和期货账户资金加总不够完全扣除时，会将剩余部分在股票账户中扣除，允许股票账户最终为负数
    """
    config = _capital_gains_tax_config("2025-10-09", "2026-01-31", {"stock": 100000, "future": 200000})

    def init(context):
        context.s1 = "000001.XSHE"
        context.f1 = "IM2603"

    def handle_bar(context, bar_dict):
        today = context.now.date()

        if today == date(2025, 10, 13):
            order_value(context.s1, 100000)
            buy_open(context.f1, 1)  # 开仓价为 7077.6 元
        elif today == date(2025, 11, 13):
            pos = get_position(context.s1)
            order_shares(context.s1, -pos.quantity)
            sell_close(context.f1, 1)
        elif today == date(2025, 11, 14):
            # 将两个账户的资金都出金至只剩下 100 元
            withdraw(DEFAULT_ACCOUNT_TYPE.STOCK, context.stock_account.cash - 100)
            withdraw(DEFAULT_ACCOUNT_TYPE.FUTURE, context.future_account.cash - 100)

    result = _run_sys_analyser(config, init, handle_bar)
    tax_amount = 1219.31376
    _assert_capital_gains_tax_events(result, [("2025-11-28", tax_amount)])
    assert isclose(_cash(result, "future", "2025-11-28"), 0, rel_tol=0, abs_tol=1e-4)
    assert isclose(_cash(result, "stock", "2025-11-28"), 200 - tax_amount, rel_tol=0, abs_tol=1e-4)
