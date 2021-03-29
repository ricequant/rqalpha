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


from rqalpha.interface import AbstractFrontendValidator
from rqalpha.const import ORDER_TYPE, POSITION_EFFECT
from rqalpha.utils.logger import user_system_log

from rqalpha.utils.i18n import gettext as _


class PriceValidator(AbstractFrontendValidator):
    def __init__(self, env):
        self._env = env

    def can_submit_order(self, order, account=None):
        if (order.type != ORDER_TYPE.LIMIT) or (order.position_effect == POSITION_EFFECT.EXERCISE):
            return True

        # FIXME: it may be better to round price in data source
        limit_up = round(self._env.price_board.get_limit_up(order.order_book_id), 4)
        if order.price > limit_up:
            reason = _(
                "Order Creation Failed: limit order price {limit_price} is higher "
                "than limit up {limit_up}, order_book_id={order_book_id}"
            ).format(
                order_book_id=order.order_book_id,
                limit_price=order.price,
                limit_up=limit_up
            )
            user_system_log.warn(reason)
            return False

        limit_down = round(self._env.price_board.get_limit_down(order.order_book_id), 4)
        if order.price < limit_down:
            reason = _(
                "Order Creation Failed: limit order price {limit_price} is lower "
                "than limit down {limit_down}, order_book_id={order_book_id}"
            ).format(
                order_book_id=order.order_book_id,
                limit_price=order.price,
                limit_down=limit_down
            )
            user_system_log.warn(reason)
            return False

        return True

    def can_cancel_order(self, order, account=None):
        return True
