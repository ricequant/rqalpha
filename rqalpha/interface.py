# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），
#         您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、
#         本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，
#         否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。

import abc
from datetime import datetime, date
from typing import Any, Union, Optional, Iterable, Dict, List, Sequence, TYPE_CHECKING
if TYPE_CHECKING:
    from rqalpha.portfolio.account import Account

import numpy
from six import with_metaclass
import pandas

from rqalpha.utils.typing import DateLike
from rqalpha.model.tick import TickObject
from rqalpha.model.order import Order
from rqalpha.model.trade import Trade
from rqalpha.model.instrument import Instrument
from rqalpha.const import POSITION_DIRECTION, TRADING_CALENDAR_TYPE, INSTRUMENT_TYPE, SIDE, MARKET


class AbstractPosition(with_metaclass(abc.ABCMeta)):
    """
    仓位接口，主要用于构建仓位信息

    您可以在 Mod 的 start_up 阶段通过 Portfolio.register_instrument_type 来注册 Position 类型
    """

    @abc.abstractmethod
    def get_state(self):
        # type: () -> Any
        """
        主要用于进行持久化时候，提供对应需要持久化的数据
        """
        raise NotImplementedError

    @abc.abstractmethod
    def set_state(self, state):
        # type: (Any) -> None
        """
        主要用于持久化恢复时，根据提供的持久化数据进行恢复 Position 的实现
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def order_book_id(self):
        # type: () -> str
        """
        返回当前持仓的 order_book_id
        """
        raise NotImplementedError

    @property
    def direction(self):
        # type: () -> POSITION_DIRECTION
        """
        返回当前持仓的方向
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def market_value(self):
        # type: () -> Union[int, float]
        """
        返回当前持仓的市值
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def transaction_cost(self):
        # type: () -> Union[int, float]
        # 返回当前持仓的当日交易费用
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def position_pnl(self):
        # type: () -> Union[int, float]
        """
        返回当前持仓当日的持仓盈亏
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def trading_pnl(self):
        # type: () -> Union[int, float]
        """
        返回当前持仓当日的交易盈亏
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def closable(self):
        # type: () -> Union[int, float]
        """
        返回可平仓位
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def today_closable(self):
        # type: () -> Union[int, float]
        """
        返回今仓中的可平仓位
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def quantity(self):
        # type: () -> Union[int, float]
        """
        返回当前持仓量
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def avg_price(self):
        # type: () -> Union[int, float]
        """
        开仓均价
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def pnl(self):
        # type: () -> float
        """
        该持仓的累计盈亏
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def equity(self):
        # type: () -> float
        """
        当前持仓市值
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def prev_close(self):
        # type: () -> float
        """
        昨日收盘价
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def last_price(self):
        # type: () -> float
        """
        当前最新价
        """
        raise NotImplementedError


class AbstractStrategyLoader(with_metaclass(abc.ABCMeta)):
    """
    策略加载器，其主要作用是加载策略，并将策略运行所需要的域环境传递给策略执行代码。

    在扩展模块中，可以通过调用 ``env.set_strategy_loader`` 来替换默认的策略加载器。
    """
    @abc.abstractmethod
    def load(self, scope):
        """
        [Required]

        load 函数负责组装策略代码和策略代码所在的域，并输出最终组装好的可执行域。

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
        [Required]

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


class AbstractPriceBoard(with_metaclass(abc.ABCMeta)):
    """
    RQAlpha多个地方需要使用最新「行情」，不同的数据源其最新价格获取的方式不尽相同

    因此抽离出 `AbstractPriceBoard`, 您可以自行进行扩展并替换默认 PriceBoard
    """
    @abc.abstractmethod
    def get_last_price(self, order_book_id):
        # type: (str) -> float
        """
        获取合约的最新价
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_limit_up(self, order_book_id):
        # type: (str) -> float
        """
        获取合约的涨停价
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_limit_down(self, order_book_id):
        # type: (str) -> float
        """
        获取合约的跌停价
        """
        raise NotImplementedError

    def get_a1(self, order_book_id):
        # type: (str) -> Union[float, numpy.nan]
        """
        获取合约的卖一价
        """
        raise NotImplementedError

    def get_b1(self, order_book_id):
        # type: (str) -> Union[float, numpy.nan]
        """
        获取合约的买一价
        """
        raise NotImplementedError


class AbstractDataSource(object):
    """
    数据源接口。RQAlpha 中通过 :class:`DataProxy` 进一步进行了封装，向上层提供更易用的接口。

    在扩展模块中，可以通过调用 ``env.set_data_source`` 来替换默认的数据源。可参考 :class:`BaseDataSource`。
    """

    def get_instruments(self, id_or_syms: Optional[Iterable[str]] = None, types: Optional[Iterable[INSTRUMENT_TYPE]] = None) -> Iterable[Instrument]:
        """
        获取 instrument，
        可指定 order_book_id 或 symbol 或 instrument type，id_or_syms 优先级高于 types，
        id_or_syms 和 types 均为 None 时返回全部 instruments
        """
        raise NotImplementedError

    def get_trading_calendars(self):
        # type: () -> Dict[TRADING_CALENDAR_TYPE, pandas.DatetimeIndex]
        """
        获取交易日历，DataSource 应返回所有支持的交易日历种类
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

    def get_dividend(self, instrument):
        # type: (Instrument) -> numpy.ndarray | None
        """
        获取股票/基金分红信息

        :param instrument: 合约对象
        :type instrument: :class:`~Instrument`

        :return: `numpy.ndarray` | `None`
            返回分红信息的结构化数组，包含以下字段:
            
            =========================   ===================================================
            字段名                       类型和描述  
            =========================   ===================================================
            book_closure_date           '<i8' - 股权登记日，格式为 YYYYMMDD 的整数
            announcement_date           '<i8' - 公告日期，格式为 YYYYMMDD 的整数  
            dividend_cash_before_tax    '<f8' - 税前现金分红，单位为元
            ex_dividend_date            '<i8' - 除权除息日，格式为 YYYYMMDD 的整数
            payable_date                '<i8' - 分红派息日，格式为 YYYYMMDD 的整数
            round_lot                   '<f8' - 分红最小单位，例如：10 代表每 10 股派发
            =========================   ===================================================
            
            数据示例::
            
                array([(19910430, 19910430, 3.   , 19910502, 19910502, 10.),
                       (19920320, 19920314, 2.   , 19920323, 19920323, 10.),
                       (19930521, 19930509, 3.   , 19930524, 19930524, 10.)],
                      dtype=[('book_closure_date', '<i8'), ('announcement_date', '<i8'), 
                             ('dividend_cash_before_tax', '<f8'), ('ex_dividend_date', '<i8'), 
                             ('payable_date', '<i8'), ('round_lot', '<f8')])
            
            如果该合约没有分红记录，则返回 None
        """
        raise NotImplementedError

    def get_split(self, instrument) -> Optional[numpy.ndarray]:
        """
        获取股票拆股信息

        :param instrument: 合约对象
        :type instrument: :class:`~Instrument`

        :return: `numpy.ndarray` | `None`
            返回拆股信息的结构化数组，包含以下字段:
            
            =========================   ===================================================
            字段名                       类型和描述  
            =========================   ===================================================
            ex_date                     '<i8' - 除权日，格式为 YYYYMMDDHHMMSS 的整数
            split_factor                '<f8' - 拆股比例，表示每股拆分后的股数
            =========================   ===================================================
            
            数据示例::
            
                array([(19910502000000, 1.4 ), (19920323000000, 1.5 ),
                       (19930524000000, 1.85), (19940711000000, 1.5 ),
                       (19950925000000, 1.2 ), (19960527000000, 2.  )],
                      dtype=[('ex_date', '<i8'), ('split_factor', '<f8')])
            
            其中 split_factor 表示拆股倍数：
            - 1.5 表示每 1 股拆为 1.5 股（即 2 拆 3）
            - 2.0 表示每 1 股拆为 2 股（即 1 拆 2） 
            
            如果该合约没有拆股记录，则返回 None
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

    def get_open_auction_bar(self, instrument, dt):
        # type: (Instrument, Union[datetime, date]) -> Dict
        """
        获取指定资产当日的集合竞价 Bar 数据，该 Bar 数据应包含的字段有：
            datetime, open, limit_up, limit_down, volume, total_turnover
        """
        raise NotImplementedError
    
    def get_open_auction_volume(self, instrument, dt):
        """
        获取指定资产当日的集合竞价成交量

        :param instrument: 合约对象
        :type instrument: class:`~Instrument`

        :param dt: 集合竞价时间
        :type dt: datetime.datetime

        :return: `float`
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

    def history_bars(self, instrument, bar_count, frequency, fields, dt, skip_suspended=True,
                     include_now=False, adjust_type='pre', adjust_orig=None):
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
        :param bool include_now: 是否包含当天最新数据
        :param str adjust_type: 复权类型，'pre', 'none', 'post'
        :param datetime.datetime adjust_orig: 复权起点；

        :return: `Optional[numpy.ndarray]`, fields 不合法时返回 None

        """
        raise NotImplementedError

    def history_ticks(self, instrument, count, dt):
        # type: (Instrument, int, datetime) -> List[TickObject]
        """
        获取指定合约历史 tick 对象

        :param instrument: 合约对象
        :param int count: 获取的 tick 数量
        :param dt: 时间

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

    def get_futures_trading_parameters(self, instrument, dt):
        """
        获取期货合约的时序手续费信息
        :param instrument: 合约对象
        :type instrument: :class:`~Instrument`

        :param datetime.datetime dt: 交易日
        
        :return: :class:`FuturesTradingParameters`
        """
        raise NotImplementedError

    def get_merge_ticks(self, order_book_id_list, trading_date, last_dt=None):
        """
        获取合并的 ticks

        :param list order_book_id_list: 合约名列表
        :param datetime.date trading_date: 交易日
        :param datetime.datetime last_dt: 仅返回 last_dt 之后的时间

        :return: Iterable object of Tick
        """
        raise NotImplementedError

    def get_share_transformation(self, order_book_id):
        """
        获取股票转换信息
        :param order_book_id: 合约代码
        :return: (successor, conversion_ratio), (转换后的合约代码，换股倍率)
        """
        raise NotImplementedError

    def is_suspended(self, order_book_id, dates):
        # type: (str, Sequence[DateLike]) -> Sequence[bool]
        raise NotImplementedError

    def is_st_stock(self, order_book_id, dates):
        # type: (str, Sequence[DateLike]) -> Sequence[bool]
        raise NotImplementedError

    def get_algo_bar(self, id_or_ins, start_min, end_min, dt):
        # type: (Union[str, Instrument], int, int, datetime) -> Optional[numpy.void]
        # 格式: (date, VWAP, TWAP, volume) -> 案例 (20200102, 16.79877183, 16.83271429, 144356044)
        raise NotImplementedError


class AbstractBroker(with_metaclass(abc.ABCMeta)):
    """
    券商接口。

    RQAlpha 将产生的订单提交给此对象，此对象负责对订单进行撮合（不论是自行撮合还是委托给外部的真实交易所），
    并通过 ``EVENT.ORDER_*`` 及 ``EVENT.TRADE`` 事件将撮合结果反馈进入 RQAlpha。

    在扩展模块中，可以通过调用 ``env.set_broker`` 来替换默认的 Broker。
    """

    @abc.abstractmethod
    def submit_order(self, order):
        # type: (Order) -> None
        # 提交订单。RQAlpha 会生成 :class:`~Order` 对象，再通过此接口提交到 Broker。
        raise NotImplementedError

    @abc.abstractmethod
    def cancel_order(self, order):
        """
        [Required]

        撤单。

        :param order: 订单
        :type order: :class:`~Order`
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_open_orders(self, order_book_id=None):
        """
        [Required]

        获得当前未完成的订单。

        :return: list[:class:`~Order`]
        """
        raise NotImplementedError


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

    @abc.abstractmethod
    def should_resume(self):
        """
        是否应该以 resume 模式运行
        :return: bool
        """
        raise NotImplementedError

    @abc.abstractmethod
    def should_run_init(self):
        """
        是否应该执行策略的 init 函数
        :return: bool
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


class AbstractFrontendValidator(with_metaclass(abc.ABCMeta)):
    """
    前端风控接口，下撤单请求在到达券商代理模块前会经过前端风控。

    扩展模块可以通过 env.add_frontend_validator 添加自定义的前端风控逻辑
    """
    @abc.abstractmethod
    def validate_submission(self, order: Order, account: Optional['Account'] = None) -> Optional[str]:
        """
        进行下单前的验证，若通过则返回 None

        :return: `Optional[str]`
        """
        raise NotImplementedError
    
    @abc.abstractmethod
    def validate_cancellation(self, order: Order, account: Optional['Account'] = None) -> Optional[str]:
        """
        进行撤销订单前的验证，若通过则返回 None

        :return: `Optional[str]`
        """
        raise NotImplementedError


class AbstractTransactionCostDecider((with_metaclass(abc.ABCMeta))):
    """
    订单税费计算接口，通过实现次接口可以定义不同市场、不同合约的个性化税费计算逻辑。
    """
    @abc.abstractmethod
    def get_trade_tax(self, trade: Trade) -> float:
        """
        计算指定交易应付的印花税
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_trade_commission(self, trade: Trade) -> float:
        """
        计算指定交易应付的佣金
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_order_transaction_cost(self, order: Order) -> float:
        """
        计算指定订单应付的交易成本（税 + 费）
        """
        raise NotImplementedError
    
    def get_transaction_cost_with_value(self, value: float, side: SIDE) -> float:
        """
        计算指定价格交易应付的交易成本（税 + 费）
        """
        raise NotImplementedError
