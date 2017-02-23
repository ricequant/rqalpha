# -*- coding: utf-8 -*-
#
# Copyright 2017 Ricequant, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import six
import pickle

from ..const import ACCOUNT_TYPE
from ..environment import Environment
from ..utils.logger import user_system_log, system_log
from ..utils.i18n import gettext as _
from ..utils.repr import property_repr
from ..utils.proxy import PortfolioProxy


class RunInfo(object):
    """
    策略运行信息
    """
    __repr__ = property_repr

    def __init__(self, config):
        self._run_id = config.base.run_id
        self._start_date = config.base.start_date
        self._end_date = config.base.end_date
        self._frequency = config.base.frequency
        self._stock_starting_cash = config.base.stock_starting_cash
        self._future_starting_cash = config.base.future_starting_cash
        self._slippage = config.base.slippage
        self._benchmark = config.base.benchmark
        self._matching_type = config.base.matching_type
        self._commission_multiplier = config.base.commission_multiplier
        self._margin_multiplier = config.base.margin_multiplier
        self._run_type = config.base.run_type

    @property
    def run_id(self):
        """
        :property getter: 标识策略每次运行的唯一id
        """
        return self._run_id

    @property
    def start_date(self):
        """
        :property getter: 策略的开始日期
        """
        return self._start_date

    @property
    def end_date(self):
        """
        :property getter: 策略的结束日期
        """
        return self._end_date

    @property
    def frequency(self):
        """
        :property getter: 策略频率，'1d'或'1m'
        """
        return self._frequency

    @property
    def stock_starting_cash(self):
        """
        :property getter: 股票账户初始资金
        """
        return self._stock_starting_cash

    @property
    def future_starting_cash(self):
        """
        :property getter: 期货账户初始资金
        """
        return self._future_starting_cash

    @property
    def slippage(self):
        """
        :property getter: 滑点水平
        """
        return self._slippage

    @property
    def benchmark(self):
        """
        :property getter: 基准合约代码
        """
        return self._benchmark

    @property
    def matching_type(self):
        """
        :property getter: 撮合方式
        """
        return self._matching_type

    @property
    def commission_multiplier(self):
        """
        :property getter: 手续费倍率
        """
        return self._commission_multiplier

    @property
    def margin_multiplier(self):
        """
        :property getter: 保证金倍率
        """
        return self._margin_multiplier

    @property
    def run_type(self):
        """
        :property getter: 运行类型
        """
        return self._run_type


class StrategyContext(object):
    def __repr__(self):
        items = ("%s = %r" % (k, v)
                 for k, v in six.iteritems(self.__dict__)
                 if not callable(v) and not k.startswith("_"))
        return "Context({%s})" % (', '.join(items),)

    def __init__(self):
        self._proxy_portfolio_dict = None
        self._config = None

    def get_state(self):
        dict_data = {}
        for key, value in six.iteritems(self.__dict__):
            if key.startswith("_"):
                continue
            try:
                # system_log.debug("persist {})
                dict_data[key] = pickle.dumps(value)
            except Exception as e:
                user_system_log.warn("context.{} can not pickle", key)
        return pickle.dumps(dict_data)

    def set_state(self, state):
        dict_data = pickle.loads(state)
        for key, value in six.iteritems(dict_data):
            try:
                self.__dict__[key] = pickle.loads(value)
                system_log.debug("restore context.{} {}", key, type(self.__dict__[key]))
            except Exception as e:
                user_system_log.warn('context.{} can not restore', key)

    @property
    def universe(self):
        """
        在运行 :func:`update_universe`, :func:`subscribe` 或者 :func:`unsubscribe` 的时候，合约池会被更新。

        需要注意，合约池内合约的交易时间（包含股票的策略默认会在股票交易时段触发）是handle_bar被触发的依据。

        :property getter: list[`str`]
        """
        return Environment.get_instance().universe

    @property
    def now(self):
        """
        使用以上的方式就可以在handle_bar中拿到当前的bar的时间，比如day bar的话就是那天的时间，minute bar的话就是这一分钟的时间点。
        """
        return Environment.get_instance().calendar_dt

    @property
    def run_info(self):
        """
        :property getter: :class:`~RunInfo`
        """
        config = Environment.get_instance().config
        return RunInfo(config)

    @property
    def portfolio(self):
        """
        该投资组合在单一股票或期货策略中分别为股票投资组合和期货投资组合。在股票+期货的混合策略中代表汇总之后的总投资组合。

        =========================   =========================   ==============================================================================
        属性                         类型                        注释
        =========================   =========================   ==============================================================================
        starting_cash               float                       初始资金，为子组合初始资金的加总
        cash                        float                       可用资金，为子组合可用资金的加总
        total_returns               float                       投资组合至今的累积收益率。计算方法是现在的投资组合价值/投资组合的初始资金
        daily_returns               float                       投资组合每日收益率
        daily_pnl                   float                       当日盈亏，子组合当日盈亏的加总
        market_value                float                       投资组合当前的市场价值，为子组合市场价值的加总
        portfolio_value             float                       总权益，为子组合总权益加总
        pnl                         float                       当前投资组合的累计盈亏
        start_date                  datetime.datetime           策略投资组合的回测/实时模拟交易的开始日期
        annualized_returns          float                       投资组合的年化收益率
        positions                   dict                        一个包含所有仓位的字典，以order_book_id作为键，position对象作为值
        =========================   =========================   ==============================================================================

        :property getter: :class:`~MixedPortfolio` | :class:`~StockPortfolio` | :class:`~FuturePortfolio`
        """
        env = Environment.get_instance()
        account_list = env.config.base.account_list
        if len(account_list) == 1:
            if account_list[0] == ACCOUNT_TYPE.STOCK:
                return self.stock_portfolio
            elif account_list[0] == ACCOUNT_TYPE.FUTURE:
                return self.future_portfolio
        return Environment.get_instance().account.portfolio

    @property
    def stock_portfolio(self):
        """
        获取股票投资组合信息。

        在单独股票类型策略中，内容与portfolio一致，都代表当前投资组合；在期货+股票混合策略中代表股票子组合；在单独期货策略中，不能被访问。

        =========================   =========================   ==============================================================================
        属性                         类型                        注释
        =========================   =========================   ==============================================================================
        starting_cash               float                       回测或实盘交易给算法策略设置的初始资金
        cash                        float                       可用资金
        total_returns               float                       投资组合至今的累积收益率。计算方法是现在的投资组合价值/投资组合的初始资金
        daily_returns               float                       当前最新一天的每日收益
        daily_pnl                   float                       当日盈亏，当日投资组合总权益-昨日投资组合总权益
        market_value                float                       投资组合当前所有证券仓位的市值的加总
        portfolio_value             float                       总权益，包含市场价值和剩余现金
        pnl                         float                       当前投资组合的累计盈亏
        start_date                  date                        策略投资组合的回测/实时模拟交易的开始日期
        annualized_returns          float                       投资组合的年化收益率
        positions                   dict                        一个包含所有证券仓位的字典，以order_book_id作为键，position对象作为值
        dividend_receivable         float                       投资组合在分红现金收到账面之前的应收分红部分
        =========================   =========================   ==============================================================================

        :property getter: :class:`~StockPortfolio`
        """
        if getattr(self, "_proxy_portfolio_dict", None) is None:
            self._proxy_portfolio_dict = {}
        self._proxy_portfolio_dict[ACCOUNT_TYPE.STOCK] = PortfolioProxy(
            Environment.get_instance().accounts[ACCOUNT_TYPE.STOCK].portfolio)
        return self._proxy_portfolio_dict[ACCOUNT_TYPE.STOCK]

    @property
    def future_portfolio(self):
        """
        获取期货投资组合信息。

        在单独期货类型策略中，内容与portfolio一致，都代表当前投资组合；在期货+股票混合策略中代表期货子组合；在单独股票策略中，不能被访问。

        =========================   =========================   ==============================================================================
        属性                         类型                        注释
        =========================   =========================   ==============================================================================
        starting_cash               float                       初始资金
        cash                        float                       可用资金
        frozen_cash                 float                       冻结资金
        total_returns               float                       投资组合至今的累积收益率，当前总权益/初始资金
        daily_returns               float                       当日收益率 = 当日收益 / 昨日总权益
        market_value                float                       投资组合当前所有期货仓位的名义市值的加总
        pnl                         float                       累计盈亏，当前投资组合总权益-初始资金
        daily_pnl                   float                       当日盈亏，当日浮动盈亏 + 当日平仓盈亏 - 当日费用
        daily_holding_pnl           float                       当日浮动盈亏
        daily_realized_pnl          float                       当日平仓盈亏
        portfolio_value             float                       总权益，昨日总权益+当日盈亏
        transaction_cost            float                       总费用
        start_date                  date                        回测开始日期
        annualized_returns          float                       投资组合的年化收益率
        positions                   dict                        一个包含期货仓位的字典，以order_book_id作为键，position对象作为值
        margin                      float                       已占用保证金
        =========================   =========================   ==============================================================================

        :property getter: :class:`~FuturePortfolio`
        """
        if getattr(self, "_proxy_portfolio_dict", None) is None:
            self._proxy_portfolio_dict = {}
        self._proxy_portfolio_dict[ACCOUNT_TYPE.FUTURE] = PortfolioProxy(
            Environment.get_instance().accounts[ACCOUNT_TYPE.FUTURE].portfolio)
        return self._proxy_portfolio_dict[ACCOUNT_TYPE.FUTURE]

    @property
    def slippage(self):
        raise NotImplementedError

    @property
    def benchmark(self):
        raise NotImplementedError

    @property
    def margin_rate(self):
        raise NotImplementedError

    @property
    def commission(self):
        raise NotImplementedError

    @property
    def short_selling_allowed(self):
        raise NotImplementedError

    @slippage.setter
    def slippage(self, value):
        user_system_log.warn(_("[deprecated] {} is no longer used.").format('context.slippage'))

    @benchmark.setter
    def benchmark(self, value):
        user_system_log.warn(_("[deprecated] {} is no longer used.").format('context.benchmark'))

    @margin_rate.setter
    def margin_rate(self, value):
        user_system_log.warn(_("[deprecated] {} is no longer used.").format('context.margin_rate'))

    @commission.setter
    def commission(self, value):
        user_system_log.warn(_("[deprecated] {} is no longer used.").format('context.commission'))

    @short_selling_allowed.setter
    def short_selling_allowed(self, value):
        user_system_log.warn(_("[deprecated] {} is no longer used.").format('context.short_selling_allowed'))
