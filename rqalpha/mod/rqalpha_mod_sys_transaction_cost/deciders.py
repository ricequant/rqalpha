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

from collections import defaultdict

from rqalpha.interface import AbstractTransactionCostDecider
from rqalpha.environment import Environment
from rqalpha.const import SIDE, HEDGE_TYPE, COMMISSION_TYPE, POSITION_EFFECT


class StockTransactionCostDecider(AbstractTransactionCostDecider):
    def __init__(self, commission_rate, commission_multiplier, min_commission):
        self.commission_rate = commission_rate
        self.commission_multiplier = commission_multiplier
        self.commission_map = defaultdict(lambda: min_commission)
        self.min_commission = min_commission

        self.env = Environment.get_instance()

    def _get_order_commission(self, order_book_id, side, price, quantity):
        commission = price * quantity * self.commission_rate * self.commission_multiplier
        return max(commission, self.min_commission)

    def _get_tax(self, order_book_id, side, cost_money):
        raise NotImplementedError

    def get_trade_commission(self, trade):
        """
        计算手续费这个逻辑比较复杂，按照如下算法来计算：
        1.  定义一个剩余手续费的概念，根据order_id存储在commission_map中，默认为min_commission
        2.  当trade来时计算该trade产生的手续费cost_money
        3.  如果cost_money > commission
            3.1 如果commission 等于 min_commission，说明这是第一笔trade，此时，直接commission置0，返回cost_money即可
            3.2 如果commission 不等于 min_commission, 则说明这不是第一笔trade,此时，直接cost_money - commission即可
        4.  如果cost_money <= commission
            4.1 如果commission 等于 min_commission, 说明是第一笔trade, 此时，返回min_commission(提前把最小手续费收了)
            4.2 如果commission 不等于 min_commission， 说明不是第一笔trade, 之前的trade中min_commission已经收过了，所以返回0.
        """
        order_id = trade.order_id
        commission = self.commission_map[order_id]
        cost_commission = trade.last_price * trade.last_quantity * self.commission_rate * self.commission_multiplier
        if cost_commission > commission:
            if commission == self.min_commission:
                self.commission_map[order_id] = 0
                return cost_commission
            else:
                self.commission_map[order_id] = 0
                return cost_commission - commission
        else:
            if commission == self.min_commission:
                self.commission_map[order_id] -= cost_commission
                return commission
            else:
                self.commission_map[order_id] -= cost_commission
                return 0

    def get_trade_tax(self, trade):
        return self._get_tax(trade.order_book_id, trade.side, trade.last_price * trade.last_quantity)

    def get_order_transaction_cost(self, order):
        commission = self._get_order_commission(order.order_book_id, order.side, order.frozen_price, order.quantity)
        tax = self._get_tax(order.order_book_id, order.side, order.frozen_price * order.quantity)
        return tax + commission


class CNStockTransactionCostDecider(StockTransactionCostDecider):
    def __init__(self, commission_multiplier, min_commission, tax_multiplier):
        super(CNStockTransactionCostDecider, self).__init__(0.0008, commission_multiplier, min_commission)
        self.tax_rate = 0.001
        self.tax_multiplier = tax_multiplier

    def _get_tax(self, order_book_id, side, cost_money):
        instrument = Environment.get_instance().get_instrument(order_book_id)
        if instrument.type != 'CS':
            return 0
        return cost_money * self.tax_rate * self.tax_multiplier if side == SIDE.SELL else 0


class CNFutureTransactionCostDecider(AbstractTransactionCostDecider):
    def __init__(self, commission_multiplier):
        self.commission_multiplier = commission_multiplier
        self.hedge_type = HEDGE_TYPE.SPECULATION

        self.env = Environment.get_instance()

    def _get_commission(self, order_book_id, position_effect, price, quantity, close_today_quantity):
        info = self.env.data_proxy.get_commission_info(order_book_id)
        commission = 0
        if info['commission_type'] == COMMISSION_TYPE.BY_MONEY:
            contract_multiplier = self.env.get_instrument(order_book_id).contract_multiplier
            if position_effect == POSITION_EFFECT.OPEN:
                commission += price * quantity * contract_multiplier * info[
                    'open_commission_ratio']
            else:
                commission += price * (
                        quantity - close_today_quantity
                ) * contract_multiplier * info['close_commission_ratio']
                commission += price * close_today_quantity * contract_multiplier * info['close_commission_today_ratio']
        else:
            if position_effect == POSITION_EFFECT.OPEN:
                commission += quantity * info['open_commission_ratio']
            else:
                commission += (quantity - close_today_quantity) * info['close_commission_ratio']
                commission += close_today_quantity * info['close_commission_today_ratio']
        return commission * self.commission_multiplier

    def get_trade_commission(self, trade):
        return self._get_commission(
            trade.order_book_id, trade.position_effect, trade.last_price, trade.last_quantity, trade.close_today_amount
        )

    def get_trade_tax(self, trade):
        return 0

    def get_order_transaction_cost(self, order):
        close_today_quantity = order.quantity if order.position_effect == POSITION_EFFECT.CLOSE_TODAY else 0

        return self._get_commission(
            order.order_book_id, order.position_effect, order.frozen_price, order.quantity, close_today_quantity
        )
