from rqalpha.interface import AbstractBenchmarkPortfolio
from rqalpha.environment import Environment
from rqalpha.events import EVENT
from rqalpha.utils.i18n import gettext as _


class BackTestPriceSeriesBenchmarkPortfolio(AbstractBenchmarkPortfolio):
    def __init__(self, order_book_id):
        self._order_book_id = order_book_id
        self._return_series = None
        self._index = 0

        event_bus = Environment.get_instance().event_bus
        event_bus.add_listener(EVENT.POST_SYSTEM_INIT, self._on_system_init)
        event_bus.prepend_listener(EVENT.AFTER_TRADING, self._on_after_trading)

    def _on_system_init(self, _):
        env = Environment.get_instance()
        bar_count = len(env.config.base.trading_calendar) + 1
        end_date = env.config.base.end_date
        close_series = env.data_proxy.history_bars(
            self._order_book_id, bar_count, "1d", "close", end_date, skip_suspended=False, adjust_type='pre'
        )
        if len(close_series) < bar_count:
            raise RuntimeError(_("Valid benchmark: unable to load enough close price."))

        self._return_series = (close_series - close_series[0]) / close_series[0]

    def _on_after_trading(self, _):
        self._index += 1

    @property
    def daily_returns(self):
        return self._return_series[self._index]


class RealTimePriceSeriesBenchmarkPortfolio(AbstractBenchmarkPortfolio):
    def __init__(self, order_book_id):
        self._order_book_id = order_book_id

    @property
    def daily_returns(self):
        pass
