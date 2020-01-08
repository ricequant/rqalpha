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
import six
from collections import UserDict
from collections.abc import Mapping
from typing import Dict, Type

from rqalpha.environment import Environment
from rqalpha.const import DEFAULT_ACCOUNT_TYPE, POSITION_DIRECTION
from rqalpha.model.asset_position import AssetPosition
from rqalpha.utils.repr import property_repr
from rqalpha.utils.class_helper import deprecated_property


class PositionProxy(object):
    __abandon_properties__ = [
        "positions",
        "long",
        "short"
    ]

    def __init__(self, long, short):
        # type: (AssetPosition, AssetPosition) -> PositionProxy
        self._long = long
        self._short = short

    __repr__ = property_repr

    @property
    def type(self):
        raise NotImplementedError

    @property
    def order_book_id(self):
        return self._long.order_book_id

    @property
    def last_price(self):
        return self._long.last_price

    @property
    def market_value(self):
        return self._long.market_value - self._short.market_value

    # -- PNL 相关
    @property
    def position_pnl(self):
        """
        [float] 昨仓盈亏，当前交易日盈亏中来源于昨仓的部分

        多方向昨仓盈亏 = 昨日收盘时的持仓 * 合约乘数 * (最新价 - 昨收价)
        空方向昨仓盈亏 = 昨日收盘时的持仓 * 合约乘数 * (昨收价 - 最新价)

        """
        return self._long.position_pnl + self._short.position_pnl

    @property
    def trading_pnl(self):
        """
        [float] 交易盈亏，当前交易日盈亏中来源于当日成交的部分

        单比买方向成交的交易盈亏 = 成交量 * (最新价 - 成交价)
        单比卖方向成交的交易盈亏 = 成交量 * (成交价 - 最新价)

        """
        return self._long.trading_pnl + self._short.trading_pnl

    @property
    def daily_pnl(self):
        """
        [float] 当日盈亏

        当日盈亏 = 昨仓盈亏 + 交易盈亏

        """
        return self._long.position_pnl + self._long.trading_pnl + self._short.position_pnl +\
               self._short.trading_pnl - self.transaction_cost

    @property
    def pnl(self):
        """
        [float] 累计盈亏

        (最新价 - 平均开仓价格) * 持仓量 * 合约乘数

        """
        return self._long.pnl + self._short.pnl

    # -- Quantity 相关
    @property
    def open_orders(self):
        return Environment.get_instance().broker.get_open_orders(self.order_book_id)

    # -- Margin 相关
    @property
    def margin(self):
        """
        [float] 保证金

        保证金 = 持仓量 * 最新价 * 合约乘数 * 保证金率

        股票保证金 = 市值 = 持仓量 * 最新价

        """
        return self._long.margin + self._short.margin

    @property
    def transaction_cost(self):
        """
        [float] 交易费率
        """
        return self._long.transaction_cost + self._short.transaction_cost

    @property
    def positions(self):
        return [self._long, self._short]

    @property
    def long(self):
        return self._long

    @property
    def short(self):
        return self._short


class StockPositionProxy(PositionProxy):

    __abandon_properties__ = PositionProxy.__abandon_properties__ + [
        "margin"
    ]

    @property
    def type(self):
        return DEFAULT_ACCOUNT_TYPE.STOCK

    def split_(self, ratio):
        self._long.apply_split(ratio)

    def dividend_(self, dividend_per_share):
        self._long.apply_dividend(dividend_per_share)

    @property
    def quantity(self):
        return self._long.quantity

    @property
    def sellable(self):
        """
        [int] 该仓位可卖出股数。T＋1 的市场中sellable = 所有持仓 - 今日买入的仓位 - 已冻结
        """
        return self._long.closable

    @property
    def avg_price(self):
        """
        [float] 平均开仓价格
        """
        return self._long.avg_price

    @property
    def value_percent(self):
        """
        [float] 获得该持仓的实时市场价值在股票投资组合价值中所占比例，取值范围[0, 1]
        """
        accounts = Environment.get_instance().portfolio.accounts
        if DEFAULT_ACCOUNT_TYPE.STOCK not in accounts:
            return 0
        total_value = accounts[DEFAULT_ACCOUNT_TYPE.STOCK].total_value
        return 0 if total_value == 0 else self.market_value / total_value


class FuturePositionProxy(PositionProxy):

    __abandon_properties__ = PositionProxy.__abandon_properties__ +[
        "holding_pnl",
        "buy_holding_pnl",
        "sell_holding_pnl",
        "realized_pnl",
        "buy_realized_pnl",
        "sell_realized_pnl",
        "buy_avg_holding_price",
        "sell_avg_holding_price"
    ]

    @property
    def type(self):
        return DEFAULT_ACCOUNT_TYPE.FUTURE

    @property
    def margin_rate(self):
        return self._long.margin_rate

    @property
    def contract_multiplier(self):
        return self._long.contract_multiplier

    @property
    def buy_market_value(self):
        """
        [float] 多方向市值
        """
        return self._long.market_value

    @property
    def sell_market_value(self):
        """
        [float] 空方向市值
        """
        return self._short.market_value

    @property
    def buy_position_pnl(self):
        """
        [float] 多方向昨仓盈亏
        """
        return self._long.position_pnl

    @property
    def sell_position_pnl(self):
        """
        [float] 空方向昨仓盈亏
        """
        return self._short.position_pnl

    @property
    def buy_trading_pnl(self):
        """
        [float] 多方向交易盈亏
        """
        return self._long.trading_pnl

    @property
    def sell_trading_pnl(self):
        """
        [float] 空方向交易盈亏
        """
        return self._short.trading_pnl

    @property
    def buy_daily_pnl(self):
        """
        [float] 多方向每日盈亏
        """
        return self.buy_position_pnl + self.buy_trading_pnl

    @property
    def sell_daily_pnl(self):
        """
        [float] 空方向每日盈亏
        """
        return self.sell_position_pnl + self.sell_trading_pnl

    @property
    def buy_pnl(self):
        """
        [float] 买方向累计盈亏
        """
        return self._long.pnl

    @property
    def sell_pnl(self):
        """
        [float] 空方向累计盈亏
        """
        return self._short.pnl

    @property
    def buy_old_quantity(self):
        """
        [int] 多方向昨仓
        """
        return self._long.old_quantity

    @property
    def sell_old_quantity(self):
        """
        [int] 空方向昨仓
        """
        return self._short.old_quantity

    @property
    def buy_today_quantity(self):
        """
        [int] 多方向今仓
        """
        return self._long.today_quantity

    @property
    def sell_today_quantity(self):
        """
        [int] 空方向今仓
        """
        return self._short.today_quantity

    @property
    def buy_quantity(self):
        """
        [int] 多方向持仓
        """
        return self.buy_old_quantity + self.buy_today_quantity

    @property
    def sell_quantity(self):
        """
        [int] 空方向持仓
        """
        return self.sell_old_quantity + self.sell_today_quantity

    @property
    def buy_margin(self):
        """
        [float] 多方向持仓保证金
        """
        return self._long.margin

    @property
    def sell_margin(self):
        """
        [float] 空方向持仓保证金
        """
        return self._short.margin

    @property
    def buy_avg_open_price(self):
        """
        [float] 多方向平均开仓价格
        """
        return self._long.avg_price

    @property
    def sell_avg_open_price(self):
        """
        [float] 空方向平均开仓价格
        """
        return self._short.avg_price

    @property
    def buy_transaction_cost(self):
        """
        [float] 多方向交易费率
        """
        return self._long.transaction_cost

    @property
    def sell_transaction_cost(self):
        """
        [float] 空方向交易费率
        """
        return self._short.transaction_cost

    @property
    def closable_today_sell_quantity(self):
        return self._long.today_closable

    @property
    def closable_today_buy_quantity(self):
        return self._long.today_closable

    @property
    def closable_buy_quantity(self):
        """
        [float] 可平多方向持仓
        """
        return self._long.closable

    @property
    def closable_sell_quantity(self):
        """
        [float] 可平空方向持仓
        """
        return self._short.closable

    holding_pnl = deprecated_property("holding_pnl", "position_pnl")
    buy_holding_pnl = deprecated_property("buy_holding_pnl", "buy_position_pnl")
    sell_holding_pnl = deprecated_property("sell_holding_pnl", "sell_position_pnl")
    realized_pnl = deprecated_property("realized_pnl", "trading_pnl")
    buy_realized_pnl = deprecated_property("buy_realized_pnl", "buy_trading_pnl")
    sell_realized_pnl = deprecated_property("sell_realized_pnl", "sell_trading_pnl")
    buy_avg_holding_price = deprecated_property("buy_avg_holding_price", "buy_avg_open_price")
    sell_avg_holding_price = deprecated_property("sell_avg_holding_price", "sell_avg_open_price")


class PositionProxyDict(UserDict):
    def __init__(self, positions, position_proxy_cls):
        # type: (Dict[str, Dict[POSITION_DIRECTION, AssetPosition]], Type) -> PositionProxyDict
        super(PositionProxyDict, self).__init__()
        self._positions = positions
        self._position_proxy_cls = position_proxy_cls

    def __getitem__(self, order_book_id):
        if order_book_id not in self._positions:
            long = AssetPosition(order_book_id, POSITION_DIRECTION.LONG)
            short = AssetPosition(order_book_id, POSITION_DIRECTION.SHORT)
        else:
            positions = self._positions[order_book_id]
            long = positions[POSITION_DIRECTION.LONG]
            short = positions[POSITION_DIRECTION.SHORT]
        return self._position_proxy_cls(long, short)

    def keys(self):
        return self._positions.keys()

    def __contains__(self, item):
        return item in self._positions

    def __iter__(self):
        return iter(self._positions)

    def __len__(self):
        return len(self._positions)

    def __setitem__(self, key, value):
        raise TypeError("{} object does not support item assignment".format(self.__class__.__name__))

    def __delitem__(self, key):
        raise TypeError("{} object does not support item deletion".format(self.__class__.__name__))

    def __repr__(self):
        return repr({k: self[k] for k in self._positions.keys()})
