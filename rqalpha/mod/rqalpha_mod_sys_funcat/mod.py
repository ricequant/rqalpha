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

from rqalpha.interface import AbstractMod
from rqalpha.environment import Environment
from rqalpha.events import EVENT
from rqalpha.execution_context import ExecutionContext
from rqalpha.const import EXECUTION_PHASE


class FuncatAPIMod(AbstractMod):
    def start_up(self, env, mod_config):
        try:
            import funcat
        except ImportError:
            six.print_("-" * 50)
            six.print_(">>> Missing funcat. Please run `pip install funcat`")
            six.print_("-" * 50)
            raise

        from funcat.data.backend import DataBackend
        from funcat.context import set_current_date
        from funcat.utils import get_date_from_int

        from rqalpha.api import history_bars

        class RQAlphaDataBackend(DataBackend):
            """
            目前仅支持日数据
            """
            skip_suspended = False

            def __init__(self):
                from rqalpha.api import (
                    all_instruments,
                    instruments,
                )

                self.set_current_date = set_current_date
                self.all_instruments = all_instruments
                self.instruments = instruments
                self.rqalpha_env = Environment.get_instance()

                self.rqalpha_env.event_bus.add_listener(EVENT.PRE_BEFORE_TRADING, self._pre_before_trading)
                self.rqalpha_env.event_bus.add_listener(EVENT.PRE_BAR, self._pre_handle_bar)

                self.fetch_data_by_api = True

            def _pre_before_trading(self, *args, **kwargs):
                calendar_date = self.rqalpha_env.calendar_dt.date()
                self.set_current_date(calendar_date)

            def _pre_handle_bar(self, *args, **kwargs):
                calendar_date = self.rqalpha_env.calendar_dt.date()
                self.set_current_date(calendar_date)

            def _history_bars(self, order_book_id, bar_count, freq, dt):
                if self.fetch_data_by_api and ExecutionContext.phase() in (
                        EXECUTION_PHASE.BEFORE_TRADING,
                        EXECUTION_PHASE.ON_BAR,
                        EXECUTION_PHASE.ON_TICK,
                        EXECUTION_PHASE.AFTER_TRADING,
                        EXECUTION_PHASE.SCHEDULED):
                        bars = history_bars(
                            order_book_id, bar_count, freq, fields=None)
                else:
                    bars = self.rqalpha_env.data_proxy.history_bars(
                        order_book_id, bar_count, freq,
                        field=["datetime", "open", "high", "low", "close", "volume"],
                        dt=dt)
                return bars

            def get_price(self, order_book_id, start, end, freq):
                """
                :param order_book_id: e.g. 000002.XSHE
                :param start: 20160101
                :param end: 20160201
                :returns:
                :rtype: numpy.rec.array
                """
                start = get_date_from_int(start)
                end = get_date_from_int(end)

                scale = 1
                if freq[-1] == "m":
                    scale *= 240. / int(freq[:-1])
                bar_count = int(((end - start).days + 1) * scale)

                dt = datetime.datetime.combine(end, datetime.time(23, 59, 59))
                bars = self._history_bars(order_book_id, bar_count, freq, dt)

                if bars is None or len(bars) == 0:
                    raise KeyError("empty bars {}".format(order_book_id))
                bars = bars.copy()

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