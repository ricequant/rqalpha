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

import abc


from six import with_metaclass


class AbstractStrategyLoader(with_metaclass(abc.ABCMeta)):
    """
    策略加载器，其主要作用是加载策略，并将策略运行所需要的域环境传递给策略执行代码。

    在扩展模块中，可以通过调用 ``env.set_strategy_loader`` 来替换默认的策略加载器。
    """
    @abc.abstractmethod
    def load(self, strategy, scope):
        """
        【Required】

        load 函数负责组装策略代码和策略代码所在的域，并输出最终组装好的可执行域。

        :param str strategy: 策略标识符，对应 ``config.base.strategy_file``，相应的命令行参数为 ``-f``。
        :param dict scope: 策略代码运行环境，在传入时，包含了所有基础API。
            通过在 scope 中添加函数可以实现自定义API；通过覆盖 scope 中相应的函数，可以覆盖原API。

        :return: scope，其中应包含策略相应函数，如 ``init``, ``before_trading`` 等
        """
        raise NotImplementedError


class AbstractEventSource(with_metaclass(abc.ABCMeta)):
    """
    事件源接口。RQAlpha 从此对象中获取事件，驱动整个事件循环。

    在扩展模块中，可以通过调用 ``env.set_event_source`` 来替换默认的事件源。
    """
    @abc.abstractmethod
    def events(self, start_date, end_date, frequency):
        """
        【Required】

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


class AbstractDataSource(object):
    """
    数据源接口。RQAlpha 中通过 :class:`DataProxy` 进一步进行了封装，向上层提供更易用的接口。

    在扩展模块中，可以通过调用 ``env.set_data_source`` 来替换默认的数据源。可参考 :class:`BaseDataSource`。
    """
    def get_all_instruments(self):
        """
        获取所有Instrument。

        :return: list[:class:`~Instrument`]
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
        :param str tenor: 利率期限

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
        根据 dt 来获取对应的 Bar 数据

        :param instrument: 合约对象
        :type instrument: :class:`~Instrument`

        :param datetime.datetime dt: calendar_datetime

        :param str frequency: 周期频率，`1d` 表示日周期, `1m` 表示分钟周期

        :return: `numpy.ndarray` | `dict`
        """
        raise NotImplementedError

    def get_settle_price(self, instrument, date):
        """
        获取期货品种在 date 的结算价

        :param instrument: 合约对象
        :type instrument: :class:`~Instrument`

        :param datetime.date date: 结算日期

        :return: `str`
        """
        raise NotImplementedError

    def history_bars(self, instrument, bar_count, frequency, fields, dt, skip_suspended=True):
        """
        获取历史数据

        :param instrument: 合约对象
        :type instrument: :class:`~Instrument`

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
        :type instrument: :class:`~Instrument`

        :param str frequency: 周期频率，`1d` 表示日周期, `1m` 表示分钟周期
        :param datetime.datetime dt: 时间

        :return: :class:`~Snapshot`
        """
        raise NotImplementedError

    def get_trading_minutes_for(self, instrument, trading_dt):
        """

        获取证券某天的交易时段，用于期货回测

        :param instrument: 合约对象
        :type instrument: :class:`~Instrument`

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


class AbstractBroker(with_metaclass(abc.ABCMeta)):
    """
    券商接口。

    RQAlpha 将产生的订单提交给此对象，此对象负责对订单进行撮合（不论是自行撮合还是委托给外部的真实交易所），
    并通过 ``EVENT.ORDER_*`` 及 ``EVENT.TRADE`` 事件将撮合结果反馈进入 RQAlpha。

    在扩展模块中，可以通过调用 ``env.set_broker`` 来替换默认的 Broker。
    """
    @abc.abstractmethod
    def get_accounts(self):
        """
        [Required]

        获取账号信息。系统初始化时，RQAlpha 会调用此接口，获取账户信息。

        RQAlpha 支持混合策略，因此返回的账户信息为一个字典(dict)，key 为账户类型（``rqalpha.const.ACCOUNT_TYPE``)，
        value 为对应的 :class:`~Account` 对象。

        :return: dict
        """
        raise NotImplementedError

    @abc.abstractmethod
    def submit_order(self, order):
        """
        【Required】

        提交订单。在当前版本，RQAlpha 会生成 :class:`~Order` 对象，再通过此接口提交到 Broker。
        TBD: 由 Broker 对象生成 Order 并返回？
        """
        raise NotImplementedError

    @abc.abstractmethod
    def cancel_order(self, order):
        """
        【Required】

        撤单。

        :param order: 订单
        :type order: :class:`~Order`
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_open_orders(self):
        """
        【Required】

        获得当前未完成的订单。

        :return: list[:class:`~Order`]
        """
        raise NotImplementedError

    def before_trading(self):
        """
        【Optional】

        RQAlpha 会在 `EVENT.BEFORE_TRADING` 事件被触发前调用此接口。
        """
        pass

    def after_trading(self):
        """
        【Optional】

        RQAlpha 会在 `EVENT.AFTER_TRADING` 事件被触发前调用此接口。
        """
        pass

    def bar(self, bar_dict):
        """
        【Optional】

        RQAlpha 会在 `EVENT.BAR` 事件被出发前调用此接口。

        Broker 根据自己的业务场景来选择是否实现，比如说自带撮合引擎的Broker，会通过 `update` 函数来触发撮合。

        :param calendar_dt: 实际时间
        :param trading_dt: 交易时间
        :param bar_dict: dict[:class:`~BarObject`]
        """
        pass


class AbstractMod(with_metaclass(abc.ABCMeta)):
    """
    扩展模块接口。
    """
    @abc.abstractmethod
    def start_up(self, env, mod_config):
        """
        RQAlpha 在系统启动时会调用此接口；在此接口中，可以通过调用 ``env`` 的相应方法来覆盖系统默认组件。

        :param env: 系统环境
        :type env: :class:`~Environment`
        :param mod_config: 模块配置参数
        """
        raise NotImplementedError

    def tear_down(self, code, exception=None):
        """
        RQAlpha 在系统退出前会调用此接口。

        :param code: 退出代码
        :type code: rqalpha.const.EXIT_CODE
        :param exception: 如果在策略执行过程中出现错误，此对象为相应的异常对象
        """
        raise NotImplementedError


class AbstractPersistProvider(with_metaclass(abc.ABCMeta)):
    """
    持久化服务提供者接口。

    扩展模块可以通过调用 ``env.set_persist_provider`` 接口来替换默认的持久化方案。
    """
    @abc.abstractmethod
    def store(self, key, value):
        """
        store

        :param str key:
        :param bytes value:
        :return:
        """
        raise NotImplementedError

    @abc.abstractmethod
    def load(self, key):
        """
        :param str key:
        :return: bytes 如果没有对应的值，返回 None
        """
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
