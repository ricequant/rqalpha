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

from rqalpha.interface import AbstractEventSource
from rqalpha.events import Event, EVENT
from rqalpha.environment import Environment
from rqalpha.utils import get_account_type
from rqalpha.utils.exception import CustomException, CustomError, patch_user_exc
from rqalpha.utils.datetime_func import convert_int_to_datetime
from rqalpha.const import ACCOUNT_TYPE

ONE_MINUTE = datetime.timedelta(minutes=1)


class SimulationEventSource(AbstractEventSource):
    def __init__(self, env, account_list):
        self._env = env
        self._account_list = account_list
        self._universe_changed = False
        Environment.get_instance().event_bus.add_listener(EVENT.POST_UNIVERSE_CHANGED, self._on_universe_changed)

    def _on_universe_changed(self, universe):
        self._universe_changed = True

    def _get_universe(self):
        universe = Environment.get_instance().universe
        if len(universe) == 0 and ACCOUNT_TYPE.STOCK not in self._account_list:
            error = CustomError()
            error.set_msg("Current universe is empty. Please use subscribe function before trade")
            raise patch_user_exc(CustomException(error))
        return universe

    @staticmethod
    def _get_stock_trading_minutes(trading_date):
        trading_minutes = set()
        current_dt = datetime.datetime.combine(trading_date, datetime.time(9, 31))
        am_end_dt = current_dt.replace(hour=11, minute=30)
        pm_start_dt = current_dt.replace(hour=13, minute=1)
        pm_end_dt = current_dt.replace(hour=15, minute=0)
        delta_minute = datetime.timedelta(minutes=1)
        while current_dt <= am_end_dt:
            trading_minutes.add(current_dt)
            current_dt += delta_minute

        current_dt = pm_start_dt
        while current_dt <= pm_end_dt:
            trading_minutes.add(current_dt)
            current_dt += delta_minute
        return trading_minutes

    def _get_future_trading_minutes(self, trading_date):
        trading_minutes = set()
        universe = self._get_universe()
        for order_book_id in universe:
            if get_account_type(order_book_id) == ACCOUNT_TYPE.STOCK:
                continue
            trading_minutes.update(self._env.data_proxy.get_trading_minutes_for(order_book_id, trading_date))
        return set([convert_int_to_datetime(minute) for minute in trading_minutes])

    def _get_trading_minutes(self, trading_date):
        trading_minutes = set()
        for account_type in self._account_list:
            if account_type == ACCOUNT_TYPE.STOCK:
                trading_minutes = trading_minutes.union(self._get_stock_trading_minutes(trading_date))
            elif account_type == ACCOUNT_TYPE.FUTURE:
                trading_minutes = trading_minutes.union(self._get_future_trading_minutes(trading_date))
        return sorted(list(trading_minutes))

    def events(self, start_date, end_date, frequency):
        if frequency == "1d":
            # 根据起始日期和结束日期，获取所有的交易日，然后再循环获取每一个交易日
            for day in self._env.data_proxy.get_trading_dates(start_date, end_date):
                date = day.to_pydatetime()
                dt_before_trading = date.replace(hour=0, minute=0)
                dt_bar = date.replace(hour=15, minute=0)
                dt_after_trading = date.replace(hour=15, minute=30)
                dt_settlement = date.replace(hour=17, minute=0)
                yield Event(EVENT.BEFORE_TRADING, dt_before_trading, dt_before_trading)
                yield Event(EVENT.BAR, dt_bar, dt_bar)

                yield Event(EVENT.AFTER_TRADING, dt_after_trading, dt_after_trading)
                yield Event(EVENT.SETTLEMENT, dt_settlement, dt_settlement)
        else:
            for day in self._env.data_proxy.get_trading_dates(start_date, end_date):
                before_trading_flag = True
                date = day.to_pydatetime()
                last_dt = None
                done = False

                dt_before_day_trading = date.replace(hour=8, minute=30)

                while True:
                    if done:
                        break
                    exit_loop = True
                    trading_minutes = self._get_trading_minutes(date)
                    for calendar_dt in trading_minutes:
                        if last_dt is not None and calendar_dt < last_dt:
                            continue

                        if calendar_dt < dt_before_day_trading:
                            trading_dt = calendar_dt.replace(year=date.year,
                                                             month=date.month,
                                                             day=date.day)
                        else:
                            trading_dt = calendar_dt
                        if before_trading_flag:
                            before_trading_flag = False
                            yield Event(EVENT.BEFORE_TRADING, trading_dt, trading_dt)
                        if self._universe_changed:
                            self._universe_changed = False
                            last_dt = calendar_dt
                            exit_loop = False
                            break
                        # yield handle bar
                        yield Event(EVENT.BAR, calendar_dt, trading_dt)
                    if exit_loop:
                        done = True

                dt = date.replace(hour=15, minute=30)
                yield Event(EVENT.AFTER_TRADING, dt, dt)

                dt = date.replace(hour=17, minute=0)
                yield Event(EVENT.SETTLEMENT, dt, dt)
