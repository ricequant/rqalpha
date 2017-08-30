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

import six
from datetime import datetime

from rqalpha.const import DEFAULT_ACCOUNT_TYPE
from rqalpha.model.base_position import Positions
from rqalpha.model.portfolio import Portfolio
from rqalpha.model.trade import Trade
from rqalpha.model.base_account import BaseAccount
from rqalpha.utils.i18n import gettext as _

from rqalpha.const import ORDER_TYPE, SIDE, POSITION_EFFECT, MATCHING_TYPE


def init_portfolio(env):
    accounts = {}
    config = env.config
    start_date = config.base.start_date
    units = 0

    BaseAccount.AGGRESSIVE_UPDATE_LAST_PRICE = True

    for account_type, starting_cash in six.iteritems(config.base.accounts):
        if account_type == DEFAULT_ACCOUNT_TYPE.STOCK.name:
            if starting_cash == 0:
                raise RuntimeError(_(u"stock starting cash can not be 0, using `--account stock 100000`"))
            StockAccount = env.get_account_model(DEFAULT_ACCOUNT_TYPE.STOCK.name)
            init_positions = generate_init_position(env, account_type)
            accounts[DEFAULT_ACCOUNT_TYPE.STOCK.name] = StockAccount(starting_cash, init_positions)
            units += accounts[DEFAULT_ACCOUNT_TYPE.STOCK.name].total_value
        elif account_type == DEFAULT_ACCOUNT_TYPE.FUTURE.name:
            if starting_cash == 0:
                raise RuntimeError(_(u"future starting cash can not be 0, using `--account future 100000`"))
            FutureAccount = env.get_account_model(DEFAULT_ACCOUNT_TYPE.FUTURE.name)
            init_positions = generate_init_position(env, account_type)
            accounts[DEFAULT_ACCOUNT_TYPE.FUTURE.name] = FutureAccount(starting_cash, init_positions)
            units += accounts[DEFAULT_ACCOUNT_TYPE.FUTURE.name].total_value
        else:
            raise NotImplementedError
    return Portfolio(start_date, 1, units, accounts)


def generate_init_position(env, account_type):
    date = datetime.combine(env.config.base.start_date, datetime.min.time())
    init_positions = env.config.base.init_positions

    if account_type == DEFAULT_ACCOUNT_TYPE.STOCK.name:
        StockPosition = env.get_position_model(DEFAULT_ACCOUNT_TYPE.STOCK.name)
        stock_init_position = Positions(StockPosition)
        if init_positions and "STOCK" in init_positions:
            stock_init_positions = init_positions["STOCK"]
            for position in stock_init_positions:
                order_book_id, quantity = position[0], position[1]
                instrument = env.get_instrument(order_book_id)
                if instrument is None:
                    raise RuntimeError(_(u'{order_book_id} is invalid, please check your positions setting.'
                                         .format(order_book_id=order_book_id)))
                if not instrument.listing:
                    raise RuntimeError(
                        _(u'{order_book_id} is not listed or has been delisted, please check you positions setting.'
                          .format(order_book_id=order_book_id)))
                last_price = env.data_proxy.get_prev_close(order_book_id, date)
                stock_init_position[order_book_id] = StockPosition(order_book_id)
                trade = Trade.__from_create__(
                    order_id='2342',
                    price=last_price,
                    amount=quantity,
                    side=SIDE.BUY,
                    position_effect=POSITION_EFFECT.OPEN,
                    order_book_id=order_book_id
                )
                stock_init_position[order_book_id].apply_trade(trade)
                stock_init_position[order_book_id].set_last_price(last_price)
        return stock_init_position
    elif account_type == DEFAULT_ACCOUNT_TYPE.FUTURE.name:
        FuturePosition = env.get_position_model(DEFAULT_ACCOUNT_TYPE.FUTURE.name)
        future_init_position = Positions(FuturePosition)
        if init_positions and "FUTURE" in init_positions:
            future_init_positions = init_positions["FUTURE"]
            for position in future_init_positions:
                order_book_id, quantity = position[0], position[1]
                last_price = env.data_proxy.get_prev_close(order_book_id, date)
                instrument = env.get_instrument(order_book_id)
                if instrument is None:
                    raise RuntimeError(_(u'{order_book_id} is invalid, please check your positions setting.'
                                         .format(order_book_id=order_book_id)))
                if not instrument.listing:
                    raise RuntimeError(
                        _(u'{order_book_id} is not listed or has been delisted, please check you positions setting.'
                          .format(order_book_id=order_book_id)))
                future_init_position[order_book_id] = FuturePosition(order_book_id)
                if quantity > 0:
                    side = SIDE.BUY
                else:
                    side = SIDE.SELL
                trade = Trade.__from_create__(
                    order_id='8888',
                    price=last_price,
                    amount=abs(quantity),
                    side=side,
                    position_effect=POSITION_EFFECT.OPEN,
                    order_book_id=order_book_id
                )
                future_init_position[order_book_id].apply_trade(trade)
                future_init_position[order_book_id].set_last_price(last_price)
        return future_init_position
    else:
        raise NotImplementedError


