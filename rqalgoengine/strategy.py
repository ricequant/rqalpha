# -*- coding: utf-8 -*-

from .analyser import Position, Portfolio, Order
from .analyser.commission import AStockCommission
from .analyser.tax import AStockTax
from .analyser.portfolio_manager import PortfolioManager
from .analyser.simulation_exchange import SimuExchange
from .analyser.slippage import FixedPercentSlippageDecider
from .instruments import Instrument
from .scope import export_as_api


class Strategy(object):
    def __init__(self, data_proxy, trading_params, **kwargs):
        self._init = kwargs.get("init", lambda _: None)
        self._handle_bar = kwargs.get("handle_bar", lambda _, __: None)
        self._before_trading = kwargs.get("before_trading", lambda _: None)
        self.trading_params = trading_params
        self.now = None

        self.slippage_decider = kwargs.get("slippage", FixedPercentSlippageDecider())
        self.commission_decider = kwargs.get("commission", AStockCommission())
        self.tax_decider = kwargs.get("tax", AStockTax())

        self._simu_exchange = kwargs.get("simu_exchange", SimuExchange(data_proxy, self.trading_params))
        self._portfolio_mgr = PortfolioManager()

        self._simu_exchange.set_strategy(self)

    def on_dt_change(self, dt):
        self.now = dt

        self._simu_exchange.on_dt_change(dt)

    @export_as_api
    def order_shares(self, id_or_ins, amount, style=None):
        """
        Place an order by specified number of shares. Order type is also
            passed in as parameters if needed. If style is omitted, it fires a
            market order by default.
        :PARAM id_or_ins: the instrument to be ordered
        :type id_or_ins: str or Instrument
        :param float amount: Number of shares to order. Positive means buy,
            negative means sell. It will be rounded down to the closest
            integral multiple of the lot size
        :param style: Order type and default is `MarketOrder()`. The
            available order types are: `MarketOrder()` and
            `LimitOrder(limit_price)`
        :return:  A unique order id.
        :rtype: int
        """
        # TODO handle str or Instrument
        order_book_id = id_or_ins

        order = self._simu_exchange.create_order(order_book_id, amount, style)

        return order.order_id

    @export_as_api
    def order_lots(self, id_or_ins, amount, style=None):
        """
        Place an order by specified number of lots. Order type is also passed
            in as parameters if needed. If style is omitted, it fires a market
            order by default.
        :param id_or_ins: the instrument to be ordered
        :type id_or_ins: str or Instrument
        :param float amount: Number of lots to order. Positive means buy,
            negative means sell.
        :param style: Order type and default is `MarketOrder()`. The
            available order types are: `MarketOrder()` and
            `LimitOrder(limit_price)`
        :return:  A unique order id.
        :rtype: int
        """
        raise NotImplementedError

    @export_as_api
    def order_value(self, id_or_ins, cash_amount, style=None):
        """
        Place ann order by specified value amount rather than specific number
            of shares/lots. Negative cash_amount results in selling the given
            amount of value, if the cash_amount is larger than you current
            security’s position, then it will sell all shares of this security.
            Orders are always truncated to whole lot shares.
        :param id_or_ins: the instrument to be ordered
        :type id_or_ins: str or Instrument
        :param float cash_amount: Cash amount to buy / sell the given value of
            securities. Positive means buy, negative means sell.
        :param style: Order type and default is `MarketOrder()`. The
            available order types are: `MarketOrder()` and
            `LimitOrder(limit_price)`
        :return:  A unique order id.
        :rtype: int
        """
        raise NotImplementedError

    @export_as_api
    def order_percent(self, id_or_ins, percent, style=None):
        """
        Place an order for a security for a given percent of the current
            portfolio value, which is the sum of the positions value and
            ending cash balance. A negative percent order will result in
            selling given percent of current portfolio value. Orders are
            always truncated to whole shares. Percent should be a decimal
            number (0.50 means 50%), and its absolute value is <= 1.
        :param id_or_ins: the instrument to be ordered
        :type id_or_ins: str or Instrument
        :param float percent: Percent of the current portfolio value. Positive
            means buy, negative means selling give percent of the current
            portfolio value. Orders are always truncated according to lot size.
        :param style: Order type and default is `MarketOrder()`. The
            available order types are: `MarketOrder()` and
            `LimitOrder(limit_price)`
        :return:  A unique order id.
        :rtype: int
        """
        raise NotImplementedError

    @export_as_api
    def order_target_value(self, id_or_ins, cash_amount, style=None):
        """
        Place an order to adjust a position to a target value. If there is no
            position for the security, an order is placed for the whole amount
            of target value. If there is already a position for the security,
            an order is placed for the difference between target value and
            current position value.
        :param id_or_ins: the instrument to be ordered
        :type id_or_ins: str or Instrument
        :param float cash_amount: Target cash value for the adjusted position
            after placing order.
        :param style: Order type and default is `MarketOrder()`. The
            available order types are: `MarketOrder()` and
            `LimitOrder(limit_price)`
        :return:  A unique order id.
        :rtype: int
        """
        raise NotImplementedError

    @export_as_api
    def order_target_percent(self, id_or_ins, percent, style=None):
        """
        Place an order to adjust position to a target percent of the portfolio
            value, so that your final position value takes the percentage you
            defined of your whole portfolio.
            position_to_adjust = target_position - current_position
            Portfolio value is calculated as sum of positions value and ending
            cash balance. The order quantity will be rounded down to integral
            multiple of lot size. Percent should be a decimal number (0.50
            means 50%), and its absolute value is <= 1. If the
            position_to_adjust calculated is positive, then it fires buy
            orders, otherwise it fires sell orders.
        :param id_or_ins: the instrument to be ordered
        :type id_or_ins: str or Instrument
        :param float percent: Number of percent to order. It will be rounded down
            to the closest integral multiple of the lot size
        :param style: Order type and default is `MarketOrder()`. The
            available order types are: `MarketOrder()` and
            `LimitOrder(limit_price)`
        :return:  A unique order id.
        :rtype: int
        """
        raise NotImplementedError

    def _order_to_target_shares(self, order_book_id, amount, style=None):
        pass

    @export_as_api
    def get_order(self, order_id):
        """
        Get a specified order by the unique order_id. The order object will be
            discarded at end of handle_bar.
        :param int order_id: order’s unique identifier returned by function
            like `order_shares`
        :return: an `Order` object.
        """
        raise NotImplementedError

    @export_as_api
    def get_open_orders(self):
        raise NotImplementedError

    @export_as_api
    def cancel_order(self, order_id):
        self._simu_exchange.cancel_order(order_id)

    @export_as_api
    def update_universe(self, id_or_symbols):
        """
        This method takes one or a list of id_or_symbol(s) as argument(s), to
            update the current subscription set of the instruments. It takes
            effect on the next bar event.
        :param id_or_symbols: one or a list of id_or_symbol(s).
        :type id_or_symbols: str or an iterable of strings
        """
        raise NotImplementedError

    @export_as_api
    def instruments(self, id_or_symbols):
        """
        Convert a string or a list of strings as order_book_id to instrument
            object(s).
        :param id_or_symbols: Passed in strings / iterable of strings are
            interpreted as order_book_ids. China market’s order_book_ids are
            like ‘000001.XSHE’ while US’s market’s order_book_ids are like
            ‘AAPL.US’
        :type id_or_symbols: str or iterable of strings
        :return: one / a list of instrument(s) object(s) - by the
            id_or_symbol(s) requested.
        """
        raise NotImplementedError

    @export_as_api
    def history(self, bar_count, frequency, field):
        raise NotImplementedError

    @export_as_api
    def is_st_stock(self, order_book_id):
        """
        instrument, = _get_instruments([order_book_id])
        return instrument.is_st
        """
        raise NotImplementedError

    @property
    def slippage(self):
        raise NotImplementedError

    @property
    def commission(self):
        raise NotImplementedError

    @property
    def benchmark(self):
        raise NotImplementedError

    @property
    def short_selling_allowed(self):
        raise NotImplementedError

    @property
    def portfolio(self):
        return self._simu_exchange.portfolio

    def __repr__(self):
        items = ("%s = %r" % (k, v) for k, v in self.__dict__.items() if not callable(v))
        return "Context({%s})" % (', '.join(items), )
