# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），
#         您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、
#         本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，
#         否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。

import time
from typing import TYPE_CHECKING, Optional
from functools import cached_property

from rqalpha.utils import id_gen, get_position_direction
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.repr import property_repr, properties
from rqalpha.environment import Environment
from rqalpha.const import POSITION_EFFECT, SIDE, MARKET
from rqalpha.model.instrument import Instrument

if TYPE_CHECKING:
    from rqalpha.interface import TransactionCost

# TODO: 改成 namedtuple，提升性能
class Trade(object):

    __repr__ = property_repr  # type: ignore

    trade_id_gen = id_gen(int(time.time()) * 10000)

    def __init__(self):
        self._calendar_dt = None
        self._trading_dt = None
        self._price = None
        self._amount = None
        self._order_id = None
        self._transaction_cost = None
        self._trade_id = None
        self._close_today_amount = None
        self._side = None
        self._position_effect = None
        self._order_book_id = None
        self._frozen_price = None
        self._kwargs = {}

    @classmethod
    def __from_create__(
            cls, order_id, price, amount, side, position_effect, order_book_id, transaction_cost: "Optional[TransactionCost]" = None,
            trade_id=None, close_today_amount=0, frozen_price=0., calendar_dt=None, trading_dt=None, **kwargs
    ):
        from rqalpha.interface import TransactionCostArgs

        trade = cls()
        trade_id = trade_id or next(trade.trade_id_gen)

        for value in (price, amount, frozen_price):
            if value != value:
                raise RuntimeError(_(
                    "price, amount, and frozen_price of trade {trade_id} is not supposed to be nan, "
                    "current_value is {price}, {amount}, {commission}, {tax}, {frozen_price}"
                ).format(
                    trade_id=trade_id, price=price, amount=amount,
                    frozen_price=frozen_price
                ))

        env = Environment.get_instance()
        ins = env.data_proxy.instrument_not_none(order_book_id)
        if transaction_cost is None:
            transaction_cost = env.calc_transaction_cost(TransactionCostArgs(
                ins, price, amount, side, position_effect, order_id=order_id, close_today_quantity=close_today_amount,
            ))

        trade._calendar_dt = calendar_dt or env.calendar_dt
        trade._trading_dt = trading_dt or env.trading_dt
        trade._price = price
        trade._amount = amount
        trade._order_id = order_id
        trade._transaction_cost = transaction_cost
        trade._trade_id = trade_id
        trade._close_today_amount = close_today_amount
        trade._side = side
        trade._position_effect = position_effect
        trade._order_book_id = order_book_id
        trade._frozen_price = frozen_price
        trade._kwargs = kwargs
        return trade

    order_book_id = property(lambda self: self._order_book_id)
    trading_datetime = property(lambda self: self._trading_dt)
    datetime = property(lambda self: self._calendar_dt)
    order_id = property(lambda self: self._order_id)
    last_price = property(lambda self: self._price)
    last_quantity = property(lambda self: self._amount)
    commission = property(lambda self: self._transaction_cost.commission)
    tax = property(lambda self: self._transaction_cost.tax)
    transaction_cost = property(lambda self: self._transaction_cost.total)
    side = property(lambda self: self._side)
    position_effect = property(lambda self: self._position_effect or (
        POSITION_EFFECT.OPEN if self._side == SIDE.BUY else POSITION_EFFECT.CLOSE
    ))
    position_direction = property(lambda self: get_position_direction(self._side, self._position_effect))
    exec_id = property(lambda self: self._trade_id)
    frozen_price = property(lambda self: self._frozen_price)
    close_today_amount = property(lambda self: self._close_today_amount)

    def __getattr__(self, item):
        try:
            return self.__dict__["_kwargs"][item]
        except KeyError:
            raise AttributeError("'{}' object has no attribute '{}'".format(self.__class__.__name__, item))  # type: ignore

    def __simple_object__(self):
        return properties(self)

    @cached_property
    def _ins(self) -> Instrument:
        return self.env.data_proxy.instrument_not_none(self.order_book_id)
    
    @cached_property
    def market(self) -> MARKET:
        return self._ins.market
