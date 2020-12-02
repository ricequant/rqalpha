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

from datetime import datetime
from typing import Optional, Dict, List
from itertools import chain


import rqalpha
from rqalpha.core.events import EventBus
from rqalpha.const import INSTRUMENT_TYPE
from rqalpha.utils.logger import system_log, user_log, user_system_log
from rqalpha.core.global_var import GlobalVars
from rqalpha.utils.i18n import gettext as _


class Environment(object):
    _env = None  # type: Environment

    def __init__(self, config):
        Environment._env = self
        self.config = config
        self.data_proxy = None  # type: Optional[rqalpha.data.data_proxy.DataProxy]
        self.data_source = None
        self.price_board = None
        self.event_source = None
        self.strategy_loader = None
        self.global_vars = GlobalVars()
        self.persist_provider = None
        self.persist_helper = None
        self.broker = None
        self.profile_deco = None
        self.system_log = system_log
        self.user_log = user_log
        self.user_system_log = user_system_log
        self.event_bus = EventBus()
        self.portfolio = None  # type: Optional[rqalpha.portfolio.Portfolio]
        self.calendar_dt = None  # type: Optional[datetime]
        self.trading_dt = None  # type: Optional[datetime]
        self.mod_dict = None
        self.user_strategy = None
        self._frontend_validators = {}  # type: Dict[INSTRUMENT_TYPE, List]
        self._default_frontend_validators = []
        self._transaction_cost_decider_dict = {}

        # Environment.event_bus used in StrategyUniverse()
        from rqalpha.core.strategy_universe import StrategyUniverse
        self._universe = StrategyUniverse()

    @classmethod
    def get_instance(cls):
        """
        返回已经创建的 Environment 对象
        """
        if Environment._env is None:
            raise RuntimeError(
                _(u"Environment has not been created. Please Use `Environment.get_instance()` after RQAlpha init"))
        return Environment._env

    def set_data_proxy(self, data_proxy):
        self.data_proxy = data_proxy

    def set_data_source(self, data_source):
        self.data_source = data_source

    def set_price_board(self, price_board):
        self.price_board = price_board

    def set_strategy_loader(self, strategy_loader):
        self.strategy_loader = strategy_loader

    def set_portfolio(self, portfolio):
        self.portfolio = portfolio

    def set_hold_strategy(self):
        self.config.extra.is_hold = True

    def cancel_hold_strategy(self):
        self.config.extra.is_hold = False

    def set_persist_helper(self, helper):
        self.persist_helper = helper

    def set_persist_provider(self, provider):
        self.persist_provider = provider

    def set_event_source(self, event_source):
        self.event_source = event_source

    def set_broker(self, broker):
        self.broker = broker

    def add_frontend_validator(self, validator, instrument_type=None):
        if instrument_type:
            self._frontend_validators.setdefault(instrument_type, []).append(validator)
        else:
            self._default_frontend_validators.append(validator)

    def can_submit_order(self, order):
        instrument_type = self.data_proxy.instruments(order.order_book_id).type
        account = self.portfolio.get_account(order.order_book_id)
        for v in chain(self._frontend_validators.get(instrument_type, []), self._default_frontend_validators):
            if not v.can_submit_order(order, account):
                return False
        return True

    def can_cancel_order(self, order):
        instrument_type = self.data_proxy.instruments(order.order_book_id).type
        account = self.portfolio.get_account(order.order_book_id)
        for v in chain(self._frontend_validators.get(instrument_type, []), self._default_frontend_validators):
            if not v.can_cancel_order(order, account):
                return False
        return True

    def get_universe(self):
        return self._universe.get()

    def update_universe(self, universe):
        self._universe.update(universe)

    def get_bar(self, order_book_id):
        return self.data_proxy.get_bar(order_book_id, self.calendar_dt, self.config.base.frequency)

    def get_last_price(self, order_book_id):
        return self.data_proxy.get_last_price(order_book_id)

    def get_instrument(self, order_book_id):
        return self.data_proxy.instruments(order_book_id)

    def get_account_type(self, order_book_id):
        return self.portfolio.get_account_type(order_book_id)

    def get_account(self, order_book_id):
        return self.portfolio.get_account(order_book_id)

    def get_open_orders(self, order_book_id=None):
        return self.broker.get_open_orders(order_book_id)

    def set_transaction_cost_decider(self, instrument_type, decider):
        # type: (INSTRUMENT_TYPE, rqalpha.interface.AbstractTransactionCostDecider) -> None
        self._transaction_cost_decider_dict[instrument_type] = decider

    def _get_transaction_cost_decider(self, order_book_id):
        instrument_type = self.data_proxy.instruments(order_book_id).type
        try:
            return self._transaction_cost_decider_dict[instrument_type]
        except KeyError:
            raise NotImplementedError(_(u"No such transaction cost decider, order_book_id = {}".format(
                order_book_id
            )))

    def get_trade_tax(self, trade):
        return self._get_transaction_cost_decider(trade.order_book_id).get_trade_tax(trade)

    def get_trade_commission(self, trade):
        return self._get_transaction_cost_decider(trade.order_book_id).get_trade_commission(trade)

    def get_order_transaction_cost(self, order):
        return self._get_transaction_cost_decider(order.order_book_id).get_order_transaction_cost(order)

    def update_time(self, calendar_dt, trading_dt):
        # type: (datetime, datetime) -> None
        self.calendar_dt = calendar_dt
        self.trading_dt = trading_dt
