===============================
sys_analyser Mod
===============================

RQAlpha 策略分析 Mod。

启用该 Mod 后会记录下来每天的下单、成交、投资组合、持仓等信息，并计算风险度指标，最终以csv、plot图标等形式输出分析结果。

该模块是系统模块，不可删除

开启或关闭策略分析 Mod
===============================

..  code-block:: bash

    # 关闭策略分析 Mod
    $ rqalpha mod disable sys_analyser

    # 启用策略分析 Mod
    $ rqalpha mod enable sys_analyser

模块配置项
===============================

您可以通过直接修改 `sys_analyser` Mod 的配置信息来选择需要启用的功能。

默认配置项如下：

..  code-block:: python

   {
        # 策略基准，该基准将用于风险指标计算和收益曲线图绘制
        #   若基准为单指数/股票，此处直接设置 order_book_id，如："000300.XSHG"
        #   若基准为复合指数，则需传入 order_book_id 和权重构成的字典，如：{"000300.XSHG": 0.2. "000905.XSHG": 0.8}
        "benchmark": None,
        # 当不输出 csv/pickle/plot 等内容时，关闭该项可关闭策略运行过程中部分收集数据的逻辑，用以提升性能
        "record": True,
        # 回测结果输出的文件路径，该文件为 pickle 格式，内容为每日净值、头寸、流水及风险指标等；若不设置则不输出该文件
        "output_file": None,
        # 回测报告的数据目录，报告为 csv 格式；若不设置则不输出报告
        "report_save_path": None,
        # 是否在回测结束后绘制收益曲线图，当为True时使用默认模版展示，或设置模版名称来指定使用对应模版展示
        # 当前模版: 'default', 'ricequant'
        'plot': False,
        # 收益曲线图路径，若设置则将收益曲线图保存为 png 文件
        'plot_save_file': None,
        # 收益曲线图设置
        'plot_config': {
            # 是否在收益图中展示买卖点
            'open_close_points': False,
            # 是否在收益图中展示周度指标和收益曲线
            'weekly_indicators': False
        },
    }

您可以通过如下方式来修改模块的配置信息，比如下面的示例中介绍了如何开启显示回测收益曲线图

..  code-block:: python

    from rqalpha import run
    config = {
        "base": {
            "strategy_file": "strategy.py",
            "start_date": "2015-01-09",
            "end_date": "2015-03-09",
            "frequency": "1d",
            "accounts": {
                "stock": 100000
            }
        }
        "mod": {
            "sys_analyser": {
                "enabled": True,
                "plot": True
            }
        }
    }
    run(config)

扩展命令
===============================

在启用该 Mod 的情况下，您可以使用如下命令:

..  code-block:: bash

    $ rqalpha plot result_pickle_file_path --hide --plot-save target_plot_img_path

*   增加 :code:`rqalpha report` 命令，根据生成的 :code:`pickle` 文件来生成报告 :code:`csv` 文件

..  code-block:: bash

    $ rqalpha report result_pickle_file_path target_report_csv_path
