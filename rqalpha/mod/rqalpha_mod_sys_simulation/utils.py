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

import datetime
import six

from rqalpha.model.portfolio import Portfolio
from rqalpha.model.trade import Trade
from rqalpha.utils.i18n import gettext as _

from rqalpha.const import SIDE, POSITION_EFFECT


def _fake_trade(order_book_id, quantity, price):
    return Trade.__from_create__(0, price, abs(quantity),
                                 SIDE.BUY if quantity > 0 else SIDE.SELL,
                                 POSITION_EFFECT.OPEN, order_book_id)


def _filter_positions(env, account_type):
    positions = env.config.base.init_positions
    futures = [ins.order_book_id for ins in env.data_proxy.all_instruments('Future')]
    if account_type == 'FUTURE':
        return [position for position in positions if position[0] in futures]
    else:
        return [position for position in positions if position[0] not in futures]


def init_portfolio(env):
    accounts = {}
    config = env.config
    start_date = datetime.datetime.combine(config.base.start_date, datetime.time.min)
    units = 0

    for account_type, starting_cash in six.iteritems(config.base.accounts):
        if starting_cash == 0:
            raise RuntimeError(_(u"{} starting cash can not be 0, using `--account {} 100000`").format(account_type, account_type))

        account_model = env.get_account_model(account_type)

        trades = []
        for order_book_id, quantity in _filter_positions(env, account_type):
            instrument = env.get_instrument(order_book_id)
            if instrument is None:
                raise RuntimeError(_(u'invalid order book id {} in initial positions').format(order_book_id))
            if not instrument.listing:
                raise RuntimeError(_(u'instrument {} in initial positions is not listing').format(order_book_id))

            bars = env.data_proxy.history_bars(order_book_id, 1, '1d', 'close',
                                               env.data_proxy.get_previous_trading_date(start_date),
                                               adjust_type='none')
            if bars is None:
                raise RuntimeError(_(u'the close price of {} in initial positions is not available').format(order_book_id))

            price = bars[0]
            trades.append(_fake_trade(order_book_id, quantity, price))

        account = account_model(starting_cash)
        account.fast_forward(trades=trades)
        account.apply_settlement()

        units += account.total_value
        accounts[account_type] = account

    return Portfolio(1, units, accounts)

