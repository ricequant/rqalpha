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
from rqalpha.model.trade import Trade
from rqalpha.const import SIDE, POSITION_EFFECT, RUN_TYPE
from rqalpha.utils.logger import system_log
from rqalpha.events import EVENT

from .booking_account import BookingAccount

# noinspection PyUnresolvedReferences
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

    def __init__(self):
        self.env = None
        self.mod_config = None
        self.booking_account = None

    def _get_old_position_list(self):
        """
        get old positions from booking service
        :return: list of position dict
        """
        raise NotImplementedError

    def _get_trade_list(self):
        """
        get trades from booking service
        :return: list of trade dict
        """
        raise NotImplementedError

    def start_up(self, env, mod_config):
        self.env = env
        self.mod_config = mod_config

        if env.config.base.run_type != RUN_TYPE.LIVE_TRADING:
            system_log.info("Mod booking will only run in live trading")
            return

        if env.config.base.init_positions:
            raise RuntimeError("RQAlpha receive init positions. rqalpha_mod_sys_booking does not support init_positions")

        self.booking_account = BookingAccount(register_event=True)

        # 昨仓
        trades = []
        position_list = self._get_old_position_list()
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

        trades = []
        trade_list = self._get_trade_list()
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