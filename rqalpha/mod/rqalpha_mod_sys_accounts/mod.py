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

from typing import Any

from rqalpha.interface import AbstractMod
from rqalpha.const import DEFAULT_ACCOUNT_TYPE, INSTRUMENT_TYPE
from rqalpha import export_as_api
from rqalpha.utils import INST_TYPE_IN_STOCK_ACCOUNT
from rqalpha.environment import Environment

from .account_model import StockAccount, FutureAccount
from .api import api_future, api_stock, api_base


class AccountMod(AbstractMod):

    def start_up(self, env, mod_config):
        # type: (Environment, Any) -> None

        FutureAccount.forced_liquidation = mod_config.future_forced_liquidation
        FutureAccount.enable_position_validator = mod_config.validate_future_position
        StockAccount.enable_position_validator = mod_config.validate_stock_position
        StockAccount.dividend_reinvestment = mod_config.dividend_reinvestment
        StockAccount.cash_return_by_stock_delisted = mod_config.cash_return_by_stock_delisted
        StockAccount.t1 = mod_config.stock_t1

        # 注入 Account
        env.set_account_model(DEFAULT_ACCOUNT_TYPE.STOCK.name, StockAccount, INST_TYPE_IN_STOCK_ACCOUNT)
        env.set_account_model(DEFAULT_ACCOUNT_TYPE.FUTURE.name, FutureAccount, (INSTRUMENT_TYPE.FUTURE, ))

        # 注入 API
        for export_name in api_base.__all__:
            export_as_api(getattr(api_base, export_name))

        if DEFAULT_ACCOUNT_TYPE.FUTURE.name in env.config.base.accounts:
            # 注入期货API
            for export_name in api_future.__all__:
                export_as_api(getattr(api_future, export_name))
        if DEFAULT_ACCOUNT_TYPE.STOCK.name in env.config.base.accounts:
            # 注入股票API
            for export_name in api_stock.__all__:
                export_as_api(getattr(api_stock, export_name))

    def tear_down(self, code, exception=None):
        pass
