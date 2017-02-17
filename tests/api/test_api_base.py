#!/usr/bin/env python
# encoding: utf-8
import inspect

def test_get_order():
    from rqalpha.api import order_shares, get_order
    def init(context):
        context.s1 = '000001.XSHE'
        context.amount = 100

    def handle_bar(context, bar_dict):
        order_id = order_shares(context.s1, context.amount, style=LimitOrder(9.5))
        order = get_order(order_id)
        assert order.order_book_id == context.s1
        assert order.quantity == context.amount
        assert order.unfilled_quantity + order.filled_quantity == order.quantity
test_get_order_code_new = "".join(inspect.getsourcelines(test_get_order)[0])


def test_get_open_order():
    from rqalpha.api import order_shares, get_open_orders, get_order
    def init(context):
        context.s1 = '000001.XSHE'
        context.limitprice = 8.9
        context.amount = 100
        context.counter = 0
        context.order_id = None

    def handle_bar(context, bar_dict):
        context.counter += 1

        order = order_shares(context.s1, context.amount, style=LimitOrder(context.limitprice))
        context.order_id = order.order_id
        print('cash: ', context.portfolio.cash)
        print('check_get_open_orders done')
        print(order.order_id)
        print(get_open_orders().keys())
        print(get_open_orders())
        print(get_order(order.order_id))
        if context.counter == 2:
            assert order.order_id in get_open_orders()
        context.counter = 0
test_get_open_order_code_new = "".join(inspect.getsourcelines(test_get_open_order)[0])


def test_cancel_order():
    from rqalpha.api import order_shares, cancel_order, get_order
    def init(context):
        context.s1 = '000001.XSHE'
        context.limitprice = 8.59
        context.amount = 100

    def handle_bar(context, bar_dict):
        order_id = order_shares(context.s1, context.amount, style=LimitOrder(context.limitprice))
        cancel_order(order_id)
        order = get_order(order_id)
        assert order.order_book_id == context.s1
        assert order.filled_quantity == 0
        return order_id
        assert order.price == context.limitprice
test_cancel_order_code_new = "".join(inspect.getsourcelines(test_cancel_order)[0])


def test_update_universe():
    from rqalpha.api import update_universe, history_bars
    def init(context):
        context.s1 = '000001.XSHE'
        context.s2 = '600340.XSHG'
        context.order_count = 0
        context.amount = 100

    def handle_bar(context, bar_dict):
        context.order_count += 1
        if context.order_count == 1:
            update_universe(context.s2)
            his = history_bars(context.s2, 5, '1d', 'close')
            print(sorted(his.tolist()))
            print(sorted([24.1, 23.71, 23.82, 23.93, 23.66]))
            assert sorted(his.tolist()) == sorted([26.06, 26.13, 26.54, 26.6, 26.86])
test_update_universe_code_new = "".join(inspect.getsourcelines(test_update_universe)[0])


def test_subscribe():
    from rqalpha.api import subscribe
    def init(context):
        context.f1 = 'AU88'
        context.amount = 1
        subscribe(context.f1)

    def handle_bar(context, bar_dict):
        assert context.f1 in context.universe
test_subscribe_code_new = "".join(inspect.getsourcelines(test_subscribe)[0])


def test_unsubscribe():
    from rqalpha.api import subscribe, unsubscribe
    def init(context):
        context.f1 = 'AU88'
        context.amount = 1
        subscribe(context.f1)
        unsubscribe(context.f1)

    def handle_bar(context, bar_dict):
        assert context.f1 not in context.universe
test_unsubscribe_code_new = "".join(inspect.getsourcelines(test_unsubscribe)[0])


def test_get_yield_curve():
    from rqalpha.api import get_yield_curve
    def init(context):
        pass

    def handle_bar(context, bar_dict):
        df = get_yield_curve('20161101')
        assert df.iloc[0, 0] == 0.019923
        assert df.iloc[0, 6] == 0.021741
test_get_yield_curve_code_new = "".join(inspect.getsourcelines(test_get_yield_curve)[0])


def test_history_bars():
    from rqalpha.api import history_bars
    def init(context):
        context.s1 = '000001.XSHE'
        pass

    def handle_bar(context, bar_dict):
        return_list = history_bars(context.s1, 5, '1d', 'close')
        if str(context.now.date()) == '2016-12-29':
            assert return_list.tolist() == [9.08, 9.1199, 9.08, 9.06, 9.08]
test_history_bars_code_new = "".join(inspect.getsourcelines(test_history_bars)[0])


def test_all_instruments():
    from rqalpha.api import all_instruments
    def init(context):
        pass

    def handle_bar(context, bar_dict):
        df = all_instruments('FenjiA')
        df_to_assert = df.loc[df['order_book_id'] == '150247.XSHE']
        assert df_to_assert.iloc[0, 0] == 'CMAJ'
        assert df_to_assert.iloc[0, 7] == '工银中证传媒A'
        assert all_instruments().shape >= (8000, 4)
        assert all_instruments('CS').shape >= (3000, 16)
        assert all_instruments('ETF').shape >= (120, 9)
        assert all_instruments('LOF').shape >= (130, 9)
        assert all_instruments('FenjiMu').shape >= (10, 9)
        assert all_instruments('FenjiA').shape >= (120, 9)
        assert all_instruments('FenjiB').shape >= (140, 9)
        assert all_instruments('INDX').shape >= (500, 8)
        assert all_instruments('Future').shape >= (3500, 16)
test_all_instruments_code_new = "".join(inspect.getsourcelines(test_all_instruments)[0])

def test_instruments_code():
    from rqalpha.api import instruments
    def init(context):
        context.s1 = '000001.XSHE'
        pass

    def handle_bar(context, bar_dict):
        print('hello')
        ins = instruments(context.s1)
        assert ins.sector_code_name == '金融'
        assert ins.symbol == '平安银行'
        assert ins.order_book_id == context.s1
        assert ins.type == 'CS'
        print('world')
test_instruments_code_new = "".join(inspect.getsourcelines(test_instruments_code)[0])


def test_sector():
    from rqalpha.api import sector
    def init(context):
        pass

    def handle_bar(context, bar_dict):
        assert len(sector('金融')) >= 180
test_sector_code_new = "".join(inspect.getsourcelines(test_sector)[0])


def test_industry():
    from rqalpha.api import industry, instruments
    def init(context):
        context.s1 = '000001.XSHE'
        context.s2 = '600340.XSHG'

    def handle_bar(context, bar_dict):
        ins_1 = instruments(context.s1)
        ins_2 = instruments(context.s2)
        industry_list_1 = industry(ins_1.industry_name)
        industry_list_2 = industry(ins_2.industry_name)
        assert context.s1 in industry_list_1
        assert context.s2 in industry_list_2
test_industry_code_new = "".join(inspect.getsourcelines(test_industry)[0])


def test_concept():
    from rqalpha.api import concept, instruments
    def init(context):
        context.s1 = '000002.XSHE'

    def handle_bar(context, bar_dict):
        ins = instruments(context.s1)
        concept_list = concept(ins.concept_names[:4])  # 取 concept_names 的前4个字，即 context.s1 的第一个概念
        assert context.s1 in concept_list
        assert len(concept_list) >= 90
test_concept_code_new = "".join(inspect.getsourcelines(test_concept)[0])


def test_get_trading_dates():
    from rqalpha.api import get_trading_dates
    import datetime
    def init(context):
        pass

    def handle_bar(context, bar_dict):
        trading_dates_list = get_trading_dates('2016-12-15', '2017-01-03')
        correct_dates_list = [datetime.date(2016, 12, 15), datetime.date(2016, 12, 16), datetime.date(2016, 12, 19),
                              datetime.date(2016, 12, 20), datetime.date(2016, 12, 21), datetime.date(2016, 12, 22),
                              datetime.date(2016, 12, 23), datetime.date(2016, 12, 26), datetime.date(2016, 12, 27),
                              datetime.date(2016, 12, 28), datetime.date(2016, 12, 29), datetime.date(2016, 12, 30),
                              datetime.date(2017, 1, 3)]
        assert sorted([item.strftime("%Y%m%d") for item in correct_dates_list]) == sorted(
            [item.strftime("%Y%m%d") for item
             in trading_dates_list])
test_get_trading_dates_code_new = "".join(inspect.getsourcelines(test_get_trading_dates)[0])


def test_get_previous_trading_date():
    from rqalpha.api import get_previous_trading_date
    def init(context):
        pass

    def handle_bar(context, bar_dict):
        assert str(get_previous_trading_date('2017-01-03').date()) == '2016-12-30'
        assert str(get_previous_trading_date('2016-01-03').date()) == '2015-12-31'
        assert str(get_previous_trading_date('2015-01-03').date()) == '2014-12-31'
        assert str(get_previous_trading_date('2014-01-03').date()) == '2014-01-02'
        assert str(get_previous_trading_date('2010-01-03').date()) == '2009-12-31'
        assert str(get_previous_trading_date('2009-01-03').date()) == '2008-12-31'
        assert str(get_previous_trading_date('2005-01-05').date()) == '2005-01-04'
test_get_previous_trading_date_code_new = "".join(inspect.getsourcelines(test_get_previous_trading_date)[0])


def test_get_next_trading_date():
    from rqalpha.api import get_next_trading_date
    def init(context):
        pass

    def handle_bar(context, bar_dict):
        assert str(get_next_trading_date('2017-01-03').date()) == '2017-01-04'
        assert str(get_next_trading_date('2007-01-03').date()) == '2007-01-04'
test_get_next_trading_date_code_new = "".join(inspect.getsourcelines(test_get_next_trading_date)[0])


def test_get_dividend():
    from rqalpha.api import get_dividend
    import pandas
    def init(context):
        pass

    def handle_bar(context, bar_dict):
        df = get_dividend('000001.XSHE', start_date='20130104')
        df_to_assert = df.loc[df['book_closure_date'] == '	2013-06-19']
        assert df.shape >= (4, 5)
        assert df_to_assert.iloc[0, 1] == 0.9838
        assert df_to_assert.iloc[0, 3] == pandas.tslib.Timestamp('2013-06-20 00:00:00')
test_get_dividend_code_new = "".join(inspect.getsourcelines(test_get_dividend)[0])

# =================== 以下把代码写为纯字符串 ===================

test_get_order_code = '''
from rqalpha.api import order_shares, get_order
def init(context):
    context.s1 = '000001.XSHE'
    context.amount = 100

def handle_bar(context, bar_dict):
    assert 1 == 2
    order_id = order_shares(context.s1, context.amount, style=LimitOrder(9.5))
    order = get_order(order_id)
    assert order.order_book_id == context.s1
    assert order.quantity == context.amount
    assert order.unfilled_quantity + order.filled_quantity == order.quantity

'''

test_get_open_order_code = '''
from rqalpha.api import order_shares, get_open_orders
def init(context):
    context.s1 = '000001.XSHE'
    context.limitprice = 8.9
    context.amount = 100
    context.counter = 0
    context.order_id = None

def handle_bar(context, bar_dict):
    context.counter += 1

    order = order_shares(context.s1, context.amount, style=LimitOrder(context.limitprice))
    context.order_id = order.order_id
    print('cash: ', context.portfolio.cash)
    print('check_get_open_orders done')
    print(order.order_id)
    print(get_open_orders().keys())
    print(get_open_orders())
    print(get_order(order.order_id))
    if context.counter == 2:
        assert order.order_id in get_open_orders()
    context.counter = 0
'''

test_cancel_order_code = '''
from rqalpha.api import order_shares, cancel_order, get_order
def init(context):
    context.s1 = '000001.XSHE'
    context.limitprice = 8.59
    context.amount = 100

def handle_bar(context, bar_dict):
    order_id = order_shares(context.s1, context.amount, style=LimitOrder(context.limitprice))
    cancel_order(order_id)
    order = get_order(order_id)
    assert order.order_book_id == context.s1
    assert order.filled_quantity == 0
    return order_id
    assert order.price == context.limitprice
'''

test_update_universe_code = '''
from rqalpha.api import update_universe, history_bars
def init(context):
    context.s1 = '000001.XSHE'
    context.s2 = '600340.XSHG'
    context.order_count = 0
    context.amount = 100

def handle_bar(context, bar_dict):
    context.order_count += 1
    if context.order_count == 1:
        update_universe(context.s2)
        his = history_bars(context.s2, 5, '1d', 'close')
        print(sorted(his.tolist()))
        print(sorted([24.1, 23.71, 23.82, 23.93, 23.66]))
        assert sorted(his.tolist()) == sorted([26.06, 26.13, 26.54, 26.6, 26.86])
'''

test_subscribe_code = '''
from rqalpha.api import subscribe
def init(context):
    context.f1 = 'AU88'
    context.amount = 1
    subscribe(context.f1)

def handle_bar(context, bar_dict):
    assert context.f1 in context.universe
'''

test_unsubscribe_code = '''
from rqalpha.api import subscribe, unsubscribe
def init(context):
    context.f1 = 'AU88'
    context.amount = 1
    subscribe(context.f1)
    unsubscribe(context.f1)

def handle_bar(context, bar_dict):
    assert context.f1 not in context.universe
'''

test_get_yield_curve_code = '''
from rqalpha.api import get_yield_curve
def init(context):
    pass

def handle_bar(context, bar_dict):
    df = get_yield_curve('20161101')
    assert df.iloc[0, 0] == 0.019923
    assert df.iloc[0, 6] == 0.021741
'''

test_history_bars_code = '''
from rqalpha.api import history_bars
def init(context):
    context.s1 = '000001.XSHE'
    pass

def handle_bar(context, bar_dict):
    return_list = history_bars(context.s1, 5, '1d', 'close')
    if str(context.now.date()) == '2016-12-29':
        assert return_list.tolist() == [9.08, 9.1199, 9.08, 9.06, 9.08]
'''

test_all_instruments_code = '''
from rqalpha.api import all_instruments
def init(context):
    pass

def handle_bar(context, bar_dict):
    df = all_instruments('FenjiA')
    df_to_assert = df.loc[df['order_book_id'] == '150247.XSHE']
    assert df_to_assert.iloc[0, 0] == 'CMAJ'
    assert df_to_assert.iloc[0, 7] == '工银中证传媒A'
    assert all_instruments().shape >= (8000, 4)
    assert all_instruments('CS').shape >= (3000, 16)
    assert all_instruments('ETF').shape >= (120, 9)
    assert all_instruments('LOF').shape >= (130, 9)
    assert all_instruments('FenjiMu').shape >= (10, 9)
    assert all_instruments('FenjiA').shape >= (120, 9)
    assert all_instruments('FenjiB').shape >= (140, 9)
    assert all_instruments('INDX').shape >= (500, 8)
    assert all_instruments('Future').shape >= (3500, 16)
'''

test_instruments_code = '''
from rqalpha.api import instruments
def init(context):
    context.s1 = '000001.XSHE'
    pass

def handle_bar(context, bar_dict):
    print('hello')
    ins = instruments(context.s1)
    assert ins.sector_code_name == '金融'
    assert ins.symbol == '平安银行'
    assert ins.order_book_id == context.s1
    assert ins.type == 'CS'
    print('world')
'''

test_sector_code = '''
from rqalpha.api import sector
def init(context):
    pass

def handle_bar(context, bar_dict):
    assert len(sector('金融')) >= 180
'''

test_industry_code = '''
from rqalpha.api import industry, instruments
def init(context):
    context.s1 = '000001.XSHE'
    context.s2 = '600340.XSHG'

def handle_bar(context, bar_dict):
    ins_1 = instruments(context.s1)
    ins_2 = instruments(context.s2)
    industry_list_1 = industry(ins_1.industry_name)
    industry_list_2 = industry(ins_2.industry_name)
    assert context.s1 in industry_list_1
    assert context.s2 in industry_list_2
'''

test_concept_code = '''
from rqalpha.api import concept, instruments
def init(context):
    context.s1 = '000002.XSHE'

def handle_bar(context, bar_dict):
    ins = instruments(context.s1)
    concept_list = concept(ins.concept_names[:4])  # 取 concept_names 的前4个字，即 context.s1 的第一个概念
    assert context.s1 in concept_list
    assert len(concept_list) >= 90
'''

test_get_trading_dates_code = '''
from rqalpha.api import get_trading_dates
import datetime
def init(context):
    pass

def handle_bar(context, bar_dict):
    trading_dates_list = get_trading_dates('2016-12-15', '2017-01-03')
    correct_dates_list = [datetime.date(2016, 12, 15), datetime.date(2016, 12, 16), datetime.date(2016, 12, 19),
                          datetime.date(2016, 12, 20), datetime.date(2016, 12, 21), datetime.date(2016, 12, 22),
                          datetime.date(2016, 12, 23), datetime.date(2016, 12, 26), datetime.date(2016, 12, 27),
                          datetime.date(2016, 12, 28), datetime.date(2016, 12, 29), datetime.date(2016, 12, 30),
                          datetime.date(2017, 1, 3)]
    assert sorted([item.strftime("%Y%m%d") for item in correct_dates_list]) == sorted([item.strftime("%Y%m%d") for item
                                                                                       in trading_dates_list])
'''

test_get_previous_trading_date_code = '''
from rqalpha.api import get_previous_trading_date
def init(context):
    pass

def handle_bar(context, bar_dict):
    assert str(get_previous_trading_date('2017-01-03').date()) == '2016-12-30'
    assert str(get_previous_trading_date('2016-01-03').date()) == '2015-12-31'
    assert str(get_previous_trading_date('2015-01-03').date()) == '2014-12-31'
    assert str(get_previous_trading_date('2014-01-03').date()) == '2014-01-02'
    assert str(get_previous_trading_date('2010-01-03').date()) == '2009-12-31'
    assert str(get_previous_trading_date('2009-01-03').date()) == '2008-12-31'
    assert str(get_previous_trading_date('2005-01-05').date()) == '2005-01-04'
'''

test_get_next_trading_date_code = '''

from rqalpha.api import get_next_trading_date
def init(context):
    pass

def handle_bar(context, bar_dict):
    assert str(get_next_trading_date('2017-01-03').date()) == '2017-01-04'
    assert str(get_next_trading_date('2007-01-03').date()) == '2007-01-04'

'''

test_get_dividend_code = '''
from rqalpha.api import get_dividend
import pandas
def init(context):
    pass

def handle_bar(context, bar_dict):
    df = get_dividend('000001.XSHE', start_date='20130104')
    df_to_assert = df.loc[df['book_closure_date'] == '	2013-06-19']
    assert df.shape >= (4, 5)
    assert df_to_assert.iloc[0, 1] == 0.9838
    assert df_to_assert.iloc[0, 3] == pandas.tslib.Timestamp('2013-06-20 00:00:00')
'''
