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

import pickle
from datetime import datetime, date
from typing import Set

from rqalpha.portfolio import Portfolio, Account
from rqalpha.const import DEFAULT_ACCOUNT_TYPE
from rqalpha.environment import Environment
from rqalpha.utils.logger import user_system_log, system_log
from rqalpha.utils.repr import property_repr


class RunInfo(object):
    """
    策略运行信息
    """
    __repr__ = property_repr

    def __init__(self, config):
        self._start_date = config.base.start_date
        self._end_date = config.base.end_date
        self._frequency = config.base.frequency
        self._stock_starting_cash = config.base.accounts.get(DEFAULT_ACCOUNT_TYPE.STOCK, 0)
        self._future_starting_cash = config.base.accounts.get(DEFAULT_ACCOUNT_TYPE.FUTURE, 0)
        self._margin_multiplier = config.base.margin_multiplier
        self._run_type = config.base.run_type

        try:
            self._matching_type = config.mod.sys_simulation.matching_type
            self._slippage = config.mod.sys_simulation.slippage
            self._commission_multiplier = config.mod.sys_transaction_cost.commission_multiplier
        except:
            pass

    @property
    def start_date(self):
        # type: () -> date
        """
        策略的开始日期
        """
        return self._start_date

    @property
    def end_date(self):
        # type: () -> date
        """
        策略的结束日期
        """
        return self._end_date

    @property
    def frequency(self):
        # type: () -> str
        """
        '1d'或'1m'
        """
        return self._frequency

    @property
    def stock_starting_cash(self):
        # type: () -> float
        """
        股票账户初始资金
        """
        return self._stock_starting_cash

    @property
    def future_starting_cash(self):
        # type: () -> float
        """
        期货账户初始资金
        """
        return self._future_starting_cash

    @property
    def slippage(self):
        # type: () -> float
        """
        滑点水平
        """
        return self._slippage

    @property
    def matching_type(self):
        # type: () -> str
        """
        撮合方式
        """
        return self._matching_type

    @property
    def commission_multiplier(self):
        # type: () -> float
        """
        手续费倍率
        """
        return self._commission_multiplier

    @property
    def margin_multiplier(self):
        # type: () -> float
        """
        保证金倍率
        """
        return self._margin_multiplier

    @property
    def run_type(self):
        # type: () -> str
        """
        运行类型
        """
        return self._run_type


class StrategyContext(object):
    """
    策略上下文
    """
    def __repr__(self):
        items = ("%s = %r" % (k, v)
                 for k, v in self.__dict__.items()
                 if not callable(v) and not k.startswith("_"))
        return "Context({%s})" % (', '.join(items),)

    def __init__(self):
        self._config = None

    def get_state(self):
        dict_data = {}
        for key, value in self.__dict__.items():
            if key.startswith("_"):
                continue
            try:
                dict_data[key] = pickle.dumps(value)
            except Exception as e:
                user_system_log.warn("context.{} can not pickle", key)
        return pickle.dumps(dict_data)

    def set_state(self, state):
        dict_data = pickle.loads(state)
        for key, value in dict_data.items():
            try:
                self.__dict__[key] = pickle.loads(value)
                system_log.debug("restore context.{} {}", key, type(self.__dict__[key]))
            except Exception as e:
                user_system_log.warn('context.{} can not restore', key)

    @property
    def universe(self):
        # type: () -> Set[str]
        """
        在运行 :func:`update_universe`, :func:`subscribe` 或者 :func:`unsubscribe` 的时候，合约池会被更新。

        需要注意，合约池内合约的交易时间（包含股票的策略默认会在股票交易时段触发）是handle_bar被触发的依据。
        """
        return Environment.get_instance().get_universe()

    @property
    def now(self):
        # type: () -> datetime
        """
        当前 Bar/Tick 所对应的时间
        """
        return Environment.get_instance().calendar_dt

    @property
    def run_info(self):
        # type: () -> RunInfo
        """
        测略运行信息
        """
        config = Environment.get_instance().config
        return RunInfo(config)

    @property
    def portfolio(self):
        # type: () -> Portfolio
        """
        策略投资组合，可通过该对象获取当前策略账户、持仓等信息
        """
        return Environment.get_instance().portfolio

    @property
    def stock_account(self):
        # type: () -> Account
        """
        股票账户
        """
        return self.portfolio.accounts[DEFAULT_ACCOUNT_TYPE.STOCK]

    @property
    def future_account(self):
        # type: () -> Account
        """
        期货账户
        """
        return self.portfolio.accounts[DEFAULT_ACCOUNT_TYPE.FUTURE]

    @property
    def config(self):
        return Environment.get_instance().config
