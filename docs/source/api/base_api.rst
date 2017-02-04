.. _api-base-api:

==================
Base API
==================

基本方法
==================


init
------------------

.. py:function:: init(context)

    【必须实现】

    初始化方法 - 在回测和实时模拟交易只会在启动的时候触发一次。你的算法会使用这个方法来设置你需要的各种初始化配置。 context 对象将会在你的算法的所有其他的方法之间进行传递以方便你可以拿取到。

    :param context: 策略上下文
    :type context: :class:`~StrategyContext` object

    示例如下::

        def init(context):
            # cash_limit的属性是根据用户需求自己定义的，你可以定义无限多种自己随后需要的属性，ricequant的系统默认只是会占用context.portfolio的关键字来调用策略的投资组合信息
            context.cash_limit = 5000

handle_bar
------------------

.. py:function:: handle_bar(context, bar_dict)

    【必须实现】

    bar数据的更新会自动触发该方法的调用。策略具体逻辑可在该方法内实现，包括交易信号的产生、订单的创建等。在实时模拟交易中，该函数在交易时间内会每分钟被触发一次。

    :param context: 策略上下文
    :type context: :class:`~StrategyContext` object

    :param bar_dict: key为order_book_id，value为bar数据。当前合约池内所有合约的bar数据信息都会更新在bar_dict里面
    :type bar_dict: :class:`~BarDict` object

    示例如下::

        def handle_bar(context, bar_dict):
            # put all your algorithm main logic here.
            # ...
            order_shares('000001.XSHE', 500)
            # ...

before_trading
------------------

.. py:function:: before_trading(context)

    【选择实现】

    每天在策略开始交易前会被调用。不能在这个函数中发送订单。需要注意，该函数的触发时间取决于用户当前所订阅合约的交易时间。

    举例来说，如果用户订阅的合约中存在有夜盘交易的期货合约，则该函数可能会在前一日的20:00触发，而不是早晨08:00.

    :param context: 策略上下文
    :type context: :class:`~StrategyContext` object

    示例如下::

        def before_trading(context, bar_dict):
            # 拿取财务数据的逻辑，自己构建SQLAlchemy query
            fundamental_df = get_fundamentals(your_own_query)

            # 把查询到的财务数据保存到conext对象中
            context.fundamental_df = fundamental_df

            # 手动更新股票池
            update_universe(context.fundamental_df.columns.values)

after_trading
------------------

.. py:function:: after_trading(context)

    【选择实现】

    每天在收盘后被调用。不能在这个函数中发送订单。您可以在该函数中进行当日收盘后的一些计算。

    在实时模拟交易中，该函数会在每天15:30触发。

    :param context: 策略上下文
    :type context: :class:`~StrategyContext` object

交易相关函数
=================


order_shares - 指定股数交易（股票专用）
------------------------------------------------------

.. py:function:: order_shares(id_or_ins, amount, style=MarketOrder())

    落指定股数的买/卖单，最常见的落单方式之一。如有需要落单类型当做一个参量传入，如果忽略掉落单类型，那么默认是市价单（market order）。

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]

    :param int amount: 下单量, 正数代表买入，负数代表卖出。将会根据一手xx股来向下调整到一手的倍数，比如中国A股就是调整成100股的倍数。

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :return: :class:`~Order` object

    示例::

        #购买Buy 2000 股的平安银行股票，并以市价单发送：
        order_shares('000001.XSHE', 2000)
        #卖出2000股的平安银行股票，并以市价单发送：
        order_shares('000001.XSHE', -2000)
        #购买1000股的平安银行股票，并以限价单发送，价格为￥10：
        order_shares('000001.XSHG', 1000, style=LimitOrder(10))

order_lots - 指定手数交易（股票专用）
------------------------------------------------------

.. py:function:: order_lots(id_or_ins, amount, style=MarketOrder())


    指定手数发送买/卖单。如有需要落单类型当做一个参量传入，如果忽略掉落单类型，那么默认是市价单（market order）。

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]

    :param int amount: 下单量, 正数代表买入，负数代表卖出。将会根据一手xx股来向下调整到一手的倍数，比如中国A股就是调整成100股的倍数。

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :return: :class:`~Order` object

    示例::

        #买入20手的平安银行股票，并且发送市价单：
        order_lots('000001.XSHE', 20)
        #买入10手平安银行股票，并且发送限价单，价格为￥10：
        order_lots('000001.XSHE', 10, style=LimitOrder(10))

order_value - 指定价值交易（股票专用）
------------------------------------------------------

.. py:function:: order_value(id_or_ins, cash_amount, style=MarketOrder())

    使用想要花费的金钱买入/卖出股票，而不是买入/卖出想要的股数，正数代表买入，负数代表卖出。股票的股数总是会被调整成对应的100的倍数（在A中国A股市场1手是100股）。当您提交一个卖单时，该方法代表的意义是您希望通过卖出该股票套现的金额。如果金额超出了您所持有股票的价值，那么您将卖出所有股票。需要注意，如果资金不足，该API将不会创建发送订单。

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]

    :param float cash_amount: 需要花费现金购买/卖出证券的数目。正数代表买入，负数代表卖出。

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :return: :class:`~Order` object

    示例::

        #买入价值￥10000的平安银行股票，并以市价单发送。如果现在平安银行股票的价格是￥7.5，那么下面的代码会买入1300股的平安银行，因为少于100股的数目将会被自动删除掉：
        order_value('000001.XSHE', 10000)
        #卖出价值￥10000的现在持有的平安银行：
        order_value('000001.XSHE', -10000)

order_percent - 一定比例下单（股票专用）
------------------------------------------------------

.. py:function:: order_percent(id_or_ins, percent, style=MarketOrder())

    发送一个等于目前投资组合价值（市场价值和目前现金的总和）一定百分比的买/卖单，正数代表买，负数代表卖。股票的股数总是会被调整成对应的一手的股票数的倍数（1手是100股）。百分比是一个小数，并且小于或等于1（<=100%），0.5表示的是50%.需要注意，如果资金不足，该API将不会创建发送订单。

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]

    :param float percent: 占有现有的投资组合价值的百分比。正数表示买入，负数表示卖出。

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :return: :class:`~Order` object

    示例::

        #买入等于现有投资组合50%价值的平安银行股票。如果现在平安银行的股价是￥10/股并且现在的投资组合总价值是￥2000，那么将会买入200股的平安银行股票。（不包含交易成本和滑点的损失）：
        order_percent('000001.XSHG', 0.5)

order_target_value - 目标价值下单（股票专用）
------------------------------------------------------

.. py:function:: order_target_value(id_or_ins, cash_amount, style=MarketOrder())

    买入/卖出并且自动调整该证券的仓位到一个目标价值。如果还没有任何该证券的仓位，那么会买入全部目标价值的证券。如果已经有了该证券的仓位，则会买入/卖出调整该证券的现在仓位和目标仓位的价值差值的数目的证券。需要注意，如果资金不足，该API将不会创建发送订单。

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]

    :param float percent: 最终的该证券的仓位目标价值。

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :return: :class:`~Order` object

    示例::

        #如果现在的投资组合中持有价值￥3000的平安银行股票的仓位并且设置其目标价值为￥10000，以下代码范例会发送价值￥7000的平安银行的买单到市场。（向下调整到最接近每手股数即100的倍数的股数）：
        order_target_value('000001.XSHE', 10000)

order_target_percent - 目标比例下单（股票专用）
------------------------------------------------------

.. py:function:: order_target_percent(id_or_ins, percent, style=MarketOrder())

    买入/卖出证券以自动调整该证券的仓位到占有一个指定的投资组合的目标百分比。

    *   如果投资组合中没有任何该证券的仓位，那么会买入等于现在投资组合总价值的目标百分比的数目的证券。
    *   如果投资组合中已经拥有该证券的仓位，那么会买入/卖出目标百分比和现有百分比的差额数目的证券，最终调整该证券的仓位占据投资组合的比例至目标百分比。

    其实我们需要计算一个position_to_adjust (即应该调整的仓位)

    `position_to_adjust = target_position - current_position`

    投资组合价值等于所有已有仓位的价值和剩余现金的总和。买/卖单会被下舍入一手股数（A股是100的倍数）的倍数。目标百分比应该是一个小数，并且最大值应该<=1，比如0.5表示50%。

    如果position_to_adjust 计算之后是正的，那么会买入该证券，否则会卖出该证券。 需要注意，如果资金不足，该API将不会创建发送订单。

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]

    :param float percent: 仓位最终所占投资组合总价值的目标百分比。

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :return: :class:`~Order` object

    示例::

        #如果投资组合中已经有了平安银行股票的仓位，并且占据目前投资组合的10%的价值，那么以下代码会买入平安银行股票最终使其占据投资组合价值的15%：
        order_target_percent('000001.XSHE', 0.15)

buy_open - 买开（期货专用）
------------------------------------------------------

.. py:function:: buy_open(id_or_ins, amount, style=MarketOrder())

    买入开仓。

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]

    :param int amount: 下单手数

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :return: :class:`~Order` object

    示例::

        #以价格为3500的限价单开仓买入2张上期所AG1607合约：
        buy_open('AG1607', amount=2, style=LimitOrder(3500))

sell_close - 平多仓（期货专用）
------------------------------------------------------

.. py:function:: sell_close(id_or_ins, amount, style=MarketOrder())

    平多仓

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]

    :param int amount: 下单手数

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :return: :class:`~Order` object

sell_open - 卖开（期货专用）
------------------------------------------------------

.. py:function:: sell_open(id_or_ins, amount, style=MarketOrder())

    卖出开仓

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]

    :param int amount: 下单手数

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :return: :class:`~Order` object

buy_close - 平空仓（期货专用）
------------------------------------------------------

.. py:function:: buy_close(id_or_ins, amount, style=MarketOrder())

    平空仓

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]

    :param int amount: 下单手数

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :return: :class:`~Order` object

    示例::

        #市价单将现有IF1603空仓买入平仓2张：
        buy_close('IF1603', 2)

cancel_order - 撤单
------------------------------------------------------

.. py:function:: cancel_order(order)

    撤单

    :param order: 需要撤销的order对象
    :type order: :class:`~Order` object

get_open_orders - 拿到未成交订单信息
------------------------------------------------------

.. py:function:: get_open_orders()

    :return: List[:class:`~Order` object]


Context属性
=================

.. py:class:: StrategyContext

    该类用来存储于策略相关的上线文信息。

    .. py:attribute:: now

        使用以上的方式就可以在handle_bar中拿到当前的bar的时间，比如day bar的话就是那天的时间，minute bar的话就是这一分钟的时间点。

        返回数据类型为datetime.datetime

    .. py:attribute:: universe

        在运行 :func:`update_universe`, :func:`subscribe` 或者 :func:`unsubscribe` 的时候，合约池会被更新。

        需要注意，合约池内合约的交易时间（包含股票的策略默认会在股票交易时段触发）是handle_bar被触发的依据。

    .. py:attribute:: run_info

        =========================   =========================   ==============================================================================
        属性                         类型                        注释
        =========================   =========================   ==============================================================================
        run_id                      str                         标识策略每次运行的唯一id
        run_type                    RUN_TYPE                    运行类型
        start_date                  datetime.date               策略的开始日期
        end_date                    datetime.date               策略的结束日期
        frequency                   str                         策略频率，'1d'或'1m'
        stock_starting_cash         float                       股票账户初始资金
        future_starting_cash        float                       期货账户初始资金
        slippage                    float                       滑点水平
        margin_multiplier           float                       保证金倍率
        commission_multiplier       float                       佣金倍率
        benchmark                   str                         基准合约代码
        matching_type               MATCHING_TYPE               撮合方式
        =========================   =========================   ==============================================================================

    .. py:attribute:: portfolio

        该投资组合在单一股票或期货策略中分别为股票投资组合和期货投资组合。在股票+期货的混合策略中代表汇总之后的总投资组合。

        =========================   =========================   ==============================================================================
        属性                         类型                        注释
        =========================   =========================   ==============================================================================
        starting_cash               float                       初始资金，为子组合初始资金的加总
        cash                        float                       可用资金，为子组合可用资金的加总
        total_returns               float                       投资组合至今的累积收益率。计算方法是现在的投资组合价值/投资组合的初始资金
        daily_returns               float                       投资组合每日收益率
        daily_pnl                   float                       当日盈亏，子组合当日盈亏的加总
        market_value                float                       投资组合当前的市场价值，为子组合市场价值的加总
        portfolio_value             float                       总权益，为子组合总权益加总
        pnl                         float                       当前投资组合的累计盈亏
        start_date                  datetime.datetime           策略投资组合的回测/实时模拟交易的开始日期
        annualized_returns          float                       投资组合的年化收益率
        positions                   dict                        一个包含所有仓位的字典，以order_book_id作为键，position对象作为值
        =========================   =========================   ==============================================================================

    .. py:attribute:: stock_portfolio

        获取股票投资组合信息。

        在单独股票类型策略中，内容与portfolio一致，都代表当前投资组合；在期货+股票混合策略中代表股票子组合；在单独期货策略中，不能被访问。

        =========================   =========================   ==============================================================================
        属性                         类型                        注释
        =========================   =========================   ==============================================================================
        starting_cash               float                       回测或实盘交易给算法策略设置的初始资金
        cash                        float                       可用资金
        total_returns               float                       投资组合至今的累积收益率。计算方法是现在的投资组合价值/投资组合的初始资金
        daily_returns               float                       当前最新一天的每日收益
        daily_pnl                   float                       当日盈亏，当日投资组合总权益-昨日投资组合总权益
        market_value                float                       投资组合当前所有证券仓位的市值的加总
        portfolio_value             float                       总权益，包含市场价值和剩余现金
        pnl                         float                       当前投资组合的累计盈亏
        start_date                  datetime.datetime           策略投资组合的回测/实时模拟交易的开始日期
        annualized_returns          float                       投资组合的年化收益率
        positions                   dict                        一个包含所有证券仓位的字典，以order_book_id作为键，position对象作为值
        dividend_receivable         float                       投资组合在分红现金收到账面之前的应收分红部分
        =========================   =========================   ==============================================================================

    .. py:attribute:: future_portfolio

        获取期货投资组合信息。

        在单独期货类型策略中，内容与portfolio一致，都代表当前投资组合；在期货+股票混合策略中代表期货子组合；在单独股票策略中，不能被访问。

        =========================   =========================   ==============================================================================
        属性                         类型                        注释
        =========================   =========================   ==============================================================================
        starting_cash               float                       初始资金
        cash                        float                       可用资金
        frozen_cash                 float                       冻结资金
        total_returns               float                       投资组合至今的累积收益率，当前总权益/初始资金
        daily_returns               float                       当日收益率 = 当日收益 / 昨日总权益
        market_value                float                       投资组合当前所有期货仓位的名义市值的加总
        pnl                         float                       累计盈亏，当前投资组合总权益-初始资金
        daily_pnl                   float                       当日盈亏，当日浮动盈亏 + 当日平仓盈亏 - 当日费用
        daily_holding_pnl           float                       当日浮动盈亏
        daily_realized_pnl          float                       当日平仓盈亏
        portfolio_value             float                       总权益，昨日总权益+当日盈亏
        transaction_cost            float                       总费用
        start_date                  datetime.datetime           回测开始日期
        annualized_returns          float                       投资组合的年化收益率
        positions                   dict                        一个包含期货仓位的字典，以order_book_id作为键，position对象作为值
        margin                      float                       已占用保证金
        =========================   =========================   ==============================================================================

scheduler定时器
======================================================

scheduler.run_daily - 每天运行
------------------------------------------------------

.. py:function:: scheduler.run_daily(function)

    每日运行一次指定的函数，只能在init内使用。

    注意，schedule一定在其对应时间点的handle_bar之后执行。

    :param func function: 使传入的function每日运行。注意，function函数一定要包含（并且只能包含）context, bar_dict两个输入参数

    以下的范例代码片段是一个非常简单的例子，在每天交易后查询现在portfolio中剩下的cash的情况::

        #scheduler调用的函数需要包括context, bar_dict两个输入参数
        def log_cash(context, bar_dict):
            logger.info("Remaning cash: %r" % context.portfolio.cash)

        def init(context):
            #...
            # 每天运行一次
            scheduler.run_daily(log_cash)

scheduler.run_weekly - 每周运行
------------------------------------------------------

.. py:function:: scheduler.run_weekly(function, weekday=x, tradingday=t)

    每周运行一次指定的函数，只能在init内使用。

    注意：

    *   tradingday中的负数表示倒数。
    *   tradingday表示交易日。如某周只有四个交易日，则此周的tradingday=4与tradingday=-1表示同一天。
    *   weekday和tradingday不能同时使用。

    :param func function: 使传入的function每日交易开始前运行。注意，function函数一定要包含（并且只能包含）context, bar_dict两个输入参数。

    :param int weekday: 1~5 分别代表周一至周五，用户必须指定

    :param int tradingday: 范围为[-5,1],[1,5] 例如，1代表每周第一个交易日，-1代表每周倒数第一个交易日，用户可以不填写。

    以下的代码片段非常简单，在每周二固定运行打印一下现在的portfolio剩余的资金::

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

.. py:function:: scheduler.run_monthly(function, tradingday=t)

    每月运行一次指定的函数，只能在init内使用。

    注意:

    *   tradingday的负数表示倒数。
    *   tradingday表示交易日，如某月只有三个交易日，则此月的tradingday=3与tradingday=-1表示同一。

    :param func function: 使传入的function每日交易开始前运行。注意，function函数一定要包含（并且只能包含）context, bar_dict两个输入参数。

    :param int tradingday: 范围为[-23,1], [1,23] ，例如，1代表每月第一个交易日，-1代表每月倒数第一个交易日，用户必须指定。

    以下的代码片段非常简单的展示了每个月第一个交易日的时候我们进行一次财务数据查询，这样子会非常有用在一些根据财务数据来自动调节仓位股票组合的算法来说::

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

    :param str time_rule: 定时具体几点几分运行某个函数。time_rule='before_trading' 表示开始交易前运行；market_open(hour=x, minute=y)表示A股市场开市后x小时y分钟运行，market_close(hour=x, minute=y)表示A股市场收市前x小时y分钟运行。如果不设置time_rule默认的值是中国A股市场开市后一分钟运行。

    market_open, market_close参数如下：

    =========================   =========================   ==============================================================================
    参数                         类型                        注释
    =========================   =========================   ==============================================================================
    hour                        int - option [1,4]          具体在market_open/market_close后/前第多少小时执行, 股票的交易时间为[9:31 - 11:30],[13:01 - 15:00]共240分钟，所以hour的范围为 [1,4]
    minute                      int - option [1,240]        具体在market_open/market_close的后/前第多少分钟执行,同上，股票每天交易时间240分钟，所以minute的范围为 [1,240],中午休市的时间区间会被忽略。    
    =========================   =========================   ==============================================================================

    示例:

    *   每天的开市后10分钟运行::

            scheduler.run_daily(function, time_rule=market_open(minute=10))

    *   每周的第t个交易日闭市前1小时运行::

            scheduler.run_weekly(function, tradingday=t, time_rule=market_close(hour=1))

    *   每月的第t个交易日开市后1小时运行::

            scheduler.run_monthly(function, tradingday=t, time_rule=market_open(hour=1))

    *   每天开始交易前运行::

            scheduler.run_daily(function, time_rule='before_trading')

数据查询相关函数
======================================================

all_instruments - 所有合约基础信息
------------------------------------------------------

.. py:function:: all_instruments(type=None)

    获取某个国家市场的所有合约信息。使用者可以通过这一方法很快地对合约信息有一个快速了解，目前仅支持中国市场。

    :param str type: 需要查询合约类型，例如：type='CS'代表股票。默认是所有类型

    :return: `pandas DataFrame` 所有合约的基本信息。

    其中type参数传入的合约类型和对应的解释如下：

    =========================   ===================================================
    合约类型                      说明
    =========================   ===================================================
    CS                          Common Stock, 即股票
    ETF                         Exchange Traded Fund, 即交易所交易基金
    LOF                         Listed Open-Ended Fund，即上市型开放式基金
    FenjiMu                     Fenji Mu Fund, 即分级母基金
    FenjiA                      Fenji A Fund, 即分级A类基金
    FenjiB                      Fenji B Funds, 即分级B类基金
    INDX                        Index, 即指数
    Future                      Futures，即期货，包含股指、国债和商品期货
    hour                        int - option [1,4]
    minute                      int - option [1,240]
    =========================   ===================================================

    示例:

    获取中国市场所有分级基金的基础信息::

        [In]all_instruments('FenjiA')
        [Out]
            abbrev_symbol    order_book_id    product    sector_code  symbol
        0    CYGA    150303.XSHE    null    null    华安创业板50A
        1    JY500A    150088.XSHE    null    null    金鹰500A
        2    TD500A    150053.XSHE    null    null    泰达稳健
        3    HS500A    150110.XSHE    null    null    华商500A
        4    QSAJ    150235.XSHE    null    null    鹏华证券A
        ...

instruments - 合约详细信息
------------------------------------------------------

.. py:function:: instruments(order_book_id)

    获取某个国家市场内一个或多个合约的详细信息。目前仅支持中国市场。

    :param order_book_id: 合约代码或者合约代码列表
    :type order_book_id: `str` | List[`str`]

    :return: :class:`~StockInstrument` | :class:`~FutureInstrument`

    目前系统并不支持跨国家市场的同时调用。传入 order_book_id list必须属于同一国家市场，不能混合着中美两个国家市场的order_book_id。

    示例:

    *   获取单一股票合约的详细信息::

            [In]instruments('000001.XSHE')
            [Out]
            Instrument(order_book_id=000001.XSHE, symbol=平安银行, abbrev_symbol=PAYH, listed_date=19910403, de_listed_date=null, board_type=MainBoard, sector_code_name=金融, sector_code=Financials, round_lot=100, exchange=XSHE, special_type=Normal, status=Active)

    *   获取多个股票合约的详细信息::

            [In]instruments(['000001.XSHE', '000024.XSHE'])
            [Out]
            [Instrument(order_book_id=000001.XSHE, symbol=平安银行, abbrev_symbol=PAYH, listed_date=19910403, de_listed_date=null, board_type=MainBoard, sector_code_name=金融, sector_code=Financials, round_lot=100, exchange=XSHE, special_type=Normal, status=Active), Instrument(order_book_id=000024.XSHE, symbol=招商地产, abbrev_symbol=ZSDC, listed_date=19930607, de_listed_date=null, board_type=MainBoard, sector_code_name=金融, sector_code=Financials, round_lot=100, exchange=XSHE, special_type=Normal, status=Active)]

    *   获取合约已上市天数::

            instruments('000001.XSHE').days_from_listed()

    *   获取合约距离到期天数::

            instruments('IF1701').days_to_expire()

history_bars - 某一合约历史数据
------------------------------------------------------

.. py:function:: history_bars(order_book_id, bar_count, frequency, fields)

    获取指定合约的历史行情，同时支持日以及分钟历史数据。不能在init中调用。 注意，该API会自动跳过停牌数据。

    日回测获取分钟历史数据：不支持

    日回测获取日历史数据

    =========================   ===================================================
    调用时间                      返回数据
    =========================   ===================================================
    T日before_trading            T-1日day bar
    T日handle_bar                T日day bar
    =========================   ===================================================

    分钟回测获取日历史数据

    =========================   ===================================================
    调用时间                      返回数据
    =========================   ===================================================
    T日before_trading            T-1日day bar
    T日handle_bar                T-1日day bar
    =========================   ===================================================

    分钟回测获取分钟历史数据

    =========================   ===================================================
    调用时间                      返回数据
    =========================   ===================================================
    T日before_trading            T-1日最后一个minute bar
    T日handle_bar                T日当前minute bar
    =========================   ===================================================

    :param order_book_id: 合约代码或者合约代码列表
    :type order_book_id: `str` | List[`str`]

    :param int bar_count: 获取的历史数据数量，必填项

    :param str frequency: 获取数据什么样的频率进行。'1d'或'1m'分别表示每日和每分钟，必填项

    :param str fields: 返回数据字段。必填项。见下方列表。

    =========================   ===================================================
    fields                      字段名
    =========================   ===================================================
    datetime                    时间戳
    open                        开盘价
    high                        最高价
    low                         最低价
    close                       收盘价
    volume                      成交量
    total_turnover              成交额
    datetime                    int类型时间戳
    open_interest               持仓量（期货专用）
    basis_spread                期现差（股指期货专用）
    settlement                  结算价（期货日线专用）
    prev_settlement             结算价（期货日线专用）
    =========================   ===================================================

    :return: `ndarray`, 方便直接与talib等计算库对接，效率较history返回的DataFrame更高。

    示例:

    获取最近5天的日线收盘价序列（策略当前日期为20160706）::

        [In]
        logger.info(history_bars('000002.XSHE', 5, '1d', 'close'))
        [Out]
        [ 8.69  8.7   8.71  8.81  8.81]

current_snapshot - 当前快照数据
------------------------------------------------------

.. py:function:: current_snapshot(order_book_id)

    获得当前市场快照数据。只能在日内交易阶段调用，获取当日调用时点的市场快照数据。市场快照数据记录了每日从开盘到当前的数据信息，可以理解为一个动态的day bar数据。在目前分钟回测中，快照数据为当日所有分钟线累积而成，一般情况下，最后一个分钟线获取到的快照数据应当与当日的日线行情保持一致。需要注意，在实盘模拟中，该函数返回的是调用当时的市场快照情况，所以在同一个handle_bar中不同时点调用可能返回的数据不同。如果当日截止到调用时候对应股票没有任何成交，那么snapshot中的close, high, low, last几个价格水平都将以0表示。

    :param str order_book_id: 合约代码或简称

    :return: :class:`~Snapshot`

    示例：

    在handle_bar中调用该函数，假设策略当前时间是20160104 09:33::

        [In]
        logger.info(current_snapshot('000001.XSHE'))
        [Out]
        2016-01-04 09:33:00.00  INFO
        Snapshot(order_book_id: '000001.XSHE', datetime: datetime.datetime(2016, 1, 4, 9, 33), open: 10.0, high: 10.025, low: 9.9667, last: 9.9917, volume: 2050320, total_turnover: 20485195, prev_close: 9.99)

get_future_contracts - 期货可交易合约列表
------------------------------------------------------

.. py:function:: get_future_contracts(underlying_symbol)

    获取某一期货品种在策略当前日期的可交易合约order_book_id列表。按照到期月份，下标从小到大排列，返回列表中第一个合约对应的就是该品种的近月合约。

    :param str underlying_symbol: 期货合约品种，例如沪深300股指期货为'IF'

    :return: list[`str`]

    示例:

    获取某一天的主力合约代码（策略当前日期是20161201）::

        [In]
        logger.info(get_future_contracts('IF'))
        [Out]
        ['IF1612', 'IF1701', 'IF1703', 'IF1706']

get_trading_dates - 交易日列表
------------------------------------------------------

.. py:function:: get_trading_dates(start_date, end_date)

    获取某个国家市场的交易日列表（起止日期加入判断）。目前仅支持中国市场。

    :param start_date: 开始日期
    :type start_date: `str` | `date` | `datetime` | `pandas.Timestamp`

    :param end_date: 结束如期
    :type end_date: `str` | `date` | `datetime` | `pandas.Timestamp`

    :return: list[`datetime.date`]

    示例::

        [In]get_trading_dates(start_date='2016-05-05', end_date='20160505')
        [Out]
        [datetime.date(2016, 5, 5)]

get_previous_trading_date - 上一交易日
------------------------------------------------------

.. py:function:: get_previous_trading_date(date)

    获取指定日期的上一交易日。

    :param date: 指定日期
    :type date: `str` | `date` | `datetime` | `pandas.Timestamp`

    :return: `datetime.date`

    示例::

        [In]get_previous_trading_date(date='2016-05-02')
        [Out]
        [datetime.date(2016, 4, 29)]

get_next_trading_date - 下一交易日
------------------------------------------------------

.. py:function:: get_next_trading_date(date)

    获取指定日期的下一交易日

    :param date: 指定日期
    :type date: `str` | `date` | `datetime` | `pandas.Timestamp`

    :return: `datetime.date`

    示例::

        [In]get_next_trading_date(date='2016-05-01')
        [Out]
        [datetime.date(2016, 5, 3)]

get_yield_curve - 收益率曲线
------------------------------------------------------

.. py:function:: get_yield_curve(date=None, tenor=None)

    获取某个国家市场指定日期的收益率曲线水平。

    数据为2002年至今的中债国债收益率曲线，来源于中央国债登记结算有限责任公司。

    :param date: 查询日期，默认为策略当前日期前一天
    :type date: `str` | `date` | `datetime` | `pandas.Timestamp`

    :param str tenor: 标准期限，'0S' - 隔夜，'1M' - 1个月，'1Y' - 1年，默认为全部期限

    :return: `pandas.DataFrame` - 查询时间段内无风险收益率曲线

    示例::

        [In]
        get_yield_curve('20130104')

        [Out]
                        0S      1M      2M      3M      6M      9M      1Y      2Y  \
        2013-01-04  0.0196  0.0253  0.0288  0.0279  0.0280  0.0283  0.0292  0.0310

                        3Y      4Y   ...        6Y      7Y      8Y      9Y     10Y  \
        2013-01-04  0.0314  0.0318   ...    0.0342  0.0350  0.0353  0.0357  0.0361
        ...

is_suspended - 全天停牌判断
------------------------------------------------------

.. py:function:: is_suspended(order_book_id, count)

    判断某只股票是否全天停牌。

    :param str order_book_id: 某只股票的代码或股票代码列表，可传入单只股票的order_book_id, symbol

    :param int count: 回溯获取的数据个数。默认为当前能够获取到的最近的数据

    :return: count为1时 `bool`; count>1时 `pandas.DataFrame`

is_st_stock - ST股判断
------------------------------------------------------

.. py:function:: is_st_stock(order_book_id, count=1)

    判断一只或多只股票在一段时间内是否为ST股（包括ST与*ST）。

    ST股是有退市风险因此风险比较大的股票，很多时候您也会希望判断自己使用的股票是否是'ST'股来避开这些风险大的股票。另外，我们目前的策略比赛也禁止了使用'ST'股。

    :param str order_book_id: 某只股票的代码或股票代码列表，可传入单只股票的order_book_id, symbol

    :param int count: 回溯获取的数据个数。默认为当前能够获取到的最近的数据

    :return: count为1时 `bool`; count>1时 `pandas.DataFrame`

其他方法
======================================================

update_universe
------------------------------------------------------

.. py:function:: update_universe(id_or_ins)

    该方法用于更新现在关注的证券的集合（e.g.：股票池）。PS：会在下一个bar事件触发时候产生（新的关注的股票池更新）效果。并且update_universe会是覆盖（overwrite）的操作而不是在已有的股票池的基础上进行增量添加。比如已有的股票池为['000001.XSHE', '000024.XSHE']然后调用了update_universe(['000030.XSHE'])之后，股票池就会变成000030.XSHE一个股票了，随后的数据更新也只会跟踪000030.XSHE这一个股票了。

    :param id_or_ins: 标的物
    :type id_or_ins: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]

.. py:function:: subscribe(id_or_ins)

    订阅合约行情。该操作会导致合约池内合约的增加，从而影响handle_bar中处理bar数据的数量。

    需要注意，用户在初次编写策略时候需要首先订阅合约行情，否则handle_bar不会被触发。

    :param id_or_ins: 标的物
    :type id_or_ins: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]

.. py:function:: unsubscribe(id_or_ins)

    取消订阅合约行情。取消订阅会导致合约池内合约的减少，如果当前合约池中没有任何合约，则策略直接退出。

    :param id_or_ins: 标的物
    :type id_or_ins: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]

类
======================================================

Bar
------------------------------------------------------

.. py:class:: Bar
    
    .. py:attribute:: order_book_id

        【str】交易标的代码

    .. py:attribute:: symbol

        【str】合约简称

    .. py:attribute:: datetime

        【datetime.datetime】 时间戳

    .. py:attribute:: open

        【float】开盘价

    .. py:attribute:: close

        【float】收盘价

    .. py:attribute:: high

        【float】最高价

    .. py:attribute:: low

        【float】最低价

    .. py:attribute:: volume

        【float】成交量

    .. py:attribute:: total_turnover

        【float】成交额

    .. py:attribute:: prev_close

        【float】昨日收盘价

    .. py:attribute:: limit_up

        【float】涨停价

    .. py:attribute:: limit_down

        【float】跌停价

    .. py:attribute:: is_nan

        【bool】当前bar数据是否有行情。例如，获取已经到期的合约数据，is_nan此时为True

    .. py:attribute:: suspended

        【bool】是否全天停牌

    .. py:attribute:: prev_settlement

        【float】昨结算（期货日线数据专用）

    .. py:attribute:: settlement

        【float】结算（期货日线数据专用）

Snapshot
------------------------------------------------------

.. py:class:: Snapshot

    .. py:attribute:: order_book_id
        
        【str】股票代码

    .. py:attribute:: datetime
        
        【datetime.datetime】当前快照数据的时间戳

    .. py:attribute:: open
        
        【float】当日开盘价

    .. py:attribute:: last
        
        【float】当前最新价

    .. py:attribute:: high
        
        【float】截止到当前的最高价

    .. py:attribute:: low
        
        【float】截止到当前的最低价

    .. py:attribute:: prev_close
        
        【float】昨日收盘价

    .. py:attribute:: volume
        
        【float】截止到当前的成交量

    .. py:attribute:: total_turnover
        
        【float】截止到当前的成交额

    .. py:attribute:: open_interest
        
        【float】截止到当前的持仓量（期货专用）

    .. py:attribute:: prev_settlement
        
        【float】昨日结算价（期货专用）

Order
------------------------------------------------------

.. py:class:: Order

    .. py:attribute:: order_id

        【int】唯一标识订单的id

    .. py:attribute:: order_book_id

        【str】合约代码

    .. py:attribute:: datetime

        【datetime.datetime】订单创建时间

    .. py:attribute:: side

        【SIDE】订单方向

    .. py:attribute:: price

        【float】订单价格，只有在订单类型为'限价单'的时候才有意义

    .. py:attribute:: quantity

        【int】订单数量

    .. py:attribute:: filled_quantity

        【int】订单已成交数量

    .. py:attribute:: unfilled_quantity

        【int】订单未成交数量

    .. py:attribute:: type

        【ORDER_TYPE】订单类型

    .. py:attribute:: transaction_cost

        【float】费用

    .. py:attribute:: avg_price

        【float】成交均价

    .. py:attribute:: status

        【ORDER_STATUS】订单状态

    .. py:attribute:: message

        【str】信息。比如拒单时候此处会提示拒单原因

    .. py:attribute:: trading_datetime

        【datetime.datetime】订单的交易日期（对应期货夜盘）

    .. py:attribute:: position_effect

        【POSITION_EFFECT】订单开平（期货专用）

MixedPortfolio
------------------------------------------------------

.. py:class:: MixedPortfolio

    .. py:attribute:: starting_cash

        【float】初始资金，为子组合初始资金的加总

    .. py:attribute:: cash

        【float】可用资金，为子组合可用资金的加总

    .. py:attribute:: frozen_cash

        【float】冻结资金

    .. py:attribute:: total_returns

        【float】投资组合至今的累积收益率。计算方法是现在的投资组合价值/投资组合的初始资金

    .. py:attribute:: daily_returns

        【float】投资组合每日收益率

    .. py:attribute:: daily_pnl

        【float】当日盈亏，子组合当日盈亏的加总

    .. py:attribute:: market_value

        【float】投资组合当前的市场价值，为子组合市场价值的加总

    .. py:attribute:: portfolio_value

        【float】总权益，为子组合总权益加总

    .. py:attribute:: transaction_cost

        【float】总费用

    .. py:attribute:: pnl

        【float】当前投资组合的累计盈亏

    .. py:attribute:: start_date

        【datetime.datetime】策略投资组合的回测/实时模拟交易的开始日期

    .. py:attribute:: annualized_returns

        【float】投资组合的年化收益率

    .. py:attribute:: positions

        【dict】一个包含所有仓位的字典，以order_book_id作为键，position对象作为值，关于position的更多的信息可以在下面的部分找到。

StockPortfolio
------------------------------------------------------

.. py:class:: StockPortfolio

    .. py:attribute:: starting_cash

        【float】回测或实盘交易给算法策略设置的初始资金
    
    .. py:attribute:: cash

        【float】可用资金
    
    .. py:attribute:: frozen_cash

        【float】冻结资金
    
    .. py:attribute:: total_returns

        【float】投资组合至今的累积收益率。计算方法是现在的投资组合价值/投资组合的初始资金
    
    .. py:attribute:: daily_returns

        【float】当前最新一天的每日收益
    
    .. py:attribute:: daily_pnl

        【float】当日盈亏，当日投资组合总权益-昨日投资组合总权益
    
    .. py:attribute:: market_value

        【float】投资组合当前所有证券仓位的市值的加总
    
    .. py:attribute:: portfolio_value

        【float】总权益，包含市场价值和剩余现金
    
    .. py:attribute:: transaction_cost

        【float】总费用
    
    .. py:attribute:: pnl

        【float】当前投资组合的累计盈亏
    
    .. py:attribute:: start_date

        【datetime.datetime】策略投资组合的回测/实时模拟交易的开始日期
    
    .. py:attribute:: annualized_returns

        【float】投资组合的年化收益率
    
    .. py:attribute:: positions

        【dict】一个包含股票子组合仓位的字典，以order_book_id作为键，position对象作为值，关于position的更多的信息可以在下面的部分找到。
    
    .. py:attribute:: dividend_receivable

        【float】投资组合在分红现金收到账面之前的应收分红部分。具体细节在分红部分

FuturePortfolio
------------------------------------------------------

.. py:class:: FuturePortfolio

    .. py:attribute:: starting_cash

        【float】初始资金
    
    .. py:attribute:: cash

        【float】可用资金
    
    .. py:attribute:: frozen_cash

        【float】冻结资金
    
    .. py:attribute:: total_returns

        【float】投资组合至今的累积收益率，当前总权益/初始资金
    
    .. py:attribute:: daily_returns

        【float】当日收益率 = 当日收益 / 昨日总权益
    
    .. py:attribute:: market_value

        【float】投资组合当前所有期货仓位的名义市值的加总
    
    .. py:attribute:: daily_pnl

        【float】当日盈亏，当日浮动盈亏 + 当日平仓盈亏 - 当日费用
    
    .. py:attribute:: daily_holding_pnl

        【float】当日浮动盈亏
    
    .. py:attribute:: daily_realized_pnl

        【float】当日平仓盈亏
    
    .. py:attribute:: portfolio_value

        【float】总权益，昨日总权益+当日盈亏
    
    .. py:attribute:: transaction_cost

        【float】总费用
    
    .. py:attribute:: pnl

        【float】累计盈亏，当前投资组合总权益-初始资金
    
    .. py:attribute:: start_date

        【Date】回测开始日期
    
    .. py:attribute:: annualized_returns

        【float】投资组合的年化收益率
    
    .. py:attribute:: positions

        【dict】一个包含期货子组合仓位的字典，以order_book_id作为键，position对象作为值
    
    .. py:attribute:: margin

        【float】已占用保证金
    
    .. py:attribute:: buy_margin

        【float】多头保证金
    
    .. py:attribute:: sell_margin

        【float】空头保证金

StockPosition
------------------------------------------------------

.. py:class:: StockPosition

    .. py:attribute:: order_book_id

        【str】合约代码
    
    .. py:attribute:: quantity

        【int】当前持仓股数
    
    .. py:attribute:: pnl

        【float】持仓累计盈亏
    
    .. py:attribute:: bought_quantity

        【int】该证券的总买入股数，例如：如果你的投资组合并没有任何平安银行的成交，那么平安银行这个股票的仓位就是0
    
    .. py:attribute:: sold_quantity

        【int】该证券的总卖出股数，例如：如果你的投资组合曾经买入过平安银行股票200股并且卖出过100股，那么这个属性会返回100
    
    .. py:attribute:: bought_value

        【float】该证券的总买入的价值，等于每一个该证券的 买入成交价 * 买入股数 总和
    
    .. py:attribute:: sold_value

        【float】该证券的总卖出价值，等于每一个该证券的 卖出成交价 * 卖出股数 总和
    
    .. py:attribute:: total_orders

        【int】该仓位的总订单的次数
    
    .. py:attribute:: total_trades

        【int】该仓位的总成交的次数
    
    .. py:attribute:: sellable

        【int】该仓位可卖出股数。T＋1的市场中sellable = 所有持仓-今日买入的仓位
    
    .. py:attribute:: avg_price

        【float】获得该持仓的买入均价，计算方法为每次买入的数量做加权平均
    
    .. py:attribute:: market_value

        【float】获得该持仓的实时市场价值
    
    .. py:attribute:: value_percent

        【float】获得该持仓的实时市场价值在总投资组合价值中所占比例，取值范围[0, 1]

FuturePosition
------------------------------------------------------

.. py:class:: FuturePosition

    .. py:attribute:: order_book_id

        【str】合约代码

    .. py:attribute:: pnl

        【float】累计盈亏

    .. py:attribute:: daily_pnl

        【float】当日盈亏，当日浮动盈亏+当日平仓盈亏

    .. py:attribute:: daily_holding_pnl

        【float】当日持仓盈亏

    .. py:attribute:: daily_realized_pnl

        【float】当日平仓盈亏

    .. py:attribute:: transaction_cost

        【float】仓位交易费用

    .. py:attribute:: margin

        【float】仓位总保证金

    .. py:attribute:: market_value

        【float】当前仓位的名义价值。如果当前净持仓为空方向持仓，则名义价值为负

    .. py:attribute:: buy_daily_pnl

        【float】多头仓位当日盈亏

    .. py:attribute:: buy_pnl

        【float】多头仓位累计盈亏

    .. py:attribute:: buy_transaction_cost

        【float】多头费用

    .. py:attribute:: closable_buy_quantity

        【float】可平多头持仓

    .. py:attribute:: buy_margin

        【float】多头持仓占用保证金

    .. py:attribute:: buy_today_quantity

        【int】多头今仓

    .. py:attribute:: buy_quantity

        【int】多头持仓

    .. py:attribute:: buy_avg_open_price

        【float】多头开仓均价

    .. py:attribute:: buy_avg_holding_price

        【float】多头持仓均价

    .. py:attribute:: sell_daily_pnl

        【float】空头仓位当日盈亏

    .. py:attribute:: sell_pnl

        【float】空头仓位累计盈亏

    .. py:attribute:: sell_transaction_cost

        【float】空头费用

    .. py:attribute:: closable_sell_quantity

        【int】可平空头持仓

    .. py:attribute:: sell_margin

        【float】空头持仓占用保证金

    .. py:attribute:: sell_today_quantity

        【int】空头今仓

    .. py:attribute:: sell_quantity

        【int】空头持仓

    .. py:attribute:: sell_avg_open_price

        【float】空头开仓均价

    .. py:attribute:: sell_avg_holding_price

        【float】空头持仓均价

StockInstrument
------------------------------------------------------

.. py:class:: StockInstrument

    .. py:attribute:: order_book_id

        【str】证券代码，证券的独特的标识符。应以'.XSHG'或'.XSHE'结尾，前者代表上证，后者代表深证
    
    .. py:attribute:: symbol

        【str】证券的简称，例如'平安银行'
    
    .. py:attribute:: abbrev_symbol

        【str】证券的名称缩写，在中国A股就是股票的拼音缩写。例如：'PAYH'就是平安银行股票的证券名缩写
    
    .. py:attribute:: round_lot

        【int 一手对应多少股，中国A股一手是100股
    
    .. py:attribute:: sector_code

        【str】板块缩写代码，全球通用标准定义
    
    .. py:attribute:: sector_code_name

        【str】以当地语言为标准的板块代码名
    
    .. py:attribute:: industry_code

        【str】国民经济行业分类代码，具体可参考下方“Industry列表”
    
    .. py:attribute:: industry_name

        【str】国民经济行业分类名称
    
    .. py:attribute:: listed_date

        【str】该证券上市日期
    
    .. py:attribute:: de_listed_date

        【str】退市日期
    
    .. py:attribute:: type

        【str】合约类型，目前支持的类型有: 'CS', 'INDX', 'LOF', 'ETF', 'FenjiMu', 'FenjiA', 'FenjiB', 'Future'
    
    .. py:attribute:: concept_names

        【str】概念股分类，例如：'铁路基建'，'基金重仓'等
    
    .. py:attribute:: exchange

        【str】交易所，'XSHE' - 深交所, 'XSHG' - 上交所
    
    .. py:attribute:: board_type

        【str】板块类别，'MainBoard' - 主板,'GEM' - 创业板
    
    .. py:attribute:: status

        【str】合约状态。'Active' - 正常上市, 'Delisted' - 终止上市, 'TemporarySuspended' - 暂停上市, 'PreIPO' - 发行配售期间, 'FailIPO' - 发行失败
    
    .. py:attribute:: special_type

        【str】特别处理状态。'Normal' - 正常上市, 'ST' - ST处理, 'StarST' - *ST代表该股票正在接受退市警告, 'PT' - 代表该股票连续3年收入为负，将被暂停交易, 'Other' - 其他

FutureInstrument
------------------------------------------------------

.. py:class:: FutureInstrument

    .. py:attribute:: order_book_id

        【str】期货代码，期货的独特的标识符（郑商所期货合约数字部分进行了补齐。例如原有代码'ZC609'补齐之后变为'ZC1609'）。主力连续合约UnderlyingSymbol+88，例如'IF88' ；指数连续合约命名规则为UnderlyingSymbol+99
    
    .. py:attribute:: symbol

        【str】期货的简称，例如'沪深1005'
    
    .. py:attribute:: abbrev_symbol

        【str】期货的名称缩写，例如'HS1005'。主力连续合约与指数连续合约都为'null'
    
    .. py:attribute:: round_lot

        【float】期货全部为1.0
    
    .. py:attribute:: listed_date

        【str】期货的上市日期。主力连续合约与指数连续合约都为'0000-00-00'
    
    .. py:attribute:: type

        【str】合约类型，'Future'
    
    .. py:attribute:: contract_multiplier

        【float】合约乘数，例如沪深300股指期货的乘数为300.0
    
    .. py:attribute:: underlying_order_book_id

        【str】合约标的代码，目前除股指期货(IH, IF, IC)之外的期货合约，这一字段全部为'null'
    
    .. py:attribute:: underlying_symbol

        【str】合约标的名称，例如IF1005的合约标的名称为'IF'
    
    .. py:attribute:: maturity_date

        【str】期货到期日。主力连续合约与指数连续合约都为'0000-00-00'
    
    .. py:attribute:: settlement_method

        【str】交割方式，'CashSettlementRequired' - 现金交割, 'PhysicalSettlementRequired' - 实物交割
    
    .. py:attribute:: product

        【str】产品类型，'Index' - 股指期货, 'Commodity' - 商品期货, 'Government' - 国债期货
    
    .. py:attribute:: exchange

        【str】交易所，'DCE' - 大连商品交易所, 'SHFE' - 上海期货交易所，'CFFEX' - 中国金融期货交易所, 'CZCE'- 郑州商品交易所

Instrument对象也支持如下方法：

合约已上市天数。::

    instruments(order_book_id).days_from_listed()

如果合约首次上市交易，天数为0；如果合约尚未上市或已经退市，则天数值为-1

合约距离到期天数。::

    instruments(order_book_id).days_to_expire()

如果策略已经退市，则天数值为-1

枚举常量
======================================================

ORDER_STATUS - 订单状态
------------------------------------------------------

.. py:class:: ORDER_STATUS

    .. py:attribute:: PENDING_NEW

        待报


    .. py:attribute:: ACTIVE

        可撤

    .. py:attribute:: FILLED

        全成

    .. py:attribute:: CANCELLED


        已撤

    .. py:attribute:: REJECTED

        拒单

SIDE - 买卖方向
------------------------------------------------------

.. py:class:: SIDE

    .. py:attribute:: BUY

        买

    .. py:attribute:: SELL

        卖

POSITION_EFFECT - 开平
------------------------------------------------------

.. py:class:: POSITION_EFFECT

    .. py:attribute:: OPEN

        开仓

    .. py:attribute:: CLOSE

        平仓

ORDER_TYPE - 订单类型
------------------------------------------------------

.. py:class:: ORDER_TYPE

    .. py:attribute:: MARKET

        市价单

    .. py:attribute:: LIMIT

        限价单

RUN_TYPE - 策略运行类型
------------------------------------------------------

.. py:class:: RUN_TYPE

    ..  py:attribute:: BACKTEST

        回测

    ..  py:attribute:: PAPER_TRADING

        实盘模拟

MATCHING_TYPE - 撮合方式
------------------------------------------------------

.. py:class:: MATCHING_TYPE

    ..  py:attribute:: CURRENT_BAR_CLOSE

        以当前bar收盘价撮合

    ..  py:attribute:: NEXT_BAR_OPEN

        以下一bar数据开盘价撮合








