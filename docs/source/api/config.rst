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

在设计 RQAlpha API 的时候，考虑到以上随时变化的需求，将这部分需要以参数的方式严格从代码层面剥离。同一份策略代码，通过启动策略时传入不同的参数来实现完全不同的策略开发、风控、运行和调优等的功能。

目前支持的参数如下：

*   `-d[--data-bundle-path]` : 数据源所存储的文件路径
*   `-f[--strategy-file]` : 启动的策略文件路径
*   `-s[--start-date]` : 回测起始日期
*   `-e[--end-date]` : 回测结束日期(如果是实盘，则忽略该配置)
*   `-r[--rid]` : 可以指定回测的唯一ID，用户区分多次回测的结果
*   `-i[--init-cash]` : [Deprecated]股票起始资金，不建议使用该参数，使用 `--stock-starting-cash` 代替。
*   `--stock-starting-cash` : 股票起始资金，默认为0
*   `--future-starting-cash` : 期货起始资金，默认为0
*   `--benchmark` : Benchmark，如果不设置，默认没有基准参照
*   `--slippage` : 设置滑点
*   `--commission-multiplier` : 设置手续费乘数，默认为1
*   `--margin-multiplier` : 设置保证金乘数，默认为1
*   `--kind` : 设置策略类型，目前支持 `stock` (股票策略)、`future` (期货策略)及 `stock_future` (混合策略)
*   `--frequency` : 目前支持 `1d` (日线回测) 和 `1m` (分钟线回测)，如果要进行分钟线，请注意是否拥有对应的数据源，目前开源版本是不提供对应的数据源的
*   `--match-engine` : 启用的回测引擎，目前支持 `current_bar` (当前Bar收盘价撮合) 和 `next_bar` (下一个Bar开盘价撮合)
*   `--run-type` : 运行类型，`b` 为回测，`p` 为模拟交易, `r` 为实盘交易
*   `--resume` : 在模拟交易和实盘交易中，RQAlpha支持策略的pause && resume，该选项表示开启 resume 功能
*   `--handle-split/--not-handle-split` : 选择是否开启自动处理, 默认不开启
*   `--risk-grid/--no-risk-grid` : 选择是否开启Alpha/Beta 等风险指标的实时计算，默认开启
*   `--log-level` : 选择日期的输出等级，有 `verbose` | `info` | `warning` | `error` 等选项，您可以通过设置 `verbose` 来查看最详细的日志，或者设置 `error` 只查看错误级别的日志输出
*   `--plot/--no-plot` : 在回测结束后，选择是否查看图形化的收益曲线
*   `-o[--output-file]` : 指定回测结束时将回测数据输出到指定文件中
*   `--fast-match` : 默认关闭，如果当前撮合引擎为 `current_bar` 开启该选项会立刻进行撮合，不会等到当前bar结束
*   `--progress/--no-progress` : 开启该选项，可以在命令行查看回测进度


