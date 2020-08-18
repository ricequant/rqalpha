# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），
#         您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、
#         本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，
#         否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。v

__config__ = {
    "base": {
        "start_date": "2016-12-01",
        "end_date": "2016-12-31",
        "frequency": "1d",
        "accounts": {
            "stock": 1000000,
            "future": 1000000,
        }
    },
    "extra": {
        "log_level": "error",
    },
    "mod": {
        "sys_progress": {
            "enabled": True,
            "show": True,
        },
    },
}


def test_get_open_order():
    def init(context):
        context.s1 = '000001.XSHE'
        context.limitprice = 8.9
        context.amount = 100
        context.counter = 0
        context.order_id = None

    def handle_bar(context, _):
        context.counter += 1

        order = order_shares(context.s1, context.amount, style=LimitOrder(context.limitprice))
        context.order_id = order.order_id
        if context.counter == 2:
            assert order.order_id in get_open_orders()
        context.counter = 0

    return locals()


def test_submit_order():
    def init(context):
        context.s1 = '000001.XSHE'
        context.amount = 100
        context.fired = False

    def handle_bar(context, bar_dict):
        if not context.fired:
            submit_order(context.s1, context.amount, SIDE.BUY, bar_dict[context.s1].limit_up * 0.99)
            context.fired = True
        if context.fired:
            assert context.portfolio.positions[context.s1].quantity == context.amount

    return locals()


def test_cancel_order():
    def init(context):
        context.s1 = '000001.XSHE'
        context.amount = 100

    def handle_bar(context, bar_dict):
        order = order_shares(context.s1, context.amount, style=LimitOrder(bar_dict[context.s1].limit_down))
        cancel_order(order)
        assert order.order_book_id == context.s1
        assert order.filled_quantity == 0
        assert order.price == bar_dict[context.s1].limit_down
        assert order.status == ORDER_STATUS.CANCELLED

    return locals()


def test_update_universe():
    def init(context):
        context.s1 = '000001.XSHE'
        context.s2 = '600340.XSHG'
        context.order_count = 0
        context.amount = 100

    def handle_bar(context, _):
        context.order_count += 1
        if context.order_count == 1:
            update_universe(context.s2)
            his = history_bars(context.s2, 5, '1d', 'close')
            assert sorted(his.tolist()) == sorted([26.06, 26.13, 26.54, 26.6, 26.86])

    return locals()


def test_subscribe():
    def init(context):
        context.f1 = 'AU88'
        context.amount = 1
        subscribe(context.f1)

    def handle_bar(context, _):
        assert context.f1 in context.universe

    return locals()


def test_unsubscribe():
    def init(context):
        context.f1 = 'AU88'
        context.amount = 1
        subscribe(context.f1)
        unsubscribe(context.f1)

    def handle_bar(context, _):
        assert context.f1 not in context.universe

    return locals()


def test_get_yield_curve():
    def handle_bar(_, __):
        df = get_yield_curve('20161101')
        assert df.iloc[0, 0] == 0.019923
        assert df.iloc[0, 6] == 0.021741

    return locals()


def test_history_bars():
    import numpy

    from rqalpha.utils.exception import RQInvalidArgument

    __config__ = {
        "base": {
            "start_date": "2005-01-04",
            "end_date": "2005-01-31",
        }
    }

    def handle_bar(context, _):
        if str(context.now.date()) == '2005-01-10':
            return_list = history_bars("000001.XSHE", 5, '1d', 'close')
            assert return_list.tolist() == [6.52, 6.46, 6.52, 6.51, 6.59]
            try:
                history_bars("300555.XSHE", 5, "1d")
            except RQInvalidArgument:
                pass
            else:
                raise AssertionError("instrument has not been listed yet, RQInvalidArgument is supposed to be raised")

        return_list = history_bars("000003.XSHE", 100, "1d")
        assert len(return_list) == 0
        assert isinstance(return_list, numpy.ndarray)

    return locals()


def test_all_instruments():
    __config__ = {"base": {
        "start_date": "2017-01-01",
        "end_date": "2017-01-31",
    }}

    def handle_bar(context, _):
        date = context.now.replace(hour=0, minute=0, second=0)
        df = all_instruments('CS')
        assert (df['listed_date'] <= date).all()
        assert (df['de_listed_date'] > date).all()
        # assert all(not is_suspended(o) for o in df['order_book_id'])
        assert (df['type'] == 'CS').all()

        df1 = all_instruments('Stock')
        assert sorted(df['order_book_id']) == sorted(df1['order_book_id'])

        df2 = all_instruments('Future')

        assert (df2['type'] == 'Future').all()
        assert (df2['listed_date'] <= date).all()
        assert (df2['de_listed_date'] >= date).all()

        df3 = all_instruments(['Future', 'Stock'])
        assert sorted(list(df['order_book_id']) + list(df2['order_book_id'])) == sorted(df3['order_book_id'])

    return locals()


def test_instruments_code():
    def init(context):
        context.s1 = '000001.XSHE'

    def handle_bar(context, _):
        ins = instruments(context.s1)
        assert ins.sector_code_name == '金融'
        assert ins.symbol == '平安银行'
        assert ins.order_book_id == context.s1
        assert ins.type == 'CS'

    return locals()


def test_sector():
    def handle_bar(_, __):
        assert len(sector('金融')) >= 80, "sector('金融') 返回结果少于 80 个"

    return locals()


def test_industry():
    def init(context):
        context.s1 = '000001.XSHE'
        context.s2 = '600340.XSHG'

    def handle_bar(context, _):
        ins_1 = instruments(context.s1)
        ins_2 = instruments(context.s2)
        industry_list_1 = industry(ins_1.industry_name)
        industry_list_2 = industry(ins_2.industry_name)
        assert context.s1 in industry_list_1
        assert context.s2 in industry_list_2

    return locals()


def test_get_trading_dates():
    import datetime

    def init(_):
        trading_dates_list = get_trading_dates('2016-12-15', '2017-01-03')
        correct_dates_list = [datetime.date(2016, 12, 15), datetime.date(2016, 12, 16), datetime.date(2016, 12, 19),
                              datetime.date(2016, 12, 20), datetime.date(2016, 12, 21), datetime.date(2016, 12, 22),
                              datetime.date(2016, 12, 23), datetime.date(2016, 12, 26), datetime.date(2016, 12, 27),
                              datetime.date(2016, 12, 28), datetime.date(2016, 12, 29), datetime.date(2016, 12, 30),
                              datetime.date(2017, 1, 3)]
        assert sorted([item.strftime("%Y%m%d") for item in correct_dates_list]) == sorted(
            [item.strftime("%Y%m%d") for item
             in trading_dates_list])

    return locals()


def test_get_previous_trading_date():
    def init(_):
        assert str(get_previous_trading_date('2017-01-03').date()) == '2016-12-30'
        assert str(get_previous_trading_date('2016-01-03').date()) == '2015-12-31'
        assert str(get_previous_trading_date('2015-01-03').date()) == '2014-12-31'
        assert str(get_previous_trading_date('2014-01-03').date()) == '2014-01-02'
        assert str(get_previous_trading_date('2010-01-03').date()) == '2009-12-31'
        assert str(get_previous_trading_date('2009-01-03').date()) == '2008-12-31'
        assert str(get_previous_trading_date('2005-01-05').date()) == '2005-01-04'

    return locals()


def test_get_next_trading_date():
    def init(_):
        assert str(get_next_trading_date('2017-01-03').date()) == '2017-01-04'
        assert str(get_next_trading_date('2007-01-03').date()) == '2007-01-04'

    return locals()


def test_get_dividend():
    def handle_bar(_, __):
        df = get_dividend('000001.XSHE', start_date='20130104')
        df_to_assert = df[df['book_closure_date'] == 20130619]
        assert len(df) >= 4
        assert df_to_assert[0]['dividend_cash_before_tax'] == 1.7
        assert df_to_assert[0]['payable_date'] == 20130620

    return locals()


def test_current_snapshot():
    def handle_bar(_, bar_dict):
        snapshot = current_snapshot('000001.XSHE')
        bar = bar_dict['000001.XSHE']

        assert snapshot.last == bar.close
        for field in (
                "open", "high", "low", "prev_close", "volume", "total_turnover", "order_book_id", "datetime",
                "limit_up", "limit_down"
        ):
            assert getattr(bar, field) == getattr(snapshot, field), "snapshot.{} = {}, bar.{} = {}".format(
                field, getattr(snapshot, field), field, getattr(bar, field)
            )

    return locals()


def test_get_position():
    def assert_position(pos, obid, dir, today_quantity, old_quantity):
        assert pos.order_book_id == obid
        assert pos.direction == dir, "Direction of {} is expected to be {} instead of {}".format(
            pos.order_book_id, dir, pos.direction
        )
        assert pos._today_quantity == today_quantity
        assert pos._old_quantity == old_quantity
        assert pos.quantity == (today_quantity + old_quantity)

    def init(context):
        context.counter = 0
        context.expected_avg_price = None

    def handle_bar(context, bar_dict):
        context.counter += 1

        if context.counter == 1:
            order_shares("000001.XSHE", 300)
        elif context.counter == 5:
            order_shares("000001.XSHE", -100)
        elif context.counter == 10:
            sell_open("RB1701", 5)
        elif context.counter == 15:
            buy_close("RB1701", 2)

        if context.counter == 1:
            pos = [p for p in get_positions() if p.direction == POSITION_DIRECTION.LONG][0]
            assert_position(pos, "000001.XSHE", POSITION_DIRECTION.LONG, 300, 0)
        elif 1 < context.counter < 5:
            pos = [p for p in get_positions() if p.direction == POSITION_DIRECTION.LONG][0]
            assert_position(pos, "000001.XSHE", POSITION_DIRECTION.LONG, 0, 300)
        elif 5 <= context.counter < 10:
            pos = get_position("000001.XSHE", POSITION_DIRECTION.LONG)
            assert_position(pos, "000001.XSHE", POSITION_DIRECTION.LONG, 0, 200)
        elif context.counter == 10:
            pos = get_position("RB1701", POSITION_DIRECTION.SHORT)
            assert_position(pos, "RB1701", POSITION_DIRECTION.SHORT, 5, 0)
        elif 10 < context.counter < 15:
            pos = get_position("RB1701", POSITION_DIRECTION.SHORT)
            assert_position(pos, "RB1701", POSITION_DIRECTION.SHORT, 0, 5)
        elif context.counter >= 15:
            pos = get_position("RB1701", POSITION_DIRECTION.SHORT)
            assert_position(pos, "RB1701", POSITION_DIRECTION.SHORT, 0, 3)

    return locals()


def test_subscribe_event():
    def init(_):
        subscribe_event(EVENT.BEFORE_TRADING, on_before_trading)

    def before_trading(context):
        context.before_trading_ran = True

    def on_before_trading(context, _):
        assert context.before_trading_ran
        context.before_trading_ran = False

    return locals()


def test_order():
    __config__ = {
        "base": {
            "accounts": {
                "stock": 100000000,
                "future": 100000000,
            }
        },
    }

    def init(context):
        context.counter = 0

        context.stock = '000001.XSHE'
        context.future = 'IF88'

    def handle_bar(context, bar_dict):
        context.counter += 1
        if context.counter == 1:
            order(context.stock, 200)
            order(context.future, -100)
        elif context.counter == 2:
            assert get_position(context.stock).quantity == 200
            assert get_position(context.future, POSITION_DIRECTION.SHORT).quantity == 100
            order(context.stock, -100)
            order(context.future, 200)
        elif context.counter == 3:
            assert get_position(context.stock).quantity == 100
            assert get_position(context.future, POSITION_DIRECTION.LONG).quantity == 100
            assert get_position(context.future, POSITION_DIRECTION.SHORT).quantity == 0

    return locals()


def test_order_to():
    __config__ = {
        "base": {
            "accounts": {
                "stock": 100000000,
                "future": 100000000,
            }
        },
    }

    def init(context):
        context.counter = 0

        context.stock = '000001.XSHE'
        context.future = 'IF88'

    def handle_bar(context, bar_dict):
        context.counter += 1
        if context.counter == 1:
            order_to(context.stock, 200)
            order_to(context.future, -100)
        elif context.counter == 2:
            assert get_position(context.stock).quantity == 200
            assert get_position(context.future, POSITION_DIRECTION.SHORT).quantity == 100
            order_to(context.stock, 100)
            order_to(context.future, 100)
        elif context.counter == 3:
            assert get_position(context.stock).quantity == 100
            assert get_position(context.future, POSITION_DIRECTION.LONG).quantity == 100
            assert get_position(context.future, POSITION_DIRECTION.SHORT).quantity == 0

    return locals()


def test_deposit():
    __config__ = {
        "base": {
            "accounts": {
                "stock": 100000000,
                "future": 100000000,
            }
        },
    }

    def init(context):
        context.counter = 0

        context.stock = '000001.XSHE'
        context.future = 'IF88'

    def handle_bar(context, bar_dict):
        context.counter += 1
        if context.counter == 1:
            order(context.stock, 200)
            order(context.future, -100)

        elif context.counter == 2:
            unit_net_value = context.portfolio.unit_net_value
            units = context.portfolio.units
            total_value = context.portfolio.total_value
            cash = context.portfolio.accounts["STOCK"].cash
            deposit("STOCK", 50000000)
            assert int(context.portfolio.accounts["STOCK"].cash) == int(cash) + 50000000
            assert context.portfolio.units > units
            assert context.portfolio.total_value > total_value
            assert context.portfolio.unit_net_value == unit_net_value

        elif context.counter == 3:
            unit_net_value = context.portfolio.unit_net_value
            units = context.portfolio.units
            total_value = context.portfolio.total_value
            cash = context.portfolio.accounts["FUTURE"].cash
            flag = withdraw("FUTURE", 50000000)
            assert context.portfolio.accounts["FUTURE"].cash == cash - 50000000
            assert context.portfolio.units < units
            assert context.portfolio.total_value < total_value
            assert context.portfolio.unit_net_value == unit_net_value
        elif context.counter == 6:
            try:
                flag = withdraw("FUTURE", 100000000)
            except ValueError as err:
                assert True, "捕获输入异常"
            else:
                assert False, "未报出当前账户可取出金额不足异常"

    return locals()
