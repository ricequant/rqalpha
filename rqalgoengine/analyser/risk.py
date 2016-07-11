# -*- coding: utf-8 -*-


# TODO make field readonly

class Risk(object):
    def __init__(self):
        self.volatility = .0

    def __repr__(self):
        return "Risk({0})".format(self.__dict__)
