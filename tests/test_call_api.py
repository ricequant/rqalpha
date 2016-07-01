# -*- coding: utf-8 -*-
from six import print_ as print

from rqalgoengine import Strategy, StrategyExecutor
from rqalgoengine.data import RqDataProxy, MyDataProxy


def test_import_api():
    from rqalgoengine.scope.api import (
        order_shares, order_percent, order_lots, order_value,
        order_target_value, order_target_percent, get_order,
        get_open_orders, cancel_order, update_universe,
        instruments, history, is_st_stock,
    )
