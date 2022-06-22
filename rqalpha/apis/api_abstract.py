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

from typing import Union, Optional, List

from rqalpha.api import export_as_api
from rqalpha.core.execution_context import ExecutionContext
from rqalpha.const import EXECUTION_PHASE
from rqalpha.model.instrument import Instrument
from rqalpha.model.order import MarketOrder, LimitOrder, OrderStyle, Order
from rqalpha.utils.arg_checker import apply_rules, verify_that
from rqalpha.utils.functools import instype_singledispatch


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.SCHEDULED,
    EXECUTION_PHASE.GLOBAL
)
@apply_rules(
    verify_that('amount').is_number(),
    verify_that('style').is_instance_of((MarketOrder, LimitOrder, type(None)))
)
@instype_singledispatch
def order_shares(id_or_ins, amount, price=None, style=None):
    # type: (Union[str, Instrument], int, Optional[float], Optional[OrderStyle]) -> Optional[Order]
    """
    指定股数的买/卖单，最常见的落单方式之一。如有需要落单类型当做一个参量传入，如果忽略掉落单类型，那么默认是市价单（market order）。

    :param id_or_ins: 下单标的物
    :param amount: 下单量, 正数代表买入，负数代表卖出。将会根据一手xx股来向下调整到一手的倍数，比如中国A股就是调整成100股的倍数。
    :param price: 下单价格，默认为None，表示 :class:`~MarketOrder`, 此参数主要用于简化 `style` 参数。
    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`

    :example:

    .. code-block:: python

        #购买Buy 2000 股的平安银行股票，并以市价单发送：
        order_shares('000001.XSHE', 2000)
        #卖出2000股的平安银行股票，并以市价单发送：
        order_shares('000001.XSHE', -2000)
        #购买1000股的平安银行股票，并以限价单发送，价格为￥10：
        order_shares('000001.XSHG', 1000, style=LimitOrder(10))
    """
    raise NotImplementedError


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.SCHEDULED,
    EXECUTION_PHASE.GLOBAL
)
@apply_rules(
    verify_that('cash_amount').is_number(),
    verify_that('style').is_instance_of((MarketOrder, LimitOrder, type(None)))
)
@instype_singledispatch
def order_value(id_or_ins, cash_amount, price=None, style=None):
    # type: (Union[str, Instrument], float, Optional[float], Optional[OrderStyle]) -> Optional[Order]
    """
    使用想要花费的金钱买入/卖出股票，而不是买入/卖出想要的股数，正数代表买入，负数代表卖出。股票的股数总是会被调整成对应的100的倍数（在A中国A股市场1手是100股）。
    如果资金不足，该API将会使用最大可用资金发单。

    需要注意：
    当您提交一个买单时，cash_amount 代表的含义是您希望买入股票消耗的金额（包含税费），最终买入的股数不仅和发单的价格有关，还和税费相关的参数设置有关。
    当您提交一个卖单时，cash_amount 代表的意义是您希望卖出股票的总价值。如果金额超出了您所持有股票的价值，那么您将卖出所有股票。

    :param id_or_ins: 下单标的物
    :param cash_amount: 需要花费现金购买/卖出证券的数目。正数代表买入，负数代表卖出。
    :param price: 下单价格，默认为None，表示 :class:`~MarketOrder`, 此参数主要用于简化 `style` 参数。
    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`

    :example:

    .. code-block:: python

        #花费最多￥10000买入平安银行股票，并以市价单发送。具体下单的数量与您策略税费相关的配置有关。
        order_value('000001.XSHE', 10000)
        #卖出价值￥10000的现在持有的平安银行：
        order_value('000001.XSHE', -10000)
    """
    raise NotImplementedError


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.SCHEDULED,
    EXECUTION_PHASE.GLOBAL
)
@apply_rules(
    verify_that('percent', pre_check=True).is_number().is_greater_or_equal_than(-1).is_less_or_equal_than(1),
    verify_that('style').is_instance_of((MarketOrder, LimitOrder, type(None)))
)
@instype_singledispatch
def order_percent(id_or_ins, percent, price=None, style=None):
    # type: (Union[str, Instrument], float, Optional[float], Optional[OrderStyle]) -> Optional[Order]
    """
    发送一个花费价值等于目前投资组合（市场价值和目前现金的总和）一定百分比现金的买/卖单，正数代表买，负数代表卖。股票的股数总是会被调整成对应的一手的股票数的倍数（1手是100股）。百分比是一个小数，并且小于或等于1（<=100%），0.5表示的是50%.需要注意，如果资金不足，该API将会使用最大可用资金发单。

    需要注意：

    发送买单时，percent 代表的是期望买入股票消耗的金额（包含税费）占投资组合总权益的比例。
    发送卖单时，percent 代表的是期望卖出的股票总价值占投资组合总权益的比例。

    :param id_or_ins: 下单标的物
    :param percent: 占有现有的投资组合价值的百分比。正数表示买入，负数表示卖出。
    :param price: 下单价格，默认为None，表示 :class:`~MarketOrder`, 此参数主要用于简化 `style` 参数。
    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`

    :example:

    .. code-block:: python

        #花费等于现有投资组合50%价值的现金买入平安银行股票：
        order_percent('000001.XSHG', 0.5)
    """
    raise NotImplementedError


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.SCHEDULED,
    EXECUTION_PHASE.GLOBAL
)
@apply_rules(
    verify_that('cash_amount').is_number(),
    verify_that('style').is_instance_of((MarketOrder, LimitOrder, type(None)))
)
@instype_singledispatch
def order_target_value(id_or_ins, cash_amount, price=None, style=None):
    # type: (Union[str, Instrument], float, Optional[float], Optional[OrderStyle]) -> Optional[Order]
    """
    买入/卖出并且自动调整该证券的仓位到一个目标价值。
    加仓时，cash_amount 代表现有持仓的价值加上即将花费（包含税费）的现金的总价值。
    减仓时，cash_amount 代表调整仓位的目标价至。

    需要注意，如果资金不足，该API将会使用最大可用资金发单。

    :param id_or_ins: 下单标的物
    :param cash_amount: 最终的该证券的仓位目标价值。
    :param price: 下单价格，默认为None，表示 :class:`~MarketOrder`, 此参数主要用于简化 `style` 参数。
    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`

    :example:

    .. code-block:: python

        #如果现在的投资组合中持有价值￥3000的平安银行股票的仓位，以下代码范例会发送花费 ￥7000 现金的平安银行买单到市场。（向下调整到最接近每手股数即100的倍数的股数）：
        order_target_value('000001.XSHE', 10000)
    """
    raise NotImplementedError


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.SCHEDULED,
    EXECUTION_PHASE.GLOBAL
)
@apply_rules(
    verify_that('percent', pre_check=True).is_number().is_greater_or_equal_than(0).is_less_or_equal_than(1),
    verify_that('style').is_instance_of((MarketOrder, LimitOrder, type(None)))
)
@instype_singledispatch
def order_target_percent(id_or_ins, percent, price=None, style=None):
    # type: (Union[str, Instrument], float, Optional[float], Optional[OrderStyle]) -> Optional[Order]
    """
    买入/卖出证券以自动调整该证券的仓位到占有一个目标价值。

    加仓时，percent 代表证券已有持仓的价值加上即将花费的现金（包含税费）的总值占当前投资组合总价值的比例。
    减仓时，percent 代表证券将被调整到的目标价至占当前投资组合总价值的比例。

    其实我们需要计算一个position_to_adjust (即应该调整的仓位)

    `position_to_adjust = target_position - current_position`

    投资组合价值等于所有已有仓位的价值和剩余现金的总和。买/卖单会被下舍入一手股数（A股是100的倍数）的倍数。目标百分比应该是一个小数，并且最大值应该<=1，比如0.5表示50%。

    如果 position_to_adjust 计算之后是正的，那么会买入该证券，否则会卖出该证券。需要注意，如果需要买入证券而资金不足，该 API 将使用最大可用资金发出订单。

    另外，如果您希望大量调整股票仓位，推荐使用 order_target_portfolio 而非在循环中调取 order_target_percent，前者将拥有更好的性能。

    :param id_or_ins: 下单标的物
    :param percent: 仓位最终所占投资组合总价值的目标百分比。
    :param price: 下单价格，默认为None，表示 :class:`~MarketOrder`, 此参数主要用于简化 `style` 参数。
    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`

    :example:

    .. code-block:: python

        #如果投资组合中已经有了平安银行股票的仓位，并且占据目前投资组合的10%的价值，那么以下代码会消耗相当于当前投资组合价值5%的现金买入平安银行股票：
        order_target_percent('000001.XSHE', 0.15)
    """
    raise NotImplementedError


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.SCHEDULED,
    EXECUTION_PHASE.GLOBAL
)
@apply_rules(
    verify_that('amount', pre_check=True).is_number().is_greater_or_equal_than(0),
    verify_that('style').is_instance_of((MarketOrder, LimitOrder, type(None)))
)
@instype_singledispatch
def buy_open(id_or_ins, amount, price=None, style=None):
    # type: (Union[str, Instrument], int, Optional[float], Optional[OrderStyle]) -> Union[Order, List[Order], None]
    """
    买入开仓。

    :param id_or_ins: 下单标的物
    :param amount: 下单手数
    :param price: 下单价格，默认为None，表示 :class:`~MarketOrder`, 此参数主要用于简化 `style` 参数。
    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`

    :example:

    .. code-block:: python

        #以价格为3500的限价单开仓买入2张上期所AG1607合约：
        buy_open('AG1607', amount=2, price=3500))
    """
    raise NotImplementedError


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.SCHEDULED,
    EXECUTION_PHASE.GLOBAL
)
@apply_rules(
    verify_that('amount', pre_check=True).is_number().is_greater_or_equal_than(0),
    verify_that('style').is_instance_of((MarketOrder, LimitOrder, type(None)))
)
@instype_singledispatch
def buy_close(id_or_ins, amount, price=None, style=None, close_today=False):
    # type: (Union[str, Instrument], int, Optional[float], Optional[OrderStyle], Optional[bool]) -> Union[Order, List[Order], None]
    """
    平卖仓

    :param id_or_ins: 下单标的物
    :param amount: 下单手数
    :param price: 下单价格，默认为None，表示 :class:`~MarketOrder`, 此参数主要用于简化 `style` 参数。
    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :param close_today: 是否指定发平今仓单，默认为False，发送平仓单

    :example:

    .. code-block:: python

        #市价单将现有IF1603空仓买入平仓2张：
        buy_close('IF1603', 2)
    """
    raise NotImplementedError


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.SCHEDULED,
    EXECUTION_PHASE.GLOBAL
)
@apply_rules(
    verify_that('amount', pre_check=True).is_number().is_greater_or_equal_than(0),
    verify_that('style').is_instance_of((MarketOrder, LimitOrder, type(None)))
)
@instype_singledispatch
def sell_open(id_or_ins, amount, price=None, style=None):
    # type: (Union[str, Instrument], int, Optional[float], Optional[OrderStyle]) -> Union[Order, List[Order], None]
    """
    卖出开仓

    :param id_or_ins: 下单标的物
    :param amount: 下单手数
    :param price: 下单价格，默认为None，表示 :class:`~MarketOrder`, 此参数主要用于简化 `style` 参数。
    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    """
    raise NotImplementedError


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.SCHEDULED,
    EXECUTION_PHASE.GLOBAL
)
@apply_rules(
    verify_that('amount', pre_check=True).is_number().is_greater_or_equal_than(0),
    verify_that('style').is_instance_of((MarketOrder, LimitOrder, type(None)))
)
@instype_singledispatch
def sell_close(id_or_ins, amount, price=None, style=None, close_today=False):
    # type: (Union[str, Instrument], float, Optional[float], Optional[OrderStyle], Optional[bool]) -> Union[Order, List[Order], None]
    """
    平买仓

    :param id_or_ins: 下单标的物
    :param amount: 下单手数
    :param price: 下单价格，默认为None，表示 :class:`~MarketOrder`, 此参数主要用于简化 `style` 参数。
    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :param close_today: 是否指定发平今仓单，默认为False，发送平仓单
    """
    raise NotImplementedError


@export_as_api
@apply_rules(verify_that("quantity").is_number())
@instype_singledispatch
def order(order_book_id, quantity, price=None, style=None):
    # type: (Union[str, Instrument], int, Optional[float], Optional[OrderStyle]) -> List[Order]
    """
      全品种通用智能调仓函数

      如果不指定 price, 则相当于下 MarketOrder

      如果 order_book_id 是股票，等同于调用 order_shares

      如果 order_book_id 是期货，则进行智能下单:

          *   quantity 表示调仓量
          *   如果 quantity 为正数，则先平 Sell 方向仓位，再开 Buy 方向仓位
          *   如果 quantity 为负数，则先平 Buy 反向仓位，再开 Sell 方向仓位

      :param order_book_id: 下单标的物
      :param quantity: 调仓量
      :param price: 下单价格
      :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`

      :example:

      ..  code-block:: python3
          :linenos:

          # 当前仓位为0
          # RB1710 多方向调仓2手：调整后变为 BUY 2手
          order('RB1710', 2)

          # RB1710 空方向调仓3手：先平多方向2手 在开空方向1手，调整后变为 SELL 1手
          order('RB1710', -3)

    """
    raise NotImplementedError


@export_as_api
@apply_rules(verify_that("quantity").is_number())
@instype_singledispatch
def order_to(order_book_id, quantity, price=None, style=None):
    # type: (Union[str, Instrument], int, Optional[float], Optional[OrderStyle]) -> List[Order]
    """
    全品种通用智能调仓函数

    如果不指定 price, 则相当于 MarketOrder

    如果 order_book_id 是股票，则表示仓位调整到多少股

    如果 order_book_id 是期货，则进行智能调仓:

        *   quantity 表示调整至某个仓位
        *   quantity 如果为正数，则先平 SELL 方向仓位，再 BUY 方向开仓 quantity 手
        *   quantity 如果为负数，则先平 BUY 方向仓位，再 SELL 方向开仓 -quantity 手

    :param order_book_id: 下单标的物
    :param int quantity: 调仓量
    :param float price: 下单价格
    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :example:

    ..  code-block:: python3
        :linenos:

        # 当前仓位为0
        # RB1710 调仓至 BUY 2手
        order_to('RB1710', 2)

        # RB1710 调仓至 SELL 1手
        order_to('RB1710', -1)
    """
    raise NotImplementedError


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.SCHEDULED,
    EXECUTION_PHASE.GLOBAL
)
@apply_rules(verify_that("amount", pre_check=True).is_number().is_greater_or_equal_than(1))
@instype_singledispatch
def exercise(id_or_ins, amount, convert=False):
    # type: (Union[str, Instrument], int, Optional[bool]) -> Optional[Order]
    """
        行权。针对期权、可转债等含权合约，行使合约权利方被赋予的权利。

        :param id_or_ins: 行权合约，order_book_id 或 Instrument 对象
        :param amount: 参与行权的合约数量
        :param convert: 是否为转股（转债行权时可用）

        :example:

        .. code-block:: python

            # 行使一张豆粕1905购2350的权力
            exercise("M1905C2350", 1)

        """
    raise NotImplementedError
