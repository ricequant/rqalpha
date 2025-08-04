# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称"米筐科技"）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称"Apache 2.0 许可"），
#         您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可"原样"不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、
#         本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，
#         否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。

from numpy.testing import assert_equal
from rqalpha.apis import *

__config__ = {
    "base": {
        "start_date": "2016-03-07",
        "end_date": "2016-03-10",
        "frequency": "1d",
        "accounts": {
            "stock": 1000000,
            "future": 1000000
        }
    },
    "extra": {
        "log_level": "error",
    },
    "mod": {
        "sys_progress": {
            "enabled": True,
            "show": True,
        },
    },
}


def test_stock_position_queue_open_close():
    """
    测试股票开仓和平仓时的 position_queue
    """
    def init(context):
        context.s = "000001.XSHE"
        context.counter = 0

    def handle_bar(context, bar_dict):
        context.counter += 1

        if context.counter == 1:
            # 第一天买入1000股
            order_shares(context.s, 1000)
            position = get_position(context.s)
            assert_equal(position.quantity, 1000)

            # 检查 position_queue
            queue = position.position_queue
            assert_equal(len(queue), 1)
            assert_equal(queue[0][0], context.now.date())
            assert_equal(queue[0][1], 1000)

        elif context.counter == 2:
            # 第二天再买入500股
            order_shares(context.s, 500)
            position = get_position(context.s)
            assert_equal(position.quantity, 1500)

            # 检查 position_queue
            queue = position.position_queue
            assert_equal(len(queue), 2)
            assert_equal(queue[0][0], date(2016, 3, 7))
            assert_equal(queue[0][1], 1000)
            assert_equal(queue[1][0], context.now.date())
            assert_equal(queue[1][1], 500)

        elif context.counter == 3:
            # 第三天卖出800股，应该先卖出第一天买入的部分
            order_shares(context.s, -800)
            position = get_position(context.s)
            assert_equal(position.quantity, 700)

            # 检查 position_queue
            queue = position.position_queue
            assert_equal(len(queue), 2)
            assert_equal(queue[0][0], date(2016, 3, 7))
            assert_equal(queue[0][1], 200)  # 1000 - 800 = 200
            assert_equal(queue[1][0], date(2016, 3, 8))
            assert_equal(queue[1][1], 500)

        elif context.counter == 4:
            # 第四天全部卖出
            order_shares(context.s, -700)
            position = get_position(context.s)
            assert_equal(position.quantity, 0)

            # 检查 position_queue
            queue = position.position_queue
            assert_equal(len(queue), 0)  # 应该为空

    return locals()


def test_stock_position_queue_short_selling():
    """
    测试股票卖空时的 position_queue
    注意：此测试需要在支持卖空的环境中运行，否则会跳过测试
    """
    __config__ = {
        "base": {
            "start_date": "2016-03-07",
            "end_date": "2016-03-10",
            "accounts": {
                "stock": 1000000
            }
        },
        "mod": {
            "sys_accounts": {
                "stock_t0": True,  # 启用T+0交易以便测试卖空
                "future_forced_liquidation": True,
                "validate_stock_position": False  # 禁用股票仓位检查以启用卖空
            }
        }
    }

    def init(context):
        context.s = "000001.XSHE"
        context.counter = 0

    def handle_bar(context, bar_dict):
        context.counter += 1

        if context.counter == 1:
            # 尝试卖空1000股
            order_shares(context.s, -1000)
            position = get_position(context.s)

            # 检查 position_queue
            queue = position.position_queue
            assert_equal(len(queue), 1)
            assert_equal(queue[0][0], context.now.date())
            assert_equal(queue[0][1], -1000)

        elif context.counter == 2:
            # 第二天买入500股平仓一部分
            order_shares(context.s, 500)
            position = get_position(context.s)

            # 检查 position_queue
            queue = position.position_queue
            assert_equal(len(queue), 1)
            assert_equal(queue[0][0], date(2016, 3, 7))
            assert_equal(queue[0][1], -500)

        elif context.counter == 3:
            # 第三天买入足够股数平仓
            current_position = get_position(context.s)
            if current_position.quantity < 0:
                order_shares(context.s, -current_position.quantity + 500)
                position = get_position(context.s)

                # 检查 position_queue
                queue = position.position_queue
                assert_equal(len(queue), 1)
                assert_equal(queue[0][0], context.now.date())
                assert_equal(queue[0][1], 500)  # 应该变成+500

    return locals()


def test_stock_position_queue_split():
    """
    测试股票拆分时的 position_queue
    """
    __config__ = {
        "base": {
            "start_date": "2024-06-17",
            "end_date": "2024-06-19"
        },
        "mod": {
            "sys_accounts": {
                "validate_stock_position": False  # 禁用股票仓位检查以启用卖空
            }
        }
    }

    def init(context):
        context.s = "688032.XSHG"
        context.counter = 0

    def handle_bar(context, bar_dict):
        context.counter += 1

        if context.counter == 1:
            # 第一天买入1000股
            order_shares(context.s, -303)
            position = get_position(context.s)
            assert_equal(position.quantity, -303)

            # 检查 position_queue
            queue = position.position_queue
            assert_equal(len(queue), 1)
            assert_equal(queue[0][0], context.now.date())
            assert_equal(queue[0][1], -303)

        elif context.counter == 2:
            order_shares(context.s, -415)
        elif context.counter == 3:
            position = get_position(context.s)
            assert_equal(position.quantity, -1070)

            # 检查 position_queue
            queue = position.position_queue
            assert_equal(len(queue), 2)
            assert_equal(queue[0][0], date(2024, 6, 17))
            assert_equal(queue[0][1] + queue[1][1], -1070)

    return locals()


def test_stock_position_queue_delist():
    """
    测试股票退市时的 position_queue
    """
    __config__ = {
        "base": {
            "start_date": "2018-12-25",
            "end_date": "2019-01-05"
        }
    }

    def init(context):
        context.s = "000979.XSHE"  # 这只股票在2018-12-28退市
        context.counter = 0

    def handle_bar(context, bar_dict):
        context.counter += 1

        if context.counter == 1:
            # 买入股票
            order_shares(context.s, 1000)
            position = get_position(context.s)
            assert_equal(position.quantity, 1000)

            # 检查 position_queue
            queue = position.position_queue
            assert_equal(len(queue), 1)
            assert_equal(queue[0][0], context.now.date())
            assert_equal(queue[0][1], 1000)

        elif context.counter > 3:  # 退市后
            # 退市后应该没有持仓了
            position = get_position(context.s)
            assert_equal(position.quantity, 0)

            # 检查 position_queue
            queue = position.position_queue
            assert_equal(len(queue), 0)  # 应该为空

    return locals()


def test_future_position_queue_close_today():
    """
    测试期货平今仓时的 position_queue
    """
    __config__ = {
        "base": {
            "start_date": "2016-03-07",
            "end_date": "2016-03-08",
            "accounts": {
                "future": 10000000
            }
        }
    }

    def init(context):
        context.f = "IF1603"  # 选择一个期货合约
        context.initial_position = 0
        context.initial_queue_length = 0
        subscribe(context.f)

    def handle_bar(context, bar_dict):
        # 检查初始持仓
        initial_position = get_position(context.f, POSITION_DIRECTION.LONG)
        context.initial_position = initial_position.quantity
        context.initial_queue_length = len(initial_position.position_queue)

        # 买入开仓2手
        buy_open(context.f, 2)
        position = get_position(context.f, POSITION_DIRECTION.LONG)
        expected_quantity = context.initial_position + 2
        assert_equal(position.quantity, expected_quantity)

        # 检查 position_queue 总数量
        queue = position.position_queue
        total_quantity_in_queue = sum(q[1] for q in queue)
        assert_equal(total_quantity_in_queue, expected_quantity)

        # 检查今日持仓
        today_position = 0
        for q in queue:
            if q[0] == context.now.date():
                today_position += q[1]
        assert today_position > 0, "今日应该有持仓"

        # 平今仓1手
        sell_close(context.f, 1, close_today=True)
        position = get_position(context.f, POSITION_DIRECTION.LONG)
        expected_quantity_after_close = expected_quantity - 1
        assert_equal(position.quantity, expected_quantity_after_close)

        # 检查 position_queue 总数量
        queue = position.position_queue
        total_quantity_in_queue = sum(q[1] for q in queue)
        assert_equal(total_quantity_in_queue, expected_quantity_after_close)

        # 检查今日持仓是否减少
        today_position_after_close = 0
        for q in queue:
            if q[0] == context.now.date():
                today_position_after_close += q[1]

        # 如果今日有持仓，应该比之前少1手
        if today_position_after_close > 0:
            assert_equal(today_position - today_position_after_close, 1)

    return locals()


def test_comprehensive_position_queue():
    """
    综合测试 position_queue 的各种情况
    """
    __config__ = {
        "base": {
            "start_date": "2016-03-07",
            "end_date": "2016-03-11",
            "accounts": {
                "stock": 1000000,
                "future": 1000000
            }
        }
    }

    def init(context):
        context.stock = "000001.XSHE"
        context.future = "IF1603"
        context.counter = 0
        subscribe(context.future)

    def handle_bar(context, bar_dict):
        context.counter += 1

        if context.counter == 1:
            # 第一天：股票买入1000股，期货买入开仓2手
            order_shares(context.stock, 1000)
            buy_open(context.future, 2)

            # 检查股票 position_queue
            stock_position = get_position(context.stock)
            stock_queue = stock_position.position_queue
            assert_equal(len(stock_queue), 1)
            assert_equal(stock_queue[0][0], context.now.date())
            assert_equal(stock_queue[0][1], 1000)

            # 检查期货 position_queue
            future_position = get_position(context.future, POSITION_DIRECTION.LONG)
            future_queue = future_position.position_queue
            assert_equal(len(future_queue), 1)
            assert_equal(future_queue[0][0], context.now.date())
            assert_equal(future_queue[0][1], 2)

        elif context.counter == 2:
            # 第二天：股票卖出500股，期货平今仓1手
            order_shares(context.stock, -500)
            sell_close(context.future, 1, close_today=False)  # 不强制平今

            # 检查股票 position_queue
            stock_position = get_position(context.stock)
            stock_queue = stock_position.position_queue
            assert_equal(len(stock_queue), 1)
            assert_equal(stock_queue[0][0], date(2016, 3, 7))
            assert_equal(stock_queue[0][1], 500)  # 1000 - 500 = 500

            # 检查期货 position_queue
            future_position = get_position(context.future, POSITION_DIRECTION.LONG)
            future_queue = future_position.position_queue
            assert_equal(len(future_queue), 1)
            assert_equal(future_queue[0][0], date(2016, 3, 7))
            assert_equal(future_queue[0][1], 1)  # 2 - 1 = 1

        elif context.counter == 3:
            # 第三天：股票买入200股，期货卖出开仓1手
            order_shares(context.stock, 200)
            sell_open(context.future, 1)

            # 检查股票 position_queue
            stock_position = get_position(context.stock)
            stock_queue = stock_position.position_queue
            assert_equal(len(stock_queue), 2)
            assert_equal(stock_queue[0][0], date(2016, 3, 7))
            assert_equal(stock_queue[0][1], 500)
            assert_equal(stock_queue[1][0], context.now.date())
            assert_equal(stock_queue[1][1], 200)

            # 检查期货多头 position_queue
            future_long_position = get_position(context.future, POSITION_DIRECTION.LONG)
            future_long_queue = future_long_position.position_queue
            assert_equal(len(future_long_queue), 1)
            assert_equal(future_long_queue[0][0], date(2016, 3, 7))
            assert_equal(future_long_queue[0][1], 1)

            # 检查期货空头 position_queue
            future_short_position = get_position(context.future, POSITION_DIRECTION.SHORT)
            future_short_queue = future_short_position.position_queue
            assert_equal(len(future_short_queue), 1)
            assert_equal(future_short_queue[0][0], context.now.date())
            assert_equal(future_short_queue[0][1], 1)

        elif context.counter == 4:
            # 第四天：股票卖出全部，期货平掉所有仓位
            order_shares(context.stock, -700)
            sell_close(context.future, 1)  # 平掉多头
            buy_close(context.future, 1)   # 平掉空头

            # 检查股票 position_queue
            stock_position = get_position(context.stock)
            stock_queue = stock_position.position_queue
            assert_equal(len(stock_queue), 0)  # 应该为空

            # 检查期货多头 position_queue
            future_long_position = get_position(context.future, POSITION_DIRECTION.LONG)
            future_long_queue = future_long_position.position_queue
            assert_equal(len(future_long_queue), 0)  # 应该为空

            # 检查期货空头 position_queue
            future_short_position = get_position(context.future, POSITION_DIRECTION.SHORT)
            future_short_queue = future_short_position.position_queue
            assert_equal(len(future_short_queue), 0)  # 应该为空

    return locals()
