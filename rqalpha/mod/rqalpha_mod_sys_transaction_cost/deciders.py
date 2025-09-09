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
from datetime import datetime

from rqalpha.interface import AbstractTransactionCostDecider, TransactionCostArgs, TransactionCost
from rqalpha.environment import Environment
from rqalpha.const import SIDE, HEDGE_TYPE, COMMISSION_TYPE, POSITION_EFFECT, INSTRUMENT_TYPE
from rqalpha.core.events import EVENT


STOCK_PIT_TAX_CHANGE_DATE = datetime(2023, 8, 28)


class StockTransactionCostDecider(AbstractTransactionCostDecider):
    def __init__(self, commission_multiplier, min_commission, tax_multiplier, pit_tax, event_bus):
        self.commission_rate = 0.0008
        self.commission_multiplier = commission_multiplier
        self.commission_map = defaultdict(lambda: min_commission)
        self.min_commission = min_commission

        self.tax_rate = 0.0005
        if pit_tax:
            event_bus.add_listener(EVENT.PRE_BEFORE_TRADING, self._update_tax_rate)
        self.tax_multiplier = tax_multiplier

        self.env = Environment.get_instance()

    def _update_tax_rate(self, event):
        if event.trading_dt < STOCK_PIT_TAX_CHANGE_DATE:
            self.tax_rate = 0.001
        else:
            self.tax_rate = 0.0005

    def _calc_commission(self, args: TransactionCostArgs) -> float:
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
        cost_commission = args.price * args.quantity * self.commission_rate * self.commission_multiplier
        order_id = args.order_id
        if order_id is None:
            return max(cost_commission, self.min_commission) 
        commission = self.commission_map[order_id]
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

    def _calc_tax(self, args: TransactionCostArgs) -> float:
        if args.side == SIDE.BUY or args.instrument.type != INSTRUMENT_TYPE.CS:
            return 0
        cost_money = args.price * args.quantity
        return cost_money * self.tax_rate * self.tax_multiplier

    def calc(self, args: TransactionCostArgs) -> TransactionCost:
        return TransactionCost(commission=self._calc_commission(args), tax=self._calc_tax(args), other_fees=0)

class FuturesTransactionCostDecider(AbstractTransactionCostDecider):
    def __init__(self, commission_multiplier):
        self.commission_multiplier = commission_multiplier
        self.hedge_type = HEDGE_TYPE.SPECULATION

        self.env = Environment.get_instance()

    def _calc_commission(self, args: TransactionCostArgs) -> float:
        ins = args.instrument
        info = self.env.data_proxy.get_futures_trading_parameters(ins.order_book_id, self.env.trading_dt)
        commission = 0
        if info.commission_type == COMMISSION_TYPE.BY_MONEY:
            contract_multiplier = ins.contract_multiplier
            if args.position_effect == POSITION_EFFECT.OPEN:
                commission += args.price * args.quantity * contract_multiplier * info.open_commission_ratio
            else:
                commission += args.price * (
                        args.quantity - args.close_today_quantity
                ) * contract_multiplier * info.close_commission_ratio
                commission += args.price * args.close_today_quantity * contract_multiplier * info.close_commission_today_ratio
        else:
            if args.position_effect == POSITION_EFFECT.OPEN:
                commission += args.quantity * info.open_commission_ratio
            else:
                commission += (args.quantity - args.close_today_quantity) * info.close_commission_ratio
                commission += args.close_today_quantity * info.close_commission_today_ratio
        return commission * self.commission_multiplier

    def calc(self, args: TransactionCostArgs) -> TransactionCost:
        return TransactionCost(commission=self._calc_commission(args), tax=0, other_fees=0)
