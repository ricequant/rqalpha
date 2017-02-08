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

运行以下命令，将会在指定目录生成一个examples文件夹，其中包含几个有趣的样例策略::

    $ rqalpha examples -d ./

运行回测
==================

运行 RQAlpha 需要传递一些参数，可以通过命令 `rqalpha help` 查看，或者查看文档 :ref: `intro-config` 来获取相关信息。

运行如下命令::

    $ cd examples
    $ rqalpha run -f multi_rsi.py -s 2014-01-01 -e 2016-01-01 -o result.pkl --plot --progress -stock-starting-cash 100000

等待回测结束后，将显示您的收益率和Risk。

绘制回测结果
==================

如果运行完回测后，还需要再次绘制回测结果，可以运行以下命令::

    $ rqalpha plot result.pkl

分析结果
==================

RQAlpha可以输出一个DataFrame，其中包含了每天的Portfolio信息、Risk信息、Trades和Positions。其中Index是交易日，columns包括:

*   alpha
*   annualized_returns
*   benchmark_annualized_returns
*   benchmark_daily_returns
*   benchmark_total_returns
*   beta
*   cash
*   daily_returns
*   downside_risk
*   information_rate
*   market_value
*   max_drawdown
*   pnl
*   portfolio_value
*   positions
*   sharpe
*   sortino
*   total_commission
*   total_returns
*   total_tax
*   tracking_error
*   trades
*   volatility

其中positions是当日的持仓信息，trades是当日的交易信息。

::

    import pandas as pd
    df = pd.read_pickle("result.pkl")
    print(df.iloc[-1])

    '''
    alpha                                                                   0.0180666
    annualized_returns                                                      0.0559331
    benchmark_annualized_returns                                            0.0454542
    benchmark_daily_returns                                               8.87784e-05
    benchmark_total_returns                                                  0.525913
    beta                                                                     0.518371
    cash                                                                      4971.44
    daily_returns                                                          0.00250376
    downside_risk                                                            0.246409
    information_rate                                                        0.0380054
    market_value                                                               162796
    max_drawdown                                                            -0.602535
    pnl                                                                           419
    portfolio_value                                                            167767
    positions                       {'000068.XSHE': Position({{'value_percent': 0....
    sharpe                                                                    2.35011
    sortino                                                                   2.62967
    total_commission                                                          2585.89
    total_returns                                                            0.677674
    total_tax                                                                 1172.01
    tracking_error                                                           0.269138
    trades                                                                         []
    volatility                                                               0.275721
    Name: 2016-07-01 00:00:00, dtype: object
    '''
