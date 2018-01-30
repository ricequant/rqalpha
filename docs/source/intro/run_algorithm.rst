.. _intro-run-alogirhtm:

====================
多种方式运行策略
====================

在策略开发过程中，每个人都会有不同的需求，比如

*   不同的时间周期进行回测，
*   想直接基于回测数据进行编程分析，或直接看一下收益结果。
*   想将回测好的策略直接用于实盘交易
*   不同的品种设置不同的风控标准

在设计 RQAlpha API 的时候，考虑到以上随时变化的需求，将这部分需要以参数方式的配置严格从代码层面剥离。同一份策略代码，通过启动策略时传入不同的参数来实现完全不同的策略开发、风控、运行和调优等的功能。

.. warning::

    我们提供了多种方式来配置策略参数，请务必理解参数配置的优先级顺序，以避免在设置参数的时候因为优先级搞错而导致设置无效的问题！

    参数配置优先级：策略代码中配置 > 命令行传参 = :code:`run_file | run_code | run_func` 函数传参 > 用户配置文件 > 系统默认配置文件

命令行运行
------------------------------------------------------

在命令行模式中，我们预先定义了常用的参数作为命令行的 option，您可以直接在控制台输入参数来配置 RQAlpha，但并不是所有的参数都可以通过命令行来配置，如果有一些特殊的参数需要配置，请结合其他方式来配置您的策略。当然您也可以扩展命令行，来实现您指定的命令行 option 选项。

命令行参数
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

===========   =============================   ==============================================================================
参数名缩写      参数名全称                        说明
===========   =============================   ==============================================================================
-d            `- -` data-bundle-path          数据源所存储的文件路径
-f            `- -` strategy-file             启动的策略文件路径
-s            `- -` start-date                回测起始日期
-e            `- -` end-date                  回测结束日期(如果是实盘，则忽略该配置)
-bm           `- -` benchmark                 Benchmark，如果不设置，默认没有基准参照
-mm           `- -` margin-multiplier         设置保证金乘数，默认为1
-a            `- -` account                   设置账户类型及起始资金，比如股票期货混合策略，起始资金分别为10000, 20000 :code:`--account stock 10000 --account future 20000`
-fq           `- -` frequency                 目前支持 :code:`1d` (日线回测) 和 :code:`1m` (分钟线回测)，如果要进行分钟线，请注意是否拥有对应的数据源，目前开源版本是不提供对应的数据源的
-rt           `- -` run-type                  运行类型，:code:`b` 为回测，:code:`p` 为模拟交易, :code:`r` 为实盘交易
N/A           `- -` resume                    在模拟交易和实盘交易中，RQAlpha支持策略的pause && resume，该选项表示开启 resume 功能
-l            `- -` log-level                 选择日期的输出等级，有 :code:`verbose` | code:`info` | :code:`warning` | :code:`error` 等选项，您可以通过设置 :code:`verbose` 来查看最详细的日志，或者设置 :code:`error` 只查看错误级别的日志输出
N/A           `- -` locale                    选择语言， 支持 :code:`en` | :code:`cn`
N/A           `- -` disable-user-system-log   关闭用户策略产生的系统日志(比如订单未成交等提示)
N/A           `- -` enable-profiler           启动策略逐行性能分析，启动后，在回测结束，会打印策略的运行性能分析报告，可以看到每一行消耗的时间
N/A           `- -` config                    设置配置文件路径
-mc           `- -` mod-config                配置 mod ，支持多个。:code:`-mc funcat_api.enabled True` 就可以启动一个 mod
===========   =============================   ==============================================================================

传递 Mod 参数
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

对于 mod 的参数传递，可以使用 :code:`-mc` 传递 mod 设置。

- :code:`-mc sys_stock_realtime.enabled True` 启动 sys_stock_realtime 这个 mod。
- :code:`-mc sys_stock_realtime.fps 60` 设置 sys_stock_realtime 的 fps 参数为 60。

.. code-block:: python3

   rqalpha run -rt p -fq 1m -f strategy.py --account stock 100000 -mc sys_stock_realtime.enabled True -mc sys_stock_realtime.fps 60

系统内置 Mod Option扩展
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

系统内置 Mod 也提供了启动参数的扩展，当您开启了对应的 Mod 时，即可使用:

===========   =============================   ==============================================================================
参数名缩写      参数名全称                        说明
===========   =============================   ==============================================================================
N/A           `- -` report                    [sys_analyser]保存交易详情
-o            `- -` output-file               [sys_analyser]指定回测结束时将回测数据输出到指定文件中
-p            `- -` plot                      [sys_analyser]在回测结束后，查看图形化的收益曲线
N/A           `- -` no-plot                   [sys_analyser]在回测结束后，不查看图形化的收益曲线
N/A           `- -` plot-save                 [sys_analyser]将plot的收益图以指定文件路径保存
N/A           `- -` progress                  [sys_progress]开启命令行显示回测进度条
N/A           `- -` no-progress               [sys_progress]关闭命令行查看回测进度
N/A           `- -` short-stock               [sys_risk]允许股票卖空
N/A           `- -` no-short-stock            [sys_risk]不允许股票卖空
N/A           `- -` signal                    [sys_simulation]开启信号模式，不进行撮合，直接成交
-sp           `- -` slippage                  [sys_simulation]设置滑点
-cm           `- -` commission-multiplier     [sys_simulation]设置手续费乘数，默认为1
-me           `- -` match-engine              [sys_simulation]启用的回测引擎，目前支持 :code:`current_bar` (当前Bar收盘价撮合) 和 :code:`next_bar` (下一个Bar开盘价撮合)
-r            `- -` rid                       [sys_simulation]可以指定回测的唯一ID，用户区分多次回测的结果
===========   =============================   ==============================================================================

通过 Mod 自定义扩展命令行参数
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

RQAlpha 非常灵活，您可以在您的 Mod 中扩展命令行，我们以 `sys_analyser Mod <https://github.com/ricequant/rqalpha/tree/master/rqalpha/mod/rqalpha_mod_sys_analyser>`_ 添加自定义option :code:`--plot` 来实现展示收益图为例，来介绍以下如何扩展您自己的命令行参数。

.. note::

    rqalpha_mod_sys_analyser 对应源码请访问 `这里 <https://github.com/ricequant/rqalpha/blob/master/rqalpha/mod/rqalpha_mod_sys_analyser/__init__.py>`_ 进行查看。

RQAlpha 使用 `click <http://click.pocoo.org/5/>`_ 来实现命令行参数配置，您需要通过 click 来构建 option。
通过 :code:`from rqalpha import cli` 来获取命令行对象。

.. code-block:: python

    import click
    from rqalpha import cli

接下来我们命令 :code:`rqalpha run` 中添加参数 :code:`--plot` 来实现画图的功能

.. code-block:: python

    cli.commands['run'].params.append(
        click.Option(
            ('-p', '--plot/--no-plot', 'mod__sys_analyser__plot'),
            default=None,
            help="[sys_analyser] plot result"
        )
    )

我们还希望可以通过 :code:`$ rqalpha plot result_pickle_file_path` 来将之前通过pickle文件报错的某次回测的结果进行画图

.. code-block:: python

    @cli.command()
    @click.argument('result_pickle_file_path', type=click.Path(exists=True), required=True)
    @click.option('--show/--hide', 'show', default=True)
    @click.option('--plot-save', 'plot_save_file', default=None, type=click.Path(), help="save plot result to file")
    def plot(result_pickle_file_path, show, plot_save_file):
        """
        [sys_analyser] draw result DataFrame
        """
        import pandas as pd
        from .plot import plot_result

        result_dict = pd.read_pickle(result_pickle_file_path)
        plot_result(result_dict, show, plot_save_file)

使用配置文件运行策略
------------------------------------------------------

在每次运行策略时，有一些参数是固定不变的，我们可以将不经常改变的参数写入配置文件。

RQAlpha 在运行策略时候会在当前目录下寻找 `config.yml` 或者  `config.json` 文件作为用户配置文件来读取。

创建 `config.yml` 配置文件
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::

    我们假设在当前目录下存在 `buy_and_hold.py` 策略文件

::

    # config.yml
    base:
      # 启动的策略文件路径
      strategy_file: .buy_and_hold.py
      # 回测起始日期
      start_date: 2015-06-01
      # 回测结束日期(如果是实盘，则忽略该配置)
      end_date: 2050-01-01
      # 目前支持 `1d` (日线回测) 和 `1m` (分钟线回测)，如果要进行分钟线，请注意是否拥有对应的数据源，目前开源版本是不提供对应的数据源的。
      frequency: 1d
      # Benchmark，如果不设置，默认没有基准参照。
      benchmark: ~
      accounts:
        # 设置 股票为交易品种  初始资金为 100000 元
        stock:  100000
    extra:
      # 开启日志输出
      log_level: verbose
    mod:
      sys_analyser:
        enabled: true
        # 开启 plot 功能
        plot: true

当创建好 `config.yml` 文件后，执行 :code:`$ rqalpha run` 即可运行策略。

创建默认配置文件模板
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

您可以通过该命令在当前目录下创建一份包含了 RQAlpha 基础配置项的全部参数默认值的模板文件。

.. code-block:: bash

    $ rqalpha generate_config

::

    # see more config
    # http://rqalpha.readthedocs.io/zh_CN/stable/intro/run_algorithm.html
    version: 0.1.6

    # 白名单，设置可以直接在策略代码中指定哪些模块的配置项目
    whitelist: [base, extra, validator, mod]

    base:
      # 数据源所存储的文件路径
      data_bundle_path: ~
      # 启动的策略文件路径
      strategy_file: strategy.py
      # 策略源代码
      source_code: ~
      # 回测起始日期
      start_date: 2015-06-01
      # 回测结束日期(如果是实盘，则忽略该配置)
      end_date: 2050-01-01
      # 设置保证金乘数，默认为1
      margin_multiplier: 1
      # 运行类型，`b` 为回测，`p` 为模拟交易, `r` 为实盘交易。
      run_type: b
      # 目前支持 `1d` (日线回测) 和 `1m` (分钟线回测)，如果要进行分钟线，请注意是否拥有对应的数据源，目前开源版本是不提供对应的数据源的。
      frequency: 1d
      # Benchmark，如果不设置，默认没有基准参照。
      benchmark: ~
      # 在模拟交易和实盘交易中，RQAlpha支持策略的pause && resume，该选项表示开启 resume 功能
      resume_mode: false
      # 在模拟交易和实盘交易中，RQAlpha支持策略的pause && resume，该选项表示开启 persist 功能呢，
      # 其会在每个bar结束对进行策略的持仓、账户信息，用户的代码上线文等内容进行持久化
      persist: false
      persist_mode: real_time
      # 设置策略可交易品种，目前支持 `stock` (股票账户)、`future` (期货账户)，您也可以自行扩展
      accounts:
        # 如果想设置使用某个账户，只需要增加对应的初始资金即可
        stock: ~
        future: ~

    extra:
      # 选择日期的输出等级，有 `verbose` | `info` | `warning` | `error` 等选项，您可以通过设置 `verbose` 来查看最详细的日志，
      # 或者设置 `error` 只查看错误级别的日志输出
      log_level: info
      user_system_log_disabled: false
      # 通过该参数可以将预定义变量传入 `context` 内。
      context_vars: ~
      # force_run_init_when_pt_resume: 在PT的resume模式时，是否强制执行用户init。主要用于用户改代码。
      force_run_init_when_pt_resume: false
      # enable_profiler: 是否启动性能分析
      enable_profiler: false
      is_hold: false
      locale: zh_Hans_CN

    validator:
      # cash_return_by_stock_delisted: 开启该项，当持仓股票退市时，按照退市价格返还现金
      cash_return_by_stock_delisted: false
      # close_amount: 在执行order_value操作时，进行实际下单数量的校验和scale，默认开启
      close_amount: true


.. warning::

    生成的默认配置模板中不包含 Mod 相关的配置信息，每个 Mod 的配置信息请参考 Mod 对应的文档。

策略内配置参数信息
------------------------------------------------------

RQAlpha 提供了策略内配置参数信息的功能，您可以方便的在策略文件中配置参数，我们以 `test_f_buy_and_hold 文件 <https://github.com/ricequant/rqalpha/blob/master/tests/test_f_buy_and_hold.py>`_ 为例来介绍此种策略运行方式。

.. code-block:: python

    # test_f_buy_and_hold.py
    def init(context):
        context.s1 = "IF88"
        subscribe(context.s1)
        logger.info("Interested in: " + str(context.s1))


    def handle_bar(context, bar_dict):
        buy_open(context.s1, 1)


    __config__ = {
        "base": {
            "start_date": "2015-01-09",
            "end_date": "2015-03-09",
            "frequency": "1d",
            "matching_type": "current_bar",
            "benchmark": None,
            "accounts": {
                "future": 1000000
            }
        },
        "extra": {
            "log_level": "error",
        },
        "mod": {
            "sys_progress": {
                "enabled": True,
                "show": True,
            },
        },
    }

RQAlpha 会自动识别策略中的 :code:`__config__` 变量。

.. warning::

    虽然 RQAlpha 提供了此种方式来配置策略，但主要用于自动化测试中对每个策略进行参数配置，不建议在策略开发和运行中使用此方式运行策略。

通过引用 RQAlpha 库在代码中运行策略
------------------------------------------------------

并不是所有业务场景下都需要使用 :code:`rqalpha run` 命令行的方式来运行策略，您也可以在您的脚本/程序中直接运行 RQAlpha。

.. note::

  即使通过代码方式启动策略，RQAlpha 也会寻找代码执行目录是否存在 `config.yml` / `config.json` 文件，作为用户配置文件来加载配置。但代码中传入的 `config` 优先级更高。

使用 :code:`run_file` 函数来运行策略
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

此种模式下，您需要指定策略文件路径，并传入配置参数以启动策略

.. code-block:: python

    # run_file_demo
    from rqalpha import run_file

    config = {
      "base": {
        "start_date": "2016-06-01",
        "end_date": "2016-12-01",
        "benchmark": "000300.XSHG",
        "accounts": {
            "stock": 100000
        }
      },
      "extra": {
        "log_level": "verbose",
      },
      "mod": {
        "sys_analyser": {
          "enabled": True,
          "plot": True
        }
      }
    }

    strategy_file_path = "./buy_and_hold.py"

    run_file(strategy_file_path, config)

使用 :code:`run_code` 函数来运行策略
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

此种模式下，您需要以字符串的方式传入策略源码，并传入配置参数以启动策略

.. code-block:: python
    
    # run_code_demo
    from rqalpha import run_code

    code = """
    from rqalpha.api import *


    def init(context):
        logger.info("init")
        context.s1 = "000001.XSHE"
        update_universe(context.s1)
        context.fired = False


    def before_trading(context):
        pass


    def handle_bar(context, bar_dict):
        if not context.fired:
            # order_percent并且传入1代表买入该股票并且使其占有投资组合的100%
            order_percent(context.s1, 1)
            context.fired = True
    """

    config = {
      "base": {
        "start_date": "2016-06-01",
        "end_date": "2016-12-01",
        "benchmark": "000300.XSHG"，
        "accounts": {
            "stock": 100000
        }
      },
      "extra": {
        "log_level": "verbose",
      },
      "mod": {
        "sys_analyser": {
          "enabled": True,
          "plot": True
        }
      }
    }

    run_code(code, config)

使用 :code:`run_func` 函数来运行策略
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

此种模式下，您只需要在当前环境下定义策略函数，并传入指定运行的函数，即可运行策略。

.. code-block:: python

    # run_func_demo
    from rqalpha.api import *
    from rqalpha import run_func


    def init(context):
        logger.info("init")
        context.s1 = "000001.XSHE"
        update_universe(context.s1)
        context.fired = False


    def before_trading(context):
        pass


    def handle_bar(context, bar_dict):
        if not context.fired:
            # order_percent并且传入1代表买入该股票并且使其占有投资组合的100%
            order_percent(context.s1, 1)
            context.fired = True


    config = {
      "base": {
        "start_date": "2016-06-01",
        "end_date": "2016-12-01",
        "benchmark": "000300.XSHG",
        "accounts": {
            "stock": 100000
        }
      },
      "extra": {
        "log_level": "verbose",
      },
      "mod": {
        "sys_analyser": {
          "enabled": True,
          "plot": True
        }
      }
    }

    # 您可以指定您要传递的参数
    run_func(init=init, before_trading=before_trading, handle_bar=handle_bar, config=config)

    # 如果你的函数命名是按照 API 规范来，则可以直接按照以下方式来运行
    # run_func(**globals())



