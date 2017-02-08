
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


class AbstractStrategyLoader(with_metaclass(abc.ABCMeta)):
    """
    策略加载器，其主要作用是加载策略，并将策略运行所需要的域环境传递给策略执行代码。
    """

    @abc.abstractmethod
    def load(self, strategy, scope):
        """
        load 函数负责组装策略代码和策略代码所在的域，并输出最终组装好的可执行域

        :param str strategy: 策略相关参数，可以是路径，也可以是源码本身，
            原则就是根据strategy可以获取到源码，
            系统会将 `config.base.strategy_file` 作为参数传递给load函数。

        :param dict scope: 域，系统会将默认的API函数等内容加载到scope中，这样函数就可以直接调用对应的API了，
            通过自定义load函数，可以更改scope，来增加自定义API 等功能。

        :return: scope
        """
        raise NotImplementedError


class AbstractEventSource:
    """
    事件生成模块，RQAlpha 会使用该模块来实现完整的事件触发
    """
    def events(self, start_date, end_date, frequency):
        """
        扩展 EventSource 必须实现 events 函数。

        events 是一个 event generator, 在相应事件的时候需要以如下格式来传递事件

        .. code-block:: python

            yield trading_datetime, calendar_datetime, EventEnum

        其中 trading_datetime 为基于交易日的 datetime, calendar_datetime 为基于自然日的 datetime (因为夜盘的存在，交易日和自然日未必相同)

        EventEnum 为 :class:`~Events`

        :param datetime.date start_date: 起始日期, 系统会将 `config.base.start_date` 传递 events 函数

        :param datetime.date end_date: 结束日期，系统会将 `config.base.end_date` 传递给 events 函数

        :param str frequency: 周期频率，`1d` 表示日周期, `1m` 表示分钟周期

        :return: None
        """
        raise NotImplementedError


class AbstractDataSource:
    """
    数据源模块，RQAlpha 支持自定义数据源，也可以基于已有默认数据源模块进行扩展，
    因为 RQAlpha 内部使用了一些数据，所以必须实现对应的接口函数。
    """
    def get_all_instruments(self):
        """
        获取所有Instrument。

        :return: list[:class:`~StockInstrument` | :class:`~FutureInstrument`]
        """
        raise NotImplementedError

    def get_trading_calendar(self):
        """
        获取交易日历

        :return: list[`pandas.Timestamp`]
        """
        raise NotImplementedError

    def get_yield_curve(self, start_date, end_date, tenor=None):
        """
        获取国债利率

        :param pandas.Timestamp str start_date: 开始日期

        :param pandas.Timestamp end_date: 结束日期

        :param bool tenor: 利率期限

        :return: pandas.DataFrame, [start_date, end_date]
        """
        raise NotImplementedError

    def get_dividend(self, order_book_id, adjusted=True):
        """
        获取股票/基金分红信息

        :param str order_book_id: 合约名
        :param bool adjusted: 是否经过前复权处理
        :return:
        """
        raise NotImplementedError

    def get_split(self, order_book_id):
        """
        获取拆股信息

        :param str order_book_id: 合约名

        :return: `pandas.DataFrame`
        """

        raise NotImplementedError

    def get_bar(self, instrument, dt, frequency):
        """
        根据 dt 来获取 对应的Bar 数据

        :param instrument: 合约对象
        :type instrument: :class:`~StockInstrument` | :class:`~FutureInstrument`

        :param datetime.datetime dt: calendar_datetime

        :param str frequency: 周期频率，`1d` 表示日周期, `1m` 表示分钟周期

        :return: `numpy.ndarray` | `dict`
        """
        raise NotImplementedError

    def get_settle_price(self, instrument, date):
        """
        获取期货品种在date的结算价

        :param instrument: 合约对象
        :type instrument: :class:`~StockInstrument` | :class:`~FutureInstrument`

        :param datetime.date date: 结算日期

        :return: `str`
        """
        raise NotImplementedError

    def history_bars(self, instrument, bar_count, frequency, fields, dt, skip_suspended=True):
        """
        获取历史数据

        :param instrument: 合约对象
        :type instrument: :class:`~StockInstrument` | :class:`~FutureInstrument`

        :param int bar_count: 获取的历史数据数量

        :param str frequency: 周期频率，`1d` 表示日周期, `1m` 表示分钟周期

        :param str fields: 返回数据字段

        =========================   ===================================================
        fields                      字段名
        =========================   ===================================================
        datetime                    时间戳
        open                        开盘价
        high                        最高价
        low                         最低价
        close                       收盘价
        volume                      成交量
        total_turnover              成交额
        datetime                    int类型时间戳
        open_interest               持仓量（期货专用）
        basis_spread                期现差（股指期货专用）
        settlement                  结算价（期货日线专用）
        prev_settlement             结算价（期货日线专用）
        =========================   ===================================================

        :param datetime.datetime dt: 时间

        :param bool skip_suspended: 是否跳过停牌日

        :return: `numpy.ndarray`

        """
        raise NotImplementedError

    def current_snapshot(self, instrument, frequency, dt):
        """
        获得当前市场快照数据。只能在日内交易阶段调用，获取当日调用时点的市场快照数据。
        市场快照数据记录了每日从开盘到当前的数据信息，可以理解为一个动态的day bar数据。
        在目前分钟回测中，快照数据为当日所有分钟线累积而成，一般情况下，最后一个分钟线获取到的快照数据应当与当日的日线行情保持一致。
        需要注意，在实盘模拟中，该函数返回的是调用当时的市场快照情况，所以在同一个handle_bar中不同时点调用可能返回的数据不同。
        如果当日截止到调用时候对应股票没有任何成交，那么snapshot中的close, high, low, last几个价格水平都将以0表示。

        :param instrument: 合约对象
        :type instrument: :class:`~StockInstrument` | :class:`~FutureInstrument`

        :param str frequency: 周期频率，`1d` 表示日周期, `1m` 表示分钟周期

        :param datetime.datetime dt: 时间

        :return: :class:`~Snapshot`
        """
        raise NotImplementedError

    def get_trading_minutes_for(self, instrument, trading_dt):
        """

        获取证券某天的交易时段，用于期货回测

        :param instrument: 合约对象
        :type instrument: :class:`~StockInstrument` | :class:`~FutureInstrument`

        :param datetime.datetime trading_dt: 交易日。注意期货夜盘所属交易日规则。

        :return: list[`datetime.datetime`]
        """
        raise NotImplementedError

    def available_data_range(self, frequency):
        """
        此数据源能提供数据的时间范围

        :param str frequency: 周期频率，`1d` 表示日周期, `1m` 表示分钟周期

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


class AbstractMod:
    def start_up(self, env, mod_config):
        raise NotImplementedError

    def tear_down(self, code, exception=None):
        raise NotImplementedError


class AbstractPersistProvider:
    def store(self, key, value):
        raise NotImplementedError

    def load(self, key):
        raise NotImplementedError


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


