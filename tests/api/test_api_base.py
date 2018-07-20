#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2017 Ricequant, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from rqalpha.api import *

from ..utils import make_test_strategy_decorator

test_strategies = []

as_test_strategy = make_test_strategy_decorator({
        "base": {
            "start_date": "2016-12-01",
            "end_date": "2016-12-31",
            "frequency": "1d",
            "accounts": {
                "stock": 1000000
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
    }, test_strategies)


@as_test_strategy()
def test_get_order():
    def init(context):
        context.s1 = '000001.XSHE'
        context.amount = 100

    def handle_bar(context, _):
        order_id = order_shares(context.s1, context.amount, style=LimitOrder(9.5))
        order = get_order(order_id)
        assert order.order_book_id == context.s1
        assert order.quantity == context.amount
        assert order.unfilled_quantity + order.filled_quantity == order.quantity
    return init, handle_bar


@as_test_strategy()
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
    return init, handle_bar


@as_test_strategy()
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
    return init, handle_bar


@as_test_strategy()
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
    return init, handle_bar


@as_test_strategy()
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
    return init, handle_bar


@as_test_strategy()
def test_subscribe():
    def init(context):
        context.f1 = 'AU88'
        context.amount = 1
        subscribe(context.f1)

    def handle_bar(context, _):
        assert context.f1 in context.universe
    return init, handle_bar


@as_test_strategy()
def test_unsubscribe():
    def init(context):
        context.f1 = 'AU88'
        context.amount = 1
        subscribe(context.f1)
        unsubscribe(context.f1)

    def handle_bar(context, _):
        assert context.f1 not in context.universe
    return init, handle_bar


@as_test_strategy
def test_get_yield_curve():
    def handle_bar(_, __):
        df = get_yield_curve('20161101')
        assert df.iloc[0, 0] == 0.019923
        assert df.iloc[0, 6] == 0.021741
    return handle_bar


def test_history_bars():
    def handle_bar(context, _):
        return_list = history_bars(context.s1, 5, '1d', 'close')
        if str(context.now.date()) == '2016-12-29':
            assert return_list.tolist() == [9.08, 9.12, 9.08, 9.06, 9.08]
    return handle_bar


@as_test_strategy()
def test_all_instruments():
    def handle_bar(context, _):
        date = context.now.replace(hour=0, minute=0, second=0)
        df = all_instruments('CS')
        assert (df['listed_date'] <= date).all()
        assert (df['de_listed_date'] >= date).all()
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
    return handle_bar


@as_test_strategy()
def test_instruments_code():
    def init(context):
        context.s1 = '000001.XSHE'

    def handle_bar(context, _):
        ins = instruments(context.s1)
        assert ins.sector_code_name == '金融'
        assert ins.symbol == '平安银行'
        assert ins.order_book_id == context.s1
        assert ins.type == 'CS'
    return init, handle_bar


@as_test_strategy()
def test_sector():
    def handle_bar(_, __):
        assert len(sector('金融')) >= 80, "sector('金融') 返回结果少于 80 个"
    return handle_bar


@as_test_strategy()
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
    return init, handle_bar


@as_test_strategy()
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
    return init


@as_test_strategy()
def test_get_previous_trading_date():
    def init(_):
        assert str(get_previous_trading_date('2017-01-03').date()) == '2016-12-30'
        assert str(get_previous_trading_date('2016-01-03').date()) == '2015-12-31'
        assert str(get_previous_trading_date('2015-01-03').date()) == '2014-12-31'
        assert str(get_previous_trading_date('2014-01-03').date()) == '2014-01-02'
        assert str(get_previous_trading_date('2010-01-03').date()) == '2009-12-31'
        assert str(get_previous_trading_date('2009-01-03').date()) == '2008-12-31'
        assert str(get_previous_trading_date('2005-01-05').date()) == '2005-01-04'
    return init


@as_test_strategy()
def test_get_next_trading_date():
    def init(_):
        assert str(get_next_trading_date('2017-01-03').date()) == '2017-01-04'
        assert str(get_next_trading_date('2007-01-03').date()) == '2007-01-04'
    return init


@as_test_strategy()
def test_get_dividend():
    def handle_bar(_, __):
        df = get_dividend('000001.XSHE', start_date='20130104')
        df_to_assert = df[df['book_closure_date'] == 20130619]
        assert len(df) >= 4
        assert df_to_assert[0]['dividend_cash_before_tax'] == 1.7
        assert df_to_assert[0]['payable_date'] == 20130620
    return handle_bar


@as_test_strategy()
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
    return handle_bar
