.. _intro-tutorial:

====================
10分钟教程
====================

在本教程中，我们假设 RQAlpha 已经正确安装在您的系统中，并且已经完成了相应回测数据的同步，如果有任何安装相关的问题，请首先查看 :ref:`intro-install`

策略运行流程
------------------------------------------------------

我们从 :ref:`intro-examples` 中选取 :ref:`intro-examples-buy-and-hold` 来进行回测。

在进行回测的过程中需要明确以下几个回测要素，您可通过生成 config.yml 传参（:ref:`intro-config`）或者通过命令行传参：

*   数据源路径
*   策略文件路径
*   回测起始时间
*   回测结束时间
*   起始资金
*   Benchmark

假如我们的策略存放在了 :code:`./rqalpha/examples/buy_and_hold.py` 路径下，回测的起始时间为 :code:`2016-06-01`, 结束时间为 :code:`2016-12-01`，我们给策略分配的起始资金为 :code:`100000`, Benchmark 设置为 :code:`000300.XSHG`

那么我们通过如下命令来运行回测

..  code-block:: bash

    rqalpha run -f ./rqalpha/examples/buy_and_hold.py -s 2016-06-01 -e 2016-12-01 --account stock 100000 --benchmark 000300.XSHG

如果我们想要以图形的方式查看回测的结果， 则增加 :code:`--plot` 参数

..  code-block:: bash

    rqalpha run -f ./rqalpha/examples/buy_and_hold.py -s 2016-06-01 -e 2016-12-01 --account stock 100000 --benchmark 000300.XSHG --plot

.. image:: https://raw.githubusercontent.com/ricequant/rq-resource/master/rqalpha/buy_and_hold.png

如果想把回测的数据保存下来，可以通过 :code:`-o` 参数将结果保存成 :code:`pkl` 文件。

..  code-block:: bash

    rqalpha run -f ./rqalpha/examples/buy_and_hold.py -s 2016-06-01 -e 2016-12-01 --account stock 100000 --benchmark 000300.XSHG --plot -o result.pkl


等回测结束后可以通过 :code:`pandas.read_pickle` 函数来读取数据进行之后的数据分析。

..  code-block:: python3
    :linenos:

    import pandas as pd

    result_dict = pd.read_pickle('result.pkl')

    result_dict.keys()
    # [out]dict_keys(['total_portfolios', 'summary', 'benchmark_portfolios', 'benchmark_positions', 'stock_positions', 'trades', 'stock_portfolios'])


策略编写流程
------------------------------------------------------

RQAlpha 抽离了策略框架的所有技术细节，以API的方式提供给策略研发者用于编写策略，从而避免陷入过多的技术细节，而非金融程序建模本身。

RQAlpha 的 API 主要分为约定函数、数据查询接口、交易接口等几类，参看 :ref:`api-base-api`。

*   约定函数: 作为 API 的入口函数，用户必须实现对应的约定函数才可以正确的使用RQAlpha

    *   :func:`init` : 初始化方法，会在程序启动的时候执行
    *   :func:`handle_bar`: bar数据更新时会自动触发调用
    *   :func:`before_trading`: 会在每天策略交易开始前调用
    *   :func:`after_trading`: 会在每天交易结束后调用

..  code-block:: python3
    :linenos:

    # 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
    def init(context):
        # 在context中保存全局变量
        context.s1 = "000001.XSHE"
        # 实时打印日志
        logger.info("RunInfo: {}".format(context.run_info))

    # before_trading此函数会在每天策略交易开始前被调用，当天只会被调用一次
    def before_trading(context):
        logger.info("开盘前执行before_trading函数")

    # 你选择的证券的数据更新将会触发此段逻辑，例如日或分钟历史数据切片或者是实时数据切片更新
    def handle_bar(context, bar_dict):
        logger.info("每一个Bar执行")
        logger.info("打印Bar数据：")
        logger.info(bar_dict[context.s1])

    # after_trading函数会在每天交易结束后被调用，当天只会被调用一次
    def after_trading(context):
        logger.info("收盘后执行after_trading函数")

至此，我们写出了一个“完整”的策略，但是该策略实际上什么也没有做。

接下来，我们需要获取数据，根据数据来确定我们的仓位逻辑，因此会使用到数据查询的 API 接口。

*   数据查询

    *   :func:`all_instruments` : 获取所有合约基础信息数据
    *   :func:`instruments` : 获取合约详细数据
    *   :func:`history_bars` : 获取某一合约的历史数据
    *   :func:`current_snapshot` : 获取当前快照数据
    *   :func:`get_future_contracts` : 获取期货可以交易合约列表
    *   :func:`get_trading_dates`: 获取交易日列表
    *   :func:`get_previous_trading_date` : 获取上一日交易日
    *   :func:`get_next_trading_date` : 获取下一个交易日
    *   :func:`get_yield_curve`: 获取收益率曲线
    *   :func:`is_suspended` : 判断某股票当天是否停牌
    *   :func:`is_st_stock` : 判断某股票是否为 \*st

Ricequant 金融、财务、合约历史数据等数据接口请查看 :ref:`api-extend-api`

*   bar_dict: 在 :func:`handle_bar` 中我们可以使用 `bar_dict` 来获取相应的 :class:`Bar` 数据，`bar_dict` 是一个字典类型变量，直接通过传 `key` 的方式就可以获取到对应的 :class:`Bar` 数据。

*   我们可以引用第三方库来帮我们生成相应的指标序列，比如使用 `TA-Lib`_ 来获取移动平均线序列。

.. _TA-Lib: https://github.com/mrjbq7/ta-lib

..  code-block:: python3
    :linenos:

    import talib

    # 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
    def init(context):
        # 在context中保存全局变量
        context.s1 = "000001.XSHE"
        # 实时打印日志
        logger.info("RunInfo: {}".format(context.run_info))

        # 设置这个策略当中会用到的参数，在策略中可以随时调用，这个策略使用长短均线，我们在这里设定长线和短线的区间，在调试寻找最佳区间的时候只需要在这里进行数值改动
        context.SHORTPERIOD = 20
        context.LONGPERIOD = 120


    # before_trading此函数会在每天策略交易开始前被调用，当天只会被调用一次
    def before_trading(context):
        logger.info("开盘前执行before_trading函数")

    # 你选择的证券的数据更新将会触发此段逻辑，例如日或分钟历史数据切片或者是实时数据切片更新
    def handle_bar(context, bar_dict):
        logger.info("每一个Bar执行")
        logger.info("打印Bar数据：")
        logger.info(bar_dict[context.s1])

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
            logger.info("进行清仓")

        # 如果短均线从下往上突破长均线，为入场信号
        if short_avg[-1] - long_avg[-1] > 0 and short_avg[-2] - long_avg[-2] < 0:
            # 满仓入股
            logger.info("满仓入股")

    # after_trading函数会在每天交易结束后被调用，当天只会被调用一次
    def after_trading(context):
        logger.info("开盘前执行after_trading函数")

至此，我们已经获取到了开仓和平仓的信号，那么接下来就需要调用交易接口来进行交易了。

*   交易接口: 我们提供了多种交易接口，以方便不同的使用需求

    *   :func:`order_shares`: 【股票专用】指定股数交易
    *   :func:`order_lots`: 【股票专用】指定手数交易
    *   :func:`order_value`: 【股票专用】指定价值交易
    *   :func:`order_percent`:【股票专用】 一定比例下单
    *   :func:`order_target_value`: 【股票专用】按照目标价值下单
    *   :func:`order_target_percent`: 【股票专用】按照目标比例下单
    *   :func:`buy_open`: 【期货专用】买开
    *   :func:`sell_close`:【期货专用】 平买仓
    *   :func:`sell_open`: 【期货专用】卖开
    *   :func:`buy_close`: 【期货专用】平卖仓
    *   :func:`cancel_order`: 撤单
    *   :func:`get_open_orders`: 获取未成交订单数据

我们分别使用 :func:`order_target_value` 和 :func:`order_shares` 进行平仓和开仓的操作，顺便把日志相关的代码删除，就是一个完整的 :ref:`intro-examples-golden-cross` 了。

..  code-block:: python3
    :linenos:

    import talib

    # 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
    def init(context):
        # 在context中保存全局变量
        context.s1 = "000001.XSHE"

        # 设置这个策略当中会用到的参数，在策略中可以随时调用，这个策略使用长短均线，我们在这里设定长线和短线的区间，在调试寻找最佳区间的时候只需要在这里进行数值改动
        context.SHORTPERIOD = 20
        context.LONGPERIOD = 120


    # before_trading此函数会在每天策略交易开始前被调用，当天只会被调用一次
    def before_trading(context):
        pass

    # 你选择的证券的数据更新将会触发此段逻辑，例如日或分钟历史数据切片或者是实时数据切片更新
    def handle_bar(context, bar_dict):

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

    # after_trading函数会在每天交易结束后被调用，当天只会被调用一次
    def after_trading(context):
        pass


可以看到，我们使用 plot 函数绘制内容，也出现在了输出的结果中。


.. code-block:: bash

    $ rqalpha run -s 2014-01-01 -e 2016-01-01 -f rqalpha/examples/golden_cross.py --account stock 100000 -p -bm 000001.XSHE


.. image:: https://raw.githubusercontent.com/ricequant/rq-resource/master/rqalpha/golden_cross.png
