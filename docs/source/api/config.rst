.. _api-config:

====================
参数配置
====================

在策略开发过程中，每个人都会有不同的需求，比如

*   不同的时间周期进行回测，
*   想直接基于回测数据进行编程分析，或直接看一下收益结果。
*   想将回测好的策略直接用于实盘交易
*   不同的品种设置不同的风控标准

等等。

在设计 RQAlpha API 的时候，考虑到以上随时变化的需求，将这部分需要以参数方式的配置严格从代码层面剥离。同一份策略代码，通过启动策略时传入不同的参数来实现完全不同的策略开发、风控、运行和调优等的功能。

通过启动策略传参的方式
------------------------------------------------------

目前支持的参数如下：

===========   =============================   ==============================================================================
参数名缩写      参数名全称                        说明
===========   =============================   ==============================================================================
-d            `- -` data-bundle-path          数据源所存储的文件路径
-f            `- -` strategy-file             启动的策略文件路径
-s            `- -` start-date                回测起始日期
-e            `- -` end-date                  回测结束日期(如果是实盘，则忽略该配置)
-r            `- -` rid                       可以指定回测的唯一ID，用户区分多次回测的结果
-i            `- -` init-cash                 [Deprecated]股票起始资金，不建议使用该参数，使用 :code:`--stock-starting-cash` 代替。
-o            `- -` output-file               指定回测结束时将回测数据输出到指定文件中
-sc           `- -` stock-starting-cash       股票起始资金，默认为0
-fc           `- -` future-starting-cash      期货起始资金，默认为0
-bm           `- -` benchmark                 Benchmark，如果不设置，默认没有基准参照
-sp           `- -` slippage                  设置滑点
-cm           `- -` commission-multiplier     设置手续费乘数，默认为1
-mm           `- -` margin-multiplier         设置保证金乘数，默认为1
-st           `- -` strategy-type             设置策略类型，目前支持 :code:`stock` (股票策略)、:code:`future` (期货策略)及 :code:`stock_future` (混合策略)
-fq           `- -` frequency                 目前支持 :code:`1d` (日线回测) 和 :code:`1m` (分钟线回测)，如果要进行分钟线，请注意是否拥有对应的数据源，目前开源版本是不提供对应的数据源的
-me           `- -` match-engine              启用的回测引擎，目前支持 :code:`current_bar` (当前Bar收盘价撮合) 和 :code:`next_bar` (下一个Bar开盘价撮合)
-rt           `- -` run-type                  运行类型，:code:`b` 为回测，:code:`p` 为模拟交易, :code:`r` 为实盘交易
N/A           `- -` resume                    在模拟交易和实盘交易中，RQAlpha支持策略的pause && resume，该选项表示开启 resume 功能
N/A           `- -` handle-split              开启自动处理, 默认不开启
N/A           `- -` not-handle-split          不开启自动处理, 默认不开启
N/A           `- -` risk-grid                 开启Alpha/Beta 等风险指标的实时计算，默认开启
N/A           `- -` no-risk-grid              不开启Alpha/Beta 等风险指标的实时计算，默认开启
N/A           `- -` disable-user-system-log   关闭用户策略产生的系统日志(比如订单未成交等提示)
-l            `- -` log-level                 选择日期的输出等级，有 :code:`verbose` | :code:`info` | :code:`warning` | :code:`error` 等选项，您可以通过设置 :code:`verbose` 来查看最详细的日志，或者设置 :code:`error` 只查看错误级别的日志输出
-p            `- -` plot                      在回测结束后，查看图形化的收益曲线
N/A           `- -` no-plot                   在回测结束后，不查看图形化的收益曲线
N/A           `- -` progress                  开启命令行显示回测进度条
N/A           `- -` no-progress               关闭命令行查看回测进度
N/A           `- -` enable-profiler           启动策略逐行性能分析，启动后，在回测结束，会打印策略的运行性能分析报告，可以看到每一行消耗的时间
N/A           `- -` config                    设置配置文件路径
-mc           `- -` mod-config                配置 mod ，支持多个。:code:`-mc funcat_api.enabled True` 就可以启动一个 mod
===========   =============================   ==============================================================================

对于 mod 的参数传递，可以使用 :code:`-mc` 传递 mod 设置。

- :code:`-mc simple_stock_realtime_trade.enabled True` 启动 simple_stock_realtime_trade 这个 mod。
- :code:`-mc simple_stock_realtime_trade.fps 60` 设置 simple_stock_realtime_trade 的 fps 参数为 60。

.. code-block:: python3

   rqalpha run -rt p -fq 1m -f strategy.py -sc 100000 -mc simple_stock_realtime_trade.enabled True -mc simple_stock_realtime_trade.fps 60

.. _api-config-file:

通过配置 `config.yml` 的方式
------------------------------------------------------

除了在启动策略的时候传入参数，还可以通过指定配置文件的方式来进行参数的配置, 配置文件的配置信息优先级低于启动参数，也就是说启动参数会覆盖配置文件的配置项，配置文件的格式如下:

注: 如果没有指定 `config.yml`， RQAlpha 在运行时会自动在 `~/.rqalpha/` 文件夹下创建 `config.yml` 文件作为默认配置文件。您也可以使用 `$ rqalpha generate_config` 来生成一份默认的配置文件。

..  code-block:: bash
    :linenos:

    version: 0.1.0

    # 白名单，设置可以直接在策略代码中指定哪些模块的配置项目
    whitelist: [base, extra, validator, mod]

    base:
      # 可以指定回测的唯一ID，用户区分多次回测的结果
      run_id: 9999
      # 数据源所存储的文件路径
      data_bundle_path: ~
      # 启动的策略文件路径
      strategy_file: strategy.py
      # 回测起始日期
      start_date: 2015-06-01
      # 回测结束日期(如果是实盘，则忽略该配置)
      end_date: 2050-01-01
      # 股票起始资金，默认为0
      stock_starting_cash: 0
      # 期货起始资金，默认为0
      future_starting_cash: 0
      # 设置策略类型，目前支持 `stock` (股票策略)、`future` (期货策略)及 `stock_future` (混合策略)
      strategy_type: stock
      # 运行类型，`b` 为回测，`p` 为模拟交易, `r` 为实盘交易。
      run_type: b
      # 目前支持 `1d` (日线回测) 和 `1m` (分钟线回测)，如果要进行分钟线，请注意是否拥有对应的数据源，目前开源版本是不提供对应的数据源的。
      frequency: 1d
      # 启用的回测引擎，目前支持 `current_bar` (当前Bar收盘价撮合) 和 `next_bar` (下一个Bar开盘价撮合)
      matching_type: current_bar
      # Benchmark，如果不设置，默认没有基准参照。
      benchmark: ~
      # 设置滑点
      slippage: 0
      # 设置手续费乘数，默认为1
      commission_multiplier: 1
      # 设置保证金乘数，默认为1
      margin_multiplier: 1
      # 在模拟交易和实盘交易中，RQAlpha支持策略的pause && resume，该选项表示开启 resume 功能
      resume_mode: false
      # 在模拟交易和实盘交易中，RQAlpha支持策略的pause && resume，该选项表示开启 persist 功能呢，
      # 其会在每个bar结束对进行策略的持仓、账户信息，用户的代码上线文等内容进行持久化
      persist: false
      persist_mode: real_time
      # 选择是否开启自动处理, 默认不开启
      handle_split: false

    extra:
      # 选择日期的输出等级，有 `verbose` | `info` | `warning` | `error` 等选项，您可以通过设置 `verbose` 来查看最详细的日志，
      # 或者设置 `error` 只查看错误级别的日志输出
      log_level: info
      user_system_log_disabled: false
      # 在回测结束后，选择是否查看图形化的收益曲线
      context_vars: ~
      # force_run_init_when_pt_resume: 在PT的resume模式时，是否强制执行用户init。主要用于用户改代码。
      force_run_init_when_pt_resume: false
      # enable_profiler: 是否启动性能分析
      enable_profiler: false
      is_hold: false

    validator:
      # cash_return_by_stock_delisted: 开启该项，当持仓股票退市时，按照退市价格返还现金
      cash_return_by_stock_delisted: false
      # close_amount: 在执行order_value操作时，进行实际下单数量的校验和scale，默认开启
      close_amount: true
      # bar_limit: 在处于涨跌停时，无法买进/卖出，默认开启
      bar_limit: true


    mod:
      # 回测 / 模拟交易 支持 Mod
      simulation:
        lib: 'rqalpha.mod.simulation'
        enabled: true
        priority: 100
      # 技术分析API
      funcat_api:
        lib: 'rqalpha.mod.funcat_api'
        enabled: false
        priority: 200
      # 开启该选项，可以在命令行查看回测进度
      progress:
        lib: 'rqalpha.mod.progress'
        enabled: false
        priority: 400
      # 接收实时行情运行
      simple_stock_realtime_trade:
        lib: 'rqalpha.mod.simple_stock_realtime_trade'
        persist_path: "./persist/strategy/"
        fps: 3
        enabled: false
        priority: 500
      # 渐进式输出运行结果
      progressive_output_csv:
        lib: 'rqalpha.mod.progressive_output_csv'
        enabled: false
        output_path: "./"
        priority: 600
      risk_manager:
        lib: 'rqalpha.mod.risk_manager'
        enabled: true
        priority: 700
        # available_cash: 查可用资金是否充足，默认开启
        available_cash: true
        # available_position: 检查可平仓位是否充足，默认开启
        available_position: true
      analyser:
        priority: 100
        enabled: true
        lib: 'rqalpha.mod.analyser'
        record: true
        output_file: ~
        plot: ~
        plot_save_file: ~
        report_save_path: ~


通过策略代码的方式
------------------------------------------------------

虽然在策略代码中进行相关配置并不是建议方案，但仍然提供了在策略代码中进行参数配置的可行性，具体配置的方式如下:

定义一个 `__config__` 的 dict 类型变量，设置具体可配置项和 `config.yml` 中的内容相似，但受到 `config.yml` 中的 `whitelist` 的限制，只能配置指定模块。

范例如下 :

..  code-block:: python3
    :linenos:

    # 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
    def init(context):

        #context内引入全局变量s1
        context.s1 = "IF88"

        #初始化时订阅合约行情。订阅之后的合约行情会在handle_bar中进行更新。
        subscribe(context.s1)
        # 实时打印日志
        logger.info("Interested in: " + str(context.s1))


    # 你选择的期货数据更新将会触发此段逻辑，例如日线或分钟线更新
    def handle_bar(context, bar_dict):
        # 开始编写你的主要的算法逻辑

        # bar_dict[order_book_id] 可以获取到当前期货合约的bar信息
        # context.portfolio 可以获取到当前投资组合状态信息
        # 使用buy_open(id_or_ins, amount)方法进行买入开仓操作
        buy_open(context.s1, 1)
        # TODO: 开始编写你的算法吧！


    __config__ = {
        "base": {
            "strategy_type": "future",
            "start_date": "2015-01-09",
            "end_date": "2015-03-09",
            "frequency": "1d",
            "matching_type": "next_bar",
            "future_starting_cash": 1000000,
            "commission_multiplier": 0.01,
            "benchmark": None,
        },
        "extra": {
            "log_level": "error",
        },
        "mod": {
            "progress": {
                "enabled": True,
                "priority": 400,
            },
        },
    }

通过引入 RQAlpha 库的方式执行
------------------------------------------------------

如果您需要通过代码的方式引入 RQAlpha 来执行则可以使用如下的方式：

.. code-block:: python3

  from rqalpha import run

  config = {
      "base": {
          "strategy_file": "./rqalpha/examples/buy_and_hold.py",
          "start_date": "2016-06-01",
          "end_date": "2016-12-01",
          "stock_starting_cash": 100000,
          "benchmark": "000300.XSHG",
      },
      "extra": {
          "log_level": "verbose",
      }
  }

  run(config)

创建一个 :code:`dict` 的变量并传入到 :code:`run` 函数中即可。具体的配置参数可以查看 :ref:`api-config-file` 的 yml 配置。


优先级
------------------------------------------------------

如果用户不指定 :code:`config.yml`, RQAlpha 会使用默认的 :code:`config.yml` 来配置所有参数的默认项，指定了配置文件，则不再使用默认配置文件，所以相对来说，:code:`config.yml` 的配置方式优先级是最低的。

策略代码中配置优先级 > 启动策略命令行传参 > 指定 :code:`config.yml` 文件 > 默认 :code:`config.yml` 文件
