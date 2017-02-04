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

    :param amount: 下单量, 正数代表买入，负数代表卖出。将会根据一手xx股来向下调整到一手的倍数，比如中国A股就是调整成100股的倍数。
    :type amount: `number`

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

    :param amount: 下单量, 正数代表买入，负数代表卖出。将会根据一手xx股来向下调整到一手的倍数，比如中国A股就是调整成100股的倍数。
    :type amount: `number`

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

    :param cash_amount: 需要花费现金购买/卖出证券的数目。正数代表买入，负数代表卖出。
    :type cash_amount: `number`

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

    :param percent: 占有现有的投资组合价值的百分比。正数表示买入，负数表示卖出。
    :type percent: `float`

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

    :param percent: 最终的该证券的仓位目标价值。
    :type percent: `float`

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

    :param percent: 仓位最终所占投资组合总价值的目标百分比。
    :type percent: `float`

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

    :param amount: 下单手数
    :type amount: `number`

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

    :param amount: 下单手数
    :type amount: `number`

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :return: :class:`~Order` object

sell_open - 卖开（期货专用）
------------------------------------------------------

.. py:function:: sell_open(id_or_ins, amount, style=MarketOrder())

    卖出开仓

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]

    :param amount: 下单手数
    :type amount: `number`

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :return: :class:`~Order` object

buy_close - 平空仓（期货专用）
------------------------------------------------------

.. py:function:: buy_close(id_or_ins, amount, style=MarketOrder())

    平空仓

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str` | List[:class:`~Instrument`] | List[`str`]

    :param amount: 下单手数
    :type amount: `number`

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
        run_id	                    str	                        标识策略每次运行的唯一id
        run_type	                RUN_TYPE	                运行类型
        start_date	                datetime.date	            策略的开始日期
        end_date	                datetime.date	            策略的结束日期
        frequency	                str	                        策略频率，'1d'或'1m'
        stock_starting_cash	        float	                    股票账户初始资金
        future_starting_cash	    float	                    期货账户初始资金
        slippage	                float	                    滑点水平
        margin_multiplier	        float	                    保证金倍率
        commission_multiplier	    float	                    佣金倍率
        benchmark	                str	                        基准合约代码
        matching_type	            MATCHING_TYPE	            撮合方式
        =========================   =========================   ==============================================================================

    .. py:attribute:: portfolio

        该投资组合在单一股票或期货策略中分别为股票投资组合和期货投资组合。在股票+期货的混合策略中代表汇总之后的总投资组合。

        =========================   =========================   ==============================================================================
        属性                         类型                        注释
        =========================   =========================   ==============================================================================
        starting_cash               float                       初始资金，为子组合初始资金的加总
        cash	                    float	                    可用资金，为子组合可用资金的加总
        total_returns	            float	                    投资组合至今的累积收益率。计算方法是现在的投资组合价值/投资组合的初始资金
        daily_returns	            float                       投资组合每日收益率
        daily_pnl	                float	                    当日盈亏，子组合当日盈亏的加总
        market_value	            float	                    投资组合当前的市场价值，为子组合市场价值的加总
        portfolio_value	            float	                    总权益，为子组合总权益加总
        pnl	                        float	                    当前投资组合的累计盈亏
        start_date	                datetime.datetime	        策略投资组合的回测/实时模拟交易的开始日期
        annualized_returns	        float	                    投资组合的年化收益率
        positions	                dict	                    一个包含所有仓位的字典，以order_book_id作为键，position对象作为值
        =========================   =========================   ==============================================================================

    .. py:attribute:: stock_portfolio

        获取股票投资组合信息。

        在单独股票类型策略中，内容与portfolio一致，都代表当前投资组合；在期货+股票混合策略中代表股票子组合；在单独期货策略中，不能被访问。

        =========================   =========================   ==============================================================================
        属性                         类型                        注释
        =========================   =========================   ==============================================================================
        starting_cash	            float	                    回测或实盘交易给算法策略设置的初始资金
        cash	                    float	                    可用资金
        total_returns	            float	                    投资组合至今的累积收益率。计算方法是现在的投资组合价值/投资组合的初始资金
        daily_returns	            float	                    当前最新一天的每日收益
        daily_pnl	                float	                    当日盈亏，当日投资组合总权益-昨日投资组合总权益
        market_value	            float	                    投资组合当前所有证券仓位的市值的加总
        portfolio_value	            float	                    总权益，包含市场价值和剩余现金
        pnl	                        float                       当前投资组合的累计盈亏
        start_date	                datetime.datetime	        策略投资组合的回测/实时模拟交易的开始日期
        annualized_returns	        float	                    投资组合的年化收益率
        positions	                dict	                    一个包含所有证券仓位的字典，以order_book_id作为键，position对象作为值
        dividend_receivable	        float	                    投资组合在分红现金收到账面之前的应收分红部分
        =========================   =========================   ==============================================================================

    .. py:attribute:: future_portfolio

        获取期货投资组合信息。

        在单独期货类型策略中，内容与portfolio一致，都代表当前投资组合；在期货+股票混合策略中代表期货子组合；在单独股票策略中，不能被访问。

        =========================   =========================   ==============================================================================
        属性                         类型                        注释
        =========================   =========================   ==============================================================================
        starting_cash	            float	                    初始资金
        cash	                    float	                    可用资金
        frozen_cash	                float	                    冻结资金
        total_returns	            float	                    投资组合至今的累积收益率，当前总权益/初始资金
        daily_returns	            float	                    当日收益率 = 当日收益 / 昨日总权益
        market_value	            float	                    投资组合当前所有期货仓位的名义市值的加总
        pnl	                        float	                    累计盈亏，当前投资组合总权益-初始资金
        daily_pnl	                float	                    当日盈亏，当日浮动盈亏 + 当日平仓盈亏 - 当日费用
        daily_holding_pnl	        float	                    当日浮动盈亏
        daily_realized_pnl	        float	                    当日平仓盈亏
        portfolio_value	            float	                    总权益，昨日总权益+当日盈亏
        transaction_cost	        float	                    总费用
        start_date	                datetime.datetime	        回测开始日期
        annualized_returns	        float	                    投资组合的年化收益率
        positions	                dict	                    一个包含期货仓位的字典，以order_book_id作为键，position对象作为值
        margin	                    float	                    已占用保证金
        =========================   =========================   ==============================================================================

其他方法
=================

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

.. py:function:: get_file()




































