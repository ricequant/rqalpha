# -*- coding: utf-8 -*-
# 版权所有 2020 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），您可以在以下位置获得 Apache 2.0 许可的副本：
#         http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。
import datetime

import six
from dateutil.parser import parse
import pandas as pd

from rqalpha.const import EXECUTION_PHASE
from rqalpha.api import export_as_api
from rqalpha.apis.names import (
    VALID_HISTORY_FIELDS, VALID_MARGIN_FIELDS, VALID_SHARE_FIELDS, VALID_TURNOVER_FIELDS,
    VALID_CURRENT_PERFORMANCE_FIELDS, VALID_STOCK_CONNECT_FIELDS,
)
from rqalpha.execution_context import ExecutionContext
from rqalpha.environment import Environment
from rqalpha.utils.arg_checker import apply_rules, verify_that
from rqalpha.utils.exception import RQInvalidArgument
from rqalpha.apis.api_base import assure_order_book_id
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.logger import user_log


try:
    import rqdatac
except ImportError:
    class DummyRQDatac:
        def __getattr__(self, item):
            return self

        def __call__(self, *args, **kwargs):
            raise RuntimeError('rqdatac is required')

    rqdatac = DummyRQDatac()


def to_date(date):
    if isinstance(date, datetime.datetime):
        return date.date()
    if isinstance(date, datetime.date):
        return date

    if isinstance(date, str):
        return parse(date).date()

    raise RQInvalidArgument('unknown date value: {}'.format(date))


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('start_date').is_valid_date())
def get_split(order_book_ids, start_date=None):
    """
    获取截止T-1日的拆分信息
    :param order_book_ids:
    :param start_date: 可选参数，不传入时，表示从上市时开始获取
    :return: 传入多个标的时，返回multi-index dataframe，index为 (order_book_id, ex_dividend_date);
            传入一个标的时，返回DataFrame，index 为 ex_dividend_date
    """
    # order_book_id 支持list类型
    env = Environment.get_instance()
    dt = env.trading_dt.date() - datetime.timedelta(days=1)
    start_date = to_date(start_date)
    if start_date > dt:
        raise RQInvalidArgument(_('in get_split, start_date {} is no earlier than the previous test day {}').format(
            start_date, dt
        ))
    if isinstance(order_book_ids, six.string_types):
        order_book_ids = [order_book_ids]
    order_book_ids = [assure_order_book_id(i) for i in order_book_ids]
    return rqdatac.get_split(order_book_ids, start_date, dt)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('date').is_valid_date(ignore_none=True))
def index_components(order_book_id, date=None):
    """
    获取T日的指数成分
    :param order_book_id: 指数
    :param date: 可选，默认为策略当时时间
    :return: list of order_book_id
    """
    env = Environment.get_instance()
    dt = env.trading_dt.date()
    if date is None:
        date = dt
    else:
        date = to_date(date)
        if date > dt:
            raise RQInvalidArgument(_('in index_components, date {} is no earlier than test date {}').format(
                date, dt
            ))
    order_book_id = assure_order_book_id(order_book_id)
    return rqdatac.index_components(order_book_id, date=date)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('date').is_valid_date(ignore_none=True))
def index_weights(order_book_id, date=None):
    """
    获取T-1日的指数权重
    :param order_book_id: 指数
    :param date: 可选，默认为T-1日
    :return: pd.Series
    """
    env = Environment.get_instance()
    data_proxy = env.data_proxy
    dt = data_proxy.get_previous_trading_date(env.trading_dt.date())
    if date is None:
        date = dt
    else:
        date = to_date(date)
        if date > dt:
            raise RQInvalidArgument(_('in index_components, date {} is no earlier than previous test date {}').format(
                date, dt
            ))
    order_book_id = assure_order_book_id(order_book_id)
    return rqdatac.index_weights(order_book_id, date)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
def concept(*concept_names):
    """
    获取T日的概念股列表
    :param concept_names: 概念列表
    :return: list of order_book_id
    """
    env = Environment.get_instance()
    dt = env.trading_dt.date()

    return rqdatac.concept(*concept_names, date=dt)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('order_book_ids').are_valid_instruments(),
             verify_that('start_date').is_valid_date(ignore_none=False),
             verify_that('end_date').is_valid_date(ignore_none=True),
             verify_that('frequency').is_valid_frequency(),
             verify_that('fields').are_valid_fields(VALID_HISTORY_FIELDS, ignore_none=True),
             verify_that('adjust_type').is_in(['pre', 'post', 'none', 'internal']),
             verify_that('skip_suspended').is_instance_of(bool))
def get_price(order_book_ids, start_date, end_date=None, frequency='1d',
              fields=None, adjust_type='pre', skip_suspended=False, expect_df=False):
    """
    通过rqdatac获取截止T-1日的历史价格
    :param order_book_ids:
    :param start_date:
    :param end_date:
    :param frequency:
    :param fields:
    :param adjust_type:
    :param skip_suspended:
    :param expect_df: 为true时，总是返回multi-index dataframe
    :return: Series/DataFrame/Panel，请参考rqdatac的文档
    """
    env = Environment.get_instance()
    yesterday = env.trading_dt.date() - datetime.timedelta(days=1)
    if end_date is not None:
        end_date = to_date(end_date)
        if end_date > yesterday:
            raise RQInvalidArgument(
                _('in get_price, end_date {} is no earlier than the previous test day {}').format(
                    end_date, yesterday
                ))
    else:
        end_date = yesterday

    start_date = to_date(start_date)
    if start_date > yesterday:
        raise RQInvalidArgument(_('in get_price, start_date {} is no earlier than the previous test day {}').format(
            start_date, yesterday
        ))

    if end_date < start_date:
        raise RQInvalidArgument(_('in get_price, start_date {} > end_date {}').format(
            start_date, end_date
        ))

    if isinstance(order_book_ids, six.string_types):
        order_book_ids = assure_order_book_id(order_book_ids)
    else:
        order_book_ids = [assure_order_book_id(i) for i in order_book_ids]

    return rqdatac.get_price(order_book_ids, start_date, end_date,
                             frequency=frequency, fields=fields, adjust_type=adjust_type,
                             skip_suspended=skip_suspended, expect_df=expect_df)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('count').is_instance_of(int).is_greater_than(0),
             verify_that('fields').are_valid_fields(VALID_MARGIN_FIELDS, ignore_none=True))
def get_securities_margin(order_book_ids, count=1, fields=None, expect_df=False):
    """
    获取截止T-1日的融资融券信息
    :param order_book_ids:
    :param count: 获取多少个交易日的数据
    :param fields:
    :param expect_df:
    :return: Series/DataFrame/Panel，请参考rqdatac的文档
    """
    env = Environment.get_instance()
    data_proxy = env.data_proxy
    dt = data_proxy.get_previous_trading_date(env.trading_dt)
    if count == 1:
        start_dt = dt
    else:
        start_dt = data_proxy.get_nth_previous_trading_date(dt, count - 1)

    if isinstance(order_book_ids, six.string_types):
        order_book_ids = assure_order_book_id(order_book_ids)
    else:
        order_book_ids = [assure_order_book_id(i) for i in order_book_ids]

    return rqdatac.get_securities_margin(order_book_ids, start_dt, dt, fields=fields, expect_df=expect_df)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('count').is_instance_of(int).is_greater_than(0),
             verify_that('fields').are_valid_fields(VALID_SHARE_FIELDS, ignore_none=True))
def get_shares(order_book_ids, count=1, fields=None, expect_df=False):
    """
    获取截止T-1日的股票股本信息
    :param order_book_ids:
    :param count: 获取多少个交易日的数据
    :param fields:
    :param expect_df:
    :return: Series/DataFrame/Panel，请参考rqdatac的文档
    """
    env = Environment.get_instance()
    dt = env.trading_dt
    if count == 1:
        start_dt = dt
    else:
        start_dt = env.data_proxy.get_nth_previous_trading_date(dt, count - 1)

    if isinstance(order_book_ids, six.string_types):
        order_book_ids = assure_order_book_id(order_book_ids)
    else:
        order_book_ids = [assure_order_book_id(i) for i in order_book_ids]

    return rqdatac.get_shares(order_book_ids, start_dt, dt, fields=fields, expect_df=expect_df)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('count').is_instance_of(int).is_greater_than(0),
             verify_that('fields').are_valid_fields(VALID_TURNOVER_FIELDS, ignore_none=True))
def get_turnover_rate(order_book_ids, count=1, fields=None, expect_df=False):
    """
    获取截止T-1交易日的换手率数据
    :param order_book_ids:
    :param count:
    :param fields: str或list类型. 默认为None, 返回所有fields.
                   field 包括： 'today', 'week', 'month', 'year', 'current_year'
    :param expect_df:
    :return: Series/DataFrame/Panel，请参考rqdatac的文档
    """
    env = Environment.get_instance()
    data_proxy = env.data_proxy
    dt = data_proxy.get_previous_trading_date(env.trading_dt)
    if count == 1:
        start_dt = dt
    else:
        start_dt = data_proxy.get_nth_previous_trading_date(dt, count - 1)

    if isinstance(order_book_ids, six.string_types):
        order_book_ids = assure_order_book_id(order_book_ids)
    else:
        order_book_ids = [assure_order_book_id(i) for i in order_book_ids]

    return rqdatac.get_turnover_rate(order_book_ids, start_dt, dt, fields=fields, expect_df=expect_df)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('count').is_instance_of(int).is_greater_than(0))
def get_price_change_rate(order_book_ids, count=1, expect_df=False):
    """
    获取股票/指数截止T-1日的日涨幅
    :param order_book_ids:
    :param count: 获取多少个交易日的数据
    :param expect_df: 默认为False。当设置为True时，总是返回 multi-index DataFrame
    :return: Series/DataFrame，参见rqdatac的文档
    """
    env = Environment.get_instance()
    data_proxy = env.data_proxy

    if isinstance(order_book_ids, six.string_types):
        order_book_ids = assure_order_book_id(order_book_ids)
    else:
        order_book_ids = [assure_order_book_id(i) for i in order_book_ids]

    end_date = data_proxy.get_previous_trading_date(env.trading_dt)

    if count == 1:
        start_date = end_date
    else:
        start_date = data_proxy.get_nth_previous_trading_date(end_date, count - 1)

    return rqdatac.get_price_change_rate(order_book_ids, start_date, end_date, expect_df=expect_df)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('universe').are_valid_instruments(ignore_none=True))
def get_factor(order_book_ids, factors, count=1, universe=None, expect_df=False):
    """
    获取股票截止T-1日的因子数据
    :param order_book_ids:
    :param factors: 因子列表
    :param count: 获取多少个交易日的数据
    :param universe: 当获取横截面因子时，universe指定了因子计算时的股票池
    :param expect_df: 默认为False。当设置为True时，总是返回 multi-index DataFrame
    :return: 参见rqdatac的文档
    """
    env = Environment.get_instance()
    data_proxy = env.data_proxy
    end_date = data_proxy.get_previous_trading_date(env.trading_dt)

    if count == 1:
        start_date = end_date
    else:
        start_date = data_proxy.get_nth_previous_trading_date(end_date, count - 1)

    if isinstance(order_book_ids, six.string_types):
        order_book_ids = assure_order_book_id(order_book_ids)
    else:
        order_book_ids = [assure_order_book_id(i) for i in order_book_ids]

    return rqdatac.get_factor(order_book_ids, factors,
                              start_date=start_date, end_date=end_date,
                              universe=universe, expect_df=expect_df)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
def get_industry(industry, source='citics'):
    """
    获取T日某个行业所包含的股票列表
    :param industry: 行业名字
    :param source: 默认为中信(citics)，可选聚源(gildata)
    :return: list of order_book_id
    """
    env = Environment.get_instance()
    return rqdatac.get_industry(industry, source, env.calendar_dt)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
def get_instrument_industry(order_book_ids, source='citics', level=1):
    """
    获取T日时股票行业分类
    :param order_book_ids:
    :param source: 默认为中信(citics)，可选聚源(gildata)
    :param level: 默认为1，可选 0 1 2 3，0表示返回所有级别
    :return: DataFrame
    """
    if isinstance(order_book_ids, six.string_types):
        order_book_ids = assure_order_book_id(order_book_ids)
    else:
        order_book_ids = [assure_order_book_id(i) for i in order_book_ids]
    env = Environment.get_instance()
    return rqdatac.get_instrument_industry(order_book_ids, source, level, env.calendar_dt)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('count').is_instance_of(int).is_greater_than(0),
             verify_that('fields').are_valid_fields(VALID_STOCK_CONNECT_FIELDS, ignore_none=True))
def get_stock_connect(order_book_ids, count=1, fields=None, expect_df=False):
    """
    获取截止T-1日的获取沪深股通持股信息
    :param order_book_ids:
    :param count: 向前获取几个交易日
    :param fields: shares_holding, holding_ratio
    :param expect_df: 默认为False。当设置为True时，总是返回 multi-index DataFrame
    :return:
    """
    env = Environment.get_instance()
    end_date = env.data_proxy.get_previous_trading_date(env.trading_dt)

    if count == 1:
        start_date = end_date
    else:
        start_date = env.data_proxy.get_nth_previous_trading_date(end_date, count - 1)

    return rqdatac.get_stock_connect(order_book_ids, start_date, end_date,
                                     fields=fields, expect_df=expect_df)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('order_book_id').is_valid_instrument(),
             verify_that('quarter').is_valid_quarter(),
             verify_that('fields').are_valid_fields(VALID_CURRENT_PERFORMANCE_FIELDS, ignore_none=True))
def current_performance(order_book_id, info_date=None, quarter=None, interval='1q', fields=None):
    env = Environment.get_instance()
    dt = env.trading_dt
    if info_date is None and quarter is None:
        info_date = dt
    return rqdatac.current_performance(order_book_id, info_date, quarter, interval, fields)


@export_as_api
@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('underlying_symbol').is_instance_of(str))
def get_dominant_future(underlying_symbol, rule=0):
    dt = Environment.get_instance().trading_dt.date()
    ret = rqdatac.get_dominant_future(underlying_symbol, dt, dt, rule)
    if isinstance(ret, pd.Series) and ret.size == 1:
        return ret.item()
    else:
        user_log.warn(_("\'{0}\' future does not exist").format(underlying_symbol))
        return None


@export_as_api
class econ:
    pass


@export_as_api
class futures:
    pass


@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('reserve_type').is_in(['all', 'major', 'other']),
             verify_that('n').is_instance_of(int).is_greater_than(0))
def _econ_get_reserve_ratio(reserve_type='all', n=1):
    """
    获取截止T日的存款准备金率
    :param reserve_type: major/other/all
    :param n:
    :return: DataFrame
    """
    df = rqdatac.econ.get_reserve_ratio(reserve_type)
    if df is None or df.empty:
        return
    df.sort_values(by=['effective_date', 'reserve_type'], ascending=[False, True], inplace=True)
    effective_date_unique = df['effective_date'].unique()
    if len(effective_date_unique) <= n:
        return df

    df = df[df['effective_date'] >= effective_date_unique[n - 1]]
    return df


@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.AFTER_TRADING,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('n').is_instance_of(int).is_greater_than(0))
def _econ_get_money_supply(n=1):
    """
    获取截止T日的货币供应量指标
    :param n:
    :return: DataFrame
    """
    dt = Environment.get_instance().calendar_dt.date()

    start_date = 19780101
    end_date = 10000 * dt.year + 100 * dt.month + dt.day
    df = rqdatac.econ.get_money_supply(start_date, end_date)

    if df is None or df.empty:
        return

    df.sort_index(ascending=False, inplace=True)
    return df.head(n)


@ExecutionContext.enforce_phase(EXECUTION_PHASE.ON_INIT,
                                EXECUTION_PHASE.BEFORE_TRADING,
                                EXECUTION_PHASE.ON_BAR,
                                EXECUTION_PHASE.ON_TICK,
                                EXECUTION_PHASE.SCHEDULED)
@apply_rules(verify_that('underlying_symbol').is_instance_of(str))
def _futures_get_dominant(underlying_symbol, rule=0):
    dt = Environment.get_instance().trading_dt.date()
    ret = rqdatac.futures.get_dominant(underlying_symbol, dt, dt, rule)
    if isinstance(ret, pd.Series) and ret.size == 1:
        return ret.item()
    else:
        user_log.warn(_("\'{0}\' future does not exist").format(underlying_symbol))
        return None


econ.get_reserve_ratio = staticmethod(_econ_get_reserve_ratio)
econ.get_money_supply = staticmethod(_econ_get_money_supply)
futures.get_dominant = staticmethod(_futures_get_dominant)
