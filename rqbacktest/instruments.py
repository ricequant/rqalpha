# -*- coding: utf-8 -*-


class Instrument(object):

    def __init__(self):

        self.order_book_id = ""
        self.symbol = ""
        self.abbrev_symbol = ""
        self.round_lot = ""
        self.sector_name = ""
        self.industry_code = ""
        self.industry_name = ""
        self.type = ""

    @property
    def board_type(self):
        raise NotImplementedError

    @property
    def sector_code(self):
        raise NotImplementedError

    @property
    def listing(self):
        raise NotImplementedError

    @property
    def listed_date(self):
        raise NotImplementedError

    @property
    def maturity_date(self):
        raise NotImplementedError

    @property
    def is_st(self):
        raise NotImplementedError

    def __str__(self):
        return self.order_book_id
