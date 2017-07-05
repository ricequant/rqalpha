.. _api-extend-api:

==================
扩展 API
==================

扩展API 是Ricequant从众多的数据源中整理、归纳和维护的众多数据类型的API，RQAlpha中不支持相应数据的获取和查询，如果想要使用扩展API 可以在 `Ricequant <https://www.ricequant.com>`_ 中免费使用。或者联系我们获取全功能支持的机构版。

未来我们可能会考虑以接口和授权的方式来开放数据源的获取，届时Extend API 将可以在RQAlpha中被调用。

您也可以通过按照接口规范来进行 API 的扩展。

get_fundamentals - 查询财务数据
------------------------------------------------------

.. py:function:: get_fundamentals(query, entry_date=None, interval='1d', report_quarter=False)

    获取历史财务数据表格。目前支持中国市场超过400个指标，具体请参考 `财务数据文档 <https://www.ricequant.com/data/fundamentals>`_ 。目前仅支持中国市场。需要注意，一次查询过多股票的财务数据会导致系统运行缓慢。

    :param SQLAlchemyQueryObject query: SQLAlchmey的Query对象。其中可在'query'内填写需要查询的指标，'filter'内填写数据过滤条件。具体可参考 `sqlalchemy's query documentation <http://docs.sqlalchemy.org/en/rel_1_0/orm/tutorial.html#querying>`_ 学习使用更多的方便的查询语句。从数据科学家的观点来看，sqlalchemy的使用比sql更加简单和强大

    :param entry_date: 查询财务数据的基准日期，应早于策略当前日期。默认为策略当前日期前一天。
    :type entry_date: `str` | `datetime.date` | `datetime.datetime` | `pandas.Timestamp`

    :param str interval: 查询财务数据的间隔，默认为'1d'。例如，填写'5y'，则代表从entry_date开始（包括entry_date）回溯5年，返回数据时间以年为间隔。'd' - 天，'m' - 月， 'q' - 季，'y' - 年

    :param bool report_quarter: 是否显示报告期，默认为False，不显示。'Q1' - 一季报，'Q2' - 半年报，'Q3' - 三季报，'Q4' - 年报

    :return: `pandas.DataPanel` 如果查询结果为空，返回空 `pandas.DataFrame` 如果给定间隔为1d, 1m, 1q, 1y，返回 `pandas.DataFrame`

    :example:

    *   获取财务数据中的pe_ration和revenue指标:

    ..  code-block:: python3
        :linenos:

        # 并且通过filter过滤掉得到符合一定范围的pe_ration的结果
        # 最后只拿到按照降序排序之后的前10个
        fundamental_df = get_fundamentals(
             query(
                        fundamentals.income_statement.revenue, fundamentals.eod_derivative_indicator.pe_ratio
                    ).filter(
                        fundamentals.eod_derivative_indicator.pe_ratio > 25
                    ).filter(
                        fundamentals.eod_derivative_indicator.pe_ratio < 30
                    ).order_by(
                        fundamentals.income_statement.revenue.desc()
                    ).limit(
                        10
                    )
            )
        context.stocks = fundamental_df.columns.values
        update_universe(context.stocks)

    *   获取某些指定股票的财务数据:

    ..  code-block:: python3
        :linenos:

        def init(context):
            context.stocks = industry('A01')
            logger.info("industry stocks: " + str(context.stocks))

            #每个表都有一个stockcode在用来方便通过股票代码来过滤掉查询的数据，比如次数是只查询'A01'板块的revenue 和 pe_ratio
            context.fundamental_df = get_fundamentals(
                query(
                    fundamentals.income_statement.revenue,      fundamentals.eod_derivative_indicator.pe_ratio
                ).filter(
                    fundamentals.eod_derivative_indicator.pe_ratio > 5
                ).filter(
                    fundamentals.eod_derivative_indicator.pe_ratio < 300
                ).filter(
                    fundamentals.income_statement.stockcode.in_(context.stocks)
                    )
            )
            logger.info(context.fundamental_df)
            update_universe(context.fundamental_df.columns.values)

get_price - 合约历史数据
------------------------------------------------------

.. py:function:: get_price(order_book_id, start_date, end_date=None, frequency='1d', fields=None, adjust_type='pre', skip_suspended=False)

    获取指定合约或合约列表的历史行情（包含起止日期，日线或分钟线），不能在'handle_bar'函数中进行调用。

    注意，这一函数主要是为满足在研究平台编写策略习惯而引入。在编写策略中，使用history_bars进行数据获取会更方便。

    :param order_book_id: 合约代码，合约代码，可传入order_book_id, order_book_id list, symbol, symbol list
    :type order_book_id: `str` | list[`str`]

    :param start_date: 开始日期，用户必须指定
    :type start_date: `str` | `datetime.date` | `datetime.datetime` | `pandas.Timestamp`

    :param end_date: 结束日期，默认为策略当前日期前一天
    :type end_date: `str` | `datetime.date` | `datetime.datetime` | `pandas.Timestamp`

    :param str frequency: 历史数据的频率。 现在支持日/分钟级别的历史数据，默认为'1d'。使用者可自由选取不同频率，例如'5m'代表5分钟线

    :param str adjust_type: 权息修复方案。前复权 - pre，后复权 - post，不复权 - none，回测使用 - internal 需要注意，internal数据与回测所使用数据保持一致，仅就拆分事件对价格以及成交量进行了前复权处理，并未考虑分红派息对于股价的影响。所以在分红前后，价格会出现跳跃

    :param bool skip_suspended: 是否跳过停牌数据。默认为False，不跳过，用停牌前数据进行补齐。True则为跳过停牌期。注意，当设置为True时，函数order_book_id只支持单个合约传入

    :return: `pandas.Panel` | `pandas.DataFrame` | `pandas.Series`

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

get_dominant_future - 期货主力合约
------------------------------------------------------

.. py:function:: get_dominant_future(underlying_symbol)

    获取某一期货品种策略当前日期的主力合约代码。 合约首次上市时，以当日收盘同品种持仓量最大者作为从第二个交易日开始的主力合约。当同品种其他合约持仓量在收盘后超过当前主力合约1.1倍时，从第二个交易日开始进行主力合约的切换。日内不会进行主力合约的切换。

    :param str underlying_symbol: 期货合约品种，例如沪深300股指期货为'IF'

    :example:

    获取某一天的主力合约代码（策略当前日期是20160801）:

    ..  code-block:: python3
        :linenos:

        get_dominant_future('IF')
        #[Out]
        #'IF1608'

get_securities_margin - 融资融券信息
------------------------------------------------------

.. py:function:: get_securities_margin(order_book_id, count=1, fields=None)

    获取融资融券信息。包括 `深证融资融券数据 <http://www.szse.cn/main/disclosure/rzrqxx/rzrqjy/>`_ 以及 `上证融资融券数据 <http://www.sse.com.cn/market/othersdata/margin/detail/>`_ 情况。既包括个股数据，也包括市场整体数据。需要注意，融资融券的开始日期为2010年3月31日。

    :param order_book_id: 可输入order_book_id, order_book_id list, symbol, symbol list。另外，输入'XSHG'或'sh'代表整个上证整体情况；'XSHE'或'sz'代表深证整体情况
    :type order_book_id: `str` | list[`str`]

    :param int count: 回溯获取的数据个数。默认为当前能够获取到的最近的数据

    :param str fields: 默认为所有字段。见下方列表

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

    :return:

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

get_shares - 流通股信息
------------------------------------------------------

.. py:function:: get_shares(order_book_id, count=1, fields=None)

    :param str order_book_id: 可输入order_book_id或symbol

    :param int count: 回溯获取的数据个数。默认为当前能够获取到的最近的数据

    :param str fields: 默认为所有字段。见下方列表

    =========================   ===================================================
    fields                      字段名
    =========================   ===================================================
    total                       总股本
    circulation_a               流通A股
    management_circulation      已流通高管持股
    non_circulation_a           非流通A股合计
    total_a                     A股总股本
    =========================   ===================================================

    :return: `pandas.DateFrame` 查询时间段内某个股票的流通情况。 当fields指定为单一字段的情况时返回 `pandas.Series`

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

get_turnover_rate - 历史换手率
------------------------------------------------------

.. py:function:: get_turnover_rate(order_book_id, count=1, fields=None)

    :param order_book_id: 可输入order_book_id, order_book_id list, symbol, symbol list
    :type order_book_id: `str` | list[`str`]

    :param int count: 回溯获取的数据个数。默认为当前能够获取到的最近的数据

    :param str fields: 默认为所有字段。见下方列表

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

    :return:

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

index_components - 指数成分股
------------------------------------------------------

.. py:function:: index_components(order_book_id, date=None)

    获取某一指数的股票构成列表，也支持指数的历史构成查询。

    :param str order_book_id: 指数代码，可传入order_book_id

    :param date: 查询日期，默认为策略当前日期。如指定，则应保证该日期不晚于策略当前日期
    :type date: `str` | `date` | `datetime` | `pandas.Timestamp`

    :return: list[`order_book_id`] 构成该指数股票

    :example:

    得到上证指数在策略当前日期的构成股票的列表:

    ..  code-block:: python3
        :linenos:

        index_components('000001.XSHG')
        #[Out]['600000.XSHG', '600004.XSHG', ...]

get_dividend - 分红数据
------------------------------------------------------

.. py:function:: get_dividend(order_book_id, start_date)

    获取某只股票到策略当前日期前一天的分红情况（包含起止日期，并且进行了 `前复权处理 <https://www.ricequant.com/api/python/chn#datasources-preprocessing>`_ ）。

    :param str order_book_id: 可输入order_book_id或symbol

    :param date: 查询日期，默认为策略当前日期。如指定，则应保证该日期不晚于策略当前日期
    :type date: `str` | `date` | `datetime` | `pandas.Timestamp`

    :return: `numpy.ndarray` - 查询时间段内某个股票的分红数据

        *   declaration_announcement_date: 分红宣布日，上市公司一般会提前一段时间公布未来的分红派息事件
        *   book_closure_date: 股权登记日
        *   dividend_cash_before_tax: 税前分红
        *   ex_dividend_date: 除权除息日，该天股票的价格会因为分红而进行调整
        *   payable_date: 分红到帐日，这一天最终分红的现金会到账
        *   round_lot: 分红最小单位，例如：10代表每10股派发dividend_cash_before_tax单位的税前现金

    :example:

    获取平安银行2013-01-04 到策略当前日期前一天的分红数据:

    ..  code-block:: python3
        :linenos:

        get_dividend('000001.XSHE', start_date='20130104')
        #[Out]
        #array([(20130614, 20130619, 20130620, 20130620,  1.7 , 10),
        #       (20140606, 20140611, 20140612, 20140612,  1.6 , 10),
        #       (20150407, 20150410, 20150413, 20150413,  1.74, 10),
        #       (20160608, 20160615, 20160616, 20160616,  1.53, 10)],
        #      dtype=[('announcement_date', '<u4'), ('book_closure_date', '<u4'), ('ex_dividend_date', '<u4'), ('payable_date', '<u4'), ('dividend_cash_before_tax', '<f8'), ('round_lot', '<u4')])


get_split - 拆分数据
------------------------------------------------------

.. py:function:: get_split(order_book_id,  start_date)

    获取某只股票到策略当前日期前一天的拆分情况（包含起止日期）。

    :param str order_book_id: 证券代码，证券的独特的标识符，例如：'000001.XSHE'

    :param start_date: 开始日期，用户必须指定，需要早于策略当前日期
    :type start_date: `str` | `date` | `datetime` | `pandas.Timestamp`

    :return: `pandas.DataFrame` - 查询时间段内的某个股票的拆分数据

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

分级基金数据
------------------------------------------------------

.. py:function:: fenji.get_a_by_yield(current_yield, listing=True)

    通过传入当前的本期利率拿到对应的分级A的order_book_id list

    :param float current_yield: 本期利率，用户必须指定

    :param bool listing: 默认为True，该分级基金是否在交易所可交易

    :return: 符合当前利率水平的分级A基金的order_book_id list；如果无符合内容，则返回空列表。

    :example:

    拿到当前收益率为4的A基的代码列表:

    ..  code-block:: python3
        :linenos:

        fenji.get_a_by_yield(4)
        #[Out]
        #['150039.XSHE']

.. py:function:: fenji.get_a_by_interest_rule(interest_rule)

    通过传入当前的利率规则拿到对应的分级A的order_book_id list

    :param str interest_rule: 利率规则，例如："+3.5%", "+4%", "=7%", "\*1.4+0.55%", "利差" etc. 您也可以在研究平台使用 :func:`fenji.get_all` 来进行查询所有的组合可能。用户必须填写

    :param bool listing: 该分级基金是否在交易所可交易，默认为True

    :return: 符合当前利率规则的分级A基金的order_book_id list

    :example:

    拿到符合利率规则“+3%”的A基的代码列表:

    ..  code-block:: python3
        :linenos:

        fenji.get_a_by_interest_rule("+3%")
        #[Out]
        #['502011.XSHG', '150215.XSHE', '150181.XSHE', '150269.XSHE', '150173.XSHE', '150217.XSHE', '502027.XSHG', '150255.XSHE', '150257.XSHE', '150237.XSHE', '150100.XSHE', '150177.XSHE', '502017.XSHG', '150279.XSHE', '150271.XSHE', '150051.XSHE', '150245.XSHE', '150233.XSHE', '502004.XSHG', '150200.XSHE', '150205.XSHE', '150184.XSHE', '502049.XSHG', '150207.XSHE', '150313.XSHE', '150243.XSHE', '150239.XSHE', '150273.XSHE', '150227.XSHE', '150076.XSHE', '150203.XSHE', '150209.XSHE', '150259.XSHE', '150315.XSHE', '150283.XSHE', '150241.XSHE', '150229.XSHE', '150307.XSHE', '150186.XSHE', '150231.XSHE', '502024.XSHG', '502007.XSHG', '150305.XSHE', '150018.XSHE', '150309.XSHE', '150311.XSHE', '150235.XSHE', '150143.XSHE', '150249.XSHE', '150329.XSHE', '150251.XSHE', '150169.XSHE', '150357.XSHE', '150194.XSHE', '150179.XSHE', '150164.XSHE', '150192.XSHE', '150171.XSHE', '150022.XSHE', '150275.XSHE', '150092.XSHE', '150277.XSHE']

.. py:function:: fenji.get_all(field_list)

    获取所有分级基金信息

    :param field_list: 希望输出的数据字段名（见下表），默认为所有字段
    :type field_list: list[`str`]

    :return: `pandas.DataFrame` - 分级基金各项数据

    =========================   ===================================================
    fields                      字段名
    =========================   ===================================================
    a_b_propotion               分级A：分级B的比例
    conversion_date             下次定折日
    creation_date               创立日期
    current_yield               本期利率
    expire_date                 到期日，可能为NaN - 即不存在
    fenji_a_order_book_id       A基代码
    fenji_a_symbol              A基名称
    fenji_b_order_book_id       B基代码
    fenji_b_symbol              B基名称
    fenji_mu_orderbook_id       母基代码
    fenji_mu_symbol             母基名称
    interest_rule               利率规则
    next_yield                  下期利率
    track_index_symbol          跟踪指数
    =========================   ===================================================

    :example:

    *   拿到所有的分级基金的信息:

    ..  code-block:: python3
        :linenos:

        fenji.get_all()
        #[Out]
        #a_b_propotion    conversion_date    creation_date    current_yield    expire_date    fenji_a_order_book_id    fenji_a_symbol    fenji_b_order_book_id    fenji_b_symbol    fenji_mu_orderbook_id    fenji_mu_symbol    interest_rule    next_yield    track_index_symbol
        #0    7:3    2016-11-19    2014-05-22    2.5    NaN    161828    永益A    150162.XSHE    永益B    161827    银华永益    +1%    NaN    综合指数
        #1    1:1    2017-01-04    2015-03-17    5    NaN    150213.XSHE    成长A级    150214.XSHE    成长B级    161223    国投成长    +3.5%    5    创业成长
        #2    1:1    2016-12-15    2015-07-01    5.5    NaN    150335.XSHE    军工股A    150336.XSHE    军工股B    161628    融通军工    +4%    5.5    中证军工

    *   拿到只有2个字段的所有分级基金的信息:

    ..  code-block:: python3
        :linenos:

        fenji.get_all(field_list = ['fenji_a_order_book_id', 'current_yield'])
        #[Out]
        #current_yield    fenji_a_order_book_id
        #0    2.5    161828
        #1    5    150213.XSHE
        #2    5.5    150335.XSHE

雪球舆论数据
------------------------------------------------------

.. py:function:: xueqiu.top_stocks(field, date=None, frequency='1d', count=10)

    获取每日、每周或每月的某个指标的雪球数据的股票排名情况以及它的对应的统计数值.

    :param str field: 目前支持的雪球数据统计指标有: 昨日新增评论 - `new_comments`，总评论 - `total_comments`，昨日新增关注者 - `new_followers`，总关注者数目 - `total_followers`，卖出行为 - `sell_actions`，买入行为 - `buy_actions`

    :param date: 查询日期。默认为策略当前日期前一天。如指定，则该日期应早于策略当前日期。注意：我们最早支持的雪球数据只到2015年4月23日，之后的数据我们都会保持更新
    :type date: `str` | `datetime.date` | `datetime.datetime` | `pandas.Timestamp`

    :param str frequency: 默认是1d，即每日的数据统计。也支持每周 - 1w和每月 - 1M的统计

    :param int count: 指定返回多少个结果，默认是10个

    :return: `pandas.DataFrame` 各项舆情数据

    :example:

    获取前一天的新增留言最多的10支股票:

    ..  code-block:: python3
        :linenos:

        a= xueqiu.top_stocks('new_comments')
        logger.info ("获取按new_comments排序的当天的----------------")
        logger.info (a)

