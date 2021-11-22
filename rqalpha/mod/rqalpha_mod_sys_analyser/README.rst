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
        # 是否在回测结束后绘制收益曲线图
        'plot': False,
        # 收益曲线图路径，若设置则将收益曲线图保存为 png 文件
        'plot_save_file': None,
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

在启用该 Mod 的情况下，您可以使用如下功能:

*   :code:`rqalpha run` 命令增加 :code:`--report target_csv_path` 选项，您可以指定将报告以 :code:`csv` 格式输出至 :code:`target_csv_path` 路径
*   :code:`rqalpha run` 命令增加 :code:`--output-file target_pickle_path` / :code:`-o target_pickle_path` 选项，您可以将每日  :code:`Portfolio` / :code:`Trade` 数据以 :code:`pickle` 文件格式输出到 :code:`target_pickle_path` 路径
*   :code:`rqalpha run` 命令增加 :code:`--plot/--no-plot` / :code:`-p` 选项，您可以以图形的方式显示收益曲线图
*   :code:`rqalpha run` 命令增加 :code:`--plot-save target_plot_img_path` 选项，您可以将收益曲线图输出至 :code:`target_plot img_path` 路径

..  code-block:: bash

    $ rqalpha run -f strategy.py --report target_csv_path -o target_pickle_path --plot --plot-save target_plot_img_path

*   增加 :code:`rqalpha plot` 命令，根据生成的 :code:`pickle` 文件来显示收益曲线图
    *   :code:`--show/--hide` 选项，是否显示收益曲线图
    *   :code:`--plot-save target_plot_img_path` 选项，您可以将收益曲线图输出至 :code:`target_plot img_path` 路径

..  code-block:: bash

    $ rqalpha plot result_pickle_file_path --hide --plot-save target_plot_img_path

*   增加 :code:`rqalpha report` 命令，根据生成的 :code:`pickle` 文件来生成报告 :code:`csv` 文件

..  code-block:: bash

    $ rqalpha report result_pickle_file_path target_report_csv_path
