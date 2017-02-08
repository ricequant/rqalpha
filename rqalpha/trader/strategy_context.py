# -*- coding: utf-8 -*-
#
# Copyright 2016 Ricequant, Inc
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

import pickle
import datetime

from ..const import ACCOUNT_TYPE
from ..environment import Environment
from ..model.portfolio import StockPortfolio, FuturePortfolio
from ..utils.logger import user_log, system_log
from ..utils.i18n import gettext as _
from ..utils.repr import property_repr
from ..const import MATCHING_TYPE, RUN_TYPE
from ..proxy import PortfolioProxy


class RunInfo:

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
    def run_id(self) -> int:
        return self._run_id

    @property
    def start_date(self) -> datetime.date:
        return self._start_date

    @property
    def end_date(self) -> datetime.date:
        return self._end_date

    @property
    def frequency(self) -> str:
        return self._frequency

    @property
    def stock_starting_cash(self) -> float:
        return self._stock_starting_cash

    @property
    def future_starting_cash(self) -> float:
        return self._future_starting_cash

    @property
    def slippage(self) -> float:
        return self._slippage

    @property
    def benchmark(self) -> str:
        return self._benchmark

    @property
    def matching_type(self) -> MATCHING_TYPE:
        return self._matching_type

    @property
    def commission_multiplier(self) -> float:
        return self._commission_multiplier

    @property
    def margin_multiplier(self) -> float:
        return self._margin_multiplier

    @property
    def run_type(self) -> RUN_TYPE:
        return self._run_type


class StrategyContext:
    def __repr__(self):
        items = ("%s = %r" % (k, v)
                 for k, v in self.__dict__.items()
                 if not callable(v) and not k.startswith("_"))
        return "Context({%s})" % (', '.join(items),)

    def __init__(self):
        self._proxy_portfolio_dict = None
        self._config = None

    def get_state(self):
        dict_data = {}
        for key, value in self.__dict__.items():
            if key.startswith("_"):
                continue
            try:
                # system_log.debug("persist {} -> {}", key, value)
                dict_data[key] = pickle.dumps(value)
            except Exception as e:
                user_log.warn("context.{} can not pickle", key)
        return pickle.dumps(dict_data)

    def set_state(self, state):
        dict_data = pickle.loads(state)
        for key, value in dict_data.items():
            try:
                self.__dict__[key] = pickle.loads(value)
                system_log.debug("restore context.{} {}", key, type(self.__dict__[key]))
            except Exception as e:
                user_log.warn('context.{} can not restore', key)

    @property
    def universe(self) -> list:
        return Environment.get_instance().universe

    @property
    def now(self) -> datetime.datetime:
        return Environment.get_instance().calendar_dt

    @property
    def run_info(self) -> "RunInfo":
        config = Environment.get_instance().config
        return RunInfo(config)

    @property
    def portfolio(self) -> "Portfolio":
        env = Environment.get_instance()
        account_list = env.config.base.account_list
        if len(account_list) == 1:
            if account_list[0] == ACCOUNT_TYPE.STOCK:
                return self.stock_portfolio
            elif account_list[0] == ACCOUNT_TYPE.FUTURE:
                return self.future_portfolio
        return Environment.get_instance().account.portfolio

    @property
    def stock_portfolio(self) -> "StockPortfolio":
        if getattr(self, "_proxy_portfolio_dict", None) is None:
            self._proxy_portfolio_dict = {}
        self._proxy_portfolio_dict[ACCOUNT_TYPE.STOCK] = PortfolioProxy(
            Environment.get_instance().accounts[ACCOUNT_TYPE.STOCK].portfolio)
        return self._proxy_portfolio_dict[ACCOUNT_TYPE.STOCK]

    @property
    def future_portfolio(self) -> "FuturePortfolio":
        if getattr(self, "_proxy_portfolio_dict", None) is None:
            self._proxy_portfolio_dict = {}
        self._proxy_portfolio_dict[ACCOUNT_TYPE.FUTURE] = PortfolioProxy(
            Environment.get_instance().accounts[ACCOUNT_TYPE.FUTURE].portfolio)
        return self._proxy_portfolio_dict[ACCOUNT_TYPE.FUTURE]

    @property
    def slippage(self) -> "[Deprecated]":
        raise NotImplementedError

    @property
    def benchmark(self) -> "[Deprecated]":
        raise NotImplementedError

    @property
    def margin_rate(self) -> "[Deprecated]":
        raise NotImplementedError

    @property
    def commission(self) -> "[Deprecated]":
        raise NotImplementedError

    @property
    def short_selling_allowed(self) -> "[Deprecated]":
        raise NotImplementedError

    @slippage.setter
    def slippage(self, value):
        user_log.warn(_("[deprecated] {} is no longer used.").format('context.slippage'))

    @benchmark.setter
    def benchmark(self, value):
        user_log.warn(_("[deprecated] {} is no longer used.").format('context.benchmark'))

    @margin_rate.setter
    def margin_rate(self, value):
        user_log.warn(_("[deprecated] {} is no longer used.").format('context.margin_rate'))

    @commission.setter
    def commission(self, value):
        user_log.warn(_("[deprecated] {} is no longer used.").format('context.commission'))

    @short_selling_allowed.setter
    def short_selling_allowed(self, value):
        user_log.warn(_("[deprecated] {} is no longer used.").format('context.short_selling_allowed'))

