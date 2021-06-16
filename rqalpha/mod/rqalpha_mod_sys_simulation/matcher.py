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

from collections import defaultdict

from rqalpha.const import MATCHING_TYPE, ORDER_TYPE, POSITION_EFFECT, SIDE
from rqalpha.environment import Environment
from rqalpha.core.events import EVENT, Event
from rqalpha.model.order import Order
from rqalpha.model.trade import Trade
from rqalpha.portfolio.account import Account
from rqalpha.utils import is_valid_price
from rqalpha.utils.i18n import gettext as _
from .slippage import SlippageDecider


class AbstractMatcher:
    def match(self, account, order, open_auction):
        # type: (Account, Order, bool) -> None
        raise NotImplementedError

    def update(self):
        raise NotImplementedError


class DefaultMatcher(AbstractMatcher):
    def __init__(self, env, mod_config):
        self._slippage_decider = SlippageDecider(mod_config.slippage_model, mod_config.slippage)
        self._turnover = defaultdict(int)
        self._volume_percent = mod_config.volume_percent
        self._price_limit = mod_config.price_limit
        self._liquidity_limit = mod_config.liquidity_limit and env.config.base.frequency == "tick"
        self._inactive_limit = env.config.base.frequency != 'tick' and mod_config.inactive_limit
        self._volume_limit = mod_config.volume_limit
        self._env = env  # type: Environment
        self._deal_price_decider = self._create_deal_price_decider(mod_config.matching_type)

    def _create_deal_price_decider(self, matching_type):
        decider_dict = {
            MATCHING_TYPE.CURRENT_BAR_CLOSE: self._current_bar_close_decider,
            MATCHING_TYPE.VWAP: self._vwap_decider,
            MATCHING_TYPE.NEXT_BAR_OPEN: self._next_bar_open_decider,
            MATCHING_TYPE.NEXT_TICK_LAST: lambda order_book_id, side: self._env.price_board.get_last_price(
                order_book_id),
            MATCHING_TYPE.NEXT_TICK_BEST_OWN: lambda order_book_id, side: self._best_own_price_decider(order_book_id,
                                                                                                       side),
            MATCHING_TYPE.COUNTERPARTY_OFFER: None,
            MATCHING_TYPE.NEXT_TICK_BEST_COUNTERPARTY: lambda order_book_id, side: (
                self._env.price_board.get_a1(order_book_id) if side == SIDE.BUY else self._env.price_board.get_b1(
                    order_book_id))
        }
        return decider_dict[matching_type]

    def _current_bar_close_decider(self, order_book_id, _):
        try:
            return self._env.get_bar(order_book_id).close
        except (KeyError, TypeError):
            return 0

    def _next_bar_open_decider(self, order_book_id, _):
        try:
            return self._env.get_bar(order_book_id).open
        except (KeyError, TypeError):
            return 0

    def _vwap_decider(self, order_book_id, _):
        try:
            contract_multiplier = self._env.get_instrument(order_book_id).contract_multiplier
            bar = self._env.get_bar(order_book_id)
            return bar.total_turnover / bar.volume / contract_multiplier
        except (KeyError, TypeError, ZeroDivisionError):
            return 0

    def _best_own_price_decider(self, order_book_id, side):
        price = self._env.price_board.get_b1(order_book_id) if side == SIDE.BUY else self._env.price_board.get_a1(
            order_book_id)
        if price == 0:
            price = self._env.price_board.get_last_price(order_book_id)
        return price

    def _open_auction_deal_price_decider(self, order_book_id, _):
        return self._env.data_proxy.get_open_auction_bar(order_book_id, self._env.calendar_dt).open

    SUPPORT_POSITION_EFFECTS = (POSITION_EFFECT.OPEN, POSITION_EFFECT.CLOSE, POSITION_EFFECT.CLOSE_TODAY)
    SUPPORT_SIDES = (SIDE.BUY, SIDE.SELL)

    def match(self, account, order, open_auction):
        # type: (Account, Order, bool) -> None
        if not (order.position_effect in self.SUPPORT_POSITION_EFFECTS and order.side in self.SUPPORT_SIDES):
            raise NotImplementedError
        order_book_id = order.order_book_id
        instrument = self._env.get_instrument(order_book_id)

        if open_auction:
            deal_price = self._open_auction_deal_price_decider(order_book_id, order.side)
        else:
            deal_price = self._deal_price_decider(order_book_id, order.side)

        if not is_valid_price(deal_price):
            listed_date = instrument.listed_date.date()
            if listed_date == self._env.trading_dt.date():
                reason = _(
                    u"Order Cancelled: current security [{order_book_id}] can not be traded"
                    u" in listed date [{listed_date}]").format(
                    order_book_id=order.order_book_id,
                    listed_date=listed_date,
                )
            else:
                reason = _(u"Order Cancelled: current bar [{order_book_id}] miss market data.").format(
                    order_book_id=order.order_book_id)
            order.mark_rejected(reason)
            return

        price_board = self._env.price_board
        if order.type == ORDER_TYPE.LIMIT:
            if order.side == SIDE.BUY and order.price < deal_price:
                return
            if order.side == SIDE.SELL and order.price > deal_price:
                return
            # 是否限制涨跌停不成交
            if self._price_limit:
                if order.side == SIDE.BUY and deal_price >= price_board.get_limit_up(order_book_id):
                    return
                if order.side == SIDE.SELL and deal_price <= price_board.get_limit_down(order_book_id):
                    return
            if self._liquidity_limit:
                if order.side == SIDE.BUY and price_board.get_a1(order_book_id) == 0:
                    return
                if order.side == SIDE.SELL and price_board.get_b1(order_book_id) == 0:
                    return
        else:
            if self._price_limit:
                if order.side == SIDE.BUY and deal_price >= price_board.get_limit_up(order_book_id):
                    reason = _(
                        "Order Cancelled: current bar [{order_book_id}] reach the limit_up price."
                    ).format(order_book_id=order.order_book_id)
                    order.mark_rejected(reason)
                    return
                if order.side == SIDE.SELL and deal_price <= price_board.get_limit_down(order_book_id):
                    reason = _(
                        "Order Cancelled: current bar [{order_book_id}] reach the limit_down price."
                    ).format(order_book_id=order.order_book_id)
                    order.mark_rejected(reason)
                    return
            if self._liquidity_limit:
                if order.side == SIDE.BUY and price_board.get_a1(order_book_id) == 0:
                    reason = _(
                        "Order Cancelled: [{order_book_id}] has no liquidity."
                    ).format(order_book_id=order.order_book_id)
                    order.mark_rejected(reason)
                    return
                if order.side == SIDE.SELL and price_board.get_b1(order_book_id) == 0:
                    reason = _(
                        "Order Cancelled: [{order_book_id}] has no liquidity."
                    ).format(order_book_id=order.order_book_id)
                    order.mark_rejected(reason)
                    return

        if self._inactive_limit:
            bar_volume = self._env.get_bar(order_book_id).volume
            if bar_volume == 0:
                reason = _(u"Order Cancelled: {order_book_id} bar no volume").format(order_book_id=order.order_book_id)
                order.mark_cancelled(reason)
                return

        if self._volume_limit:
            if open_auction:
                volume = self._env.data_proxy.get_open_auction_bar(order_book_id, self._env.calendar_dt).volume
            else:
                volume = self._env.get_bar(order_book_id).volume
            if volume == volume:
                volume_limit = round(volume * self._volume_percent) - self._turnover[order.order_book_id]

                round_lot = instrument.round_lot
                volume_limit = (volume_limit // round_lot) * round_lot
                if volume_limit <= 0:
                    if order.type == ORDER_TYPE.MARKET:
                        reason = _(u"Order Cancelled: market order {order_book_id} volume {order_volume}"
                                   u" due to volume limit").format(
                            order_book_id=order.order_book_id,
                            order_volume=order.quantity
                        )
                        order.mark_cancelled(reason)
                    return

                fill = min(order.unfilled_quantity, volume_limit)
            else:
                fill = order.unfilled_quantity
        else:
            fill = order.unfilled_quantity

        ct_amount = account.calc_close_today_amount(order_book_id, fill, order.position_direction)
        price = self._slippage_decider.get_trade_price(order, deal_price)

        trade = Trade.__from_create__(
            order_id=order.order_id,
            price=price,
            amount=fill,
            side=order.side,
            position_effect=order.position_effect,
            order_book_id=order.order_book_id,
            frozen_price=order.frozen_price,
            close_today_amount=ct_amount
        )
        trade._commission = self._env.get_trade_commission(trade)
        trade._tax = self._env.get_trade_tax(trade)
        order.fill(trade)
        self._turnover[order.order_book_id] += fill

        self._env.event_bus.publish_event(Event(EVENT.TRADE, account=account, trade=trade, order=order))

        if order.type == ORDER_TYPE.MARKET and order.unfilled_quantity != 0:
            reason = _(
                u"Order Cancelled: market order {order_book_id} volume {order_volume} is"
                u" larger than {volume_percent_limit} percent of current bar volume, fill {filled_volume} actually"
            ).format(
                order_book_id=order.order_book_id,
                order_volume=order.quantity,
                filled_volume=order.filled_quantity,
                volume_percent_limit=self._volume_percent * 100.0
            )
            order.mark_cancelled(reason)

    def update(self):
        self._turnover.clear()


class CounterPartyOfferMatcher(DefaultMatcher):
    def __init__(self, env, mod_config):
        super(CounterPartyOfferMatcher, self).__init__(env, mod_config)
        self._env = env
        self._a_volume = {}
        self._b_volume = {}
        self._a_price = {}
        self._b_price = {}
        self._env.event_bus.add_listener(EVENT.TICK, self._pre_tick)

    def match(self, account, order, open_auction):
        # type: (Account, Order, bool) -> None
        #
        """限价撮合：
        订单买价>卖x价
        买量>卖x量，按照卖x价成交，订单减去卖x量，继续撮合卖x+1，直至该tick中所有报价被买完。买完后若有剩余买量，则在下一个tick继续撮合。
        买量<卖x量，按照卖x价成交。
        反之亦然
        市价单：
        按照该tick，a1，b1进行成交，剩余订单直接撤单
        """
        order_book_id = order.order_book_id

        self._pop_volume_and_price(order)
        if order.side == SIDE.BUY:
            if len(self._a_volume[order_book_id]) == 0:
                return
            volume_limit = self._a_volume[order_book_id][0]
            matching_price = self._a_price[order_book_id][0]
        else:
            if len(self._b_volume[order_book_id]) == 0:
                return
            volume_limit = self._b_volume[order_book_id][0]
            matching_price = self._b_price[order_book_id][0]

        if order.type == ORDER_TYPE.MARKET:
            amount = volume_limit
        else:
            if volume_limit != volume_limit:
                return
            amount = volume_limit
            if amount == 0.0 and order.unfilled_quantity != 0:
                # if order.unfilled_quantity != 0:
                return self.match(account, order, open_auction)

        if matching_price != matching_price:
            return

        if not (order.position_effect in self.SUPPORT_POSITION_EFFECTS and order.side in self.SUPPORT_SIDES):
            raise NotImplementedError
        if order.type == ORDER_TYPE.LIMIT:
            if order.side == SIDE.BUY and order.price < matching_price:
                return
            if order.side == SIDE.SELL and order.price > matching_price:
                return
        fill = order.unfilled_quantity
        ct_amount = account.calc_close_today_amount(order_book_id, fill, order.position_direction)

        trade = Trade.__from_create__(
            order_id=order.order_id,
            price=matching_price,
            amount=min(amount, fill),
            side=order.side,
            position_effect=order.position_effect,
            order_book_id=order.order_book_id,
            frozen_price=order.frozen_price,
            close_today_amount=ct_amount
        )
        trade._commission = self._env.get_trade_commission(trade)
        trade._tax = self._env.get_trade_tax(trade)
        order.fill(trade)
        self._env.event_bus.publish_event(Event(EVENT.TRADE, account=account, trade=trade, order=order))

        if order.side == SIDE.BUY:
            self._a_volume[order.order_book_id][0] -= min(amount, fill)
        else:
            self._b_volume[order.order_book_id][0] -= min(amount, fill)

        if order.type == ORDER_TYPE.MARKET and order.unfilled_quantity != 0:
            reason = _("Order Cancelled: market order {order_book_id} fill {filled_volume} actually").format(
                order_book_id=order.order_book_id,
                filled_volume=order.filled_quantity,
            )
            order.mark_cancelled(reason)
            return
        if order.unfilled_quantity != 0:
            self.match(account, order, open_auction)

    def _pop_volume_and_price(self, order):
        try:
            if order.side == SIDE.BUY:
                if self._a_volume[order.order_book_id][0] == 0:
                    self._a_volume[order.order_book_id].pop(0)
                    self._a_price[order.order_book_id].pop(0)
            else:
                if self._b_volume[order.order_book_id][0] == 0:
                    self._b_volume[order.order_book_id].pop(0)
                    self._b_price[order.order_book_id].pop(0)
        except IndexError:
            return

    def _pre_tick(self, event):
        order_book_id = event.tick.order_book_id
        self._a_volume[order_book_id] = event.tick.ask_vols
        self._b_volume[order_book_id] = event.tick.bid_vols

        self._a_price[order_book_id] = event.tick.asks
        self._b_price[order_book_id] = event.tick.bids

    def update(self):
        pass
