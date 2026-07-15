from rqalpha.const import ORDER_TYPE, POSITION_EFFECT, SIDE
from rqalpha.model.order import Order, ALGO_ORDER_STYLES
from rqalpha.model.instrument import Instrument
from rqalpha.portfolio.account import Account
from rqalpha.utils import is_valid_price
from rqalpha.utils.price_limits import reaches_limit
from rqalpha.utils.i18n import gettext as _
from .base import BaseMatcher, OrderRejected


class SignalMatcher(BaseMatcher):
    def _get_deal_price(self, order: Order, instrument: Instrument, open_auction: bool) -> float:
        last_price = self._env.price_board.get_last_price(order.order_book_id)
        if not is_valid_price(last_price):
            listed_date = instrument.listed_date.date()
            if listed_date == self._env.trading_dt.date():
                raise OrderRejected(self._listed_date_reject_reason(order, listed_date))
            else:
                reason = _(u"Order Cancelled: current bar [{order_book_id}] miss market data.").format(
                    order_book_id=order.order_book_id
                )
                raise OrderRejected(reason)
        if order.type == ORDER_TYPE.LIMIT:
            deal_price = order.frozen_price
        elif isinstance(order.style, ALGO_ORDER_STYLES):
            deal_price, _algo_volume = self._env.data_proxy.get_algo_bar(
                order.order_book_id, order.style, self._env.calendar_dt
            )
        else:
            deal_price = last_price

        if not is_valid_price(deal_price):
            reason = _(u"Order Cancelled: {order_book_id} bar no volume").format(order_book_id=order.order_book_id)
            raise OrderRejected(reason)
        return deal_price

    def _get_liquidity_limited_fill(self, order: Order, instrument: Instrument, open_auction: bool = False) -> int:
        return order.quantity

    def _get_execution_price(self, order, deal_price, open_auction):
        return self._slippage_decider.get_trade_price(order, deal_price)

    def _handle_unfilled_order(self, account: Account, order: Order, open_auction: bool):
        pass

    def match(self, account: Account, order: Order, open_auction: bool):
        if order.position_effect == POSITION_EFFECT.EXERCISE:
            return
        super().match(account, order, open_auction)
        if not order.is_final() and order.unfilled_quantity != 0:
            # 在 signal 模式中，所有不符合交易条件的情况都应该拒单，不会将订单留到下一个 bar 中
            # 执行父类的 matcher，存在使用限价单并且价格等于涨跌停价时，订单不执行但是状态保留 Active，需要在此处直接执行拒单
            reason = _("Order Cancelled: current bar [{order_book_id}] reach the {limit_up_or_down} price.").format(
                order_book_id=order.order_book_id, limit_up_or_down="limit_up" if order.side == SIDE.BUY else "limit_down",
            )
            order.mark_rejected(reason)

    def update(self, event):
        pass
