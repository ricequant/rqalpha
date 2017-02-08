# -*- coding: utf-8 -*-
#
# Copyright 2016 Ricequant, Inc
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

import abc

from six import with_metaclass


class Persistable(with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def get_state(self):
        """
        :return: bytes
        """
        raise NotImplementedError

    @abc.abstractmethod
    def set_state(self, state):
        """
        :param state: bytes
        :return:
        """
        raise NotImplementedError

    @classmethod
    def __subclasshook__(cls, C):
        if cls is Persistable:
            if (any("get_state" in B.__dict__ for B in C.__mro__) and
                    any("set_state" in B.__dict__ for B in C.__mro__)):
                return True
        return NotImplemented


class AbstractEventSource:
    def events(self, start_date, end_date, frequency):
        """
        calendar_dt, trading_dt, event
        """
        raise NotImplementedError


class AbstractMod:
    def start_up(self, env, mod_config):
        raise NotImplementedError

    def tear_down(self, code, exception=None):
        raise NotImplementedError


class AbstractDataSource:
    def get_all_instruments(self):
        """
        获取所有Instrument。
        :return: list of Instrument
        """
        raise NotImplementedError

    def get_trading_calendar(self):
        """
        获取交易日历
        :return: list of pd.Timestamp
        """
        raise NotImplementedError

    def get_yield_curve(self, start_date, end_date, tenor=None):
        """
        获取国债利率
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param tenor: 利率期限
        :return: pd.DataFrame, [start_date, end_date]
        """
        raise NotImplementedError

    def get_dividend(self, order_book_id, adjusted=True):
        """
        获取股票/基金分红信息
        :param order_book_id:
        :param adjusted: 是否经过前复权处理
        :return:
        """
        raise NotImplementedError

    def get_split(self, order_book_id):
        raise NotImplementedError

    def get_bar(self, instrument, dt, frequency):
        """
        获取 dt 时刻的bar
        :param instrument:
        :param dt: calendar dt
        :param frequency: '1d' '1m
        :return: np.ndarray or dict
        """
        raise NotImplementedError

    def get_settle_price(self, instrument, date):
        """
        获取期货品种在date的结算价
        :param instrument:
        :param date:
        :return:
        """
        raise NotImplementedError

    def history_bars(self, instrument, bar_count, frequency, fields, dt, skip_suspended=True):
        """
        获取历史数据
        :param instrument:
        :param bar_count:
        :param frequency:
        :param fields:
        :param dt:
        :param skip_suspended:
        :return: numpy.ndarray
        """
        raise NotImplementedError

    def current_snapshot(self, instrument, frequency, dt):
        """

        :param instrument:
        :param frequency:
        :param dt:
        :return: SnapshotObject
        """
        raise NotImplementedError

    def get_trading_minutes_for(self, instrument, trading_dt):
        """
        获取证券某天的交易时段，用于期货回测
        :param instrument:
        :param trading_dt: 交易日。注意期货夜盘所属交易日规则。
        :return:
        """
        raise NotImplementedError

    def available_data_range(self, frequency):
        """
        此数据源能提供数据的时间范围
        :param frequency:
        :return: (earliest, latest)
        """
        raise NotImplementedError


class AbstractBroker:
    def submit_order(self, order):
        raise NotImplementedError

    def cancel_order(self, order):
        raise NotImplementedError

    def before_trading(self):
        raise NotImplementedError

    def after_trading(self):
        raise NotImplementedError

    def get_open_orders(self):
        raise NotImplementedError

    def get_accounts(self):
        raise NotImplementedError

    def update(self, calendar_dt, trading_dt, bar_dict):
        raise NotImplementedError


class AbstractPersistProvider:
    def store(self, key, value):
        raise NotImplementedError

    def load(self, key):
        raise NotImplementedError


class AbstractStrategyLoader(with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def load(self, strategy, scope):
        raise NotImplementedError

