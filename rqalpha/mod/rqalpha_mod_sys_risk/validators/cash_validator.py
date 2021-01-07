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

from rqalpha.interface import AbstractFrontendValidator
from rqalpha.const import POSITION_EFFECT
from rqalpha.utils.logger import user_system_log

from rqalpha.utils.i18n import gettext as _


def is_cash_enough(env, order, account, warn=False):
    instrument = env.data_proxy.instruments(order.order_book_id)
    cost_money = instrument.calc_cash_occupation(order.frozen_price, order.quantity, order.position_direction)
    cost_money += env.get_order_transaction_cost(order)
    if cost_money <= account.cash:
        return True
    if warn:
        user_system_log.warn(
            _("Order Creation Failed: not enough money to buy {order_book_id}, needs {cost_money:.2f},"
              " cash {cash:.2f}").format(
                order_book_id=order.order_book_id,
                cost_money=cost_money,
                cash=account.cash,
            )
        )
    return False



class CashValidator(AbstractFrontendValidator):
    def __init__(self, env):
        self._env = env

    def can_submit_order(self, order, account=None):
        if (account is None) or (order.position_effect != POSITION_EFFECT.OPEN):
            return True
        return is_cash_enough(self._env, order, account, warn=True)

    def can_cancel_order(self, order, account=None):
        return True
