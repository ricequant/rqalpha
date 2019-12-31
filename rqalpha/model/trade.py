# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。

import time

from rqalpha.utils import id_gen, get_position_direction
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.repr import property_repr, properties
from rqalpha.environment import Environment
from rqalpha.const import POSITION_EFFECT, SIDE, POSITION_DIRECTION


class Trade(object):

    __repr__ = property_repr

    trade_id_gen = id_gen(int(time.time()) * 10000)

    def __init__(self):
        self._calendar_dt = None
        self._trading_dt = None
        self._price = None
        self._amount = None
        self._order_id = None
        self._commission = None
        self._tax = None
        self._trade_id = None
        self._close_today_amount = None
        self._side = None
        self._position_effect = None
        self._order_book_id = None
        self._frozen_price = None

    @classmethod
    def __from_create__(
            cls, order_id, price, amount, side, position_effect, order_book_id, commission=0., tax=0.,
            trade_id=None, close_today_amount=0, frozen_price=0, calendar_dt=None, trading_dt=None
    ):

        trade = cls()
        trade_id = trade_id or next(trade.trade_id_gen)

        for value in (price, amount, commission, tax, frozen_price):
            if value != value:
                raise RuntimeError(_(
                    "price, amount, commission, tax and frozen_price of trade {trade_id} is not supposed to be nan, "
                    "current_value is {price}, {amount}, {commission}, {tax}, {frozen_price}"
                ).format(
                    trade_id=trade_id, price=price, amount=amount, commission=commission, tax=tax,
                    frozen_price=frozen_price
                ))

        env = Environment.get_instance()
        trade._calendar_dt = calendar_dt or env.calendar_dt
        trade._trading_dt = trading_dt or env.trading_dt
        trade._price = price
        trade._amount = amount
        trade._order_id = order_id
        trade._commission = commission
        trade._tax = tax
        trade._trade_id = trade_id
        trade._close_today_amount = close_today_amount
        trade._side = side
        trade._position_effect = position_effect
        trade._order_book_id = order_book_id
        trade._frozen_price = frozen_price
        return trade

    @property
    def order_book_id(self):
        return self._order_book_id

    @property
    def trading_datetime(self):
        return self._trading_dt

    @property
    def datetime(self):
        return self._calendar_dt

    @property
    def order_id(self):
        return self._order_id

    @property
    def last_price(self):
        return self._price

    @property
    def last_quantity(self):
        return self._amount

    @property
    def commission(self):
        return self._commission

    @property
    def tax(self):
        return self._tax

    @property
    def transaction_cost(self):
        return self.tax + self.commission

    @property
    def side(self):
        return self._side

    @property
    def position_effect(self):
        if self._position_effect is None:
            if self._side == SIDE.BUY:
                return POSITION_EFFECT.OPEN
            else:
                return POSITION_EFFECT.CLOSE
        return self._position_effect

    @property
    def position_direction(self):
        # type: () -> POSITION_DIRECTION
        return get_position_direction(self._side, self._position_effect)

    @property
    def exec_id(self):
        return self._trade_id

    @property
    def frozen_price(self):
        return self._frozen_price

    @property
    def close_today_amount(self):
        return self._close_today_amount

    def __simple_object__(self):
        return properties(self)
