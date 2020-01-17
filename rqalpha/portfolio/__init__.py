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

from typing import Dict, Union
from itertools import chain


import six
import jsonpickle
import numpy as np

from rqalpha.environment import Environment
from rqalpha.interface import AbstractAccount
from rqalpha.const import DAYS_CNT, DEFAULT_ACCOUNT_TYPE
from rqalpha.utils import merge_dicts
from rqalpha.utils.repr import property_repr
from rqalpha.events import EVENT


class Portfolio(object):
    __repr__ = property_repr

    def __init__(self, static_unit_net_value, units, accounts):
        # type: (float, int, Dict[Union[str, DEFAULT_ACCOUNT_TYPE], AbstractAccount]) -> Portfolio
        self._static_unit_net_value = static_unit_net_value
        self._last_unit_net_value = static_unit_net_value
        self._units = units
        self._accounts = accounts
        self._mixed_positions = None
        self.register_event()

    def register_event(self):
        event_bus = Environment.get_instance().event_bus
        event_bus.prepend_listener(EVENT.PRE_BEFORE_TRADING, self._pre_before_trading)
        event_bus.prepend_listener(EVENT.POST_SETTLEMENT, self._post_settlement)

    def order(self, order_book_id, quantity, style, target=False):
        account_type = Environment.get_instance().get_account_type(order_book_id)
        return self.accounts[account_type].order(order_book_id, quantity, style, target)

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

    def _pre_before_trading(self, _):
        if not np.isnan(self.unit_net_value):
            self._static_unit_net_value = self.unit_net_value
        else:
            self._static_unit_net_value = self._last_unit_net_value

    def _post_settlement(self, event):
        self._last_unit_net_value = self.unit_net_value

    def get_positions(self):
        return list(chain(*(a.get_positions() for a in six.itervalues(self._accounts))))

    def get_position(self, order_book_id, direction):
        account = self._accounts[Environment.get_instance().get_account_type(order_book_id)]
        return account.get_position(order_book_id, direction)

    @property
    def accounts(self):
        """
        [dict] 账户字典
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
    def positions(self):
        """
        [dict] 持仓字典
        """
        if self._mixed_positions is None:
            self._mixed_positions = MixedPositions(self._accounts)
        return self._mixed_positions

    @property
    def cash(self):
        """
        [float] 可用资金
        """
        return sum(account.cash for account in six.itervalues(self._accounts))

    @property
    def dividend_receivable(self):
        """
        [float] 应收分红
        """
        return sum(getattr(account, 'dividend_receivable', 0) for account in six.itervalues(self._accounts))

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


class MixedPositions(dict):

    def __init__(self, accounts):
        super(MixedPositions, self).__init__()
        self._accounts = accounts

    def __missing__(self, key):
        account_type = Environment.get_instance().get_account_type(key)
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
