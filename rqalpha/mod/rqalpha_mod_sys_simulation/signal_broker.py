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


from copy import copy

from rqalpha.interface import AbstractBroker
from rqalpha.utils.logger import user_system_log
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils import is_valid_price
from rqalpha.core.events import EVENT, Event
from rqalpha.model.trade import Trade
from rqalpha.const import SIDE, ORDER_TYPE, POSITION_EFFECT

from .slippage import SlippageDecider


class SignalBroker(AbstractBroker):
    def __init__(self, env, mod_config):
        self._env = env
        self._slippage_decider = SlippageDecider(mod_config.slippage_model, mod_config.slippage)
        self._price_limit = mod_config.price_limit

    def get_open_orders(self, order_book_id=None):
        return []

    def submit_order(self, order):
        if order.position_effect == POSITION_EFFECT.EXERCISE:
            raise NotImplementedError("SignalBroker does not support exercise order temporarily")
        account = self._env.get_account(order.order_book_id)
        self._env.event_bus.publish_event(Event(EVENT.ORDER_PENDING_NEW, account=account, order=copy(order)))
        if order.is_final():
            return
        order.active()
        self._env.event_bus.publish_event(Event(EVENT.ORDER_CREATION_PASS, account=account, order=copy(order)))
        self._match(account, order)

    def cancel_order(self, order):
        user_system_log.warn(_(u"cancel_order function is not supported in signal mode"))
        return None

    def _match(self, account, order):
        order_book_id = order.order_book_id
        price_board = self._env.price_board

        last_price = price_board.get_last_price(order_book_id)

        if not is_valid_price(last_price):
            instrument = self._env.get_instrument(order_book_id)
            listed_date = instrument.listed_date.date()
            if listed_date == self._env.trading_dt.date():
                reason = _(
                    "Order Cancelled: current security [{order_book_id}] can not be traded in listed date [{listed_date}]").format(
                    order_book_id=order_book_id,
                    listed_date=listed_date,
                )
            else:
                reason = _(u"Order Cancelled: current bar [{order_book_id}] miss market data.").format(
                    order_book_id=order_book_id)
            order.mark_rejected(reason)
            self._env.event_bus.publish_event(Event(EVENT.ORDER_UNSOLICITED_UPDATE, account=account, order=copy(order)))
            return

        if order.type == ORDER_TYPE.LIMIT:
            deal_price = order.frozen_price
        else:
            deal_price = last_price

        if self._price_limit:
            """
            在 Signal 模式下，不再阻止涨跌停是否买进，price_limit 参数表示是否给出警告提示。
            """
            if order.position_effect != POSITION_EFFECT.EXERCISE:
                if order.side == SIDE.BUY and deal_price >= price_board.get_limit_up(order_book_id):
                    user_system_log.warning(
                        _(u"You have traded {order_book_id} with {quantity} lots in limit up status").format(
                            order_book_id=order_book_id, quantity=order.quantity
                        )
                    )

                if order.side == SIDE.SELL and deal_price <= price_board.get_limit_down(order_book_id):
                    user_system_log.warning(
                        _(u"You have traded {order_book_id} with {quantity} lots in limit down status").format(
                            order_book_id=order_book_id, quantity=order.quantity
                        )
                    )

        ct_amount = account.calc_close_today_amount(order_book_id, order.quantity, order.position_direction)
        trade_price = self._slippage_decider.get_trade_price(order, deal_price)
        trade = Trade.__from_create__(
            order_id=order.order_id,
            price=trade_price,
            amount=order.quantity,
            side=order.side,
            position_effect=order.position_effect,
            order_book_id=order_book_id,
            frozen_price=order.frozen_price,
            close_today_amount=ct_amount
        )
        trade._commission = self._env.get_trade_commission(trade)
        trade._tax = self._env.get_trade_tax(trade)
        order.fill(trade)

        self._env.event_bus.publish_event(Event(EVENT.TRADE, account=account, trade=trade, order=copy(order)))
