from datetime import datetime
from types import SimpleNamespace

import pytest

from rqalpha.const import MARKET, MATCHING_TYPE, ORDER_STATUS, POSITION_EFFECT, SIDE
from rqalpha.core.events import EVENT, Event
from rqalpha.environment import Environment
from rqalpha.interface import TransactionCost
from rqalpha.model.order import LimitOrder, MarketOrder, Order
from rqalpha.mod.rqalpha_mod_sys_simulation.matcher import (
    CounterPartyOfferMatcher,
    DefaultBarMatcher,
    DefaultTickMatcher,
    SignalMatcher,
)


ORDER_BOOK_ID = "000001.XSHE"


class RecordingEventBus:
    def __init__(self):
        self.events = []
        self._listeners = {}

    def add_listener(self, event_type, listener, user=False):
        self._listeners.setdefault(event_type, []).append(listener)

    def prepend_listener(self, event_type, listener, user=False):
        self._listeners.setdefault(event_type, []).insert(0, listener)

    def publish_event(self, event):
        self.events.append(event)
        for listener in self._listeners.get(event.event_type, []):
            listener(event)


class FakeInstrument:
    order_book_id = ORDER_BOOK_ID
    type = "CS"
    board_type = "MainBoard"
    round_lot = 100
    min_order_quantity = 100
    order_step_size = 100
    listed_date = datetime(2000, 1, 1)
    market = MARKET.CN
    contract_multiplier = 1

    def calc_cash_occupation(self, price, quantity, direction, dt):
        return price * quantity

    def during_call_auction(self, dt):
        return dt.hour < 9 or (dt.hour == 9 and dt.minute < 30) or (dt.hour == 14 and dt.minute >= 57)


class FakePriceBoard:
    def __init__(self, last=10.0, a1=10.2, b1=9.8, limit_up=100.0, limit_down=1.0):
        self.last = last
        self.a1 = a1
        self.b1 = b1
        self.limit_up = limit_up
        self.limit_down = limit_down

    def get_last_price(self, order_book_id):
        return self.last

    def get_a1(self, order_book_id):
        return self.a1

    def get_b1(self, order_book_id):
        return self.b1

    def get_limit_up(self, order_book_id):
        return self.limit_up

    def get_limit_down(self, order_book_id):
        return self.limit_down


class FakeDataProxy:
    def __init__(self, instrument, bar, price_board):
        self.instrument_obj = instrument
        self.bar = bar
        self.price_board = price_board
        self.algo_price = 10.0
        self.algo_volume = 1000

    def get_active_instrument(self, order_book_id, dt=None):
        return self.instrument_obj

    def instrument_not_none(self, order_book_id):
        return self.instrument_obj

    def instrument(self, order_book_id):
        return self.instrument_obj

    def get_tick_size(self, order_book_id):
        return 0.01

    def get_open_auction_bar(self, order_book_id, dt):
        return SimpleNamespace(open=self.bar.open)

    def get_open_auction_volume(self, order_book_id, dt):
        return self.bar.volume

    def get_algo_bar(self, order_book_id, order_style, dt):
        return self.algo_price, self.algo_volume

    def history_ticks(self, order_book_id, count, dt):
        return []


class FakeEnv:
    def __init__(self, *, frequency="1d", price_board=None, bar=None, partial_fill=False):
        self.calendar_dt = datetime(2020, 1, 2, 10, 0)
        self.trading_dt = datetime(2020, 1, 2, 10, 0)
        self.config = SimpleNamespace(
            base=SimpleNamespace(
                frequency=frequency,
                round_price=False,
                partial_fill_on_insufficient_cash=partial_fill,
            )
        )
        self.event_bus = RecordingEventBus()
        self.price_board = price_board or FakePriceBoard()
        self.instrument = FakeInstrument()
        self.bar = bar or SimpleNamespace(open=9.5, close=10.0, volume=1000, total_turnover=10000)
        self.data_proxy = FakeDataProxy(self.instrument, self.bar, self.price_board)

    def get_bar(self, order_book_id):
        return self.bar

    def get_instrument(self, order_book_id):
        return self.instrument

    def get_last_price(self, order_book_id):
        return self.price_board.get_last_price(order_book_id)

    def calc_transaction_cost(self, args):
        return TransactionCost.zero()


class FakeAccount:
    cash = 1000000

    def calc_close_today_amount(self, order_book_id, trade_amount, position_direction, position_effect):
        return 0


def make_mod_config(
    matching_type,
    *,
    slippage=0.0,
    price_limit=False,
    inactive_limit=True,
    volume_limit=False,
    volume_percent=1.0,
    liquidity_limit=False,
):
    return SimpleNamespace(
        matching_type=matching_type,
        slippage_model="PriceRatioSlippage",
        slippage=slippage,
        price_limit=price_limit,
        inactive_limit=inactive_limit,
        volume_limit=volume_limit,
        volume_percent=volume_percent,
        liquidity_limit=liquidity_limit,
    )


@pytest.fixture
def fake_env(monkeypatch):
    env = FakeEnv()
    monkeypatch.setattr(Environment, "_env", env)
    return env


def make_order(quantity, side=SIDE.BUY, style=None, position_effect=POSITION_EFFECT.OPEN):
    order = Order.__from_create__(
        ORDER_BOOK_ID,
        quantity,
        side,
        style or MarketOrder(),
        position_effect,
    )
    order.active()
    return order


def trade_events(env):
    return [event for event in env.event_bus.events if event.event_type == EVENT.TRADE]


def test_bar_matcher_fills_market_order_by_volume_limit_and_cancels_remainder(fake_env):
    matcher = DefaultBarMatcher(
        fake_env,
        make_mod_config(
            MATCHING_TYPE.CURRENT_BAR_CLOSE,
            volume_limit=True,
            volume_percent=0.5,
        ),
    )
    order = make_order(1000)

    matcher.match(FakeAccount(), order, open_auction=False)

    trades = trade_events(fake_env)
    assert len(trades) == 1
    assert trades[0].trade.last_quantity == 500
    assert trades[0].trade.last_price == 10.0
    assert order.filled_quantity == 500
    assert order.status == ORDER_STATUS.CANCELLED


def test_bar_matcher_leaves_non_crossed_limit_order_active(fake_env):
    matcher = DefaultBarMatcher(fake_env, make_mod_config(MATCHING_TYPE.CURRENT_BAR_CLOSE))
    order = make_order(100, style=LimitOrder(9.9))

    matcher.match(FakeAccount(), order, open_auction=False)

    assert trade_events(fake_env) == []
    assert order.filled_quantity == 0
    assert order.status == ORDER_STATUS.ACTIVE


def test_matcher_reduces_cash_limited_fill_by_order_step_for_transaction_cost(fake_env):
    matcher = DefaultBarMatcher(
        fake_env,
        make_mod_config(MATCHING_TYPE.CURRENT_BAR_CLOSE),
        partial_fill_on_insufficient_cash=True,
    )
    fake_env.calc_transaction_cost = lambda _args: TransactionCost(
        commission=5,
        tax=0,
        other_fees=0,
    )
    order = make_order(200)

    cash_fill = matcher._resolve_open_fill(
        account=SimpleNamespace(cash=2000),
        order=order,
        instrument=fake_env.instrument,
        price=10,
        fill=200,
    )

    assert cash_fill == 100


def test_matcher_keeps_affordable_fill_without_cash_clipping(fake_env, monkeypatch):
    matcher = DefaultBarMatcher(
        fake_env,
        make_mod_config(MATCHING_TYPE.CURRENT_BAR_CLOSE),
        partial_fill_on_insufficient_cash=True,
    )
    quantities = []

    def calc_cash_occupation(price, quantity, _direction, _dt):
        quantities.append(quantity)
        return price * quantity

    monkeypatch.setattr(fake_env.instrument, "calc_cash_occupation", calc_cash_occupation)
    order = make_order(200)

    cash_fill = matcher._resolve_open_fill(
        account=SimpleNamespace(cash=3000),
        order=order,
        instrument=fake_env.instrument,
        price=10,
        fill=200,
    )

    assert cash_fill == 200
    assert quantities == [200]


def test_matcher_uses_cash_occupation_to_estimate_cash_limited_fill(fake_env, monkeypatch):
    matcher = DefaultBarMatcher(
        fake_env,
        make_mod_config(MATCHING_TYPE.CURRENT_BAR_CLOSE),
        partial_fill_on_insufficient_cash=True,
    )
    monkeypatch.setattr(
        fake_env.instrument,
        "calc_cash_occupation",
        lambda price, quantity, _direction, _dt: price * quantity * 2,
    )
    order = make_order(300)

    cash_fill = matcher._resolve_open_fill(
        account=SimpleNamespace(cash=2000),
        order=order,
        instrument=fake_env.instrument,
        price=10,
        fill=300,
    )

    assert cash_fill == 100


def test_matcher_rechecks_only_unfilled_quantity_after_partial_fill(fake_env):
    matcher = DefaultBarMatcher(
        fake_env,
        make_mod_config(MATCHING_TYPE.CURRENT_BAR_CLOSE),
    )
    order = make_order(200)
    order.set_frozen_cash(2000)
    order.fill(SimpleNamespace(
        last_quantity=100,
        position_effect=POSITION_EFFECT.OPEN,
        last_price=10,
        transaction_cost=0,
    ))

    cash_fill = matcher._resolve_open_fill(
        account=SimpleNamespace(cash=500),
        order=order,
        instrument=fake_env.instrument,
        price=13,
        fill=100,
    )

    assert cash_fill == 100


def test_bar_matcher_returns_early_on_invalid_price(fake_env):
    fake_env.bar.close = 0.0
    matcher = DefaultBarMatcher(fake_env, make_mod_config(MATCHING_TYPE.CURRENT_BAR_CLOSE))
    order = make_order(100)

    matcher.match(FakeAccount(), order, open_auction=False)

    assert trade_events(fake_env) == []
    assert order.status == ORDER_STATUS.ACTIVE


def test_tick_matcher_fills_with_best_counterparty_price(monkeypatch):
    price_board = FakePriceBoard(last=10.0, a1=10.2, b1=9.8)
    env = FakeEnv(frequency="tick", price_board=price_board)
    monkeypatch.setattr(Environment, "_env", env)
    matcher = DefaultTickMatcher(
        env,
        make_mod_config(MATCHING_TYPE.NEXT_TICK_BEST_COUNTERPARTY, liquidity_limit=True),
    )
    tick = SimpleNamespace(order_book_id=ORDER_BOOK_ID, datetime=env.calendar_dt, volume=1000, last=10.0)
    matcher.update(Event(EVENT.TICK, tick=tick))
    order = make_order(100)

    matcher.match(FakeAccount(), order, open_auction=False)

    trades = trade_events(env)
    assert len(trades) == 1
    assert trades[0].trade.last_quantity == 100
    assert trades[0].trade.last_price == 10.2
    assert order.status == ORDER_STATUS.FILLED


def test_tick_matcher_rejects_invalid_price(monkeypatch):
    env = FakeEnv(frequency="tick", price_board=FakePriceBoard(last=0.0))
    monkeypatch.setattr(Environment, "_env", env)
    matcher = DefaultTickMatcher(env, make_mod_config(MATCHING_TYPE.NEXT_TICK_LAST))
    order = make_order(100)

    matcher.match(FakeAccount(), order, open_auction=False)

    assert trade_events(env) == []
    assert order.status == ORDER_STATUS.REJECTED


def test_tick_matcher_rejects_market_order_without_liquidity(monkeypatch):
    env = FakeEnv(frequency="tick", price_board=FakePriceBoard(last=10.0, a1=0.0))
    monkeypatch.setattr(Environment, "_env", env)
    matcher = DefaultTickMatcher(
        env,
        make_mod_config(MATCHING_TYPE.NEXT_TICK_LAST, liquidity_limit=True),
    )
    order = make_order(100)

    matcher.match(FakeAccount(), order, open_auction=False)

    assert trade_events(env) == []
    assert order.status == ORDER_STATUS.REJECTED


def test_counterparty_offer_rejects_order_at_price_limit(monkeypatch):
    price_board = FakePriceBoard(last=10.0, a1=0.0, b1=0.0, limit_up=10.0)
    env = FakeEnv(frequency="tick", price_board=price_board)
    monkeypatch.setattr(Environment, "_env", env)
    matcher = CounterPartyOfferMatcher(
        env,
        make_mod_config(
            MATCHING_TYPE.COUNTERPARTY_OFFER,
            slippage=0.1,
            price_limit=True,
            liquidity_limit=True,
        ),
    )
    tick = SimpleNamespace(
        order_book_id=ORDER_BOOK_ID,
        datetime=env.calendar_dt,
        volume=1000,
        last=10.0,
        asks=[10.0],
        ask_vols=[100],
        bids=[9.8],
        bid_vols=[100],
    )
    matcher._pre_tick(Event(EVENT.TICK, tick=tick))
    matcher.update(Event(EVENT.TICK, tick=tick))
    order = make_order(100)

    matcher.match(FakeAccount(), order, open_auction=False)

    assert trade_events(env) == []
    assert order.status == ORDER_STATUS.REJECTED


def test_counterparty_offer_leaves_non_crossed_limit_order_active(monkeypatch):
    env = FakeEnv(frequency="tick")
    monkeypatch.setattr(Environment, "_env", env)
    matcher = CounterPartyOfferMatcher(env, make_mod_config(MATCHING_TYPE.COUNTERPARTY_OFFER))
    tick = SimpleNamespace(
        order_book_id=ORDER_BOOK_ID,
        datetime=env.calendar_dt,
        volume=1000,
        last=10.0,
        asks=[10.0],
        ask_vols=[100],
        bids=[9.8],
        bid_vols=[100],
    )
    matcher._pre_tick(Event(EVENT.TICK, tick=tick))
    matcher.update(Event(EVENT.TICK, tick=tick))
    order = make_order(100, style=LimitOrder(9.9))

    matcher.match(FakeAccount(), order, open_auction=False)

    assert trade_events(env) == []
    assert order.filled_quantity == 0
    assert order.status == ORDER_STATUS.ACTIVE


def test_counterparty_offer_returns_early_without_quote(monkeypatch):
    env = FakeEnv(frequency="tick")
    monkeypatch.setattr(Environment, "_env", env)
    matcher = CounterPartyOfferMatcher(env, make_mod_config(MATCHING_TYPE.COUNTERPARTY_OFFER))
    tick = SimpleNamespace(
        order_book_id=ORDER_BOOK_ID,
        datetime=env.calendar_dt,
        volume=1000,
        last=10.0,
        asks=[],
        ask_vols=[],
        bids=[],
        bid_vols=[],
    )
    matcher._pre_tick(Event(EVENT.TICK, tick=tick))
    matcher.update(Event(EVENT.TICK, tick=tick))
    order = make_order(100)

    matcher.match(FakeAccount(), order, open_auction=False)

    assert trade_events(env) == []
    assert order.status == ORDER_STATUS.ACTIVE


def test_signal_matcher_fills_market_order_immediately(fake_env):
    matcher = SignalMatcher(fake_env, make_mod_config(MATCHING_TYPE.CURRENT_BAR_CLOSE))
    order = make_order(100)

    matcher.match(FakeAccount(), order, open_auction=False)

    trades = trade_events(fake_env)
    assert len(trades) == 1
    assert trades[0].trade.last_quantity == 100
    assert trades[0].trade.last_price == 10.0
    assert order.status == ORDER_STATUS.FILLED


def test_signal_matcher_rejects_invalid_price(fake_env):
    fake_env.price_board.last = 0.0
    matcher = SignalMatcher(fake_env, make_mod_config(MATCHING_TYPE.CURRENT_BAR_CLOSE))
    order = make_order(100)

    matcher.match(FakeAccount(), order, open_auction=False)

    assert trade_events(fake_env) == []
    assert order.status == ORDER_STATUS.REJECTED


def test_signal_matcher_rejects_order_at_price_limit(fake_env):
    fake_env.price_board.last = 10.0
    fake_env.price_board.limit_up = 10.0
    matcher = SignalMatcher(
        fake_env,
        make_mod_config(MATCHING_TYPE.CURRENT_BAR_CLOSE, price_limit=True),
    )
    order = make_order(100)

    matcher.match(FakeAccount(), order, open_auction=False)

    assert trade_events(fake_env) == []
    assert order.status == ORDER_STATUS.REJECTED
