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


import abc
import importlib
from rqalpha.utils import is_valid_price

from six import with_metaclass

from rqalpha.const import SIDE
from rqalpha.utils.exception import patch_user_exc
from rqalpha.environment import Environment
from rqalpha.model.order import Order
from rqalpha.const import POSITION_EFFECT, ORDER_TYPE

from rqalpha.utils.i18n import gettext as _


class SlippageDecider(object):
    def __init__(self, module_name, rate):
        try:
            if "." not in module_name:
                module = importlib.import_module("rqalpha.mod.rqalpha_mod_sys_simulation.slippage")
                slippage_cls = getattr(module, module_name)
            else:
                paths = module_name.split(".")
                module_paths, cls_name = paths[:-1], paths[-1]
                module = importlib.import_module(".".join(module_paths))
                slippage_cls = getattr(module, cls_name)
        except (ImportError, AttributeError):
            raise RuntimeError(_("Missing SlippageModel {}").format(module_name))

        self.decider = slippage_cls(rate)  # type: BaseSlippage

    def get_trade_price(self, order, price):
        return self.decider.get_trade_price(order, price)


class BaseSlippage(with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def get_trade_price(self, order, price):
        # type: (Order, float) -> float
        raise NotImplementedError


class PriceRatioSlippage(BaseSlippage):
    def __init__(self, rate=0.):
        # Rate必须在0~1之间
        if 0 <= rate < 1:
            self.rate = rate
        else:
            raise patch_user_exc(ValueError(_(u"invalid slippage rate value: value range is [0, 1)")))

    def get_trade_price(self, order, price):
        # type: (Order, float) -> float
        if order.position_effect == POSITION_EFFECT.EXERCISE:
            raise NotImplementedError("PriceRatioSlippage cannot handle exercise order")
        temp_price = price + price * self.rate * (1 if order.side == SIDE.BUY else -1)

        env = Environment.get_instance()
        limit_up = env.price_board.get_limit_up(order.order_book_id)
        limit_down = env.price_board.get_limit_down(order.order_book_id)
        if is_valid_price(limit_up):
            temp_price = min(temp_price, limit_up)
        if is_valid_price(limit_down):
            temp_price = max(temp_price, limit_down)
        return temp_price


class TickSizeSlippage(BaseSlippage):
    def __init__(self, rate=0.):
        if 0 <= rate:
            self.rate = rate
        else:
            raise patch_user_exc(ValueError(_(u"invalid slippage rate value: value range is greater than 0")))

    def get_trade_price(self, order, price):
        # type: (Order, float) -> float
        if order.position_effect == POSITION_EFFECT.EXERCISE:
            raise NotImplementedError("TickSizeSlippage cannot handle exercise order")
        tick_size = Environment.get_instance().data_proxy.instrument(order.order_book_id).tick_size()

        price = price + tick_size * self.rate * (1 if order.side == SIDE.BUY else -1)

        if price <= 0:
            raise patch_user_exc(ValueError(_(
                u"invalid slippage rate value {} which cause price <= 0"
            ).format(self.rate)))

        return price


class LimitPriceSlippage(BaseSlippage):
    """使用（限价单）挂单价作为成交价，模拟限价单的最坏情况"""
    def __init__(self, _):
        pass

    def get_trade_price(self, order, price):  # type: (Order, float) -> float
        if order.type == ORDER_TYPE.LIMIT:
            return order.price
        else:
            return price
