from rqalpha.const import MATCHING_TYPE, ORDER_TYPE, POSITION_EFFECT, SIDE
from rqalpha.environment import Environment
from rqalpha.portfolio.account import Account
from rqalpha.model.order import Order, ALGO_ORDER_STYLES
from rqalpha.model.instrument import Instrument
from rqalpha.mod.utils import round_order_quantity
from rqalpha.utils import is_valid_price
from rqalpha.utils.i18n import gettext as _
from .base import BaseMatcher, OrderRejected, OrderCancelled, OrderNotMatchable


class DefaultBarMatcher(BaseMatcher):
    SUPPORT_POSITION_EFFECTS = (POSITION_EFFECT.OPEN, POSITION_EFFECT.CLOSE, POSITION_EFFECT.CLOSE_TODAY)
    SUPPORT_SIDES = (SIDE.BUY, SIDE.SELL)

    def __init__(self, env: Environment, mod_config, partial_fill_on_insufficient_cash: bool = False):
        super(DefaultBarMatcher, self).__init__(env, mod_config, partial_fill_on_insufficient_cash)
        self._deal_price_decider = self._create_deal_price_decider(mod_config.matching_type)

    def _create_deal_price_decider(self, matching_type):
        decider_dict = {
            MATCHING_TYPE.CURRENT_BAR_CLOSE: self._current_bar_close_decider,
            MATCHING_TYPE.VWAP: self._vwap_decider,
            MATCHING_TYPE.NEXT_BAR_OPEN: self._next_bar_open_decider,
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

    def _open_auction_deal_price_decider(self, order_book_id, _):
        return self._env.data_proxy.get_open_auction_bar(order_book_id, self._env.trading_dt).open

    def _get_bar_volume(self, order, open_auction=False):
        if open_auction:
            volume = self._env.data_proxy.get_open_auction_volume(order.order_book_id, self._env.trading_dt)
        else:
            if isinstance(order.style, ALGO_ORDER_STYLES):
                _, volume = self._env.data_proxy.get_algo_bar(order.order_book_id, order.style, self._env.calendar_dt)
            else:
                volume = self._env.get_bar(order.order_book_id).volume
        return volume

    def _get_deal_price(
        self, order: Order, instrument: Instrument, open_auction: bool = False
    ) -> float:
        if open_auction:
            deal_price = self._open_auction_deal_price_decider(order.order_book_id, order.side)
        else:
            if isinstance(order.style, ALGO_ORDER_STYLES):
                deal_price, v = self._env.data_proxy.get_algo_bar(order.order_book_id, order.style, self._env.calendar_dt)
            else:
                deal_price = self._deal_price_decider(order.order_book_id, order.side)
        if is_valid_price(deal_price):
            return deal_price

        listed_date = instrument.listed_date.date()
        if listed_date == self._env.trading_dt.date():
            raise OrderRejected(self._listed_date_reject_reason(order, listed_date))
        elif isinstance(order.style, ALGO_ORDER_STYLES):
            reason = _(u"Order Rejected: {order_book_id} miss market data or bar no volume.").format(
                order_book_id=instrument.order_book_id
            )
            raise OrderRejected(reason)
        raise OrderNotMatchable(_("Current bar missing market data."))

    def _get_liquidity_limited_fill(self, order: Order, instrument: Instrument, open_auction: bool = False) -> int:
        if self._inactive_limit:
            bar_volume = self._get_bar_volume(order, open_auction=open_auction)
            if bar_volume == 0:
                reason = _(u"Order Cancelled: {order_book_id} bar no volume").format(order_book_id=order.order_book_id)
                raise OrderCancelled(reason)

        if self._volume_limit:
            volume = self._get_bar_volume(order, open_auction=open_auction)
            if volume == volume:
                volume_limit = round(volume * self._volume_percent) - self._turnover[order.order_book_id]
                volume_limit = round_order_quantity(instrument, volume_limit)
                if volume_limit <= 0:
                    if order.type == ORDER_TYPE.MARKET:
                        reason = _(u"Order Cancelled: market order {order_book_id} volume {order_volume} due to volume limit").format(
                            order_book_id=order.order_book_id, order_volume=order.quantity
                        )
                        raise OrderCancelled(reason)
                    raise OrderNotMatchable(_("Current liquidity is 0."))
                fill = min(order.unfilled_quantity, volume_limit)
            else:
                fill = order.unfilled_quantity
        else:
            fill = order.unfilled_quantity

        return fill

    def _handle_unfilled_order(self, account: Account, order: Order, open_auction: bool):
        if order.type == ORDER_TYPE.MARKET:
            reason = _(
                u"Order Cancelled: market order {order_book_id} volume {order_volume} is"
                u" larger than {volume_percent_limit} percent of current bar volume, fill {filled_volume} actually"
            ).format(
                order_book_id=order.order_book_id,
                order_volume=order.quantity,
                filled_volume=order.filled_quantity,
                volume_percent_limit=self._volume_percent * 100.0
            )
            raise OrderCancelled(reason)

    def match(self, account, order, open_auction):
        # order 是否合法
        if not (order.position_effect in self.SUPPORT_POSITION_EFFECTS and order.side in self.SUPPORT_SIDES):
            raise NotImplementedError
        super().match(account, order, open_auction)

    def update(self, event):
        self._turnover.clear()
