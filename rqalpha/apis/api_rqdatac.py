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
from typing import Union, Optional, Iterable, List

import six
from dateutil.parser import parse
import pandas as pd

from rqalpha.const import EXECUTION_PHASE
from rqalpha.api import export_as_api
from rqalpha.apis.names import (
    VALID_HISTORY_FIELDS, VALID_MARGIN_FIELDS, VALID_SHARE_FIELDS, VALID_TURNOVER_FIELDS,
    VALID_CURRENT_PERFORMANCE_FIELDS, VALID_STOCK_CONNECT_FIELDS,
)
from rqalpha.core.execution_context import ExecutionContext
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
        __name__ = "rqdatac"

        def __getattr__(self, item):
            return self

        def __call__(self, *args, **kwargs):
            raise RuntimeError(_('rqdatac is not available, extension apis will not function properly'))


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
@apply_rules(verify_that('start_date').is_valid_date())
def get_split(order_book_ids, start_date=None):
    # type: (Union[str, List[str]], Optional[Union[str, datetime.date]]) -> pd.DataFrame
    """
    获取某只股票到策略当前日期前一天的拆分情况（包含起止日期）。

    :param order_book_ids: 证券代码，证券的独特的标识符，例如：'000001.XSHE'
    :param start_date: 开始日期，用户必须指定，需要早于策略当前日期

    :return: 查询时间段内的某个股票的拆分数据

        *   ex_dividend_date: 除权除息日，该天股票的价格会因为拆分而进行调整
        *   book_closure_date: 股权登记日
        *   split_coefficient_from: 拆分因子（拆分前）
        *   split_coefficient_to: 拆分因子（拆分后）

        例如：每10股转增2股，则split_coefficient_from = 10, split_coefficient_to = 12.

    :example:

    ..  code-block:: python3
        :linenos:

        get_split('000001.XSHE', start_date='2010-01-04')
        #[Out]
        #                 book_closure_date payable_date  split_coefficient_from  \
        #ex_dividend_date
        #2013-06-20              2013-06-19   2013-06-20                      10
        #                  split_coefficient_to
        #ex_dividend_date
        #2013-06-20                        16.0
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
@apply_rules(verify_that('date').is_valid_date(ignore_none=True))
def index_components(order_book_id, date=None):
    # type: (str, Optional[Union[str, datetime.date]]) -> List[str]

    """
    获取某一指数的股票构成列表，也支持指数的历史构成查询。

    :param order_book_id: 指数代码，可传入order_book_id
    :param date: 查询日期，默认为策略当前日期。如指定，则应保证该日期不晚于策略当前日期
    :return: 构成该指数股票的 order_book_id

    :example:

    得到上证指数在策略当前日期的构成股票的列表:

    ..  code-block:: python3
        :linenos:

        index_components('000001.XSHG')
        #[Out]['600000.XSHG', '600004.XSHG', ...]
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
@apply_rules(verify_that('date').is_valid_date(ignore_none=True))
def index_weights(order_book_id, date=None):
    # type: (str, Optional[Union[str, datetime.date]]) -> pd.Series
    """
    获取T-1日的指数权重

    :param order_book_id: 指数
    :param date: 可选，默认为T-1日
    :return: 每只股票在指数中的构成权重

    :example:

    获取上证50指数上个交易日的指数构成

    .. code-block:: python3
        :linenos:

        index_weights('000016.XSHG')
        # [Out]
        # Order_book_id
        # 600000.XSHG    0.03750
        # 600010.XSHG    0.00761
        # 600016.XSHG    0.05981
        # 600028.XSHG    0.01391
        # 600029.XSHG    0.00822
        # 600030.XSHG    0.03526
        # 600036.XSHG    0.04889
        # 600050.XSHG    0.00998
        # 600104.XSHG    0.02122

    """
    env = Environment.get_instance()
    data_proxy = env.data_proxy
    dt = to_date(data_proxy.get_previous_trading_date(env.trading_dt.date()))
    if date is None:
        date = dt
    else:
        date = to_date(date)
        if date > dt:
            raise RQInvalidArgument(_('in index_weights, date {} is no earlier than previous test date {}').format(
                date, dt
            ))
    order_book_id = assure_order_book_id(order_book_id)
    return rqdatac.index_weights(order_book_id, date)


@export_as_api
def concept(*concept_names):
    # type: (*str) -> List[str]
    """
    获取T日的概念股列表

    :param concept_names: 概念名称。可以从概念列表中选择一个或多个概念填写, 可以通过 rqdatac.concept_list() 获取概念列表
    :return: 属于该概念的股票 order_book_id

    :example:

    得到一个概念的股票列表：

    .. code-block:: python3
        :linenos:

        concept('民营医院')
        # [Out]
        # ['600105.XSHG',
        # '002550.XSHE',
        # '002004.XSHE',
        # '002424.XSHE',
        # ...]

    得到某几个概念的股票列表:

    .. code-block::
        :linenos:

        concept('民营医院', '国企改革')
        # [Out]
        # ['601607.XSHG',
        # '600748.XSHG',
        # '600630.XSHG',
        # ...]

    """
    env = Environment.get_instance()
    dt = env.trading_dt.date()

    return rqdatac.concept(*concept_names, date=dt)


@export_as_api
@ExecutionContext.enforce_phase(
    EXECUTION_PHASE.ON_INIT,
    EXECUTION_PHASE.BEFORE_TRADING,
    EXECUTION_PHASE.OPEN_AUCTION,
    EXECUTION_PHASE.AFTER_TRADING,
    EXECUTION_PHASE.SCHEDULED
)
@apply_rules(verify_that('order_book_ids').are_valid_instruments(),
             verify_that('start_date').is_valid_date(ignore_none=False),
             verify_that('end_date').is_valid_date(ignore_none=True),
             verify_that('frequency').is_valid_frequency(),
             verify_that('fields').are_valid_fields(VALID_HISTORY_FIELDS, ignore_none=True),
             verify_that('adjust_type').is_in(['pre', 'post', 'none', 'internal']),
             verify_that('skip_suspended').is_instance_of(bool))
def get_price(
        order_book_ids,  # type: Union[str, Iterable[str]]
        start_date,  # type: Union[datetime.date, str]
        end_date=None,  # type: Optional[Union[datetime.date, datetime.datetime, str]]
        frequency='1d',  # type: Optional[str]
        fields=None,  # type: Optional[Iterable[str]]
        adjust_type='pre',  # type: Optional[str]
        skip_suspended=False,  # type: Optional[bool]
        expect_df=False  # type: Optional[bool]
):  # type: (...) -> Union[pd.DataFrame, pd.Panel, pd.Series]
    """
    获取指定合约或合约列表的历史行情（包含起止日期，日线或分钟线），不能在'handle_bar'函数中进行调用。

    注意，这一函数主要是为满足在研究平台编写策略习惯而引入。在编写策略中，使用history_bars进行数据获取会更方便。

    :param order_book_ids: 合约代码，合约代码，可传入order_book_id, order_book_id list, symbol, symbol list
    :param start_date: 开始日期，用户必须指定
    :param end_date: 结束日期，默认为策略当前日期前一天
    :param frequency: 历史数据的频率。 现在支持日/分钟级别的历史数据，默认为'1d'。使用者可自由选取不同频率，例如'5m'代表5分钟线
    :param fields: 期望返回的字段名称，如 open，close 等
    :param adjust_type: 权息修复方案。前复权 - pre，后复权 - post，不复权 - none
    :param skip_suspended: 是否跳过停牌数据。默认为False，不跳过，用停牌前数据进行补齐。True则为跳过停牌期。注意，当设置为True时，函数order_book_id只支持单个合约传入
    :param expect_df: 是否期望始终返回 DataFrame。pandas 0.25.0 以上该参数应设为 True，以避免因试图构建 Panel 产生异常

    当 expect_df 为 False 时，返回值的类型如下

        *   传入一个order_book_id，多个fields，函数会返回一个pandas DataFrame
        *   传入一个order_book_id，一个field，函数会返回pandas Series
        *   传入多个order_book_id，一个field，函数会返回一个pandas DataFrame
        *   传入多个order_book_id，函数会返回一个pandas Panel


        =========================   =========================   ==============================================================================
        参数                         类型                        说明
        =========================   =========================   ==============================================================================
        open                        float                       开盘价
        close                       float                       收盘价
        high                        float                       最高价
        low                         float                       最低价
        limit_up                    float                       涨停价
        limit_down                  float                       跌停价
        total_turnover              float                       总成交额
        volume                      float                       总成交量
        acc_net_value               float                       累计净值（仅限基金日线数据）
        unit_net_value              float                       单位净值（仅限基金日线数据）
        discount_rate               float                       折价率（仅限基金日线数据）
        settlement                  float                       结算价 （仅限期货日线数据）
        prev_settlement             float                       昨日结算价（仅限期货日线数据）
        open_interest               float                       累计持仓量（期货专用）
        basis_spread                float                       基差点数（股指期货专用，股指期货收盘价-标的指数收盘价）
        trading_date                pandas.TimeStamp             交易日期（仅限期货分钟线数据），对应期货夜盘的情况
        =========================   =========================   ==============================================================================

    :example:

    获取单一股票历史日线行情:

    ..  code-block:: python3
        :linenos:

        get_price('000001.XSHE', start_date='2015-04-01', end_date='2015-04-12')
        #[Out]
        #open    close    high    low    total_turnover    volume    limit_up    limit_down
        #2015-04-01    10.7300    10.8249    10.9470    10.5469    2.608977e+09    236637563.0    11.7542    9.6177
        #2015-04-02    10.9131    10.7164    10.9470    10.5943    2.222671e+09    202440588.0    11.9102    9.7397
        #2015-04-03    10.6486    10.7503    10.8114    10.5876    2.262844e+09    206631550.0    11.7881    9.6448
        #2015-04-07    10.9538    11.4015    11.5032    10.9538    4.898119e+09    426308008.0    11.8288    9.6787
        #2015-04-08    11.4829    12.1543    12.2628    11.2929    5.784459e+09    485517069.0    12.5409    10.2620
        #2015-04-09    12.1747    12.2086    12.9208    12.0255    5.794632e+09    456921108.0    13.3684    10.9403
        #2015-04-10    12.2086    13.4294    13.4294    12.1069    6.339649e+09    480990210.0    13.4294    10.9877
        #...
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
@apply_rules(verify_that('count').is_instance_of(int).is_greater_than(0),
             verify_that('fields').are_valid_fields(VALID_MARGIN_FIELDS, ignore_none=True))
def get_securities_margin(
        order_book_ids,  # type: Union[str, Iterable[str]]
        count=1,  # type: Optional[int]
        fields=None,  # type: Optional[str]
        expect_df=False  # type: Optional[bool]
):  # type: (...) -> Union[pd.Series, pd.DataFrame, pd.Panel]
    """
    获取融资融券信息。包括 `深证融资融券数据 <http://www.szse.cn/main/disclosure/rzrqxx/rzrqjy/>`_ 以及 `上证融资融券数据 <http://www.sse.com.cn/market/othersdata/margin/detail/>`_ 情况。既包括个股数据，也包括市场整体数据。需要注意，融资融券的开始日期为2010年3月31日。

    :param order_book_ids: 可输入order_book_id, order_book_id list, symbol, symbol list。另外，输入'XSHG'或'sh'代表整个上证整体情况；'XSHE'或'sz'代表深证整体情况
    :param count: 回溯获取的数据个数。默认为当前能够获取到的最近的数据
    :param fields: 期望返回的字段，默认为所有字段。见下方列表
    :param expect_df: 是否期望始终返回 DataFrame。pandas 0.25.0 以上该参数应设为 True，以避免因试图构建 Panel 产生异常

    =========================   ===================================================
    fields                      字段名
    =========================   ===================================================
    margin_balance              融资余额
    buy_on_margin_value         融资买入额
    margin_repayment            融资偿还额
    short_balance               融券余额
    short_balance_quantity      融券余量
    short_sell_value            融券卖出额
    short_sell_quantity         融券卖出量
    short_repayment_quantity    融券偿还量
    total_balance               融资融券余额
    =========================   ===================================================

    当 expect_df 为 False 时，返回值的类型如下：

        *   多个order_book_id，单个field的时候返回DataFrame，index为date，column为order_book_id
        *   单个order_book_id，多个fields的时候返回DataFrame，index为date，column为fields
        *   单个order_book_id，单个field返回Series
        *   多个order_book_id，多个fields的时候返回DataPanel Items axis为fields Major_axis axis为时间戳 Minor_axis axis为order_book_id

    :example:

    *   获取沪深两个市场一段时间内的融资余额:

    ..  code-block:: python3
        :linenos:

        logger.info(get_securities_margin('510050.XSHG', count=5))
        #[Out]
        #margin_balance    buy_on_margin_value    short_sell_quantity    margin_repayment    short_balance_quantity    short_repayment_quantity    short_balance    total_balance
        #2016-08-01    7.811396e+09    50012306.0    3597600.0    41652042.0    15020600.0    1645576.0    NaN    NaN
        #2016-08-02    7.826381e+09    34518238.0    2375700.0    19532586.0    14154000.0    3242300.0    NaN    NaN
        #2016-08-03    7.733306e+09    17967333.0    4719700.0    111043009.0    16235600.0    2638100.0    NaN    NaN
        #2016-08-04    7.741497e+09    30259359.0    6488600.0    22068637.0    17499000.0    5225200.0    NaN    NaN
        #2016-08-05    7.726343e+09    25270756.0    2865863.0    40423859.0    14252363.0    6112500.0    NaN    NaN

    *   获取沪深两个市场一段时间内的融资余额:

    ..  code-block:: python3
        :linenos:

        logger.info(get_securities_margin(['XSHE', 'XSHG'], count=5, fields='margin_balance'))
        #[Out]
        #        XSHE        XSHG
        #2016-08-01    3.837627e+11    4.763557e+11
        #2016-08-02    3.828923e+11    4.763931e+11
        #2016-08-03    3.823545e+11    4.769321e+11
        #2016-08-04    3.833260e+11    4.776380e+11
        #2016-08-05    3.812751e+11    4.766928e+11

    *   获取上证个股以及整个上证市场融资融券情况:

    ..  code-block:: python3
        :linenos:

        logger.info(get_securities_margin(['XSHG', '601988.XSHG', '510050.XSHG'], count=5))
        #[Out]
        #<class 'pandas.core.panel.Panel'>
        #Dimensions: 8 (items) x 5 (major_axis) x 3 (minor_axis)
        #Items axis: margin_balance to total_balance
        #Major_axis axis: 2016-08-01 00:00:00 to 2016-08-05 00:00:00
        #Minor_axis axis: XSHG to 510050.XSHG

    *   获取50ETF融资偿还额情况

    ..  code-block:: python3
        :linenos:

        logger.info(get_securities_margin('510050.XSHG', count=5, fields='margin_repayment'))
        #[Out]
        #2016-08-01     41652042.0
        #2016-08-02     19532586.0
        #2016-08-03    111043009.0
        #2016-08-04     22068637.0
        #2016-08-05     40423859.0
        #Name: margin_repayment, dtype: float64
    """
    env = Environment.get_instance()
    data_proxy = env.data_proxy
    dt = data_proxy.get_previous_trading_date(env.trading_dt)
    if count == 1:
        start_dt = dt
    else:
        start_dt = data_proxy.get_previous_trading_date(dt, count - 1)

    if isinstance(order_book_ids, six.string_types):
        order_book_ids = assure_order_book_id(order_book_ids)
    else:
        order_book_ids = [assure_order_book_id(i) for i in order_book_ids]

    return rqdatac.get_securities_margin(order_book_ids, start_dt, dt, fields=fields, expect_df=expect_df)


@export_as_api
@apply_rules(verify_that('count').is_instance_of(int).is_greater_than(0),
             verify_that('fields').are_valid_fields(VALID_SHARE_FIELDS, ignore_none=True))
def get_shares(
        order_book_ids,  # type: Union[str, List[str]]
        count=1,  # type: Optional[int]
        fields=None,  # type: Optional[str]
        expect_df=False  # type: Optional[bool]
):  # type: (...) -> Union[pd.DataFrame, pd.Series]
    """
    :param order_book_ids: 可输入 order_book_id, order_book_id list, symbol, symbol list
    :param count: 回溯获取的数据个数。默认为当前能够获取到的最近的数据
    :param fields: 期望返回的字段，默认为所有字段。见下方列表
    :param expect_df: 是否期望始终返回 DataFrame。pandas 0.25.0 以上该参数应设为 True，以避免因试图构建 Panel 产生异常

    =========================   ===================================================
    fields                      字段名
    =========================   ===================================================
    total                       总股本
    circulation_a               流通A股
    management_circulation      已流通高管持股
    non_circulation_a           非流通A股合计
    total_a                     A股总股本
    =========================   ===================================================

    :return: 查询时间段内某个股票的流通情况，当 expect_df 为 False 且 fields 指定为单一字段的情况时返回 pandas.Series

    :example:

    获取平安银行总股本数据:

    ..  code-block:: python3
        :linenos:

        logger.info(get_shares('000001.XSHE', count=5, fields='total'))
        #[Out]
        #2016-08-01    1.717041e+10
        #2016-08-02    1.717041e+10
        #2016-08-03    1.717041e+10
        #2016-08-04    1.717041e+10
        #2016-08-05    1.717041e+10
        #Name: total, dtype: float64
    """
    env = Environment.get_instance()
    dt = env.trading_dt
    if count == 1:
        start_dt = dt
    else:
        start_dt = env.data_proxy.get_previous_trading_date(dt, count - 1)

    if isinstance(order_book_ids, six.string_types):
        order_book_ids = assure_order_book_id(order_book_ids)
    else:
        order_book_ids = [assure_order_book_id(i) for i in order_book_ids]

    return rqdatac.get_shares(order_book_ids, start_dt, dt, fields=fields, expect_df=expect_df)


@export_as_api
@apply_rules(verify_that('count').is_instance_of(int).is_greater_than(0),
             verify_that('fields').are_valid_fields(VALID_TURNOVER_FIELDS, ignore_none=True))
def get_turnover_rate(
        order_book_ids,  # type: Union[str, List[str]]
        count=1,  # type: Optional[int]
        fields=None,  # type: Optional[set]
        expect_df=False  # type: Optional[bool]
):  # type: (...) -> Union[pd.Series, pd.DataFrame, pd.Panel]
    """
    获取截止T-1交易日的换手率数据

    :param order_book_ids: 可输入 order_book_id, order_book_id list, symbol, symbol list
    :param count: 回溯获取的数据个数。默认为当前能够获取到的最近的数据
    :param fields: 期望返回的字段，默认为所有字段。见下方列表
    :param expect_df: 是否期望始终返回 DataFrame。pandas 0.25.0 以上该参数应设为 True，以避免因试图构建 Panel 产生异常

    =========================   ===================================================
    fields                      字段名
    =========================   ===================================================
    today                       当天换手率
    week                        过去一周平均换手率
    month                       过去一个月平均换手率
    three_month                 过去三个月平均换手率
    six_month                   过去六个月平均换手率
    year                        过去一年平均换手率
    current_year                当年平均换手率
    total                       上市以来平均换手率
    =========================   ===================================================

    当 expect_df 为 False 时，返回值的类型如下：

        *   如果只传入一个order_book_id，多个fields，返回 `pandas.DataFrame`
        *   如果传入order_book_id list，并指定单个field，函数会返回一个 `pandas.DataFrame`
        *   如果传入order_book_id list，并指定多个fields，函数会返回一个 `pandas.Panel`

    :example:

    获取平安银行历史换手率情况:

   ..  code-block:: python3
        :linenos:

        logger.info(get_turnover_rate('000001.XSHE', count=5))
        #[Out]
        #           today    week   month  three_month  six_month    year  \
        #2016-08-01  0.5190  0.4478  0.3213       0.2877     0.3442  0.5027
        #2016-08-02  0.3070  0.4134  0.3112       0.2843     0.3427  0.5019
        #2016-08-03  0.2902  0.3460  0.3102       0.2823     0.3432  0.4982
        #2016-08-04  0.9189  0.4938  0.3331       0.2914     0.3482  0.4992
        #2016-08-05  0.4962  0.5031  0.3426       0.2960     0.3504  0.4994

        #          current_year   total
        #2016-08-01        0.3585  1.1341
        #2016-08-02        0.3570  1.1341
        #2016-08-03        0.3565  1.1339
        #2016-08-04        0.3604  1.1339
        #2016-08-05        0.3613  1.1338
    """
    env = Environment.get_instance()
    data_proxy = env.data_proxy
    dt = data_proxy.get_previous_trading_date(env.trading_dt)
    if count == 1:
        start_dt = dt
    else:
        start_dt = data_proxy.get_previous_trading_date(dt, count - 1)

    if isinstance(order_book_ids, six.string_types):
        order_book_ids = assure_order_book_id(order_book_ids)
    else:
        order_book_ids = [assure_order_book_id(i) for i in order_book_ids]

    return rqdatac.get_turnover_rate(order_book_ids, start_dt, dt, fields=fields, expect_df=expect_df)


@export_as_api
@apply_rules(verify_that('count').is_instance_of(int).is_greater_than(0))
def get_price_change_rate(
        order_book_ids,  # type: Union[str, List[str]]
        count=1,  # type: Optional[int]
        expect_df=False  # type: Optional[bool]
):  # type: (...) -> Union[pd.DataFrame, pd.Series]
    """
    获取股票/指数截止T-1日的日涨幅

    :param order_book_ids: 可输入 order_book_id, order_book_id list, symbol, symbol list
    :param count: 回溯获取的数据个数。默认为当前能够获取到的最近的数据
    :param expect_df: 是否期望始终返回 DataFrame。pandas 0.25.0 以上该参数应设为 True，以避免因试图构建 Panel 产生异常

    当 expect_df 为 False 时，返回值的类型如下：

        *  传入多个order_book_id，函数会返回pandas DataFrame
        *  传入一个order_book_id，函数会返回pandas Series

    :example:

    获取平安银行以及沪深300指数一段时间的涨跌幅情况:

    ..  code-block:: python3
        :linenos:

        get_price_change_rate(['000001.XSHE', '510050.XSHG'], 1)
        # [Out]
        # 2016-06-01 15:30:00.00  INFO   order_book_id  000001.XSHE  510050.XSHG
        #                                date
        #                                2016-05-31        0.026265     0.033964
        # 2016-06-02 15:30:00.00  INFO   order_book_id  000001.XSHE  510050.XSHG
        #                                date
        #                                2016-06-01       -0.006635    -0.008308

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
        start_date = data_proxy.get_previous_trading_date(end_date, count - 1)

    return rqdatac.get_price_change_rate(order_book_ids, start_date, end_date, expect_df=expect_df)


@export_as_api
@apply_rules(verify_that('universe').are_valid_instruments(ignore_none=True))
def get_factor(
        order_book_ids,  # type: Union[str, List[str]]
        factors,  # type: Union[str, List[str]]
        count=1,  # type: Optional[int]
        universe=None,  # type: Optional[Union[str, List[Union]]]
        expect_df=False  # type: Optional[bool]
):  # type: (...) -> pd.DataFrame
    """
    获取股票截止T-1日的因子数据

    :param order_book_ids:  合约代码，可传入order_book_id, order_book_id list
    :param factors: 因子名称，可查询 rqdatac.get_all_factor_names() 得到所有有效因子字段
    :param count: 获取多少个交易日的数据
    :param universe: 当获取横截面因子时，universe指定了因子计算时的股票池
    :param expect_df: 默认为False。当设置为True时，总是返回 multi-index DataFrame。pandas 0.25.0 以上该参数应设为 True，以避免因试图构建 Panel 产生异常
    """
    env = Environment.get_instance()
    data_proxy = env.data_proxy
    end_date = data_proxy.get_previous_trading_date(env.trading_dt)

    if count == 1:
        start_date = end_date
    else:
        start_date = data_proxy.get_previous_trading_date(end_date, count - 1)

    if isinstance(order_book_ids, six.string_types):
        order_book_ids = assure_order_book_id(order_book_ids)
    else:
        order_book_ids = [assure_order_book_id(i) for i in order_book_ids]

    return rqdatac.get_factor(order_book_ids, factors,
                              start_date=start_date, end_date=end_date,
                              universe=universe, expect_df=expect_df)


@export_as_api
def get_industry(industry, source='citics'):
    # type: (str, Optional[str]) -> List[str]
    """
    通过传入行业名称、行业指数代码或者行业代号，拿到 T 日指定行业的股票列表

    :param industry: 行业名字
    :param source: 默认为中信(citics)，可选聚源(gildata)
    :return: list of order_book_id

    """
    env = Environment.get_instance()
    return rqdatac.get_industry(industry, source, env.calendar_dt)


@export_as_api
def get_instrument_industry(order_book_ids, source='citics', level=1):
    # type: (Union[str, List[str]], Optional[str], Optional[int]) -> pd.DataFrame
    """
    获取T日时股票行业分类

    :param order_book_ids: 合约代码，可传入order_book_id, order_book_id list
    :param source: 默认为中信(citics)，可选聚源(gildata)
    :param level: 默认为1，可选 0 1 2 3，0表示返回所有级别
    """
    if isinstance(order_book_ids, six.string_types):
        order_book_ids = assure_order_book_id(order_book_ids)
    else:
        order_book_ids = [assure_order_book_id(i) for i in order_book_ids]
    env = Environment.get_instance()
    return rqdatac.get_instrument_industry(order_book_ids, source, level, env.calendar_dt)


@export_as_api
@apply_rules(verify_that('count').is_instance_of(int).is_greater_than(0),
             verify_that('fields').are_valid_fields(VALID_STOCK_CONNECT_FIELDS, ignore_none=True))
def get_stock_connect(order_book_ids, count=1, fields=None, expect_df=False):
    # type: (Union[str, List[str]], Optional[int], Optional[str], Optional[bool]) -> pd.DataFrame
    """
    获取截止T-1日A股股票在香港上市交易的持股情况

    :param order_book_ids: 合约代码，可传入order_book_id, order_book_id list，这里输入的是A股编码
    :param count: 向前获取几个交易日
    :param fields: 持股量（shares_holding），持股比例（holding_ratio），默认为所有字段
    :param expect_df: 默认为False。当设置为True时，总是返回 multi-index DataFrame。pandas 0.25.0 以上该参数应设为 True，以避免因试图构建 Panel 产生异常

    当 expect_df 为 False 时，返回值的类型如下：
        *  多个order_book_id，多个fields的时候返回pandas Panel
        *  单个order_book_id，多个fields的时候返回pandas DataFrame
        *  单个order_book_id，单个field返回pandas Series

    :return:
    """
    env = Environment.get_instance()
    end_date = env.data_proxy.get_previous_trading_date(env.trading_dt)

    if count == 1:
        start_date = end_date
    else:
        start_date = env.data_proxy.get_previous_trading_date(end_date, count - 1)

    return rqdatac.get_stock_connect(order_book_ids, start_date, end_date,
                                     fields=fields, expect_df=expect_df)


@export_as_api
@apply_rules(verify_that('order_book_id').is_valid_instrument(),
             verify_that('quarter').is_valid_quarter(),
             verify_that('fields').are_valid_fields(VALID_CURRENT_PERFORMANCE_FIELDS, ignore_none=True))
def current_performance(order_book_id, info_date=None, quarter=None, interval='1q', fields=None):
    # type: (str, Optional[str], Optional[str], Optional[str], Optional[str, List[str]]) -> pd.DataFrame
    """
    默认返回给定的 order_book_id 当前最近一期的快报数据

    :param order_book_id: 合约代码
    :param info_date: yyyymmdd 或者 yyyy-mm-dd。如果不填(info_date和quarter都为空)，则返回策略运行当前日期的最新发布的快报。如果填写，则从info_date当天或者之前最新的报告开始抓取。
    :param quarter: info_date参数优先级高于quarter。如果info_date填写了日期，则不查看quarter这个字段。 如果info_date没有填写而quarter 有填写，则财报回溯查询的起始报告期，例如'2015q2', '2015q4'分别代表2015年半年报以及年报。默认只获取当前报告期财务信息
    :param interval: 查询财务数据的间隔。例如，填写'5y'，则代表从报告期开始回溯5年，每年为相同报告期数据；'3q'则代表从报告期开始向前回溯3个季度。不填写默认抓取一期。
    :param fields: 抓取对应有效字段返回。默认返回所有字段。具体快报字段可参看 Ricequant 官网财务数据文档。
    """
    env = Environment.get_instance()
    dt = env.trading_dt
    if info_date is None and quarter is None:
        info_date = dt
    return rqdatac.current_performance(order_book_id, info_date, quarter, interval, fields)


@export_as_api
@apply_rules(verify_that('underlying_symbol').is_instance_of(str))
def get_dominant_future(underlying_symbol, rule=0):
    # type: (str, Optional[int]) -> Optional[str]
    """
    获取某一期货品种策略当前日期的主力合约代码。 合约首次上市时，以当日收盘同品种持仓量最大者作为从第二个交易日开始的主力合约。当同品种其他合约持仓量在收盘后超过当前主力合约1.1倍时，从第二个交易日开始进行主力合约的切换。日内不会进行主力合约的切换。

    :param underlying_symbol: 期货合约品种，例如沪深300股指期货为'IF'
    :param rule: 默认是rule=0,采用最大昨仓为当日主力合约，每个合约只能做一次主力合约，不会重复出现。针对股指期货，只在当月和次月选择主力合约。 当rule=1时，主力合约的选取只考虑最大昨仓这个条件。

    :example:

    获取某一天的主力合约代码（策略当前日期是20160801）:

    ..  code-block:: python3
        :linenos:

        get_dominant_future('IF')
        #[Out]
        #'IF1608'
    """
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


@apply_rules(verify_that('reserve_type').is_in(['all', 'major', 'other']),
             verify_that('n').is_instance_of(int).is_greater_than(0))
def _econ_get_reserve_ratio(reserve_type='all', n=1):
    # type: (str, int) -> Optional[pd.DataFrame]
    """
    获取截止T日的存款准备金率

    :param reserve_type: 目前有大型金融机构（'major'） 和 其他金融机构（'other'）两种分类。默认为all，即所有类别都会返回。
    :param n: 返回最近 n 个生效日期的存款准备金率数据
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


@apply_rules(verify_that('n').is_instance_of(int).is_greater_than(0))
def _econ_get_money_supply(n=1):
    # type: (int) -> Optional[pd.DataFrame]
    """
    获取截止T日的货币供应量指标

    :param n: 返回前 n 个消息公布日期的货币供应量指标数据
    """
    dt = Environment.get_instance().calendar_dt.date()

    start_date = 19780101
    end_date = 10000 * dt.year + 100 * dt.month + dt.day
    df = rqdatac.econ.get_money_supply(start_date, end_date)

    if df is None or df.empty:
        return

    df.sort_index(ascending=False, inplace=True)
    return df.head(n)


econ.get_reserve_ratio = staticmethod(_econ_get_reserve_ratio)
econ.get_money_supply = staticmethod(_econ_get_money_supply)


@export_as_api
class futures:
    pass


@apply_rules(verify_that('underlying_symbol').is_instance_of(str))
def _futures_get_dominant(underlying_symbol, rule=0):
    # type: (str, Optional[int]) -> Optional[str]
    """
    获取某一期货品种策略当前日期的主力合约代码。 合约首次上市时，以当日收盘同品种持仓量最大者作为从第二个交易日开始的主力合约。当同品种其他合约持仓量在收盘后超过当前主力合约1.1倍时，从第二个交易日开始进行主力合约的切换。日内不会进行主力合约的切换。

    :param underlying_symbol: 期货合约品种，例如沪深300股指期货为'IF'
    :param rule: 默认是rule=0,采用最大昨仓为当日主力合约，每个合约只能做一次主力合约，不会重复出现。针对股指期货，只在当月和次月选择主力合约。 当rule=1时，主力合约的选取只考虑最大昨仓这个条件。

    :example:

    获取某一天的主力合约代码（策略当前日期是20160801）:

    ..  code-block:: python3
        :linenos:

        get_dominant_future('IF')
        #[Out]
        #'IF1608'
    """
    dt = Environment.get_instance().trading_dt.date()
    ret = rqdatac.futures.get_dominant(underlying_symbol, dt, dt, rule)
    if ret is None or ret.empty:
        return None

    return ret.item()


@apply_rules(verify_that('which').is_instance_of(str),
             verify_that('rank_by').is_in(['short', 'long']))
def _futures_get_member_rank(which, count=1, rank_by='short'):
    # type: (str, int, str) -> pd.DataFrame
    """
    获取截止T-1日的期货或品种的会员排名情况

    :param which: 期货合约或品种
    :param count: 获取多少个交易日的数据，默认为1
    :param rank_by: short/long
    """
    env = Environment.get_instance()
    end_date = env.data_proxy.get_previous_trading_date(env.trading_dt)

    if count == 1:
        start_date = end_date
    else:
        start_date = env.data_proxy.get_previous_trading_date(end_date, count - 1)

    return rqdatac.futures.get_member_rank(which, start_date=start_date, end_date=end_date, rank_by=rank_by)


def _futures_get_warehouse_stocks(underlying_symbols, count=1):
    # type: (Union[str, List[str]], int) -> pd.DataFrame
    """
    获取截止T-1日的期货仓单数据

    :param underlying_symbols: 期货品种，可以为str或列表
    :param count: 获取多少个交易日的数据，默认为1
    """
    env = Environment.get_instance()
    end_date = env.data_proxy.get_previous_trading_date(env.trading_dt)

    if count == 1:
        start_date = end_date
    else:
        start_date = env.data_proxy.get_previous_trading_date(end_date, count - 1)

    return rqdatac.futures.get_warehouse_stocks(underlying_symbols, start_date=start_date, end_date=end_date)


futures.get_dominant = staticmethod(_futures_get_dominant)
futures.get_member_rank = staticmethod(_futures_get_member_rank)
futures.get_warehouse_stocks = staticmethod(_futures_get_warehouse_stocks)


@export_as_api
@apply_rules(verify_that('entry_date').is_valid_date(ignore_none=True),
             verify_that('interval').is_valid_interval(),
             verify_that('report_quarter').is_instance_of(bool))
def get_fundamentals(query, entry_date=None, interval='1d', report_quarter=False, expect_df=False, **kwargs):
    user_log.warn('get_fundamentals is deprecated, use get_pit_financials_ex instead')

    env = Environment.get_instance()
    dt = env.calendar_dt.date()
    if entry_date is None and 'date' in kwargs:
        entry_date = kwargs.pop('date')
    if kwargs:
        raise RQInvalidArgument('unknown arguments: {}'.format(kwargs))

    latest_query_day = dt - datetime.timedelta(days=1)

    if entry_date:
        entry_date = to_date(entry_date)
        if entry_date <= latest_query_day:
            query_date = entry_date
        else:
            raise RQInvalidArgument(
                _('in get_fundamentals entry_date {} is no earlier than test date {}').format(entry_date, dt))
    else:
        query_date = latest_query_day

    result = rqdatac.get_fundamentals(query, query_date, interval, report_quarter=report_quarter, expect_df=expect_df)
    if result is None:
        return pd.DataFrame()

    if expect_df:
        return result

    if len(result.major_axis) == 1:
        frame = result.major_xs(result.major_axis[0])
        # research 与回测返回的Frame维度相反
        return frame.T
    return result


@export_as_api
@apply_rules(verify_that('interval').is_valid_interval())
def get_financials(query, quarter=None, interval='4q', expect_df=False):
    user_log.warn('get_financials is deprecated, use get_pit_finacials_ex instead')

    if quarter is None:
        valid = True
    else:
        valid = isinstance(quarter, six.string_types) and quarter[-2] == 'q'
        if valid:
            try:
                valid = 1990 <= int(quarter[:-2]) <= 2050 and 1 <= int(quarter[-1]) <= 4
            except ValueError:
                valid = False
    if not valid:
        raise RQInvalidArgument(
            _(u"function {}: invalid {} argument, quarter should be in form of '2012q3', "
              u"got {} (type: {})").format(
                'get_financials', 'quarter', quarter, type(quarter)
            ))
    env = Environment.get_instance()
    dt = env.calendar_dt.date() - datetime.timedelta(days=1)  # Take yesterday's data as default
    year = dt.year
    mon = dt.month
    day = dt.day
    int_date = year * 10000 + mon * 100 + day
    q = (mon - 4) // 3 + 1
    y = year
    if q <= 0:
        y -= 1
        q = 4
    default_quarter = str(y) + 'q' + str(q)
    if quarter is None or quarter > default_quarter:
        quarter = default_quarter

    include_date = False
    for d in query.column_descriptions:
        if d['name'] == 'announce_date':
            include_date = True
    if not include_date:
        query = query.add_column(rqdatac.fundamentals.announce_date)

    result = rqdatac.get_financials(query, quarter, interval, expect_df=expect_df)
    if result is None:
        return pd.DataFrame()
    if isinstance(result, pd.Series):
        return result
    elif isinstance(result, pd.DataFrame):
        result = result[(result['announce_date'] <= int_date) | pd.isnull(result['announce_date'])]
        if not include_date:
            del result['announce_date']
    else:
        d = dict()
        for order_book_id in result.minor_axis:
            df = result.minor_xs(order_book_id)
            df = df[(df.announce_date < int_date) | (pd.isnull(df.announce_date))]
            d[order_book_id] = df
        pl = pd.Panel.from_dict(d, orient='minor')
        if not include_date:
            pl.drop('announce_date', axis=0, inplace=True)
            if len(pl.items) == 1:
                pl = pl[pl.items[0]]
        return pl

    return result


@export_as_api
@apply_rules(verify_that('if_adjusted').is_in([0, 1, '0', '1', 'all', 'ignore'], ignore_none=True))
def get_pit_financials(fields, quarter=None, interval=None, order_book_ids=None, if_adjusted='all'):
    if quarter is None:
        valid = True
    else:
        valid = isinstance(quarter, six.string_types) and quarter[-2] == 'q'
        if valid:
            try:
                valid = 1990 <= int(quarter[:-2]) <= 2050 and 1 <= int(quarter[-1]) <= 4
            except ValueError:
                valid = False
    if not valid:
        raise RQInvalidArgument(
            _(u"function {}: invalid {} argument, quarter should be in form of '2012q3', "
              u"got {} (type: {})").format(
                'get_pit_financials', 'quarter', quarter, type(quarter)
            ))

    env = Environment.get_instance()
    dt = env.calendar_dt.date()
    year = dt.year
    mon = dt.month
    day = dt.day
    int_date = year * 10000 + mon * 100 + day
    q = (mon - 4) // 3 + 1
    y = year
    if q <= 0:
        y -= 1
        q = 4
    default_quarter = str(y) + 'q' + str(q)
    if quarter is None or quarter > default_quarter:
        quarter = default_quarter
    result = rqdatac.get_pit_financials(fields, quarter, interval, order_book_ids, if_adjusted,
                                        max_info_date=int_date, market='cn')
    if result is None:
        return pd.DataFrame()

    if if_adjusted == 'ignore':
        result = result.reset_index().sort_values('info_date')
        result = result.groupby(['order_book_id', 'end_date'], as_index=False).fillna(method='ffill')
        result = result.drop(['info_date', 'if_adjusted'], axis=1)
        result = result.drop_duplicates(['order_book_id', 'end_date'], keep='last')
        result = result.set_index(['order_book_id', 'end_date']).sort_index()
    return result


@export_as_api
@apply_rules(verify_that('statements').is_in(['all', 'latest'], ignore_none=True))
def get_pit_financials_ex(order_book_ids, fields, count, statements='latest'):
    if isinstance(order_book_ids, str):
        order_book_ids = [order_book_ids]
    env = Environment.get_instance()
    dt = env.calendar_dt.date()
    year = dt.year
    mon = dt.month
    q = (mon - 4) // 3 + 1
    y = year
    if q <= 0:
        y -= 1
        q = 4
    end_quarter = str(y) + 'q' + str(q)

    delta_year = count // 4
    start_q = q - count % 4
    if start_q <= 0:
        start_q = 4
        delta_year += 1
    start_quarter = str(y - delta_year) + 'q' + str(start_q)

    result = rqdatac.get_pit_financials_ex(fields=fields, start_quarter=start_quarter, end_quarter=end_quarter,
        order_book_ids=order_book_ids, statements=statements, market='cn')
    return result


@export_as_api
@apply_rules(verify_that('entities').are_valid_query_entities())
def query(*entities):
    return rqdatac.query(*entities)


export_as_api(rqdatac.financials, name='financials')
export_as_api(rqdatac.financials, name='Financials')
export_as_api(rqdatac.fundamentals, name='fundamentals')
export_as_api(rqdatac.Fundamentals, name='Fundamentals')
