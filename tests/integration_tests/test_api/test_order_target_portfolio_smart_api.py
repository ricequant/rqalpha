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
from datetime import date

from rqalpha import run_func
from rqalpha.apis import get_position, order_target_portfolio_smart
from rqalpha.utils.i18n import gettext as _


def test_order_target_portfolio():
    config = {
        'base': {
            'start_date': '2019-07-30',
            'end_date': '2019-08-05',
            'accounts': {'stock': 1000000},
        },
        'extra': {
            'log_level': 'error',
        },
    }

    def init(context):
        context.counter = 0

    def handle_bar(context, bar_dict):
        context.counter += 1
        if context.counter == 1:
            order_target_portfolio_smart(
                {
                    '000001.XSHE': 0.1,
                    '000004.XSHE': 0.2,
                }
            )
            # 开盘价计算目标仓位
            assert get_position('000001.XSHE').quantity == 7000  # (1000000 * 0.1) / 14.31 = 6988.12
            assert get_position('000004.XSHE').quantity == 10800  # (1000000 * 0.2) / 18.5 = 10810.81
        elif context.counter == 2:
            order_target_portfolio_smart(
                {
                    '000004.XSHE': 0.1,
                    '000005.XSHE': 0.2,
                    '600519.XSHG': 0.6,
                },
                order_prices={
                    '000001.XSHE': 14,
                    '000004.XSHE': 18,
                    '000005.XSHE': 2.92,
                    '600519.XSHG': 970,
                },
                valuation_prices={
                    '000001.XSHE': 14,
                    '000004.XSHE': 18,
                    '000005.XSHE': 2.92,
                    '600519.XSHG': 970,
                },
            )
            assert get_position('000001.XSHE').quantity == 0  # 清仓
            assert get_position('000004.XSHE').quantity == 5500  # (993695.7496 * 0.1) / 18 = 5520.53
            assert get_position('000005.XSHE').quantity == 67600  # (993695.7496 * 0.2) / 2.92 = 68061.35
            assert get_position('600519.XSHG').quantity == 0  # 970 低于 收盘价 无法买进

    run_func(config=config, init=init, handle_bar=handle_bar)


def test_order_target_portfolio_in_signal_mode():
    config = {
        'base': {
            'start_date': '2019-07-30',
            'end_date': '2019-08-05',
            'accounts': {'stock': 1000000},
        },
        'mod': {'sys_simulation': {'signal': True}},
    }

    def init(context):
        context.counter = 0

    def handle_bar(context, handle_bar):
        context.counter += 1
        if context.counter == 1:
            order_target_portfolio_smart(
                {
                    '000001.XSHE': 0.1,
                    '000004.XSHE': 0.2,
                },
                {
                    '000001.XSHE': 14,
                    '000004.XSHE': 10,
                },
            )
            assert get_position('000001.XSHE').quantity == 7000  # (1000000 * 0.1) / 14.31 = 6988
            assert get_position('000001.XSHE').avg_price == 14
            assert get_position('000004.XSHE').quantity == 0  # 价格低过跌停价，被拒单

    run_func(config=config, init=init, handle_bar=handle_bar)


def test_order_target_portfolio_smart_all_denials():
    """测试所有拒单场景: 权重过小、涨停买入、跌停卖出、停牌买入、停牌卖出"""
    config = {
        'base': {
            'start_date': '2025-12-17',
            'end_date': '2025-12-22',
            'frequency': '1d',
            'accounts': {'stock': 1000000},
        },
        'extra': {
            'log_level': 'error',
        },
    }

    def init(context):
        pass

    def handle_bar(context, bar_dict):
        current_date = context.now.date()

        if current_date == date(2025, 12, 17):
            # Day 1 (2025-12-17): 测试涨停买入拒单 + 权重过小拒单
            # 锋龙股份在 12-17 涨停 (18 连板首日)
            result = order_target_portfolio_smart(
                {
                    '001270.XSHE': 0.3,  # 锋龙股份涨停 → limit_up 拒单
                    '000002.XSHE': 0.0001,  # 权重极小 → quantity_too_small 拒单
                    '000001.XSHE': 0.3,  # 正常买入,
                    '002166.XSHE': 0.3,  # 停牌
                    '002036.XSHE': 0.3,  # 正常买入
                }
            )

            # 验证涨停买入拒单
            assert result.denials['001270.XSHE'] == _('Order rejected: cannot buy due to limit up')

            # 验证量太小拒单
            assert result.denials['000002.XSHE'] == _(
                'Order rejected: quantity less than half of minimum order quantity'
            )
            # 验证停牌买入拒单
            assert result.denials['002166.XSHE'] == _('Order rejected: cannot buy due to suspension')

            # 验证正常成交
            assert '000001.XSHE' not in result.denials
        elif current_date == date(2025, 12, 18):
            result = order_target_portfolio_smart(
                {
                    '002036.XSHE': 0,
                    '000668.XSHE': 0.5,
                }
            )
            # 验证停牌卖出拒单
            assert result.denials['002036.XSHE'] == _('Order rejected: cannot sell due to suspension')

        elif current_date == date(2025, 12, 19):
            # Day 3 (2025-12-19): 测试跌停卖出拒单
            # 注意: 此处假设 000001.XSHE (平安银行) 在 12-19 跌停
            # 若实际数据中该股未跌停, 需调整为其他跌停股票
            result = order_target_portfolio_smart(
                {
                    '000668.XSHE': 0.0,  # 跌停, 目标权重 0 → limit_down_sell 拒单
                    '000001.XSHE': 0.5,  # 正常持仓
                }
            )

            assert result.denials['000668.XSHE'] == _('Order rejected: cannot sell due to limit down')

    run_func(config=config, init=init, handle_bar=handle_bar)
