.. _intro-examples:

==========================================
策略示例
==========================================

.. _Ricequant: https://www.ricequant.com/algorithms

在下面我们列举一些常用的算法范例，您可以通过RQAlpha运行，也可以直接登录 `Ricequant`_ 在线进行回测或模拟交易。

.. _intro-examples-buy-and-hold:

第一个策略-买入&持有
------------------------------------------------------

万事开头难，这是一个最简单的策略：在回测开始的第一天买入资金量的100%的平安银行并且一直持有。

..  code-block:: python3
    :linenos:

    # 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
    def init(context):
        logger.info("init")
        context.s1 = "000001.XSHE"
        update_universe(context.s1)
        # 是否已发送了order
        context.fired = False
        context.cnt = 1


    def before_trading(context):
        logger.info("Before Trading", context.cnt)
        context.cnt += 1


    # 你选择的证券的数据更新将会触发此段逻辑，例如日或分钟历史数据切片或者是实时数据切片更新
    def handle_bar(context, bar_dict):
        context.cnt += 1
        logger.info("handle_bar", context.cnt)
        # 开始编写你的主要的算法逻辑

        # bar_dict[order_book_id] 可以拿到某个证券的bar信息
        # context.portfolio 可以拿到现在的投资组合状态信息

        # 使用order_shares(id_or_ins, amount)方法进行落单

        # TODO: 开始编写你的算法吧！
        if not context.fired:
            # order_percent并且传入1代表买入该股票并且使其占有投资组合的100%
            order_percent(context.s1, 1)
            context.fired = True

.. _intro-examples-golden-cross:

Golden Cross算法示例
------------------------------------------------------

以下是一个我们使用TALib编写的golden cross算法的示例，使用了simple moving average方法：

..  code-block:: python3
    :linenos:

    import talib


    # 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
    def init(context):
        context.s1 = "000001.XSHE"

        # 设置这个策略当中会用到的参数，在策略中可以随时调用，这个策略使用长短均线，我们在这里设定长线和短线的区间，在调试寻找最佳区间的时候只需要在这里进行数值改动
        context.SHORTPERIOD = 20
        context.LONGPERIOD = 120


    # 你选择的证券的数据更新将会触发此段逻辑，例如日或分钟历史数据切片或者是实时数据切片更新
    def handle_bar(context, bar_dict):
        # 开始编写你的主要的算法逻辑

        # bar_dict[order_book_id] 可以拿到某个证券的bar信息
        # context.portfolio 可以拿到现在的投资组合状态信息

        # 使用order_shares(id_or_ins, amount)方法进行落单

        # TODO: 开始编写你的算法吧！

        # 因为策略需要用到均线，所以需要读取历史数据
        prices = history_bars(context.s1, context.LONGPERIOD+1, '1d', 'close')

        # 使用talib计算长短两根均线，均线以array的格式表达
        short_avg = talib.SMA(prices, context.SHORTPERIOD)
        long_avg = talib.SMA(prices, context.LONGPERIOD)

        plot("short avg", short_avg[-1])
        plot("long avg", long_avg[-1])

        # 获取当前投资组合中股票的仓位
        cur_position = get_position(context.s1).quantity
        # 计算现在portfolio中的现金可以购买多少股票
        shares = context.portfolio.cash/bar_dict[context.s1].close

        # 如果短均线从上往下跌破长均线，也就是在目前的bar短线平均值低于长线平均值，而上一个bar的短线平均值高于长线平均值
        if short_avg[-1] - long_avg[-1] < 0 and short_avg[-2] - long_avg[-2] > 0 and cur_position > 0:
            # 进行清仓
            order_target_value(context.s1, 0)

        # 如果短均线从下往上突破长均线，为入场信号
        if short_avg[-1] - long_avg[-1] > 0 and short_avg[-2] - long_avg[-2] < 0:
            # 满仓入股
            order_shares(context.s1, shares)

单股票 MACD 算法示例
------------------------------------------------------

以下是一个我们使用TALib编写的单股票MACD算法示例，使用了TALib的MACD方法：

..  code-block:: python3
    :linenos:

    import talib


    # 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
    def init(context):
        context.s1 = "000001.XSHE"

        # 使用MACD需要设置长短均线和macd平均线的参数
        context.SHORTPERIOD = 12
        context.LONGPERIOD = 26
        context.SMOOTHPERIOD = 9
        context.OBSERVATION = 100


    # 你选择的证券的数据更新将会触发此段逻辑，例如日或分钟历史数据切片或者是实时数据切片更新
    def handle_bar(context, bar_dict):
        # 开始编写你的主要的算法逻辑

        # bar_dict[order_book_id] 可以拿到某个证券的bar信息
        # context.portfolio 可以拿到现在的投资组合状态信息

        # 使用order_shares(id_or_ins, amount)方法进行落单

        # TODO: 开始编写你的算法吧！

        # 读取历史数据，使用sma方式计算均线准确度和数据长度无关，但是在使用ema方式计算均线时建议将历史数据窗口适当放大，结果会更加准确
        prices = history_bars(context.s1, context.OBSERVATION,'1d','close')

        # 用Talib计算MACD取值，得到三个时间序列数组，分别为macd, signal 和 hist
        macd, signal, hist = talib.MACD(prices, context.SHORTPERIOD,
                                        context.LONGPERIOD, context.SMOOTHPERIOD)

        plot("macd", macd[-1])
        plot("macd signal", signal[-1])

        # macd 是长短均线的差值，signal是macd的均线，使用macd策略有几种不同的方法，我们这里采用macd线突破signal线的判断方法

        # 如果macd从上往下跌破macd_signal

        if macd[-1] - signal[-1] < 0 and macd[-2] - signal[-2] > 0:
            # 获取当前投资组合中股票的仓位
            curPosition = get_position(context.s1).quantity
            #进行清仓
            if curPosition > 0:
                order_target_value(context.s1, 0)

        # 如果短均线从下往上突破长均线，为入场信号
        if macd[-1] - signal[-1] > 0 and macd[-2] - signal[-2] < 0:
            # 满仓入股
            order_target_percent(context.s1, 1)

多股票RSI算法示例
------------------------------------------------------

以下是一个我们使用TALib编写的多股票RSI算法示例，使用了TALib的RSI方法：

..  code-block:: python3
    :linenos:

    import talib


    # 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
    def init(context):

        # 选择我们感兴趣的股票
        context.s1 = "000001.XSHE"
        context.s2 = "601988.XSHG"
        context.s3 = "000068.XSHE"
        context.stocks = [context.s1, context.s2, context.s3]

        context.TIME_PERIOD = 14
        context.HIGH_RSI = 85
        context.LOW_RSI = 30
        context.ORDER_PERCENT = 0.3


    # 你选择的证券的数据更新将会触发此段逻辑，例如日或分钟历史数据切片或者是实时数据切片更新
    def handle_bar(context, bar_dict):
        # 开始编写你的主要的算法逻辑

        # bar_dict[order_book_id] 可以拿到某个证券的bar信息
        # context.portfolio 可以拿到现在的投资组合状态信息

        # 使用order_shares(id_or_ins, amount)方法进行落单

        # TODO: 开始编写你的算法吧！

        # 对我们选中的股票集合进行loop，运算每一只股票的RSI数值
        for stock in context.stocks:
            # 读取历史数据
            prices = history_bars(stock, context.TIME_PERIOD+1, '1d', 'close')

            # 用Talib计算RSI值
            rsi_data = talib.RSI(prices, timeperiod=context.TIME_PERIOD)[-1]

            cur_position = get_position(stock).quantity
            # 用剩余现金的30%来购买新的股票
            target_available_cash = context.portfolio.cash * context.ORDER_PERCENT

            # 当RSI大于设置的上限阀值，清仓该股票
            if rsi_data > context.HIGH_RSI and cur_position > 0:
                order_target_value(stock, 0)

            # 当RSI小于设置的下限阀值，用剩余cash的一定比例补仓该股
            if rsi_data < context.LOW_RSI:
                logger.info("target available cash caled: " + str(target_available_cash))
                # 如果剩余的现金不够一手 - 100shares，那么会被ricequant 的order management system reject掉
                order_value(stock, target_available_cash)

海龟交易系统
------------------------------------------------------

海龟交易系统也是非常经典的一种策略，我们也放出了范例代码如下，而关于海龟交易系统的介绍也可以参照 `这篇帖子 <https://www.ricequant.com/community/topic/62/%E8%B6%8B%E5%8A%BF%E7%AD%96%E7%95%A5%E5%B0%8F%E8%AF%95%E7%89%9B%E5%88%80-%E6%B5%B7%E9%BE%9F%E4%BA%A4%E6%98%93%E4%BD%93%E7%B3%BB%E7%9A%84%E6%9E%84%E5%BB%BA>`_ 。

..  code-block:: python3
    :linenos:

    import numpy as np
    import talib
    import math


    def get_extreme(array_high_price_result, array_low_price_result):
        np_array_high_price_result = np.array(array_high_price_result[:-1])
        np_array_low_price_result = np.array(array_low_price_result[:-1])
        max_result = np_array_high_price_result.max()
        min_result = np_array_low_price_result.min()
        return [max_result, min_result]


    def get_atr_and_unit( atr_array_result,  atr_length_result, portfolio_value_result):
        atr =  atr_array_result[ atr_length_result-1]
        unit = math.floor(portfolio_value_result * .01 / atr)
        return [atr, unit]


    def get_stop_price(first_open_price_result, units_hold_result, atr_result):
        stop_price = first_open_price_result - 2 * atr_result \
                     + (units_hold_result - 1) * 0.5 * atr_result
        return stop_price


    def init(context):
        context.trade_day_num = 0
        context.unit = 0
        context.atr = 0
        context.trading_signal = 'start'
        context.pre_trading_signal = ''
        context.units_hold_max = 4
        context.units_hold = 0
        context.quantity = 0
        context.max_add = 0
        context.first_open_price = 0
        context.s = '000300.XSHG'
        context.open_observe_time = 55
        context.close_observe_time = 20
        context.atr_time = 20


    def handle_bar(context, bar_dict):
        portfolio_value = context.portfolio.portfolio_value
        high_price = history_bars(context.s, context.open_observe_time+1, '1d', 'high')
        low_price_for_atr = history_bars(context.s, context.open_observe_time+1, '1d', 'low')
        low_price_for_extreme = history_bars(context.s, context.close_observe_time+1, '1d', 'low')
        close_price = history_bars(context.s, context.open_observe_time+2, '1d', 'close')
        close_price_for_atr = close_price[:-1]

        atr_array = talib.ATR(high_price, low_price_for_atr, close_price_for_atr, timeperiod=context.atr_time)

        maxx = get_extreme(high_price, low_price_for_extreme)[0]
        minn = get_extreme(high_price, low_price_for_extreme)[1]
        atr = atr_array[-2]

        if context.trading_signal != 'start':
            if context.units_hold != 0:
                context.max_add += 0.5 * get_atr_and_unit(atr_array, atr_array.size, portfolio_value)[0]
        else:
            context.max_add = bar_dict[context.s].last

        cur_position = get_position(context.s).quantity
        available_cash = context.portfolio.cash
        market_value = context.portfolio.market_value

        if (cur_position > 0 and
                bar_dict[context.s].last < get_stop_price(context.first_open_price, context.units_hold, atr)):        
            context.trading_signal = 'stop'
        else:
            if cur_position > 0 and bar_dict[context.s].last < minn:
                context.trading_signal = 'exit'
            else:
                if (bar_dict[context.s].last > context.max_add and context.units_hold != 0 and
                        context.units_hold < context.units_hold_max and
                        available_cash > bar_dict[context.s].last*context.unit):
                    context.trading_signal = 'entry_add'
                else:
                    if bar_dict[context.s].last > maxx and context.units_hold == 0:
                        context.max_add = bar_dict[context.s].last
                        context.trading_signal = 'entry'

        atr = get_atr_and_unit(atr_array, atr_array.size, portfolio_value)[0]
        if context.trade_day_num % 5 == 0:
            context.unit = get_atr_and_unit(atr_array, atr_array.size, portfolio_value)[1]
        context.trade_day_num += 1
        context.quantity = context.unit

        if (context.trading_signal != context.pre_trading_signal or
                (context.units_hold < context.units_hold_max and context.units_hold > 1) or
                context.trading_signal == 'stop'):
            if context.trading_signal == 'entry':
                context.quantity = context.unit
                if available_cash > bar_dict[context.s].last*context.quantity:
                    order_shares(context.s, context.quantity)
                    context.first_open_price = bar_dict[context.s].last
                    context.units_hold = 1

            if context.trading_signal == 'entry_add':
                context.quantity = context.unit
                order_shares(context.s, context.quantity)
                context.units_hold += 1

            if context.trading_signal == 'stop':
                if context.units_hold > 0:
                    order_shares(context.s, -context.quantity)
                    context.units_hold -= 1

            if context.trading_signal == 'exit':
                if cur_position > 0:
                    order_shares(context.s, -cur_position)
                    context.units_hold = 0

        context.pre_trading_signal = context.trading_signal

股指期货MACD日回测
------------------------------------------------------

以下是一个使用TALib进行股指期货主力合约日级别回测MACD算法示例：

..  code-block:: python3
    :linenos:

    # 可以自己import我们平台支持的第三方python模块，比如pandas、numpy等
    import talib


    # 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递
    def init(context):
        # context内引入全局变量s1，存储目标合约信息
        context.s1 = 'IF1606'

        # 使用MACD需要设置长短均线和macd平均线的参数
        context.SHORTPERIOD = 12
        context.LONGPERIOD = 26
        context.SMOOTHPERIOD = 9
        context.OBSERVATION = 50

        #初始化时订阅合约行情。订阅之后的合约行情会在handle_bar中进行更新
        subscribe(context.s1)


    # 你选择的期货数据更新将会触发此段逻辑，例如日线或分钟线更新
    def handle_bar(context, bar_dict):
        # 开始编写你的主要的算法逻辑
        # 获取历史收盘价序列，history_bars函数直接返回ndarray，方便之后的有关指标计算
        prices = history_bars(context.s1, context.OBSERVATION, '1d', 'close')

        # 用Talib计算MACD取值，得到三个时间序列数组，分别为macd,signal 和 hist
        macd, signal, hist = talib.MACD(prices, context.SHORTPERIOD,
                                        context.LONGPERIOD, context.SMOOTHPERIOD)

        # macd 是长短均线的差值，signal是macd的均线，如果短均线从下往上突破长均线，为入场信号，进行买入开仓操作
        if macd[-1] - signal[-1] > 0 and macd[-2] - signal[-2] < 0:
            sell_qty = get_position(context.s1, POSITION_DIRECTION.SHORT).quantity
            # 先判断当前卖方仓位，如果有，则进行平仓操作
            if sell_qty > 0:
                buy_close(context.s1, 1)
            # 买入开仓
            buy_open(context.s1, 1)

        if macd[-1] - signal[-1] < 0 and macd[-2] - signal[-2] > 0:
            buy_qty = get_position(context.s1, POSITION_DIRECTION.LONG).quantity
            # 先判断当前买方仓位，如果有，则进行平仓操作
            if buy_qty > 0:
                sell_close(context.s1, 1)
            # 卖出开仓
            sell_open(context.s1, 1)

商品期货跨品种配对交易
------------------------------------------------------

该策略为分钟级别回测。运用了简单的移动平均以及布林带（`Bollinger Bands <https://en.wikipedia.org/wiki/Bollinger_Bands>`_）作为交易信号产生源。有关对冲比率（HedgeRatio）的确定，您可以在我们的研究平台上面通过import statsmodels.api as sm引入 `statsmodels <http://statsmodels.sourceforge.net/devel/>`_ 中的OLS方法进行线性回归估计。具体估计窗口，您可以根据自己策略需要自行选择。

策略中的移动窗口选择为60分钟，即在每天开盘60分钟内不做任何交易，积累数据计算移动平均值。当然，这一移动窗口也可以根据自身需要进行灵活选择。下面例子中使用了黄金与白银两种商品期货进行配对交易。简单起见，例子中期货的价格并未做对数差处理。

..  code-block:: python3
    :linenos:

    import numpy as np


    # 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
    def init(context):
        context.s1 = 'AG1612'
        context.s2 = 'AU1612'

        # 设置全局计数器
        context.counter = 0

        # 设置滚动窗口
        context.window = 60

        # 设置对冲手数,通过研究历史数据进行价格序列回归得到该值
        context.ratio = 15

        context.up_cross_up_limit = False
        context.down_cross_down_limit = False

        # 设置入场临界值
        context.entry_score = 2

        # 初始化时订阅合约行情。订阅之后的合约行情会在handle_bar中进行更新
        subscribe([context.s1, context.s2])


    # before_trading此函数会在每天交易开始前被调用，当天只会被调用一次
    def before_trading(context):
        # 样例商品期货在回测区间内有夜盘交易,所以在每日开盘前将计数器清零
        context.counter = 0


    # 你选择的期货数据更新将会触发此段逻辑，例如日线或分钟线更新
    def handle_bar(context, bar_dict):

        # 获取当前一对合约的仓位情况。如尚未有仓位,则对应持仓量都为0
        long_pos_a = get_position(context.s1, POSITION_DIRECTION.LONG)
        short_pos_a = get_position(context.s1, POSITION_DIRECTION.SHORT)
        long_pos_b = get_position(context.s2, POSITION_DIRECTION.LONG)
        short_pos_b = get_position(context.s2, POSITION_DIRECTION.SHORT)

        context.counter += 1
        # 当累积满一定数量的bar数据时候,进行交易逻辑的判断
        if context.counter > context.window:

            # 获取当天历史分钟线价格队列
            price_array_a = history_bars(context.s1, context.window, '1m', 'close')
            price_array_b = history_bars(context.s2, context.window, '1m', 'close')

            # 计算价差序列、其标准差、均值、上限、下限
            spread_array = price_array_a - context.ratio * price_array_b
            std = np.std(spread_array)
            mean = np.mean(spread_array)
            up_limit = mean + context.entry_score * std
            down_limit = mean - context.entry_score * std

            # 获取当前bar对应合约的收盘价格并计算价差
            price_a = bar_dict[context.s1].close
            price_b = bar_dict[context.s2].close
            spread = price_a - context.ratio * price_b

            # 如果价差低于预先计算得到的下限,则为建仓信号,'买入'价差合约
            if spread <= down_limit and not context.down_cross_down_limit:
                # 可以通过logger打印日志
                logger.info('spread: {}, mean: {}, down_limit: {}'.format(spread, mean, down_limit))
                logger.info('创建买入价差中...')

                # 获取当前剩余的应建仓的数量
                qty_a = 1 - long_pos_a.quantity
                qty_b = context.ratio - short_pos_b.sell_quantity

                # 由于存在成交不超过下一bar成交量25%的限制,所以可能要通过多次发单成交才能够成功建仓
                if qty_a > 0:
                    buy_open(context.s1, qty_a)
                if qty_b > 0:
                    sell_open(context.s2, qty_b)
                if qty_a == 0 and qty_b == 0:
                    # 已成功建立价差的'多仓'
                    context.down_cross_down_limit = True
                    logger.info('买入价差仓位创建成功!')

            # 如果价差向上回归移动平均线,则为平仓信号
            if spread >= mean and context.down_cross_down_limit:
                logger.info('spread: {}, mean: {}, down_limit: {}'.format(spread, mean, down_limit))
                logger.info('对买入价差仓位进行平仓操作中...')

                # 由于存在成交不超过下一bar成交量25%的限制,所以可能要通过多次发单成交才能够成功建仓
                qty_a = long_pos_a.quantity
                qty_b = short_pos_b.quantity
                if qty_a > 0:
                    sell_close(context.s1, qty_a)
                if qty_b > 0:
                    buy_close(context.s2, qty_b)
                if qty_a == 0 and qty_b == 0:
                    context.down_cross_down_limit = False
                    logger.info('买入价差仓位平仓成功!')

            # 如果价差高于预先计算得到的上限,则为建仓信号,'卖出'价差合约
            if spread >= up_limit and not context.up_cross_up_limit:
                logger.info('spread: {}, mean: {}, up_limit: {}'.format(spread, mean, up_limit))
                logger.info('创建卖出价差中...')
                qty_a = 1 - short_pos_a.quantity
                qty_b = context.ratio - long_pos_b.quantity
                if qty_a > 0:
                    sell_open(context.s1, qty_a)
                if qty_b > 0:
                    buy_open(context.s2, qty_b)
                if qty_a == 0 and qty_b == 0:
                    context.up_cross_up_limit = True
                    logger.info('卖出价差仓位创建成功')

            # 如果价差向下回归移动平均线,则为平仓信号
            if spread < mean and context.up_cross_up_limit:
                logger.info('spread: {}, mean: {}, up_limit: {}'.format(spread, mean, up_limit))
                logger.info('对卖出价差仓位进行平仓操作中...')
                qty_a = short_pos_a.quantity
                qty_b = long_pos_b.quantity
                if qty_a > 0:
                    buy_close(context.s1, qty_a)
                if qty_b > 0:
                    sell_close(context.s2, qty_b)
                if qty_a == 0 and qty_b == 0:
                    context.up_cross_up_limit = False
                    logger.info('卖出价差仓位平仓成功!')
