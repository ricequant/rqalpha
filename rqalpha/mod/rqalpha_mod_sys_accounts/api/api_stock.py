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

import datetime
from decimal import Decimal, getcontext
from itertools import chain
from typing import Dict, List, Optional, Union, Tuple

import numpy as np
import pandas as pd
from rqalpha.api import export_as_api
from rqalpha.apis.api_abstract import (order, order_percent, order_shares,
                                       order_target_percent,
                                       order_target_value, order_to,
                                       order_value)
from rqalpha.apis.api_base import (assure_instrument, assure_order_book_id,
                                   cal_style)
from rqalpha.const import (DEFAULT_ACCOUNT_TYPE, EXECUTION_PHASE,
                           INSTRUMENT_TYPE, ORDER_TYPE, POSITION_DIRECTION,
                           POSITION_EFFECT, SIDE)
from rqalpha.core.execution_context import ExecutionContext
from rqalpha.environment import Environment
from rqalpha.mod.rqalpha_mod_sys_risk.validators.cash_validator import \
    is_cash_enough
from rqalpha.model.instrument import IndustryCode as industry_code
from rqalpha.model.instrument import IndustryCodeItem, Instrument
from rqalpha.model.instrument import SectorCode as sector_code
from rqalpha.model.instrument import SectorCodeItem
from rqalpha.model.order import LimitOrder, MarketOrder, Order, OrderStyle
from rqalpha.utils import INST_TYPE_IN_STOCK_ACCOUNT, is_valid_price
from rqalpha.utils.arg_checker import apply_rules, verify_that
from rqalpha.utils.datetime_func import to_date
from rqalpha.utils.exception import RQInvalidArgument
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.logger import user_system_log

# 使用Decimal 解决浮点数运算精度问题
getcontext().prec = 10

export_as_api(industry_code, name='industry_code')
export_as_api(sector_code, name='sector_code')

KSH_MIN_AMOUNT = 200


def _get_account_position_ins(id_or_ins):
    ins = assure_instrument(id_or_ins)
    try:
        account = Environment.get_instance().portfolio.accounts[DEFAULT_ACCOUNT_TYPE.STOCK]
    except KeyError:
        raise KeyError(_(
                u"order_book_id: {order_book_id} needs stock account, please set and try again!"
            ).format(order_book_id=ins.order_book_id))
    position = account.get_position(ins.order_book_id, POSITION_DIRECTION.LONG)
    return account, position, ins


def _round_order_quantity(ins, quantity) -> int:
    if ins.type == "CS" and ins.board_type == "KSH":
        # KSH can buy(sell) 201, 202 shares
        return 0 if abs(quantity) < KSH_MIN_AMOUNT else int(quantity)
    else:
        round_lot = ins.round_lot
        return int(Decimal(quantity) / Decimal(round_lot)) * round_lot


def _submit_order(ins, amount, side, position_effect, style, current_quantity, auto_switch_order_value):
    env = Environment.get_instance()
    if isinstance(style, LimitOrder):
        if not is_valid_price(style.get_limit_price()):
            raise RQInvalidArgument(_(u"Limit order price should be positive"))
    price = env.data_proxy.get_last_price(ins.order_book_id)
    if not is_valid_price(price):
        user_system_log.warn(
            _(u"Order Creation Failed: [{order_book_id}] No market data").format(order_book_id=ins.order_book_id))
        return

    if (side == SIDE.BUY) or (side == SIDE.SELL and current_quantity != abs(amount)):
        amount = _round_order_quantity(ins, amount)

    if amount == 0:
        user_system_log.warn(_(
            u"Order Creation Failed: 0 order quantity, order_book_id={order_book_id}"
        ).format(order_book_id=ins.order_book_id))
        return
    order = Order.__from_create__(ins.order_book_id, abs(amount), side, style, position_effect)
    if order.type == ORDER_TYPE.MARKET:
        order.set_frozen_price(price)
    if side == SIDE.BUY and auto_switch_order_value:
        account, position, ins = _get_account_position_ins(ins)
        if not is_cash_enough(env, order, account.cash):
            user_system_log.warn(_(
                "insufficient cash, use all remaining cash({}) to create order"
            ).format(account.cash))
            return _order_value(account, position, ins, account.cash, style)
    return env.submit_order(order)


def _order_shares(ins, amount, style, quantity, auto_switch_order_value):
    side, position_effect = (SIDE.BUY, POSITION_EFFECT.OPEN) if amount > 0 else (SIDE.SELL, POSITION_EFFECT.CLOSE)
    return _submit_order(ins, amount, side, position_effect, style, quantity, auto_switch_order_value)


def _order_value(account, position, ins, cash_amount, style):
    env = Environment.get_instance()
    if cash_amount > 0:
        cash_amount = min(cash_amount, account.cash)
    if isinstance(style, LimitOrder):
        price = style.get_limit_price()
    else:
        price = env.data_proxy.get_last_price(ins.order_book_id)
        if not is_valid_price(price):
            user_system_log.warn(
                _(u"Order Creation Failed: [{order_book_id}] No market data").format(order_book_id=ins.order_book_id)
            )
            return

    amount = int(Decimal(cash_amount) / Decimal(price))
    round_lot = int(ins.round_lot)
    if cash_amount > 0:
        amount = _round_order_quantity(ins, amount)
        while amount > 0:
            expected_transaction_cost = env.get_order_transaction_cost(Order.__from_create__(
                ins.order_book_id, amount, SIDE.BUY, LimitOrder(price), POSITION_EFFECT.OPEN
            ))
            if amount * price + expected_transaction_cost <= cash_amount:
                break
            amount -= round_lot
        else:
            user_system_log.warn(_(
                u"Order Creation Failed: 0 order quantity, order_book_id={order_book_id}"
            ).format(order_book_id=ins.order_book_id))
            return

    if amount < 0:
        amount = max(amount, -position.closable)

    return _order_shares(ins, amount, style, position.quantity, auto_switch_order_value=False)


@order_shares.register(INST_TYPE_IN_STOCK_ACCOUNT)
def stock_order_shares(id_or_ins, amount, price=None, style=None):
    auto_switch_order_value = Environment.get_instance().config.mod.sys_accounts.auto_switch_order_value
    account, position, ins = _get_account_position_ins(id_or_ins)
    return _order_shares(assure_instrument(id_or_ins), amount, cal_style(price, style), position.quantity,
                         auto_switch_order_value)


@order_value.register(INST_TYPE_IN_STOCK_ACCOUNT)
def stock_order_value(id_or_ins, cash_amount, price=None, style=None):
    account, position, ins = _get_account_position_ins(id_or_ins)
    return _order_value(account, position, ins, cash_amount, cal_style(price, style))


@order_percent.register(INST_TYPE_IN_STOCK_ACCOUNT)
def stock_order_percent(id_or_ins, percent, price=None, style=None):
    account, position, ins = _get_account_position_ins(id_or_ins)
    return _order_value(account, position, ins, account.total_value * percent, cal_style(price, style))


@order_target_value.register(INST_TYPE_IN_STOCK_ACCOUNT)
def stock_order_target_value(id_or_ins, cash_amount, price=None, style=None):
    account, position, ins = _get_account_position_ins(id_or_ins)
    if cash_amount == 0:
        return _submit_order(ins, position.closable, SIDE.SELL, POSITION_EFFECT.CLOSE, cal_style(price, style),
                             position.quantity, False)
    return _order_value(account, position, ins, cash_amount - position.market_value, cal_style(price, style))


@order_target_percent.register(INST_TYPE_IN_STOCK_ACCOUNT)
def stock_order_target_percent(id_or_ins, percent, price=None, style=None):
    account, position, ins = _get_account_position_ins(id_or_ins)
    if percent == 0:
        return _submit_order(ins, position.closable, SIDE.SELL, POSITION_EFFECT.CLOSE, cal_style(price, style),
                             position.quantity, False)
    else:
        return _order_value(
            account, position, ins, account.total_value * percent - position.market_value, cal_style(price, style)
        )


@order.register(INST_TYPE_IN_STOCK_ACCOUNT)
def stock_order(order_book_id, quantity, price=None, style=None):
    result_order = stock_order_shares(order_book_id, quantity, price, style)
    if result_order:
        return [result_order]
    return []


@order_to.register(INST_TYPE_IN_STOCK_ACCOUNT)
def stock_order_to(order_book_id, quantity, price=None, style=None):
    position = Environment.get_instance().portfolio.get_position(order_book_id, POSITION_DIRECTION.LONG)
    quantity = quantity - position.quantity
    result_order = stock_order_shares(order_book_id, quantity, price, style)
    if result_order:
        return [result_order]
    return []


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.SCHEDULED,
    EXECUTION_PHASE.GLOBAL
)
@apply_rules(verify_that('id_or_ins').is_valid_stock(),
             verify_that('amount').is_number(),
             verify_that('style').is_instance_of((MarketOrder, LimitOrder, type(None))))
def order_lots(id_or_ins, amount, price=None, style=None):
    # type: (Union[str, Instrument], int, Optional[float], Optional[OrderStyle]) -> Optional[Order]
    """
    指定手数发送买/卖单。如有需要落单类型当做一个参量传入，如果忽略掉落单类型，那么默认是市价单（market order）。

    :param id_or_ins: 下单标的物
    :param int amount: 下单量, 正数代表买入，负数代表卖出。将会根据一手xx股来向下调整到一手的倍数，比如中国A股就是调整成100股的倍数。
    :param float price: 下单价格，默认为None，表示 :class:`~MarketOrder`, 此参数主要用于简化 `style` 参数。
    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`

    :example:

    .. code-block:: python

        #买入20手的平安银行股票，并且发送市价单：
        order_lots('000001.XSHE', 20)
        #买入10手平安银行股票，并且发送限价单，价格为￥10：
        order_lots('000001.XSHE', 10, style=LimitOrder(10))

    """
    auto_switch_order_value = Environment.get_instance().config.mod.sys_accounts.auto_switch_order_value
    account, position, ins = _get_account_position_ins(id_or_ins)
    return _order_shares(ins, amount * int(ins.round_lot), cal_style(price, style), position.quantity,
                         auto_switch_order_value)


ORDER_TARGET_PORTFOLIO_SUPPORTED_INS_TYPES = {
    INSTRUMENT_TYPE.CS, INSTRUMENT_TYPE.ETF, INSTRUMENT_TYPE.LOF, INSTRUMENT_TYPE.INDX}


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.SCHEDULED,
    EXECUTION_PHASE.GLOBAL
)
def order_target_portfolio(target_portfolio: Dict[Union[str, Instrument], Union[float, Tuple[float, float]]]) -> List[Order]:
    """
    批量调整股票仓位至目标权重。注意：股票账户中未出现在 target_portfolio 中的资产将被平仓！

    该 API 的参数 target_portfolio 为字典，key 为 order_book_id 或 instrument，value 有两种数据类型可选：

      * value 为权重。此时将根据股票最新价计算目标持仓数量并发出市价单调仓。

      * value 为权重和价格组成的 tuple。此时将根据该价格计算目标权重并发出限价单（Signal 模式下将使用该价格撮合）。

    :param target_portfolio: 目标权重字典，key 为 order_book_id，value 为权重或权重和价格组成的 tuple。

    :example:

    .. code-block:: python

        # 调整仓位，以使平安银行和万科 A 的持仓占比分别达到 10% 和 15%
        order_target_portfolio({
            '000001.XSHE': 0.1,
            '000002.XSHE': 0.15
        })

        # 调整仓位，分别以 14 和 26 元发出限价单，目标是使平安银行和万科 A 的持仓占比分别达到 10% 和 15%
        order_target_portfolio({
            '000001.XSHE': (0.1, 14),
            '000002.XSHE': (0.15, 26)
        })
    """
    env = Environment.get_instance()
    target = {}
    for id_or_ins, target_quantity_price in target_portfolio.items():
        ins = assure_instrument(id_or_ins)
        if not ins:
            raise RQInvalidArgument(_(
                "function order_target_portfolio: invalid keys of target_portfolio, "
                "expected order_book_ids or Instrument objects, got {} (type: {})"
            ).format(id_or_ins, type(id_or_ins)))
        if ins.type not in ORDER_TARGET_PORTFOLIO_SUPPORTED_INS_TYPES:
            raise RQInvalidArgument(_(
                "function order_target_portfolio: invalid instrument type, excepted CS/ETF/LOF/INDX, got {}"
            ).format(ins.order_book_id))
        order_book_id = ins.order_book_id
        price = env.data_proxy.get_last_price(order_book_id)
        if not is_valid_price(price):
            user_system_log.warn(
                _(u"Order Creation Failed: [{order_book_id}] No market data").format(order_book_id=order_book_id)
            )
            continue
        try:
            target_percent, target_price = target_quantity_price
        except TypeError:
            target_percent = target_quantity_price
            target_price = None
        else:
            if not is_valid_price(target_price):
                raise RQInvalidArgument(_(
                    "function order_target_portfolio: invalid order price {target_price} of {id_or_ins}"
                ).format(id_or_ins=id_or_ins, target_price=target_price))
        if target_percent == 0:
            continue
        elif target_percent < 0:
            raise RQInvalidArgument(_(
                "function order_target_portfolio: invalid values of target_portfolio, "
                "excepted float between 0 and 1, got {} (key: {})"
            ).format(target_percent, id_or_ins))

        target[order_book_id] = target_percent, target_price, price
    total_percent = sum(p for p, *__ in target.values())
    if total_percent > 1 and not np.isclose(total_percent, 1):
        raise RQInvalidArgument(_("total percent should be lower than 1, current: {}").format(total_percent))

    account = env.portfolio.accounts[DEFAULT_ACCOUNT_TYPE.STOCK]
    current_quantities = {
        p.order_book_id: p.quantity for p in account.get_positions() if p.direction == POSITION_DIRECTION.LONG
    }
    for order_book_id, quantity in current_quantities.items():
        # 先把不在目标权重中的仓位平掉
        if order_book_id not in target:
            env.submit_order(Order.__from_create__(
                order_book_id, quantity, SIDE.SELL, MarketOrder(), POSITION_EFFECT.CLOSE
            ))

    account_value = account.total_value
    close_orders, open_orders = [], []
    for order_book_id, (target_percent, target_price, price) in target.items():
        delta_quantity = (account_value * target_percent / (target_price or price)) - current_quantities.get(order_book_id, 0)
        delta_quantity = _round_order_quantity(env.data_proxy.instrument(order_book_id), delta_quantity)
        if delta_quantity == 0:
            continue
        elif delta_quantity > 0:
            quantity, side, position_effect = delta_quantity, SIDE.BUY, POSITION_EFFECT.OPEN
            order_list = open_orders
        else:
            quantity, side, position_effect = abs(delta_quantity), SIDE.SELL, POSITION_EFFECT.CLOSE
            order_list = close_orders
        if target_price:
            order = Order.__from_create__(order_book_id, quantity, side, LimitOrder(target_price), position_effect)
        else:
            order = Order.__from_create__(order_book_id, quantity, side, MarketOrder(), position_effect)
            order.set_frozen_price(price)
        order_list.append(order)

    return list(env.submit_order(o) for o in chain(close_orders, open_orders))


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.OPEN_AUCTION,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('order_book_id').is_valid_instrument(),
             verify_that('count').is_greater_than(0))
def is_suspended(order_book_id, count=1):
    # type: (str, Optional[int]) -> Union[bool, pd.DataFrame]
    """
    判断某只股票是否全天停牌。

    :param order_book_id: 某只股票的代码或股票代码，可传入单只股票的order_book_id, symbol
    :param count: 回溯获取的数据个数。默认为当前能够获取到的最近的数据

    """
    dt = Environment.get_instance().calendar_dt.date()
    order_book_id = assure_order_book_id(order_book_id)
    return Environment.get_instance().data_proxy.is_suspended(order_book_id, dt, count)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.OPEN_AUCTION,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('order_book_id').is_valid_instrument())
def is_st_stock(order_book_id, count=1):
    # type: (str, Optional[int]) -> Union[bool, pd.DataFrame]
    """
    判断股票在一段时间内是否为ST股（包括ST与*ST）。

    ST股是有退市风险因此风险比较大的股票，很多时候您也会希望判断自己使用的股票是否是'ST'股来避开这些风险大的股票。另外，我们目前的策略比赛也禁止了使用'ST'股。

    :param order_book_id: 某只股票的代码，可传入单只股票的order_book_id, symbol
    :param count: 回溯获取的数据个数。默认为当前能够获取到的最近的数据
    """
    dt = Environment.get_instance().calendar_dt.date()
    order_book_id = assure_order_book_id(order_book_id)
    return Environment.get_instance().data_proxy.is_st_stock(order_book_id, dt, count)


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.ON_INIT,
    EXECUTION_PHASE.BEFORE_TRADING,
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.AFTER_TRADING,
    EXECUTION_PHASE.SCHEDULED,
)
@apply_rules(verify_that("code").is_instance_of((str, IndustryCodeItem)))
def industry(code):
    # type: (str) -> List[str]
    """
    获得属于某一行业的所有股票列表。

    :param code: 行业名称或行业代码。例如，农业可填写industry_code.A01 或 'A01'

    我们目前使用的行业分类来自于中国国家统计局的 `国民经济行业分类 <http://www.stats.gov.cn/tjsj/tjbz/hyflbz/>`_ ，可以使用这里的任何一个行业代码来调用行业的股票列表：

    =========================   ===================================================
    行业代码                      行业名称
    =========================   ===================================================
    A01                         农业
    A02                         林业
    A03                         畜牧业
    A04                         渔业
    A05                         农、林、牧、渔服务业
    B06                         煤炭开采和洗选业
    B07                         石油和天然气开采业
    B08                         黑色金属矿采选业
    B09                         有色金属矿采选业
    B10                         非金属矿采选业
    B11                         开采辅助活动
    B12                         其他采矿业
    C13                         农副食品加工业
    C14                         食品制造业
    C15                         酒、饮料和精制茶制造业
    C16                         烟草制品业
    C17                         纺织业
    C18                         纺织服装、服饰业
    C19                         皮革、毛皮、羽毛及其制品和制鞋业
    C20                         木材加工及木、竹、藤、棕、草制品业
    C21                         家具制造业
    C22                         造纸及纸制品业
    C23                         印刷和记录媒介复制业
    C24                         文教、工美、体育和娱乐用品制造业
    C25                         石油加工、炼焦及核燃料加工业
    C26                         化学原料及化学制品制造业
    C27                         医药制造业
    C28                         化学纤维制造业
    C29                         橡胶和塑料制品业
    C30                         非金属矿物制品业
    C31                         黑色金属冶炼及压延加工业
    C32                         有色金属冶炼和压延加工业
    C33                         金属制品业
    C34                         通用设备制造业
    C35                         专用设备制造业
    C36                         汽车制造业
    C37                         铁路、船舶、航空航天和其它运输设备制造业
    C38                         电气机械及器材制造业
    C39                         计算机、通信和其他电子设备制造业
    C40                         仪器仪表制造业
    C41                         其他制造业
    C42                         废弃资源综合利用业
    C43                         金属制品、机械和设备修理业
    D44                         电力、热力生产和供应业
    D45                         燃气生产和供应业
    D46                         水的生产和供应业
    E47                         房屋建筑业
    E48                         土木工程建筑业
    E49                         建筑安装业
    E50                         建筑装饰和其他建筑业
    F51                         批发业
    F52                         零售业
    G53                         铁路运输业
    G54                         道路运输业
    G55                         水上运输业
    G56                         航空运输业
    G57                         管道运输业
    G58                         装卸搬运和运输代理业
    G59                         仓储业
    G60                         邮政业
    H61                         住宿业
    H62                         餐饮业
    I63                         电信、广播电视和卫星传输服务
    I64                         互联网和相关服务
    I65                         软件和信息技术服务业
    J66                         货币金融服务
    J67                         资本市场服务
    J68                         保险业
    J69                         其他金融业
    K70                         房地产业
    L71                         租赁业
    L72                         商务服务业
    M73                         研究和试验发展
    M74                         专业技术服务业
    M75                         科技推广和应用服务业
    N76                         水利管理业
    N77                         生态保护和环境治理业
    N78                         公共设施管理业
    O79                         居民服务业
    O80                         机动车、电子产品和日用产品修理业
    O81                         其他服务业
    P82                         教育
    Q83                         卫生
    Q84                         社会工作
    R85                         新闻和出版业
    R86                         广播、电视、电影和影视录音制作业
    R87                         文化艺术业
    R88                         体育
    R89                         娱乐业
    S90                         综合
    =========================   ===================================================

    :example:

    ..  code-block:: python3
        :linenos:

        def init(context):
            stock_list = industry('A01')
            logger.info("农业股票列表：" + str(stock_list))

        #INITINFO 农业股票列表：['600354.XSHG', '601118.XSHG', '002772.XSHE', '600371.XSHG', '600313.XSHG', '600672.XSHG', '600359.XSHG', '300143.XSHE', '002041.XSHE', '600762.XSHG', '600540.XSHG', '300189.XSHE', '600108.XSHG', '300087.XSHE', '600598.XSHG', '000998.XSHE', '600506.XSHG']

    """
    if isinstance(code, IndustryCodeItem):
        code = code.code
    else:
        code = to_industry_code(code)
    cs_instruments = Environment.get_instance().data_proxy.all_instruments((INSTRUMENT_TYPE.CS, ))
    return [i.order_book_id for i in cs_instruments if i.industry_code == code]


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.ON_INIT,
    EXECUTION_PHASE.BEFORE_TRADING,
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.ON_BAR,
    EXECUTION_PHASE.ON_TICK,
    EXECUTION_PHASE.AFTER_TRADING,
    EXECUTION_PHASE.SCHEDULED,
)
@apply_rules(verify_that("code").is_instance_of((str, SectorCodeItem)))
def sector(code):
    # type: (str) -> List[str]
    """
    获得属于某一板块的所有股票列表。

    :param code: 板块名称或板块代码。例如，能源板块可填写'Energy'、'能源'或sector_code.Energy

    目前支持的板块分类如下，其取值参考自MSCI发布的全球行业标准分类:

    =========================   =========================   ==============================================================================
    板块代码                      中文板块名称                  英文板块名称
    =========================   =========================   ==============================================================================
    Energy                      能源                         energy
    Materials                   原材料                        materials
    ConsumerDiscretionary       非必需消费品                   consumer discretionary
    ConsumerStaples             必需消费品                    consumer staples
    HealthCare                  医疗保健                      health care
    Financials                  金融                         financials
    InformationTechnology       信息技术                      information technology
    TelecommunicationServices   电信服务                      telecommunication services
    Utilities                   公共服务                      utilities
    Industrials                 工业                         industrials
    =========================   =========================   ==============================================================================

    :example:

    ..  code-block:: python3
        :linenos:

        def init(context):
            ids1 = sector("consumer discretionary")
            ids2 = sector("非必需消费品")
            ids3 = sector("ConsumerDiscretionary")
            assert ids1 == ids2 and ids1 == ids3
            logger.info(ids1)
        #INIT INFO
        #['002045.XSHE', '603099.XSHG', '002486.XSHE', '002536.XSHE', '300100.XSHE', '600633.XSHG', '002291.XSHE', ..., '600233.XSHG']
    """
    if isinstance(code, SectorCodeItem):
        code = code.name
    else:
        code = to_sector_name(code)

    cs_instruments = Environment.get_instance().data_proxy.all_instruments((INSTRUMENT_TYPE.CS,))
    return [i.order_book_id for i in cs_instruments if i.sector_code == code]


@export_as_api
@apply_rules(
    verify_that("order_book_id").is_valid_instrument(),
    verify_that("start_date").is_valid_date(ignore_none=False),
)
def get_dividend(order_book_id, start_date):
    # type: (str, Union[str, datetime.date, datetime.datetime, pd.Timestamp]) -> Optional[np.ndarray]
    """
    获取某只股票到策略当前日期前一天的分红情况（包含起止日期）。

    :param order_book_id: 股票代码
    :param start_date: 开始日期，需要早于策略当前日期

    =========================   ===================================================
    fields                      字段名
    =========================   ===================================================
    announcement_date           分红宣布日
    book_closure_date           股权登记日
    dividend_cash_before_tax    税前分红
    ex_dividend_date            除权除息日
    payable_date                分红到帐日
    round_lot                   分红最小单位
    =========================   ===================================================

    :example:

    获取平安银行2013-01-04 到策略当前日期前一天的分红数据:

    ..  code-block:: python3
        :linenos:

        get_dividend('000001.XSHE', start_date='20130104')
        #[Out]
        #array([(20130614, 20130619, 20130620, 20130620,  1.7 , 10),
        #       (20140606, 20140611, 20140612, 20140612,  1.6 , 10),
        #       (20150407, 20150410, 20150413, 20150413,  1.74, 10),
        #       (20160608, 20160615, 20160616, 20160616,  1.53, 10)],
        #      dtype=[('announcement_date', '<u4'), ('book_closure_date', '<u4'), ('ex_dividend_date', '<u4'), ('payable_date', '<u4'), ('dividend_cash_before_tax', '<f8'), ('round_lot', '<u4')])

    """
    # adjusted 参数在不复权数据回测时不再提供
    env = Environment.get_instance()
    dt = env.trading_dt.date() - datetime.timedelta(days=1)
    start_date = to_date(start_date)
    if start_date > dt:
        raise RQInvalidArgument(
            _(
                u"in get_dividend, start_date {} is later than the previous test day {}"
            ).format(start_date, dt)
        )
    order_book_id = assure_order_book_id(order_book_id)
    array = env.data_proxy.get_dividend(order_book_id)
    if array is None:
        return None

    sd = start_date.year * 10000 + start_date.month * 100 + start_date.day
    ed = dt.year * 10000 + dt.month * 100 + dt.day
    return array[
        (array["announcement_date"] >= sd) & (array["announcement_date"] <= ed)
    ]


def to_industry_code(s):
    for __, v in industry_code.__dict__.items():
        if isinstance(v, IndustryCodeItem):
            if v.name == s:
                return v.code
    return s


def to_sector_name(s):
    for __, v in sector_code.__dict__.items():
        if isinstance(v, SectorCodeItem):
            if v.cn == s or v.en == s or v.name == s:
                return v.name
    # not found
    return s
