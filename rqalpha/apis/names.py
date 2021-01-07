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

from itertools import chain

from rqalpha.const import INSTRUMENT_TYPE


VALID_HISTORY_FIELDS = [
    "datetime",
    "open",
    "close",
    "high",
    "low",
    "total_turnover",
    "volume",
    "acc_net_value",
    "discount_rate",
    "unit_net_value",
    "limit_up",
    "limit_down",
    "open_interest",
    "basis_spread",
    "settlement",
    "prev_settlement",
]

VALID_TENORS = [
    "0S",
    "1M",
    "2M",
    "3M",
    "6M",
    "9M",
    "1Y",
    "2Y",
    "3Y",
    "4Y",
    "5Y",
    "6Y",
    "7Y",
    "8Y",
    "9Y",
    "10Y",
    "15Y",
    "20Y",
    "30Y",
    "40Y",
    "50Y",
]

VALID_INSTRUMENT_TYPES = list(chain(INSTRUMENT_TYPE, ("Fund", "Stock")))

VALID_MARGIN_FIELDS = [
    "margin_balance",
    "buy_on_margin_value",
    "short_sell_quantity",
    "margin_repayment",
    "short_balance_quantity",
    "short_repayment_quantity",
    "short_balance",
    "total_balance",
]

VALID_SHARE_FIELDS = [
    "total",
    "circulation_a",
    "management_circulation",
    "non_circulation_a",
    "total_a",
]

VALID_TURNOVER_FIELDS = (
    "today",
    "week",
    "month",
    "three_month",
    "six_month",
    "year",
    "current_year",
    "total",
)


VALID_STOCK_CONNECT_FIELDS = [
    'shares_holding',
    'holding_ratio',
]


VALID_CURRENT_PERFORMANCE_FIELDS = [
    'operating_revenue',
    'gross_profit',
    'operating_profit',
    'total_profit',
    'np_parent_owners',
    'net_profit_cut',
    'net_operate_cashflow',
    'total_assets',
    'se_without_minority',
    'total_shares',
    'basic_eps',
    'eps_weighted',
    'eps_cut_epscut',
    'eps_cut_weighted',
    'roe',
    'roe_weighted',
    'roe_cut',
    'roe_cut_weighted',
    'net_operate_cashflow_per_share',
    'equity_per_share',
    'operating_revenue_yoy',
    'gross_profit_yoy',
    'operating_profit_yoy',
    'total_profit_yoy',
    'np_parent_minority_pany_yoy',
    'ne_t_minority_ty_yoy',
    'net_operate_cash_flow_yoy',
    'total_assets_to_opening',
    'se_without_minority_to_opening',
    'basic_eps_yoy',
    'eps_weighted_yoy',
    'eps_cut_yoy',
    'eps_cut_weighted_yoy',
    'roe_yoy',
    'roe_weighted_yoy',
    'roe_cut_yoy',
    'roe_cut_weighted_yoy',
    'net_operate_cash_flow_per_share_yoy',
    'net_asset_psto_opening',
]

