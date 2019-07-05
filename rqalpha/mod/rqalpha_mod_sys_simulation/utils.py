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
import datetime
import six

from rqalpha.const import DEFAULT_ACCOUNT_TYPE
from rqalpha.model.base_position import Positions
from rqalpha.model.portfolio import Portfolio
from rqalpha.model.trade import Trade
from rqalpha.model.base_account import BaseAccount
from rqalpha.utils.i18n import gettext as _

from rqalpha.const import SIDE, POSITION_EFFECT


def _fake_trade(order_book_id, quantity, price):
    return Trade.__from_create__(0, price, abs(quantity),
                                 SIDE.BUY if quantity > 0 else SIDE.SELL,
                                 POSITION_EFFECT.OPEN, order_book_id)


def _filter_positions(env, account_type):
    positions = env.config.base.init_positions
    futures = [ins.order_book_id for ins in env.data_proxy.all_instruments('Future')]
    if account_type == 'FUTURE':
        return [position for position in positions if position[0] in futures]
    else:
        return [position for position in positions if position[0] not in futures]


def init_portfolio(env):
    accounts = {}
    config = env.config
    start_date = datetime.datetime.combine(config.base.start_date, datetime.time.min)
    units = 0

    if config.base.init_positions or (DEFAULT_ACCOUNT_TYPE.FUTURE.name in config.base.accounts and
                                      config.base.frequency != '1d'):
        BaseAccount.AGGRESSIVE_UPDATE_LAST_PRICE = True

    for account_type, starting_cash in six.iteritems(config.base.accounts):
        if starting_cash == 0:
            raise RuntimeError(_(u"{} starting cash can not be 0, using `--account {} 100000`").format(account_type, account_type))

        account_model = env.get_account_model(account_type)
        position_model = env.get_position_model(account_type)
        positions = Positions(position_model)

        for order_book_id, quantity in _filter_positions(env, account_type):
            instrument = env.get_instrument(order_book_id)
            if instrument is None:
                raise RuntimeError(_(u'invalid order book id {} in initial positions').format(order_book_id))
            if not instrument.listing:
                raise RuntimeError(_(u'instrument {} in initial positions is not listing').format(order_book_id))

            bars = env.data_proxy.history_bars(order_book_id, 1, '1d', 'close',
                                               env.data_proxy.get_previous_trading_date(start_date),
                                               adjust_type='none')
            if bars is None:
                raise RuntimeError(_(u'the close price of {} in initial positions is not available').format(order_book_id))

            price = bars[0]
            trade = _fake_trade(order_book_id, quantity, price)
            if order_book_id not in positions:
                positions[order_book_id] = position_model(order_book_id)
            positions[order_book_id].apply_trade(trade)
            # FIXME
            positions[order_book_id]._last_price = price

        # 变成昨仓
        for order_book_id, position in positions.items():
            position.apply_settlement()

        account = account_model(starting_cash, positions)
        units += account.total_value
        accounts[account_type] = account

    return Portfolio(config.base.start_date, 1, units, accounts)

