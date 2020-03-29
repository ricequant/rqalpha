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

from functools import lru_cache
from typing import Dict, Union, Callable, List, Optional, Tuple
from itertools import chain

import six
import jsonpickle
import numpy as np

from rqalpha.environment import Environment
from rqalpha.const import DAYS_CNT, DEFAULT_ACCOUNT_TYPE, INSTRUMENT_TYPE, POSITION_DIRECTION
from rqalpha.utils import merge_dicts
from rqalpha.utils.repr import PropertyReprMeta
from rqalpha.events import EVENT
from rqalpha.model.order import OrderStyle, Order
from rqalpha.model.instrument import Instrument
from rqalpha.interface import AbstractPosition, AbstractAccount

from .account import Account
from .base_position import PositionType, PositionProxyType

OrderApiType = Callable[[str, Union[int, float], OrderStyle, bool], List[Order]]


class Portfolio(object, metaclass=PropertyReprMeta):
    """
    投资组合，策略所有账户的集合
    """
    __repr_properties__ = (
        "total_value", "unit_net_value", "daily_pnl", "daily_returns", "total_returns", "annualized_returns", "accounts"
    )

    _account_types = {}  # type: Dict[INSTRUMENT_TYPE, Union[str, Callable[[Instrument, ], str]]]
    _order_apis = {}  # type: Dict[INSTRUMENT_TYPE, OrderApiType]

    def __init__(self, starting_cash, init_positions):
        # type: (Dict[str, float], List[Tuple[str, int]]) -> Portfolio
        self._static_unit_net_value = 1
        self._last_unit_net_value = 1

        account_args = {}
        for account_type, cash in six.iteritems(starting_cash):
            account_args[account_type] = {"type": account_type, "total_cash": cash, "init_positions": {}}
        for order_book_id, quantity in init_positions:
            account_type = self.get_account_type(order_book_id)
            if account_type in account_args:
                account_args[account_type]["init_positions"][order_book_id] = quantity
        self._accounts = {account_type: Account(**args) for account_type, args in six.iteritems(account_args)}
        self._units = sum(account.total_value for account in six.itervalues(self._accounts))

        self._register_event()

    @classmethod
    def register_instrument_type(
            cls,
            instrument_type,  # type: Union[INSTRUMENT_TYPE, str]
            upper_account_type,  # type: Union[str, Callable[[Instrument, ], str]]
            position_cls,  # type: PositionType
            order_api,  # type: OrderApiType
            position_proxy_cls=None  # type: Optional[PositionProxyType]
    ):
        cls._account_types[instrument_type] = upper_account_type
        cls._order_apis[instrument_type] = order_api
        Account.register_position_type(instrument_type, position_cls)
        if position_proxy_cls:
            from .base_position import PositionProxyDict
            PositionProxyDict.register_position_proxy_dict(instrument_type, position_proxy_cls)

    def order(self, order_book_id, quantity, style, target=False):
        # type: (str, Union[int, float], OrderStyle, Optional[bool]) -> List[Order]
        instrument_type = Environment.get_instance().data_proxy.instruments(order_book_id).type
        try:
            order_func = self._order_apis[instrument_type]  # type: OrderApiType
        except KeyError:
            raise NotImplementedError("no implementation for API order, order_book_id={}".format(order_book_id))
        return order_func(order_book_id, quantity, style, target)

    def get_state(self):
        return jsonpickle.encode({
            'static_unit_net_value': self._static_unit_net_value,
            'last_unit_net_value': self._last_unit_net_value,
            'units': self._units,
            'accounts': {
                name: account.get_state() for name, account in six.iteritems(self._accounts)
            }
        }).encode('utf-8')

    def set_state(self, state):
        state = state.decode('utf-8')
        value = jsonpickle.decode(state)
        self._static_unit_net_value = value['static_unit_net_value']
        self._last_unit_net_value = value.get('last_unit_net_value', self._static_unit_net_value)
        self._units = value['units']
        for k, v in six.iteritems(value['accounts']):
            self._accounts[k].set_state(v)

    def get_positions(self):
        return list(chain(*(a.get_positions() for a in six.itervalues(self._accounts))))

    def get_position(self, order_book_id, direction):
        # type: (str, POSITION_DIRECTION) -> AbstractPosition
        account = self._accounts[self.get_account_type(order_book_id)]
        return account.get_position(order_book_id, direction)

    @classmethod
    def get_account_type(cls, order_book_id):
        instrument =  Environment.get_instance().data_proxy.instruments(order_book_id)
        try:
            account_type = cls._account_types[instrument.type]
        except KeyError:
            raise NotImplementedError("no account_type registered, order_book_id={}, instrument_type={}".format(
                order_book_id, instrument.type
            ))
        if isinstance(account_type, str):
            return account_type
        return account_type(instrument)

    def get_account(self, order_book_id):
        return self._accounts[self.get_account_type(order_book_id)]

    @property
    def accounts(self):
        # type: () -> Dict[DEFAULT_ACCOUNT_TYPE, Account]
        """
        账户字典
        """
        return self._accounts

    @property
    def stock_account(self):
        """
        [StockAccount] 股票账户
        """
        return self._accounts.get(DEFAULT_ACCOUNT_TYPE.STOCK.name, None)

    @property
    def future_account(self):
        """
        [FutureAccount] 期货账户
        """
        return self._accounts.get(DEFAULT_ACCOUNT_TYPE.FUTURE.name, None)

    @property
    def start_date(self):
        """
        [datetime.datetime] 策略投资组合的开始日期
        """
        return Environment.get_instance().config.base.start_date

    @property
    def units(self):
        """
        [float] 份额
        """
        return self._units

    @property
    def unit_net_value(self):
        """
        [float] 实时净值
        """
        if self._units == 0:
            return np.nan
        return self.total_value / self._units

    @property
    def static_unit_net_value(self):
        """
        [float] 昨日净值
        """
        return self._static_unit_net_value

    @property
    def daily_pnl(self):
        """
        [float] 当日盈亏
        """
        return sum(account.daily_pnl for account in six.itervalues(self._accounts))

    @property
    def daily_returns(self):
        """
        [float] 当前最新一天的日收益
        """
        return np.nan if self._static_unit_net_value == 0 else self.unit_net_value / self._static_unit_net_value - 1

    @property
    def total_returns(self):
        """
        [float] 累计收益率
        """
        return self.unit_net_value - 1

    @property
    def annualized_returns(self):
        """
        [float] 累计年化收益率
        """
        if self.unit_net_value <= 0:
            return -1

        env = Environment.get_instance()
        date_count = float(env.data_proxy.count_trading_dates(env.config.base.start_date, env.trading_dt.date()))
        return self.unit_net_value ** (DAYS_CNT.TRADING_DAYS_A_YEAR / date_count) - 1

    @property
    def total_value(self):
        """
        [float]总权益
        """
        return sum(account.total_value for account in six.itervalues(self._accounts))

    @property
    def portfolio_value(self):
        """
        [Deprecated] 总权益
        """
        return self.total_value

    @property
    @lru_cache()
    def positions(self):
        """
        [dict] 持仓字典
        """
        return MixedPositions(self._accounts)

    @property
    def cash(self):
        """
        [float] 可用资金
        """
        return sum(account.cash for account in six.itervalues(self._accounts))

    @property
    def transaction_cost(self):
        """
        [float] 交易成本（税费）
        """
        return sum(account.transaction_cost for account in six.itervalues(self._accounts))

    @property
    def market_value(self):
        """
        [float] 市值
        """
        return sum(account.market_value for account in six.itervalues(self._accounts))

    @property
    def pnl(self):
        """
        [float] 收益
        """
        return (self.unit_net_value - 1) * self.units

    @property
    def starting_cash(self):
        """
        [float] 初始资金
        """
        return self.units

    @property
    def frozen_cash(self):
        """
        [float] 冻结资金
        """
        return sum(account.frozen_cash for account in six.itervalues(self._accounts))

    def _pre_before_trading(self, _):
        if not np.isnan(self.unit_net_value):
            self._static_unit_net_value = self.unit_net_value
        else:
            self._static_unit_net_value = self._last_unit_net_value

    def _post_settlement(self, event):
        self._last_unit_net_value = self.unit_net_value

    def _register_event(self):
        event_bus = Environment.get_instance().event_bus
        event_bus.prepend_listener(EVENT.PRE_BEFORE_TRADING, self._pre_before_trading)
        event_bus.prepend_listener(EVENT.POST_SETTLEMENT, self._post_settlement)


class MixedPositions(dict):

    def __init__(self, accounts):
        super(MixedPositions, self).__init__()
        self._accounts = accounts

    def __missing__(self, key):
        account_type = Portfolio.get_account_type(key)
        for a_type in self._accounts:
            if a_type == account_type:
                return self._accounts[a_type].positions[key]
        return None

    def __contains__(self, item):
        return item in self.keys()

    def __repr__(self):
        keys = []
        for account in six.itervalues(self._accounts):
            keys += account.positions.keys()
        return str(sorted(keys))

    def __len__(self):
        return sum(len(account.positions) for account in six.itervalues(self._accounts))

    def __iter__(self):
        keys = []
        for account in six.itervalues(self._accounts):
            keys += account.positions.keys()
        for key in sorted(keys):
            yield key

    def items(self):
        items = merge_dicts(*[account.positions.items() for account in six.itervalues(self._accounts)])
        for k in sorted(items.keys()):
            yield k, items[k]

    def keys(self):
        keys = []
        for account in six.itervalues(self._accounts):
            keys += list(account.positions.keys())
        return sorted(keys)
