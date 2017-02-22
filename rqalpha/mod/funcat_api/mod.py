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

import copy

import numpy as np

from rqalpha.interface import AbstractMod
from rqalpha.environment import Environment
from rqalpha.events import EVENT


class FuncatAPIMod(AbstractMod):
    def start_up(self, env, mod_config):
        try:
            import funcat
        except ImportError:
            print("-" * 50)
            print(">>> Missing funcat. Please run `pip install funcat`")
            print("-" * 50)
            raise

        from funcat.data.backend import DataBackend
        from funcat.context import set_current_date

        class RQAlphaDataBackend(DataBackend):
            """
            目前仅支持日数据
            """
            skip_suspended = False

            def __init__(self):
                from rqalpha.api import (
                    history_bars,
                    all_instruments,
                    instruments,
                )

                self.set_current_date = set_current_date

                self.history_bars = history_bars
                self.all_instruments = all_instruments
                self.instruments = instruments
                self.rqalpha_env = Environment.get_instance()

                self.rqalpha_env.event_bus.add_listener(EVENT.PRE_BEFORE_TRADING, self._pre_before_trading)
                self.rqalpha_env.event_bus.add_listener(EVENT.PRE_BAR, self._pre_handle_bar)

            def _pre_before_trading(self, *args, **kwargs):
                calendar_date = self.rqalpha_env.calendar_dt.date()
                self.set_current_date(calendar_date)

            def _pre_handle_bar(self, *args, **kwargs):
                calendar_date = self.rqalpha_env.calendar_dt.date()
                self.set_current_date(calendar_date)

            def get_price(self, order_book_id, start, end):
                """
                :param order_book_id: e.g. 000002.XSHE
                :param start: 20160101
                :param end: 20160201
                :returns:
                :rtype: numpy.rec.array
                """
                # start = get_date_from_int(start)
                # end = get_date_from_int(end)
                # bar_count = (end - start).days

                # TODO: this is slow, make it run faster
                bar_count = 1000
                origin_bars = bars = self.history_bars(order_book_id, bar_count, "1d")

                dtype = copy.deepcopy(bars.dtype)
                names = list(dtype.names)
                names[0] = "date"
                dtype.names = names
                bars = np.array(bars, dtype=dtype)

                bars["date"] = origin_bars["datetime"] / 1000000

                return bars

            def get_order_book_id_list(self):
                """获取所有的
                """
                return sorted(self.all_instruments("CS").order_book_id.tolist())

            def get_trading_dates(self, start, end):
                """获取所有的交易日

                :param start: 20160101
                :param end: 20160201
                """
                raise NotImplementedError

            def get_start_date(self):
                """获取回溯开始时间
                """
                return str(self.rqalpha_env.config.base.start_date)

            def symbol(self, order_book_id):
                """获取order_book_id对应的名字
                :param order_book_id str: 股票代码
                :returns: 名字
                :rtype: str
                """
                return self.instruments(order_book_id).symbol

        # change funcat data backend to rqalpha
        funcat.set_data_backend(RQAlphaDataBackend())

        # register funcat api into rqalpha
        from rqalpha.api.api_base import register_api
        for name in dir(funcat):
            obj = getattr(funcat, name)
            if getattr(obj, "__module__", "").startswith("funcat"):
                register_api(name, obj)

    def tear_down(self, code, exception=None):
        pass
