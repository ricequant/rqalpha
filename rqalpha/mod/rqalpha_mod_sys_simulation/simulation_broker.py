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


import jsonpickle
from itertools import chain

from rqalpha.execution_context import ExecutionContext
from rqalpha.interface import AbstractBroker, Persistable
from rqalpha.utils.i18n import gettext as _
from rqalpha.events import EVENT, Event
from rqalpha.const import MATCHING_TYPE, ORDER_STATUS, POSITION_EFFECT, EXECUTION_PHASE
from rqalpha.model.order import Order
from rqalpha.environment import Environment

from .matcher import Matcher, ExerciseMatcher


class SimulationBroker(AbstractBroker, Persistable):
    def __init__(self, env, mod_config):
        self._env = env  # type: Environment
        self._mod_config = mod_config

        self._matcher = None
        self._exercise_matcher = None

        self._match_immediately = mod_config.matching_type == MATCHING_TYPE.CURRENT_BAR_CLOSE

        self._open_orders = []
        self._open_auction_orders = []
        self._open_exercise_orders = []

        self._delayed_orders = []
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

    @property
    def matcher(self):
        if not self._matcher:
            self._matcher = Matcher(self._env, self._mod_config)
        return self._matcher

    @property
    def exercise_matcher(self):
        if not self._exercise_matcher:
            self._exercise_matcher = ExerciseMatcher(self._env)
        return self._exercise_matcher

    def get_open_orders(self, order_book_id=None):
        if order_book_id is None:
            return [order for account, order in self._open_orders]
        else:
            return [order for account, order in self._open_orders if order.order_book_id == order_book_id]

    def get_state(self):
        return jsonpickle.dumps({
            'open_orders': [o.get_state() for account, o in self._open_orders],
            'delayed_orders': [o.get_state() for account, o in self._delayed_orders]
        }).encode('utf-8')

    def set_state(self, state):
        self._open_orders = []
        self._delayed_orders = []

        value = jsonpickle.loads(state.decode('utf-8'))
        for v in value['open_orders']:
            o = Order()
            o.set_state(v)
            account = self._env.get_account(o.order_book_id)
            self._open_orders.append((account, o))
        for v in value['delayed_orders']:
            o = Order()
            o.set_state(v)
            account = self._env.get_account(o.order_book_id)
            self._delayed_orders.append((account, o))

    def submit_order(self, order):
        if order.position_effect == POSITION_EFFECT.MATCH:
            raise NotImplementedError(_("unsupported position_effect {}").format(order.position_effect))
        account = self._env.get_account(order.order_book_id)
        self._env.event_bus.publish_event(Event(EVENT.ORDER_PENDING_NEW, account=account, order=order))
        if order.position_effect == POSITION_EFFECT.EXERCISE:
            return self._open_exercise_orders.append(order)
        if order.is_final():
            return
        if self._env.config.base.frequency == '1d' and not self._match_immediately:
            if ExecutionContext.phase() == EXECUTION_PHASE.OPEN_AUCTION:
                self._open_orders.append((account, order))
                order.active()
            else:
                self._delayed_orders.append((account, order))
            return
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
            try:
                self._delayed_orders.remove((account, order))
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
        self._open_orders = self._delayed_orders
        self._delayed_orders = []

    def pre_settlement(self, __):
        self.exercise_matcher.match(self._open_exercise_orders)
        self._open_exercise_orders.clear()

    def on_bar(self, _):
        self.matcher.update(self._env.calendar_dt, self._env.trading_dt)
        self._match()

    def on_tick(self, event):
        tick = event.tick
        self.matcher.update(self._env.calendar_dt, self._env.trading_dt)
        self._match(tick.order_book_id)

    def _match(self, order_book_id=None):
        order_filter = None if order_book_id is None else lambda a_and_o: a_and_o[1].order_book_id == order_book_id
        self.matcher.match(filter(order_filter, self._open_orders), open_auction=False)
        self.matcher.match(filter(order_filter, self._open_auction_orders), open_auction=True)
        final_orders = [(a, o) for a, o in chain(self._open_orders, self._open_auction_orders) if o.is_final()]
        self._open_orders = [(a, o) for a, o in chain(self._open_orders, self._open_auction_orders) if not o.is_final()]
        self._open_auction_orders.clear()
        for account, order in final_orders:
            if order.status == ORDER_STATUS.REJECTED or order.status == ORDER_STATUS.CANCELLED:
                self._env.event_bus.publish_event(Event(EVENT.ORDER_UNSOLICITED_UPDATE, account=account, order=order))
