# -*- coding: utf-8 -*-


class Instrument(object):
    def __init__(self, dic):
        self.__dict__ = dic

    def __repr__(self):
        return "{}({})".format(type(self).__name__,
                               ", ".join(["{}={}".format(k, repr(v))
                                          for k, v in self.__dict__.items()]))
