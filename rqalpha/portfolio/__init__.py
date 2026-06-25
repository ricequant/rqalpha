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

from itertools import chain
from collections.abc import Mapping
from typing import Callable, Dict, List, Tuple, Union

import jsonpickle
import numpy as np
import six

from rqalpha.const import DEFAULT_ACCOUNT_TYPE, POSITION_DIRECTION, RUN_TYPE, TAX_TYPE
from rqalpha.environment import Environment
from rqalpha.core.events import EVENT, Event
from rqalpha.interface import AbstractPosition
from rqalpha.model.order import Order, OrderStyle
from rqalpha.portfolio.account import Account
from rqalpha.portfolio.capital_gains_tax import CapitalGainsTaxMixin
from rqalpha.utils.functools import lru_cache
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.logger import user_system_log
from rqalpha.utils.repr import PropertyReprMeta

OrderApiType = Callable[[str, Union[int, float], OrderStyle, bool], List[Order]]


class Portfolio(CapitalGainsTaxMixin, metaclass=PropertyReprMeta):
    """
    投资组合，策略所有账户的集合
    """
    __repr_properties__ = (
        "total_value", "unit_net_value", "daily_pnl", "daily_returns", "total_returns", "annualized_returns"
    )

    def __init__(
            self,
            starting_cash: Dict[str, float],
            init_positions: List[Tuple[str, int]],
            financing_rate: float,
            env: Environment,
    ):
        self._accounts = self._init_accounts(starting_cash, init_positions, financing_rate, env)
        self._static_unit_net_value = 1
        self._units = sum(account.total_value for account in six.itervalues(self._accounts))
        self._env = env
        CapitalGainsTaxMixin.__init__(self)
        env.event_bus.add_listener(EVENT.TRADE, self._on_trade)
        env.event_bus.prepend_listener(EVENT.PRE_BEFORE_TRADING, self._pre_before_trading)
        env.event_bus.add_listener(EVENT.SETTLEMENT, self._on_settlement)
        env.event_bus.add_listener(EVENT.PAY_TAXES, self._on_pay_taxes)

    @classmethod
    def _init_accounts(
        cls,
        starting_cash: Dict[str, float],
        init_positions: List[Tuple[str, int]],
        financing_rate: float,
        env: Environment,
    ) -> Dict[str, Account]:
        account_args = {}
        for account_type, cash in starting_cash.items():
            account_args[account_type] = {
                "account_type": account_type, "total_cash": cash, "init_positions": {}, "financing_rate": financing_rate, "env": env
            }
        for order_book_id, quantity in init_positions:
            account_type = env.data_proxy.instrument_not_none(order_book_id).account_type
            if account_type in account_args:
                account_args[account_type]["init_positions"][order_book_id] = quantity
        return {account_type: Account(**args) for account_type, args in account_args.items()}

    def get_state(self):
        return jsonpickle.encode({
            'static_unit_net_value': self._static_unit_net_value,
            'units': self._units,
            'annual_deductible_balance': self._annual_deductible_balance,
            'monthly_realized_pnl': self._monthly_realized_pnl,
            'accounts': {
                name: account.get_state() for name, account in self._accounts.items()
            }
        }).encode('utf-8')

    def set_state(self, state):
        state = state.decode('utf-8')
        value = jsonpickle.decode(state)
        self._static_unit_net_value = value['static_unit_net_value']
        self._units = value['units']
        self._annual_deductible_balance = value.get('annual_deductible_balance', 0)
        self._monthly_realized_pnl = value.get('monthly_realized_pnl', 0)
        for k, v in value['accounts'].items():
            self._accounts[k].set_state(v)

    def get_positions(self):
        return list(chain(*(a.get_positions() for a in six.itervalues(self._accounts))))

    def get_position(self, order_book_id: str, direction: POSITION_DIRECTION) -> AbstractPosition:
        account = self._accounts[self.get_account_type(order_book_id)]
        return account.get_position(order_book_id, direction)

    @classmethod
    def get_account_type(cls, order_book_id):
        instrument = Environment.get_instance().data_proxy.instrument_not_none(order_book_id)
        return instrument.account_type

    def get_account(self, order_book_id):
        return self._accounts[self.get_account_type(order_book_id)]

    @property
    def accounts(self) -> Dict[DEFAULT_ACCOUNT_TYPE, Account]:
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
        return self._env.config.base.start_date

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
        if self.units == 0:
            return np.nan
        return self.total_value / self.units

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

        env = self._env
        date_count = float(env.data_proxy.count_trading_dates(env.config.base.start_date, env.trading_dt.date()))
        trading_days_a_year = env.trading_days_a_year
        return self.unit_net_value ** (trading_days_a_year / date_count) - 1

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

    @property
    def cash_liabilities(self):
        """
        [float] 现金负债
        """
        return sum(account.cash_liabilities for account in six.itervalues(self._accounts))

    def _pre_before_trading(self, _):
        self._static_unit_net_value = self.unit_net_value

    def deposit_withdraw(self, account_type, amount, receiving_days=0):
        """出入金"""
        # 入金 现金增加，份额增加，总权益增加，单位净值不变
        # 出金 现金减少，份额减少，总权益减少，单位净值不变
        account_type = account_type.upper()
        if account_type not in self._accounts:
            raise ValueError(_("invalid account type {}, choose in {}".format(account_type, list(self._accounts.keys()))))
        unit_net_value = self.unit_net_value
        self._accounts[account_type].deposit_withdraw(amount, receiving_days)
        _units = self.total_value / unit_net_value
        user_system_log.debug(_("Cash add {}. units {} become to {}".format(amount, self._units, _units)))
        self._units = _units

    def finance_repay(self, amount, account_type):
        """ 融资还款 """
        if self._env.config.base.run_type == RUN_TYPE.LIVE_TRADING:
            raise ValueError("finance and report api not support LIVE_TRADING")

        if account_type not in self._accounts:
            raise ValueError(_("invalid account type {}, choose in {}".format(account_type, list(self._accounts.keys()))))
        self._accounts[account_type].finance_repay(amount)

    def _on_trade(self, event):
        delta_monthly_realized_pnl = event.account.apply_trade(event.trade, event.order)
        self._add_monthly_realized_pnl(delta_monthly_realized_pnl)

    def _on_settlement(self, event):
        tax_amount = self.calc_capital_gains_tax()
        if tax_amount > 0:
            self._env.event_bus.publish_event(Event(
                EVENT.PAY_TAXES, delta_amount=tax_amount, trading_dt=self._env.trading_dt, tax_type=TAX_TYPE.CAPITAL_GAINS
            ))

    def _on_pay_taxes(self, event):
        if event.tax_type == TAX_TYPE.DIVIDEND:
            # 只有股票账户会扣除红利税
            self.stock_account.pay_taxes(event.delta_amount, event.tax_type)
        elif event.tax_type == TAX_TYPE.CAPITAL_GAINS:
            # 1. 优先扣除股票账户现金，如果没有设置股票账户或者股票账户现金不够扣除时，扣除期货账户
            # 2. 股票和期货现金都不够扣除，或者股票账户不够扣除，但是没设置期货账户时，扣除股票账户
            # 3. 允许扣除之后股票账户资金为负数
            tax_amount = event.delta_amount
            if self.stock_account is None:
                self.future_account.pay_taxes(tax_amount, TAX_TYPE.CAPITAL_GAINS)
            else:
                if self.future_account is None or self.future_account.cash < 0 or self.stock_account.cash >= tax_amount:
                    self.stock_account.pay_taxes(tax_amount, TAX_TYPE.CAPITAL_GAINS)
                else:
                    if self.stock_account.cash < 0:  # 可能存在股票账号现金已经为负数的情况
                        futures_tax = min(tax_amount, self.future_account.cash)
                    else:
                        futures_tax = min(tax_amount - self.stock_account.cash, self.future_account.cash)
                    stock_tax = tax_amount - futures_tax
                    self.stock_account.pay_taxes(stock_tax, TAX_TYPE.CAPITAL_GAINS)
                    self.future_account.pay_taxes(futures_tax, TAX_TYPE.CAPITAL_GAINS)
        else:
            raise ValueError(f"Invalid tax type: {event.tax_type}")
        self._env.event_bus.publish_event(Event(
            EVENT.TAXES_PAID,
            order_book_id=getattr(event, "order_book_id", None),
            delta_amount=event.delta_amount,
            trading_dt=event.trading_dt,
            tax_type=event.tax_type,
        ))


class MixedPositions(Mapping):
    def __init__(self, accounts):
        super(MixedPositions, self).__init__()
        self._accounts = accounts

    def __contains__(self, item):
        account_type = Portfolio.get_account_type(item)
        return item in self._accounts[account_type].positions

    def __getitem__(self, item):
        account_type = Portfolio.get_account_type(item)
        return self._accounts[account_type].positions[item]

    def __repr__(self):
        keys = []
        for account in six.itervalues(self._accounts):
            keys += [
                order_book_id for order_book_id, position in account.positions.items()
                if getattr(position, "quantity", 0) > 0 or
                getattr(position, "buy_quantity", 0) + getattr(position, "sell_quantity", 0) > 0
            ]
        return str(sorted(keys))

    def __len__(self):
        return sum(len(account.positions) for account in six.itervalues(self._accounts))

    def __iter__(self):
        for account in self._accounts.values():
            yield from account.positions.keys()
