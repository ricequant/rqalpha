===============================
sys_analyser Mod
===============================

RQAlpha 策略分析 Mod。

启用该 Mod 后会记录下来每天的下单、成交、投资组合、持仓等信息，并计算风险度指标，最终以csv、plot图标等形式输出分析结果。

该模块是系统自带模块，不可以删除

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
    :linenos:

    {
        "record": True,
        "output_file": None,
        "report_save_path": None,
        'plot': False,
        'plot_save_file': None,
    }

您可以通过如下方式来修改模块的配置信息，比如下面的示例中介绍了如何开启显示回测收益曲线图

..  code-block:: python
    :linenos:

    from rqalpha import run
    config = {
        "base": {
            "strategy_file": "strategy.py",
            "securities": ["stock"],
            "start_date": "2015-01-09",
            "end_date": "2015-03-09",
            "frequency": "1d",
            "stock_starting_cash": 100000,
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

*   `rqalpha run` 命令增加 `--report target_csv_path` 选项，您可以指定将报告以 `csv` 格式输出至 `target_csv_path` 路径
*   `rqalpha run` 命令增加 `--output-file target_pickle_path` / `-o target_pickle_path` 选项，您可以将每日 `Portfolio`/`Trade` 数据以 `pickle` 文件格式输出到 `target_pickle_path` 路径
*   `rqalpha run` 命令增加 `--plot/--no-plot` / `-p` 选项，您可以以图形的方式显示收益曲线图
*   `rqalpha run` 命令增加 `--plot-save target_plot_img_path`选项，您可以将收益曲线图输出至 `target_plot img_path` 路径

..  code-block:: bash

    $ rqalpha run -f target_file.py --report target_csv_path -o target_pickle_path --plot --plot-save target_plot_img_path

*   增加 `rqalpha plot` 命令，根据生成的 `pickle` 文件来显示收益曲线图
    *   `--show/--hide` 选项，是否显示收益曲线图
    *   `--plot-save target_plot_img_path` 选项，您可以将收益曲线图输出至 `target_plot img_path` 路径

..  code-block:: bash

    $ rqalpha plot result_pickle_file_path --hide --plot-save target_plot_img_path

*   增加 `rqalpha report` 命令，根据生成的 `pickle` 文件来生成报告 `csv` 文件

..  code-block:: bash

    $ rqalpha report result_pickle_file_path target_report_csv_path

