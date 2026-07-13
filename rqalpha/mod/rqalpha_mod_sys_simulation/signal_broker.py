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

from typing import Dict

from rqalpha.interface import AbstractBroker
from rqalpha.utils.logger import user_system_log
from rqalpha.utils.i18n import gettext as _
from rqalpha.core.events import EVENT, Event
from rqalpha.core.execution_context import ExecutionContext
from rqalpha.const import POSITION_EFFECT, INSTRUMENT_TYPE, EXECUTION_PHASE, ORDER_STATUS
from rqalpha.model import Order
from rqalpha.utils.functools import lru_cache
from rqalpha.environment import Environment

from .matcher import AbstractMatcher, SignalMatcher


class SignalBroker(AbstractBroker):
    def __init__(self, env: Environment, mod_config, partial_fill_on_insufficient_cash: bool = False):
        self._signal_default_matcher: AbstractMatcher = SignalMatcher(env, mod_config, partial_fill_on_insufficient_cash)
        self._env: Environment = env
        self._matchers: Dict[INSTRUMENT_TYPE, AbstractMatcher] = {}

    @lru_cache(1024)
    def _get_matcher(self, order_book_id: str) -> AbstractMatcher:
        instrument_type = self._env.data_proxy.get_active_instrument(order_book_id, self._env.trading_dt).type
        try:
            return self._matchers[instrument_type]
        except KeyError:
            return self._matchers.setdefault(instrument_type, self._signal_default_matcher)

    def get_open_orders(self, order_book_id=None):
        return []

    def submit_order(self, order: Order):
        if order.position_effect == POSITION_EFFECT.EXERCISE:
            raise NotImplementedError("SignalBroker does not support exercise order temporarily")
        account = self._env.get_account(order.order_book_id)
        self._env.event_bus.publish_event(Event(EVENT.ORDER_PENDING_NEW, account=account, order=order))
        if order.is_final():
            return
        order.active()
        self._env.event_bus.publish_event(Event(EVENT.ORDER_CREATION_PASS, account=account, order=order))
        open_auction = ExecutionContext.phase() == EXECUTION_PHASE.OPEN_AUCTION
        self._get_matcher(order.order_book_id).match(account=account, order=order, open_auction=open_auction)

        if order.is_final():
            if order.status == ORDER_STATUS.REJECTED or order.status == ORDER_STATUS.CANCELLED:
                self._env.event_bus.publish_event(Event(EVENT.ORDER_UNSOLICITED_UPDATE, account=account, order=order))

    def cancel_order(self, order):
        user_system_log.warning(_(u"cancel_order function is not supported in signal mode"))
        return None

    def register_matcher(self, instrument_type: INSTRUMENT_TYPE, matcher: AbstractMatcher) -> None:
        self._matchers[instrument_type] = matcher
