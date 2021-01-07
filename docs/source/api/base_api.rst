.. _api-base-api:

==================
基础 API
==================

约定函数
==================


init - 策略初始化
---------------------------

..  py:function:: init(context)

    初始化方法 - 在回测和实时模拟交易只会在启动的时候触发一次。你的算法会使用这个方法来设置你需要的各种初始化配置。 context 对象将会在你的算法的所有其他的方法之间进行传递以方便你可以拿取到。

    :param context: 策略上下文
    :type context: :class:`~rqalpha.core.strategy_context.StrategyContext` object

    :example:

    ..  code-block:: python

        def init(context):
            # cash_limit的属性是根据用户需求自己定义的，你可以定义无限多种自己随后需要的属性，ricequant的系统默认只是会占用context.portfolio的关键字来调用策略的投资组合信息
            context.cash_limit = 5000


handle_bar - k 线数据更新
---------------------------

..  py:function:: handle_bar(context, bar_dict)

    bar数据的更新会自动触发该方法的调用。策略具体逻辑可在该方法内实现，包括交易信号的产生、订单的创建等。
    在实时模拟交易中，该函数在交易时间内会每分钟被触发一次。

    :param context: 策略上下文
    :type context: :class:`~rqalpha.core.strategy_context.StrategyContext` object

    :param bar_dict: key 为 order_book_id，value 为 bar 对象
    :type bar_dict: Dict[:class:`~rqalpha.model.bar.BarObject`]

    :example:

    ..  code-block:: python

        def handle_bar(context, bar_dict):
            # put all your algorithm main logic here.
            # ...
            order_shares('000001.XSHE', 500)
            # ...


handle_tick - 快照数据更新
---------------------------

..  py:function:: handle_tick(context, tick)

    在 tick 级别的策略中，已订阅快照数据的更新会自动触发该方法的调用。策略具体逻辑可在该方法内实现，包括交易信号的产生、订单的创建等。
    若订阅了多个合约，不同合约快照数据的更新会分别触发该方法。

    :param context: 策略上下文
    :type context: :class:`~rqalpha.core.strategy_context.StrategyContext` object

    :param tick: key为order_book_id，value为bar数据。当前合约池内所有合约的bar数据信息都会更新在bar_dict里面
    :type tick: :class:`~rqalpha.model.tick.TickObject` object

    :example:

    ..  code-block:: python

        def handle_bar(context, tick):
            # put all your algorithm main logic here.
            # ...
            order_shares(tick.order_book_id, tick.last)
            # ...


open_auction - 集合竞价
---------------------------

..  py:function:: open_auction(context, bar_dict)

    盘前集合竞价发生时会触发该函数的调用，在该函数内发出的订单会以当日开盘价被撮合。

    :param context: 策略上下文
    :type context: :class:`~rqalpha.core.strategy_context.StrategyContext` object

    :param bar_dict: key 为 order_book_id，value 为 **不完整的** bar 对象，该对象仅有 open, limit_up, limit_down 等字段，没有 close 等字段
    :type bar_dict: Dict[:class:`~rqalpha.model.bar.BarObject`]

    :example:

    ..  code-block:: python

        def open_auction(context, bar_dict):
            # put all your algorithm main logic here.
            # ...
            order_book_id = "000001.XSHE"
            order_shares(order_book_id, bar_dict[order_book_id].open)
            # ...


before_trading - 盘前
---------------------------

..  py:function:: before_trading(context)

    每天在策略开始交易前会被调用。不能在这个函数中发送订单。需要注意，该函数的触发时间取决于用户当前所订阅合约的交易时间。

    举例来说，如果用户订阅的合约中存在有夜盘交易的期货合约，则该函数可能会在前一日的20:00触发，而不是早晨08:00.

    :param context: 策略上下文
    :type context: :class:`~rqalpha.core.strategy_context.StrategyContext` object

    :example:

    ..  code-block:: python

        def before_trading(context, bar_dict):
            logger.info("This is before trading")


after_trading - 盘后
---------------------------

..  py:function:: after_trading(context)

    每天在收盘后被调用。不能在这个函数中发送订单。您可以在该函数中进行当日收盘后的一些计算。

    在实时模拟交易中，该函数会在每天15:30触发。

    :param context: 策略上下文
    :type context: :class:`~rqalpha.core.strategy_context.StrategyContext` object


.. _api-base-api-order-api:

交易接口
=================

..  module:: rqalpha.api

submit_order - 自由参数下单「通用」
------------------------------------------------------

.. autofunction:: submit_order

order - 智能下单「通用」
------------------------------------------------------

.. autofunction:: order

order_to - 智能下单「通用」
------------------------------------------------------

.. autofunction:: order_to

order_shares - 指定股数交易「股票专用」
------------------------------------------------------

..  autofunction:: order_shares


order_lots - 指定手数交易「股票专用」
------------------------------------------------------

..  autofunction:: order_lots


order_value - 指定价值交易「股票专用」
------------------------------------------------------

..  autofunction:: order_value


order_percent - 一定比例下单「股票专用」
------------------------------------------------------

..  autofunction:: order_percent


order_target_value - 目标价值下单「股票专用」
------------------------------------------------------

..  autofunction:: order_target_value


order_target_percent - 目标比例下单「股票专用」
------------------------------------------------------

..  autofunction:: order_target_percent


order_target_portfolio - 批量调仓「股票专用」
------------------------------------------------------

.. autofunction:: order_target_portfolio


buy_open - 买开「期货专用」
------------------------------------------------------

..  autofunction:: buy_open


sell_close - 平买仓「期货专用」
------------------------------------------------------

..  autofunction:: sell_close


sell_open - 卖开「期货专用」
------------------------------------------------------

..  autofunction:: sell_open


buy_close - 平卖仓「期货专用」
------------------------------------------------------

..  autofunction:: buy_close


cancel_order - 撤单
------------------------------------------------------

..  autofunction:: cancel_order


get_open_orders - 获取未成交订单数据
------------------------------------------------------

..  autofunction:: get_open_orders


exercise - 行权
------------------------------------------------------

..  autofunction:: exercise


.. _api-position-api:

持仓查询接口
======================================================

get_position - 获取持仓对象
------------------------------------------------------

.. autofunction:: get_position


get_positions - 获取全部持仓对象
------------------------------------------------------

.. autofunction:: get_positions


数据查询接口
======================================================


all_instruments - 所有合约基础信息
------------------------------------------------------

..  autofunction:: all_instruments


instruments - 合约详细信息
------------------------------------------------------

..  autofunction:: instruments


history_bars - 某一合约历史 bar 数据
------------------------------------------------------

..  autofunction:: history_bars


current_snapshot - 当前快照数据
------------------------------------------------------

..  autofunction:: current_snapshot(order_book_id)


get_trading_dates - 交易日列表
------------------------------------------------------

..  autofunction:: get_trading_dates(start_date, end_date)


get_previous_trading_date - 上一交易日
------------------------------------------------------

..  autofunction:: get_previous_trading_date(date)


get_next_trading_date - 下一交易日
------------------------------------------------------

..  autofunction:: get_next_trading_date(date)


history_ticks - 指定合约的历史 tick 数据
------------------------------------------------------

.. autofunction:: history_ticks


get_yield_curve - 收益率曲线
------------------------------------------------------

..  autofunction:: get_yield_curve(date=None, tenor=None)


industry - 行业股票列表
------------------------------------------------------

.. autofunction:: industry


sector - 板块股票列表
------------------------------------------------------

.. autofunction:: sector


get_dividend - 获取分红数据
------------------------------------------------------

..  autofunction:: get_dividend


is_suspended - 全天停牌判断
------------------------------------------------------

.. autofunction:: is_suspended(order_book_id)


is_st_stock - ST股判断
------------------------------------------------------

.. autofunction:: is_st_stock(order_book_id)


get_future_contracts - 期货可交易合约列表
------------------------------------------------------

..  autofunction:: get_future_contracts(underlying_symbol)


其他接口
======================================================

update_universe - 更新合约池
------------------------------------------------------

..  autofunction:: update_universe


subscribe - 订阅合约
------------------------------------------------------

..  autofunction:: subscribe


unsubscribe - 取消订阅合约
------------------------------------------------------

..  autofunction:: unsubscribe


subscribe_event - 订阅事件
------------------------------------------------------

..  autofunction:: subscribe_event


deposit - 入金（增加账户资金）
------------------------------------------------------

.. autofunction:: deposit


withdraw - 出金（减少账户资金）
------------------------------------------------------

.. autofunction:: withdraw


plot - 画图
------------------------------------------------------

..  autofunction:: plot


scheduler定时器
======================================================

scheduler.run_daily - 每天运行
------------------------------------------------------

..  py:function:: scheduler.run_daily(function)

    每日运行一次指定的函数，只能在init内使用。

    注意，schedule一定在其对应时间点的handle_bar之后执行。

    :param func function: 使传入的function每日运行。注意，function函数一定要包含（并且只能包含）context, bar_dict两个输入参数

    :example:

    以下的范例代码片段是一个非常简单的例子，在每天交易后查询现在portfolio中剩下的cash的情况:

    ..  code-block:: python3
        :linenos:

        #scheduler调用的函数需要包括context, bar_dict两个输入参数
        def log_cash(context, bar_dict):
            logger.info("Remaning cash: %r" % context.portfolio.cash)

        def init(context):
            #...
            # 每天运行一次
            scheduler.run_daily(log_cash)

scheduler.run_weekly - 每周运行
------------------------------------------------------

..  py:function:: scheduler.run_weekly(function, weekday=x, tradingday=t)

    每周运行一次指定的函数，只能在init内使用。

    注意：

    *   tradingday中的负数表示倒数。
    *   tradingday表示交易日。如某周只有四个交易日，则此周的tradingday=4与tradingday=-1表示同一天。
    *   weekday和tradingday不能同时使用。

    :param func function: 使传入的function每日交易开始前运行。注意，function函数一定要包含（并且只能包含）context, bar_dict两个输入参数。

    :param int weekday: 1~5 分别代表周一至周五，用户必须指定

    :param int tradingday: 范围为[-5,1],[1,5] 例如，1代表每周第一个交易日，-1代表每周倒数第一个交易日，用户可以不填写。

    :example:

    以下的代码片段非常简单，在每周二固定运行打印一下现在的portfolio剩余的资金:

    ..  code-block:: python3
        :linenos:

        #scheduler调用的函数需要包括context, bar_dict两个参数
        def log_cash(context, bar_dict):
            logger.info("Remaning cash: %r" % context.portfolio.cash)

        def init(context):
            #...
            # 每周二打印一下剩余资金：
            scheduler.run_weekly(log_cash, weekday=2)
            # 每周第二个交易日打印剩余资金：
            #scheduler.run_weekly(log_cash, tradingday=2)

scheduler.run_monthly - 每月运行
------------------------------------------------------

..  py:function:: scheduler.run_monthly(function, tradingday=t)

    每月运行一次指定的函数，只能在init内使用。

    注意:

    *   tradingday的负数表示倒数。
    *   tradingday表示交易日，如某月只有三个交易日，则此月的tradingday=3与tradingday=-1表示同一。

    :param func function: 使传入的function每日交易开始前运行。注意，function函数一定要包含（并且只能包含）context, bar_dict两个输入参数。

    :param int tradingday: 范围为[-23,1], [1,23] ，例如，1代表每月第一个交易日，-1代表每月倒数第一个交易日，用户必须指定。

    :example:

    以下的代码片段非常简单的展示了每个月第一个交易日的时候我们进行一次财务数据查询，这对根据财务数据来调节股票组合的策略会非常有用:

    ..  code-block:: python3
        :linenos:

        #scheduler调用的函数需要包括context, bar_dict两个参数
        def query_fundamental(context, bar_dict):
                # 查询revenue前十名的公司的股票并且他们的pe_ratio在25和30之间。打fundamentals的时候会有auto-complete方便写查询代码。
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

            # 将查询结果dataframe的fundamental_df存放在context里面以备后面只需：
            context.fundamental_df = fundamental_df

            # 实时打印日志看下查询结果，会有我们精心处理的数据表格显示：
            logger.info(context.fundamental_df)
            update_universe(context.fundamental_df.columns.values)

         # 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
        def init(context):
            # 每月的第一个交易日查询以下财务数据，以确保可以拿到最新更新的财务数据信息用来调整仓位
            scheduler.run_monthly(query_fundamental, tradingday=1)


time_rule - 定时间运行
------------------------------------------------------

    scheduler还可以用来做定时间运行，比如在每天开盘后的一小时后或一分钟后定时运行，这里有很多种组合可以让您达到各种自己想要达到的定时运行的目的。

    使用的方法是和上面的 :func:`scheduler.run_daily` , :func:`scheduler.run_weekly` 和 :func:`scheduler.run_monthly` 进行组合加入time_rule来一起使用。

    注意:

    *   market_open与market_close都跟随中国A股交易时间进行设置，即09:31~15:00。
    *   使用time_rule定时运行只会在分钟级别回测和实时模拟交易中有定义的效果，在日回测中只会默认依然在该天运行，并不能在固定的时间运行。
    *   在分钟回测中如未指定time_rule,则默认在开盘后一分钟运行,即09:31分。
    *   如果两个schedule，分别使用market_open 与market_close规则，但规则触发时间在同一时刻，则market_open的handle一定在market_close的handle前执行。
    *   目前暂不支持开盘交易(即 09:30分交易) ,所以time_rule(minute=0) 和time_rule(hour=0) 将不会触发任何事件。
    *   market_open(minute=120)将在11:30执行， market_open(minute=121)在13:01执行，中午休市的区间会被忽略。
    *   time_rule='before_trading'表示在开市交易前运行scheduler函数。该函数运行时间将在before_trading函数运行完毕之后handle_bar运行之前。

    `time_rule`: 定时具体几点几分运行某个函数。time_rule='before_trading' 表示开始交易前运行；market_open(hour=x, minute=y)表示A股市场开市后x小时y分钟运行，market_close(hour=x, minute=y)表示A股市场收市前x小时y分钟运行。如果不设置time_rule默认的值是中国A股市场开市后一分钟运行。

    market_open, market_close参数如下：

    =========================   =========================   ==============================================================================
    参数                         类型                        注释
    =========================   =========================   ==============================================================================
    hour                        int - option [1,4]          具体在market_open/market_close后/前第多少小时执行, 股票的交易时间为[9:31 - 11:30],[13:01 - 15:00]共240分钟，所以hour的范围为 [1,4]
    minute                      int - option [1,240]        具体在market_open/market_close的后/前第多少分钟执行,同上，股票每天交易时间240分钟，所以minute的范围为 [1,240],中午休市的时间区间会被忽略。
    =========================   =========================   ==============================================================================

    :example:

    *   每天的开市后10分钟运行:

        ..  code-block:: python3
            :linenos:

            scheduler.run_daily(function, time_rule=market_open(minute=10))

    *   每周的第t个交易日闭市前1小时运行:

        ..  code-block:: python3
            :linenos:

            scheduler.run_weekly(function, tradingday=t, time_rule=market_close(hour=1))

    *   每月的第t个交易日开市后1小时运行:

        ..  code-block:: python3
            :linenos:

            scheduler.run_monthly(function, tradingday=t, time_rule=market_open(hour=1))

    *   每天开始交易前运行:

        ..  code-block:: python3
            :linenos:

            scheduler.run_daily(function, time_rule='before_trading')


.. _api-base-types:

类
======================================================

Context - 策略上下文
------------------------------------------------------

..  module:: rqalpha.core.strategy_context

..  autoclass:: StrategyContext
    :members:


RunInfo - 策略运行信息
------------------------------------------------------

..  autoclass:: RunInfo
    :members:


Bar - k 线行情
------------------------------------------------------
..  module:: rqalpha.model.bar

..  autoclass:: BarObject
    :members:
    :show-inheritance:
    :inherited-members:


Tick - 快照行情
------------------------------------------------------
..  module:: rqalpha.model.tick

..  autoclass:: TickObject
    :members:
    :show-inheritance:
    :inherited-members:


Order - 订单
------------------------------------------------------
..  module:: rqalpha.model.order

..  autoclass:: Order
    :members:
    :show-inheritance:
    :inherited-members:


Portfolio - 投资组合
------------------------------------------------------

.. module:: rqalpha.portfolio

.. autoclass:: Portfolio
    :members:
    :show-inheritance:
    :inherited-members:


Account - 账户
------------------------------------------------------

.. module:: rqalpha.portfolio.account

.. autoclass:: Account
    :members:
    :inherited-members:


Position - 持仓
------------------------------------------------------
.. module:: rqalpha.portfolio.position

..  autoclass:: Position
    :members:
    :inherited-members:


Instrument - 交易标的
------------------------------------------------------
..  module:: rqalpha.model.instrument

..  py:class:: Instrument

    ..  py:attribute:: order_book_id

        【str】股票：证券代码，证券的独特的标识符。应以'.XSHG'或'.XSHE'结尾，前者代表上证，后者代表深证。期货：期货代码，期货的独特的标识符（郑商所期货合约数字部分进行了补齐。例如原有代码'ZC609'补齐之后变为'ZC1609'）。主力连续合约UnderlyingSymbol+88，例如'IF88' ；指数连续合约命名规则为UnderlyingSymbol+99

    ..  py:attribute:: symbol

        【str】股票：证券的简称，例如'平安银行'。期货：期货的简称，例如'沪深1005'。

    ..  py:attribute:: abbrev_symbol

        【str】证券的名称缩写，在中国A股就是股票的拼音缩写，例如：'PAYH'就是平安银行股票的证券名缩写；在期货市场中例如'HS1005'，主力连续合约与指数连续合约都为'null'。

    ..  py:attribute:: round_lot

        【int】股票：一手对应多少股，中国A股一手是100股。期货：一律为1。

    ..  py:attribute:: sector_code（股票专用）

        【str】板块缩写代码，全球通用标准定义

    ..  py:attribute:: sector_code_name（股票专用）

        【str】以当地语言为标准的板块代码名

    ..  py:attribute:: industry_code（股票专用）

        【str】国民经济行业分类代码，具体可参考下方“Industry列表”

    ..  py:attribute:: industry_name（股票专用）

        【str】国民经济行业分类名称

    ..  py:attribute:: listed_date

        【str】股票：该证券上市日期。期货：期货的上市日期，主力连续合约与指数连续合约都为'0000-00-00'。

    ..  py:attribute:: de_listed_date

        【str】股票：退市日期。期货：交割日期。

    ..  py:attribute:: type

        【str】合约类型，目前支持的类型有: 'CS', 'INDX', 'LOF', 'ETF', 'Future'

    ..  py:attribute:: concept_names（股票专用）

        【str】概念股分类，例如：'铁路基建'，'基金重仓'等

    ..  py:attribute:: exchange

        【str】交易所。股票：'XSHE' - 深交所, 'XSHG' - 上交所。期货：'DCE' - 大连商品交易所, 'SHFE' - 上海期货交易所，'CFFEX' - 中国金融期货交易所, 'CZCE'- 郑州商品交易所

    ..  py:attribute:: board_type（股票专用）

        【str】板块类别，'MainBoard' - 主板,'GEM' - 创业板

    ..  py:attribute:: status（股票专用）

        【str】合约状态。'Active' - 正常上市, 'Delisted' - 终止上市, 'TemporarySuspended' - 暂停上市, 'PreIPO' - 发行配售期间, 'FailIPO' - 发行失败

    ..  py:attribute:: special_type（股票专用）

        【str】特别处理状态。'Normal' - 正常上市, 'ST' - ST处理, 'StarST' - \*ST代表该股票正在接受退市警告, 'PT' - 代表该股票连续3年收入为负，将被暂停交易, 'Other' - 其他

    ..  py:attribute:: contract_multiplier（期货专用）

        【float】合约乘数，例如沪深300股指期货的乘数为300.0

    ..  py:attribute:: underlying_order_book_id（期货专用）

        【str】合约标的代码，目前除股指期货(IH, IF, IC)之外的期货合约，这一字段全部为'null'

    ..  py:attribute:: underlying_symbol（期货专用）

        【str】合约标的名称，例如IF1005的合约标的名称为'IF'

    ..  py:attribute:: maturity_date（期货专用）

        【str】期货到期日。主力连续合约与指数连续合约都为'0000-00-00'

    ..  py:attribute:: settlement_method（期货专用）

        【str】交割方式，'CashSettlementRequired' - 现金交割, 'PhysicalSettlementRequired' - 实物交割

    ..  py:attribute:: product（期货专用）

        【str】产品类型，'Index' - 股指期货, 'Commodity' - 商品期货, 'Government' - 国债期货

Instrument对象也支持如下方法：

合约已上市天数：

    ..  code-block:: python

        instruments(order_book_id).days_from_listed()

如果合约首次上市交易，天数为0；如果合约尚未上市或已经退市，则天数值为-1

合约距离到期天数：

    ..  code-block:: python

        instruments(order_book_id).days_to_expire()

如果策略已经退市，则天数值为-1

最小价格变动单位：

    .. code-block:: python

        instruments(order_book_id).tick_size()

枚举常量
======================================================

..  module:: rqalpha.const


POSITION_DIRECTION - 持仓方向
------------------------------------------------------

..  py:class::  POSITION_DIRECTION

    .. py:attribute::  LONG

        多方向

    .. py:attribute::  SHORT

        空方向


SIDE - 交易方向
------------------------------------------------------

..  py:class:: SIDE

    ..  py:attribute:: BUY

        买

    ..  py:attribute:: SELL

        卖


POSITION_EFFECT - 交易动作
------------------------------------------------------

..  py:class:: POSITION_EFFECT

    ..  py:attribute:: OPEN

        开仓

    ..  py:attribute:: CLOSE

        平仓

    ..  py:attribute:: CLOSE_TODAY

        平今

    ..  py:attribute:: EXERCISE

        行权

    ..  py:attribute:: MATCH

        轧差


ORDER_TYPE - 订单类型
------------------------------------------------------

..  py:class:: ORDER_TYPE

    ..  py:attribute:: MARKET

        市价单

    ..  py:attribute:: LIMIT

        限价单


ORDER_STATUS - 订单状态
------------------------------------------------------

..  py:class:: ORDER_STATUS

    ..  py:attribute:: PENDING_NEW

        待报

    ..  py:attribute:: ACTIVE

        已报

    ..  py:attribute:: FILLED

        全成

    ..  py:attribute:: CANCELLED

        已撤

    ..  py:attribute:: REJECTED

        拒单


RUN_TYPE - 策略运行类型
------------------------------------------------------

..  py:class:: RUN_TYPE

    ..  py:attribute:: BACKTEST

        回测

    ..  py:attribute:: PAPER_TRADING

        实盘模拟


EVENT - 事件类型
------------------------------------------------------

..  module::  rqalpha.events

.. py:class::  EVENT

    ..  py:attribute:: ORDER_PENDING_NEW

        订单创建成功

    ..  py:attribute:: ORDER_CREATION_PASS

        订单已报

    ..  py:attribute:: ORDER_CREATION_REJECT

        订单创建被拒

    ..  py:attribute:: ORDER_PENDING_CANCEL

        订单待撤

    ..  py:attribute:: ORDER_CANCELLATION_PASS

        订单撤单成功

    ..  py:attribute:: ORDER_CANCELLATION_REJECT

        订单撤单被拒

    ..  py:attribute:: ORDER_UNSOLICITED_UPDATE

        订单已报被拒

    ..  py:attribute:: TRADE

        成交
