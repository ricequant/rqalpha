# -*- coding: utf-8 -*-


class BarObject(object):
    def __init__(self):
        self.open = 0.0
        self.close = 0.0
        self.high = 0.0
        self.low = 0.0
        self.volume = 0.0
        self.last = 0.0
        self.acc_net_value = 0.0
        self.unit_net_value = 0.0
        self.discount_rate = 0.0
        self.total_turnover = 0.0
        self.settlement = 0.0
        self.prev_settlement = 0.0
        self.open_interest = 0.0
        self.basis_spread = 0.0
        self.datetime = None

    @property
    def instrument(self):
        pass

    @property
    def order_book_id(self):
        pass

    @property
    def symbol(self):
        pass

    @property
    def is_trading(self):
        pass

    def mavg(self, intervals, frequency="day"):
        """
        Returns moving average price for the given security for a give number
            of intervals for a frequency, by default to `"day"`.
        :param int intervals: a given number of intervals, e.g. given number
            of days
        :param str frequency: frequency of the give number of intervals, by
            default as ‘day’.
        """
        pass

    def vwap(self, intervals, frequency="day"):
        pass

    def history(self, bar_count, frequency, field):
        pass

    def __repr__(self):
        return "BarObject({0})".format(self.__dict__)

    def __getitem__(self, key):
        return self.__dict__[key]


class BarMap(object):
    def __init__(self, dt, data_proxy):
        self.dt = dt
        self.data_proxy = data_proxy

    def update_dt(self, dt):
        self.dt = dt

    def __getitem__(self, key):
        return self.data_proxy.get_data(key, self.dt)

    def __repr__(self):
        return "{0}()".format(type(self).__name__)
