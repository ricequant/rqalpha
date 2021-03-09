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

from typing import List, Tuple, Dict
from rqalpha.utils.functools import lru_cache
from itertools import chain

import jsonpickle

from rqalpha.portfolio.account import Account
from rqalpha.core.execution_context import ExecutionContext
from rqalpha.interface import AbstractBroker, Persistable
from rqalpha.utils.i18n import gettext as _
from rqalpha.core.events import EVENT, Event
from rqalpha.const import MATCHING_TYPE, ORDER_STATUS, POSITION_EFFECT, EXECUTION_PHASE, INSTRUMENT_TYPE
from rqalpha.model.order import Order
from rqalpha.environment import Environment

from .matcher import DefaultMatcher, AbstractMatcher


class SimulationBroker(AbstractBroker, Persistable):
    def __init__(self, env, mod_config):
        self._env = env  # type: Environment
        self._mod_config = mod_config

        self._matchers = {}  # type: Dict[INSTRUMENT_TYPE, AbstractMatcher]

        self._match_immediately = mod_config.matching_type in [MATCHING_TYPE.CURRENT_BAR_CLOSE, MATCHING_TYPE.VWAP]

        self._open_orders = []  # type: List[Tuple[Account, Order]]
        self._open_auction_orders = []   # type: List[Tuple[Account, Order]]
        self._open_exercise_orders = []  # type: List[Tuple[Account, Order]]

        self._frontend_validator = {}

        # 该事件会触发策略的before_trading函数
        self._env.event_bus.add_listener(EVENT.BEFORE_TRADING, self.before_trading)
        # 该事件会触发策略的handle_bar函数
        self._env.event_bus.add_listener(EVENT.BAR, self.on_bar)
        # 该事件会触发策略的handel_tick函数
        self._env.event_bus.add_listener(EVENT.TICK, self.on_tick)
        # 该事件会触发策略的after_trading函数
        self._env.event_bus.add_listener(EVENT.AFTER_TRADING, self.after_trading)
        self._env.event_bus.add_listener(EVENT.PRE_SETTLEMENT, self.pre_settlement)

    @lru_cache(1024)
    def _get_matcher(self, order_book_id):
        # type: (str) -> AbstractMatcher
        instrument_type = self._env.data_proxy.instruments(order_book_id).type
        try:
            return self._matchers[instrument_type]
        except KeyError:
            return self._matchers.setdefault(instrument_type, DefaultMatcher(self._env, self._mod_config))

    def register_matcher(self, instrument_type, matcher):
        # type: (INSTRUMENT_TYPE, AbstractMatcher) -> None
        self._matchers[instrument_type] = matcher

    def get_open_orders(self, order_book_id=None):
        if order_book_id is None:
            return [order for account, order in self._open_orders]
        else:
            return [order for account, order in self._open_orders if order.order_book_id == order_book_id]

    def get_state(self):
        return jsonpickle.dumps({
            'open_orders': [o.get_state() for account, o in self._open_orders],
            "open_auction_orders": [o.get_state() for account, o in self._open_auction_orders],
        }).encode('utf-8')

    def set_state(self, state):
        def _account_order_from_state(order_state):
            o = Order()
            o.set_state(order_state)
            account = self._env.get_account(o.order_book_id)
            return account, o

        value = jsonpickle.loads(state.decode('utf-8'))
        self._open_orders = [_account_order_from_state(v) for v in value["open_orders"]]
        self._open_auction_orders = [_account_order_from_state(v) for v in value.get("open_auction_orders", [])]

    def submit_order(self, order):
        if order.position_effect == POSITION_EFFECT.MATCH:
            raise TypeError(_("unsupported position_effect {}").format(order.position_effect))
        account = self._env.get_account(order.order_book_id)
        self._env.event_bus.publish_event(Event(EVENT.ORDER_PENDING_NEW, account=account, order=order))
        if order.is_final():
            return
        if order.position_effect == POSITION_EFFECT.EXERCISE:
            return self._open_exercise_orders.append((account, order))
        if ExecutionContext.phase() == EXECUTION_PHASE.OPEN_AUCTION:
            self._open_auction_orders.append((account, order))
        else:
            self._open_orders.append((account, order))
        order.active()
        self._env.event_bus.publish_event(Event(EVENT.ORDER_CREATION_PASS, account=account, order=order))
        if self._match_immediately:
            self._match()

    def cancel_order(self, order):
        account = self._env.get_account(order.order_book_id)

        self._env.event_bus.publish_event(Event(EVENT.ORDER_PENDING_CANCEL, account=account, order=order))

        order.mark_cancelled(_(u"{order_id} order has been cancelled by user.").format(order_id=order.order_id))

        self._env.event_bus.publish_event(Event(EVENT.ORDER_CANCELLATION_PASS, account=account, order=order))

        try:
            self._open_orders.remove((account, order))
        except ValueError:
            pass

    def before_trading(self, _):
        for account, order in self._open_orders:
            order.active()
            self._env.event_bus.publish_event(Event(EVENT.ORDER_CREATION_PASS, account=account, order=order))

    def after_trading(self, __):
        for account, order in self._open_orders:
            order.mark_rejected(_(u"Order Rejected: {order_book_id} can not match. Market close.").format(
                order_book_id=order.order_book_id
            ))
            self._env.event_bus.publish_event(Event(EVENT.ORDER_UNSOLICITED_UPDATE, account=account, order=order))
        self._open_orders = []

    def pre_settlement(self, __):
        for account, order in self._open_exercise_orders:
            self._get_matcher(order.order_book_id).match(account, order, False)
        self._open_exercise_orders.clear()

    def on_bar(self, _):
        for matcher in self._matchers.values():
            matcher.update()
        self._match()

    def on_tick(self, event):
        tick = event.tick
        self._get_matcher(tick.order_book_id).update()
        self._match(tick.order_book_id)

    def _match(self, order_book_id=None):
        order_filter = None if order_book_id is None else lambda a_and_o: a_and_o[1].order_book_id == order_book_id
        for account, order in filter(order_filter, self._open_orders):
            self._get_matcher(order.order_book_id).match(account, order, open_auction=False)
        for account, order in filter(order_filter, self._open_auction_orders):
            self._get_matcher(order.order_book_id).match(account, order, open_auction=True)
        final_orders = [(a, o) for a, o in chain(self._open_orders, self._open_auction_orders) if o.is_final()]
        self._open_orders = [(a, o) for a, o in chain(self._open_orders, self._open_auction_orders) if not o.is_final()]
        self._open_auction_orders.clear()

        for account, order in final_orders:
            if order.status == ORDER_STATUS.REJECTED or order.status == ORDER_STATUS.CANCELLED:
                self._env.event_bus.publish_event(Event(EVENT.ORDER_UNSOLICITED_UPDATE, account=account, order=order))
