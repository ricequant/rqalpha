.. _intro-overview:

====================
RQAlpha 介绍
====================

.. _Ricequant: https://www.ricequant.com/algorithms
.. _Ricequant 社区: https://www.ricequant.com/community

RQAlpha 从数据获取、算法交易、回测引擎，实盘模拟，实盘交易到数据分析，为程序化交易者提供了全套解决方案。RQAlpha 具有灵活的配置方式，强大的扩展性，用户可以非常容易地定制专属于自己的程序化交易系统。

RQAlpha 所有的策略都可以直接在 `Ricequant`_ 上进行回测和实盘模拟，并且可以通过微信和邮件实时推送您的交易信号。`Ricequant`_ 是一个开放的量化算法交易社区，为程序化交易者提供免费的回测和实盘模拟环境，并且会不间断举行实盘资金投入的量化比赛。

特点
==================

*   易于使用: RQAlpha 让您集中于策略的开发，一行简单的命令就可以执行您的策略。
*   完善的文档: 从API使用，到扩展开发，我们提供了详尽的文档来帮助您快速了解和学习RQAlpha，同时您也可以帮助我们一起来 `完善文档 <https://github.com/ricequant/rqalpha/tree/develop/docs>`_。
*   活跃的社区: 您可以通过访问 `Ricequant 社区`_ 获取和询问有关 RQAlpha 的问题，有很多优秀的童鞋会您解答。
*   稳定的环境: 每天都有会大量的算法交易在 `Ricequant`_ 上运行，无论是 RQAlpha，还是数据，我们能会做到问题秒处理，秒解决。
*   灵活的配置: RQAlpha提供了一系列的配置选项，用户可以通过简单的配置来构建适合自己的交易系统。
*   强大的扩展性: RQAlpha 定义了一系列的Mod Hook接口，开发者可以基于Mod的开发模式，扩展 RQAlpha，无论是做实时监控，还是归因分析，RQAlpha 都支持。

限制
==================

RQAlpha 本身支持不同周期的回测和实盘交易，但是目前只开放A股市场日线数据，如果用户需要做分钟回测或者更细级别的回测可以在 `Ricequant`_ 上进行，也通过实现数据层接口函数来使用自己的数据。财务数据相关的API目前只能通过 `Ricequant`_ 平台来获取。

RQAlpha 只是我们的商业版的一部分，如果您是机构希望采用我们包含数据的一体化策略开发、研究、评估系统，请邮件联系我们: public@ricequant.com，或加QQ：「4848371」 咨询，我们也会提供咨询帮助和系统维护服务等。

RQAlpha 安装
==================

请参考 :ref:`intro-install`

数据获取
==================

请参考 :ref:`intro-install-get-data`

生成样例策略
==================

运行以下命令，将会在指定目录生成一个examples文件夹，其中包含几个有趣的样例策略:

.. code-block:: bash

    $ rqalpha examples -d ./

运行回测
==================

运行 RQAlpha 需要传递一些参数，可以通过命令 `rqalpha help` 查看，或者查看文档 :ref: `intro-config` 来获取相关信息。

运行如下命令:

.. code-block:: bash

    $ cd examples
    $ rqalpha run -f rsi.py -s 2014-01-01 -e 2016-01-01 -o result.pkl --plot --progress --stock-starting-cash 100000

等待回测结束后，将显示您的收益率和Risk。

绘制回测结果
==================

如果运行完回测后，还需要再次绘制回测结果，可以运行以下命令:

.. code-block:: bash

    $ rqalpha plot result.pkl

分析结果
==================

RQAlpha可以输出一个 pickle 文件，里面为一个 dict 。keys 包括

* summary               回测摘要
* stock_portfolios      股票帐号的市值
* future_portfolios     期货帐号的市值
* total_portfolios      总账号的的市值
* benchmark_portfolios  基准帐号的市值
* stock_positions       股票持仓
* future_positions      期货仓位
* benchmark_positions   基准仓位
* trades                交易详情（交割单）
* plots                 调用plot画图时，记录的值

.. code-block:: python3

    import pickle

    result_dict = pickle.load(open("/tmp/alpha.pkl", "rb"))   # 从输出pickle中读取数据

    result_dict.keys()
    # Out: dict_keys(['stock_portfolios', 'total_portfolios', 'stock_positions',
    #                 'benchmark_portfolios', 'plots', 'summary', 'trades', 'benchmark_positions'])

    result_dict["summary"]
    # Out:
    # {'alpha': 0.027,
    #  'annualized_returns': 0.025000000000000001,
    #  'benchmark': '000001.XSHG',
    #  'benchmark_annualized_returns': -0.057285289949864038,
    #  'benchmark_total_returns': -0.059871893424000011,
    #  'beta': 0.314,
    #  'cash': -617.64200000000005,
    #  'commission_multiplier': 1,
    #  'dividend_receivable': 0.0,
    #  'downside_risk': 0.14299999999999999,
    #  'end_date': datetime.date(2017, 1, 19),
    #  'frequency': '1d',
    #  'frozen_cash': 0.0,
    #  'future_starting_cash': 0,
    #  'information_ratio': 0.45700000000000002,
    #  'margin_multiplier': 1,
    #  'market_value': 1027242.0,
    #  'matching_type': 'CURRENT_BAR_CLOSE',
    #  'max_drawdown': 0.087999999999999995,
    #  'pnl': 26624.358,
    #  'portfolio_value': 1026624.358,
    #  'run_id': 9999,
    #  'run_type': 'BACKTEST',
    #  'sharpe': 0.016,
    #  'slippage': 0,
    #  'sortino': 0.014,
    #  'start_date': datetime.date(2016, 1, 4),
    #  'starting_cash': 1000000.0,
    #  'stock_starting_cash': 1000000.0,
    #  'strategy_file': 'rqalpha/examples/simple_macd.py',
    #  'strategy_name': 'simple_macd',
    #  'strategy_type': 'stock',
    #  'total_returns': 0.027,
    #  'tracking_error': 0.18099999999999999,
    #  'transaction_cost': 27467.462,
    #  'volatility': 0.125}

    result_dict["total_portfolios"][-5:]
    # Out:
    #             annualized_returns     cash  daily_pnl  daily_returns  \
    # date
    # 2017-01-13               0.024 -617.642     1119.0          0.001
    # 2017-01-16               0.021 -617.642    -2238.0         -0.002
    # 2017-01-17               0.022 -617.642     1119.0          0.001
    # 2017-01-18               0.024 -617.642     2238.0          0.002
    # 2017-01-19               0.025 -617.642     1119.0          0.001
    #             dividend_receivable  frozen_cash  market_value        pnl  \
    # date
    # 2017-01-13                  0.0          0.0     1025004.0  24386.358
    # 2017-01-16                  0.0          0.0     1022766.0  22148.358
    # 2017-01-17                  0.0          0.0     1023885.0  23267.358
    # 2017-01-18                  0.0          0.0     1026123.0  25505.358
    # 2017-01-19                  0.0          0.0     1027242.0  26624.358
    #             portfolio_value  total_returns  transaction_cost
    # date
    # 2017-01-13      1024386.358          0.024         27467.462
    # 2017-01-16      1022148.358          0.022         27467.462
    # 2017-01-17      1023267.358          0.023         27467.462
    # 2017-01-18      1025505.358          0.026         27467.462
    # 2017-01-19      1026624.358          0.027         27467.462

    result_dict["stock_positions"][-5:]
    # Out[6]:
    #             average_cost  avg_price  bought_quantity  bought_value  \
    # date
    # 2017-01-13          9.15       9.15           111900     1023885.0
    # 2017-01-16          9.15       9.15           111900     1023885.0
    # 2017-01-17          9.15       9.15           111900     1023885.0
    # 2017-01-18          9.15       9.15           111900     1023885.0
    # 2017-01-19          9.15       9.15           111900     1023885.0
    #             market_value order_book_id     pnl  quantity  sellable  \
    # date
    # 2017-01-13     1025004.0   000001.XSHE  1119.0    111900    111900
    # 2017-01-16     1022766.0   000001.XSHE -1119.0    111900    111900
    # 2017-01-17     1023885.0   000001.XSHE     0.0    111900    111900
    # 2017-01-18     1026123.0   000001.XSHE  2238.0    111900    111900
    # 2017-01-19     1027242.0   000001.XSHE  3357.0    111900    111900
    #             sold_quantity  sold_value symbol  total_orders  total_trades  \
    # date
    # 2017-01-13              0         0.0   平安银行             1             1
    # 2017-01-16              0         0.0   平安银行             1             1
    # 2017-01-17              0         0.0   平安银行             1             1
    # 2017-01-18              0         0.0   平安银行             1             1
    # 2017-01-19              0         0.0   平安银行             1             1
    #             transaction_cost  value_percent
    # date
    # 2017-01-13           819.108          1.001
    # 2017-01-16           819.108          1.001
    # 2017-01-17           819.108          1.001
    # 2017-01-18           819.108          1.001
    # 2017-01-19           819.108          1.001
