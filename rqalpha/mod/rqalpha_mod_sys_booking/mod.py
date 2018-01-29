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


from rqalpha.interface import AbstractMod
from rqalpha.model.base_position import Positions
from rqalpha.model.trade import Trade
from rqalpha.const import SIDE, POSITION_EFFECT, POSITION_DIRECTION, CustomEnum
from rqalpha.utils.logger import system_log
from rqalpha.events import EVENT, Event

from .booking_account import BookingAccount
from .booking_position import BookingPosition

# import api
from . import api_booking


SIDE_DICT = {
    1: SIDE.BUY,
    2: SIDE.SELL,
}

POSITION_EFFECT_DICT = {
    1: POSITION_EFFECT.OPEN,
    2: POSITION_EFFECT.CLOSE,
    3: POSITION_EFFECT.CLOSE_TODAY,
}


class BookingMod(AbstractMod):

    def start_up(self, env, mod_config):
        self.env = env
        import requests

        if env.config.base.init_positions:
            raise RuntimeError("RQAlpha recieve init positions. rqalpha_mod_sys_booking do not support init_positions")

        # TODO: load pos/trade from pms
        server_url = mod_config.server_url
        booking_id = mod_config.booking_id

        if not mod_config.booking_id:
            booking_id = env.config.base.run_id
            mod_config.booking_id = booking_id

        self.booking_account = BookingAccount(register_event=True)

        resp = requests.get("{}/get_positions/{}".format(server_url, booking_id)).json()
        if resp["code"] != 200:
            raise RuntimeError(resp)

        # 昨仓
        trades = []
        position_list = resp["resp"]["positions"]
        for position_dict in position_list:
            if position_dict["buy_quantity"] != 0:
                trade = self._create_trade(
                    position_dict["order_book_id"],
                    position_dict["buy_quantity"],
                    SIDE.BUY,
                    POSITION_EFFECT.OPEN,
                )
                trades.append(trade)
            if position_dict["sell_quantity"] != 0:
                trade = self._create_trade(
                    position_dict["order_book_id"],
                    position_dict["sell_quantity"],
                    SIDE.SELL,
                    POSITION_EFFECT.OPEN,
                )
                trades.append(trade)

        system_log.info("yesterday positions trades")
        for trade in trades:
            system_log.info("trade: {:9}, qtx {}, side {}", trade.order_book_id, trade.last_quantity, trade.side)

        self.booking_account.fast_forward([], trades=trades)
        self.booking_account._settlement(None, check_delist=False)

        # 计算今仓
        resp = requests.get("{}/get_trades/{}".format(server_url, booking_id)).json()
        if resp["code"] != 200:
            raise RuntimeError(resp)

        trades = []
        trade_list = resp["resp"]["trades"]
        for trade_dict in trade_list:
            trade = self._create_trade(
                trade_dict["order_book_id"],
                trade_dict["last_quantity"],
                SIDE_DICT[trade_dict["side"]],
                POSITION_EFFECT_DICT[trade_dict["position_effect"]],
            )
            trades.append(trade)
        system_log.info("today trades: {}", trades)
        self.booking_account.fast_forward([], trades=trades)

        env.event_bus.add_listener(EVENT.BEFORE_SYSTEM_RESTORED, self.on_before_system_restore)

    def on_before_system_restore(self, event):
        helper = self.env.persist_helper
        disable_persist_keys = [
            "portfolio",
            "benchmark_portfolio",
        ]
        for key in disable_persist_keys:
            helper.unregister(key)

    def tear_down(self, code, exception=None):
        pass

    def _create_trade(self, obid, quantity, side, position_effect):
        trade = Trade.__from_create__(0, 0, quantity, side, position_effect, obid)
        return trade