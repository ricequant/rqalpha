# -*- coding: utf-8 -*-


# TODO make field readonly
# TODO use nametuple to reduce memory


class Risk(object):
    def __init__(self):
        self.volatility = .0
        self.alpha = .0
        self.beta = .0
        self.sharpe = .0
        self.sortino = .0
        self.information_rate = .0
        self.max_drawdown = .0
        self.tracking_error = .0
        self.downside_risk = .0

    def __repr__(self):
        return "Risk({0})".format(self.__dict__)
