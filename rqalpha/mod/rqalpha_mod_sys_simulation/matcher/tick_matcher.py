import datetime
from typing import Dict

from rqalpha.const import MATCHING_TYPE, ORDER_TYPE, POSITION_EFFECT, SIDE
from rqalpha.environment import Environment
from rqalpha.core.events import EVENT, Event
from rqalpha.model.order import Order
from rqalpha.model.trade import Trade
from rqalpha.model.tick import TickObject
from rqalpha.model.instrument import Instrument
from rqalpha.portfolio.account import Account
from rqalpha.utils import is_valid_price
from rqalpha.mod.utils import round_order_quantity
from rqalpha.utils.i18n import gettext as _
from .base import BaseMatcher, OrderRejected, OrderCancelled, OrderNotMatchable


class DefaultTickMatcher(BaseMatcher):
    """ tick回测使用 """

    SUPPORT_POSITION_EFFECTS = (POSITION_EFFECT.OPEN, POSITION_EFFECT.CLOSE, POSITION_EFFECT.CLOSE_TODAY)
    SUPPORT_SIDES = (SIDE.BUY, SIDE.SELL)

    def __init__(self, env: Environment, mod_config, partial_fill_on_insufficient_cash: bool = False):
        super(DefaultTickMatcher, self).__init__(env, mod_config, partial_fill_on_insufficient_cash)
        self._deal_price_decider = self._create_deal_price_decider(mod_config.matching_type)
        self._liquidity_limit = mod_config.liquidity_limit
        # 每个交易日期内的上一个时刻的tick(第一个除外)
        self._last_tick: Dict[str, TickObject] = dict()
        # 当前的tick
        self._cur_tick: Dict[str, TickObject] = dict()

        # 订阅一些事件
        self._env.event_bus.add_listener(EVENT.BEFORE_TRADING, self._on_before_trading)

    def _create_deal_price_decider(self, matching_type):
        decider_dict = {
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

    def _best_own_price_decider(self, order_book_id, side):
        """ 己方最优价 """
        price = self._env.price_board.get_b1(order_book_id) if side == SIDE.BUY else self._env.price_board.get_a1(
            order_book_id)
        if price == 0:
            price = self._env.price_board.get_last_price(order_book_id)
        return price

    def _on_before_trading(self, event):
        # 在每个交易日的盘前删除前一个交易日的数据
        self._last_tick.clear()
        self._cur_tick.clear()

    def _get_today_history_ticks(self, order_book_id, count):
        """ 获取当前交易日的历史tick数据 """
        cal_dt = self._env.calendar_dt
        tick_list = self._env.data_proxy.history_ticks(order_book_id, count, cal_dt)
        start = cal_dt if cal_dt.hour >= 19 else cal_dt - datetime.timedelta(days=1)
        start = start.replace(hour=17, minute=0, second=0, microsecond=0)
        ticks = [tick for tick in tick_list if start <= tick.datetime <= cal_dt]
        return ticks

    def _get_last_tick(self, order_book_id):
        """ 获取上一个tick """
        _last_tick = self._last_tick.get(order_book_id)
        trading_dt = self._env.trading_dt
        # 上一根tick缺失
        if not _last_tick:
            tick_list = self._get_today_history_ticks(order_book_id, 2)
            _last_tick = tick_list[0] if len(tick_list) == 2 else None
        else:
            # 两个tick之间的时间差(秒)
            diff_time = trading_dt.timestamp() - _last_tick.datetime.timestamp()
            # 在非回测状态下，时差间隔太大时，需要重新获取tick
            if diff_time > 5:
                tick_list = self._get_today_history_ticks(order_book_id, 2)
                _last_tick = tick_list[0] if len(tick_list) == 2 else None
        return _last_tick

    def _get_deal_price(self, order: Order, instrument: Instrument, open_auction: bool) -> float:
        _cur_tick = self._cur_tick.get(order.order_book_id)
        # 判断订单在交易时间下处于那个阶段
        if open_auction:
            # 集合竞价时段内撮合无视 matching_type 的设置，直接使用 last 进行撮合
            deal_price = _cur_tick.last
        else:
            deal_price = self._deal_price_decider(order.order_book_id, order.side)

        if is_valid_price(deal_price):
            return deal_price

        listed_date = instrument.listed_date.date()
        if listed_date == self._env.trading_dt.date():
            raise OrderRejected(self._listed_date_reject_reason(order, listed_date))
        else:
            # TODO：这里报错信息比较模糊，可以根据撮合类型给出更明确的提示，比如是否是熔断了，是否是涨跌停了
            reason = _(u"Order Cancelled: current tick [{order_book_id}] miss market data.").format(
                order_book_id=order.order_book_id
            )
            raise OrderRejected(reason)

    def _get_tick_volume_limit(self, order: Order, instrument: Instrument) -> int:
        order_book_id = order.order_book_id
        _cur_tick = self._cur_tick.get(order_book_id)
        _last_tick = self._get_last_tick(order_book_id)

        if _last_tick:
            volume = _cur_tick.volume - _last_tick.volume
        else:
            volume = _cur_tick.volume

        if self._volume_limit:
            volume_limit = round(volume * self._volume_percent) - self._turnover[order_book_id]
        else:
            # 主要是处理未开启时集合竞价的成交情况，只要有成交量就表示能撮合
            volume_limit = volume

        return round_order_quantity(instrument, volume_limit)

    def _get_liquidity_limited_fill(self, order: Order, instrument: Instrument, open_auction: bool = False) -> int:
        if self._liquidity_limit:
            price_board = self._env.price_board
            order_book_id = order.order_book_id
            if order.type == ORDER_TYPE.LIMIT:
                if (order.side == SIDE.BUY and price_board.get_a1(order_book_id) == 0) or \
                    (order.side == SIDE.SELL and price_board.get_b1(order_book_id) == 0):
                    raise OrderNotMatchable(_("Current tick has no liquidity."))
            else:
                if (order.side == SIDE.BUY and price_board.get_a1(order_book_id) == 0) or \
                    (order.side == SIDE.SELL and price_board.get_b1(order_book_id) == 0):
                    reason = _("Order Cancelled: [{order_book_id}] has no liquidity.").format(order_book_id=order.order_book_id)
                    raise OrderRejected(reason)

        _volume_limit_flag = self._volume_limit
        if open_auction:
            # 集合竞价默认开启成交量限制，用来保证在集合竞价中只有一笔成交
            _volume_limit_flag = True

        if _volume_limit_flag:
            volume_limit = self._get_tick_volume_limit(order, instrument)
            if volume_limit <= 0:
                # 集合竞价无法撤单
                if order.type == ORDER_TYPE.MARKET:
                    reason = _(u"Order Cancelled: market order {order_book_id} volume {order_volume} due to volume limit").format(
                        order_book_id=order.order_book_id, order_volume=order.quantity
                    )
                    raise OrderCancelled(reason)
                raise OrderNotMatchable(_("Current tick liquidity is 0."))

            # 实际成交数量
            if self._volume_limit:
                fill = min(order.unfilled_quantity, volume_limit)
            else:
                fill = order.unfilled_quantity
        else:
            # 下单数量就是成交数量
            fill = order.unfilled_quantity

        return fill

    def _handle_unfilled_order(self, account: Account, order: Order, open_auction: bool):
        if order.type == ORDER_TYPE.MARKET:
            reason = _(
                u"Order Cancelled: market order {order_book_id} volume {order_volume} is"
                u" larger than {volume_percent_limit} percent of current tick volume, fill {filled_volume} actually"
            ).format(
                order_book_id=order.order_book_id,
                order_volume=order.quantity,
                filled_volume=order.filled_quantity,
                volume_percent_limit=self._volume_percent * 100.0
            )
            raise OrderCancelled(reason)

    def match(self, account, order, open_auction):
        if not (order.position_effect in self.SUPPORT_POSITION_EFFECTS and order.side in self.SUPPORT_SIDES):
            raise NotImplementedError
        super().match(account, order, open_auction)

    def update(self, event):
        self._last_tick[event.tick.order_book_id] = self._cur_tick.get(event.tick.order_book_id)
        self._cur_tick[event.tick.order_book_id] = event.tick
        self._turnover.clear()


class CounterPartyOfferMatcher(DefaultTickMatcher):
    """限价撮合：
    订单买价>卖x价
    买量>卖x量，按照卖x价成交，订单减去卖x量，继续撮合卖x+1，直至该tick中所有报价被买完。买完后若有剩余买量，则在下一个tick继续撮合。
    买量<卖x量，按照卖x价成交。
    反之亦然
    市价单：
    按照该tick，a1，b1进行成交，剩余订单直接撤单
    """
    def __init__(self, env, mod_config, partial_fill_on_insufficient_cash: bool = False):
        super(CounterPartyOfferMatcher, self).__init__(env, mod_config, partial_fill_on_insufficient_cash)
        self._a_volume = {}
        self._b_volume = {}
        self._a_price = {}
        self._b_price = {}
        self._env.event_bus.prepend_listener(EVENT.TICK, self._pre_tick)

    def _get_deal_price(self, order: Order, instrument: Instrument, open_auction: bool) -> float:
        self._pop_volume_and_price(order)

        order_book_id = order.order_book_id
        if open_auction:
            deal_price = self._cur_tick[order_book_id].last
        elif order.side == SIDE.BUY:
            if len(self._a_volume[order_book_id]) == 0:
                raise OrderNotMatchable(_("Current counterparty offer is unavailable."))
            deal_price = self._a_price[order_book_id][0]
        else:
            if len(self._b_volume[order_book_id]) == 0:
                raise OrderNotMatchable(_("Current counterparty offer is unavailable."))
            deal_price = self._b_price[order_book_id][0]

        if is_valid_price(deal_price):
            return deal_price
        raise OrderNotMatchable(_("Current counterparty offer has no valid price."))

    def _get_liquidity_limited_fill(self, order: Order, instrument: Instrument, open_auction: bool = False) -> int:
        order_book_id = order.order_book_id

        if order.side == SIDE.BUY:
            if len(self._a_volume[order_book_id]) == 0:
                raise OrderNotMatchable(_("Current counterparty offer is unavailable."))
            amount = self._a_volume[order_book_id][0]
        else:
            if len(self._b_volume[order_book_id]) == 0:
                raise OrderNotMatchable(_("Current counterparty offer is unavailable."))
            amount = self._b_volume[order_book_id][0]
        if amount != amount or amount <= 0:
            raise OrderNotMatchable(_("Current counterparty offer has no liquidity."))

        if open_auction or self._volume_limit:
            volume_limit = self._get_tick_volume_limit(order, instrument)
            if volume_limit <= 0:
                if order.type == ORDER_TYPE.MARKET:
                    reason = _(u"Order Cancelled: market order {order_book_id} volume {order_volume} due to volume limit").format(
                        order_book_id=order.order_book_id, order_volume=order.quantity
                    )
                    raise OrderCancelled(reason)
                raise OrderNotMatchable(_("Current counterparty offer liquidity is 0."))

            if self._volume_limit:
                if open_auction:
                    return min(order.unfilled_quantity, volume_limit)
                return min(order.unfilled_quantity, amount, volume_limit)

        return min(order.unfilled_quantity, amount)

    def _get_execution_price(self, order, deal_price, open_auction):
        return deal_price

    def _publish_trade(self, account: Account, order: Order, price: float, amount: int, open_auction: bool, close_today_amount: int):
        super()._publish_trade(account, order, price, amount, open_auction, close_today_amount)
        if not open_auction:
            # 常规交易时间逐档
            if order.side == SIDE.BUY:
                self._a_volume[order.order_book_id][0] -= amount
            else:
                self._b_volume[order.order_book_id][0] -= amount

    def _handle_unfilled_order(self, account: Account, order: Order, open_auction: bool):
        if order.type == ORDER_TYPE.MARKET:
            reason = _("Order Cancelled: market order {order_book_id} fill {filled_volume} actually").format(
                order_book_id=order.order_book_id, filled_volume=order.filled_quantity
            )
            raise OrderCancelled(reason)
        self.match(account, order, open_auction)

    def _pop_volume_and_price(self, order):
        order_book_id = order.order_book_id
        if order.side == SIDE.BUY:
            volumes = self._a_volume.get(order_book_id, [])
            prices = self._a_price.get(order_book_id, [])
        else:
            volumes = self._b_volume.get(order_book_id, [])
            prices = self._b_price.get(order_book_id, [])

        while volumes and volumes[0] == 0:
            volumes.pop(0)
            prices.pop(0)

    def _pre_tick(self, event):
        order_book_id = event.tick.order_book_id
        self._a_volume[order_book_id] = event.tick.ask_vols
        self._b_volume[order_book_id] = event.tick.bid_vols

        self._a_price[order_book_id] = event.tick.asks
        self._b_price[order_book_id] = event.tick.bids
