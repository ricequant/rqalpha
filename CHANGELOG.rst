==================
CHANGELOG
==================

4.3.3
==================

- 回测和模拟交易的 :code:`--matching-type` 参数支持传入 :code:`vwap` 以启用成交量加权平均价撮合
- 股票下单 API 中限制散股交易的逻辑针对科创板股票进行了适配


4.3.2
==================

- **新增**

  - :code:`history_bars` 的 frequency 参数支持传入 :code`'1w'` 以获取周线

- **修复**

  - 修复 :code:`Order` 对象从持久化中恢复出错的问题
  - 修复通过策略内配置项配置股票分红再投资参数无效的问题
  - 修复合约在某些日期无行情导致基准收益曲线计算有误的问题
  - 修复 :code:`Order` 对象 :code:`avg_price` 字段计算有误的问题
  - 修复通过 :code:`order_target_portfolio` API 发出的订单验资风控异常的问题


4.3.0
==================

- **新增**

  - 新增出入金 API :code:`withdraw` 和 :code:`deposit`，用于为指定账户出金/入金
  - 新增使用资产收益加权作为基准的功能，参数形如 :code:`--benchmark 000300.XSHG:0.5,510050.XSHG:-1`
  - 新增按日簿记账户管理费用的功能，参数形如 :code:`--management-fee stock 0.0002`
  - :code:`Trade` 类的构造函数增加了关键字参数

- **重构**

  - 重构了 :code:`BaseDataSource` 所使用的 :code:`InstrumentStore`，使得通过 mod 扩展支持的资产品种变得更加容易
  - 重构了 :code:`AbstractDataSource` 中的 instruments 的相关接口
  - 不再支持在日级别回测中使用"下一个 bar 撮合"


4.2.5
==================

- 修复了访问持仓对象 :code:`closable` 字段会抛出异常的 bug


4.2.4
==================

- :code:`rqalpha-mod-sys-simulation` 增加配置项 :code:`inactive_limit`，开启该选项可禁止订单在成交量为 0 的 bar 成交
- :code:`rqalpha-mod-sys-transaction-cost` 增加 :code:`tax_multiplier` 配置项，用于设置印花税倍率
- :code:`Order` 类的构造函数增加关键字参数
- 移除 :code:`AbstractAccount` 接口
- 移动部分 module 至 :code:`rqalpha.core` package


4.2.1
==================

- 移除了 :code:`--disable-user-log` 及 :code:`--disable-user-system-log` 命令行参数
- 修复了 :code:`index_weights` 抛出异常的 bug
- 修复了安装某些版本 rqdatac 时更新 bundle 出现异常的问题
- 移除了部分兼容 python2 的代码、重构了 :code:`BaseDataSource` 的部分代码


4.1.4
==================

- 增加了通过环境变量 RQALPHA_PROXY 设置代理的功能
- 修复了设置初始仓位后会抛出异常的 bug
- 修复了股票拆分后持仓收益计算错误的 bug


4.1.3
==================

- 修复了在部分 windows 计算机上打开 bundle 时报错的问题


4.1.2
==================

- 修复了 base_data_source 导致的债券回测报错的问题


4.1.1
==================

- 修复了部分期货下单 API 平今仓会报错的问题
- 回测输出的收益图改为使用结算后的累计收益绘制（之前版本为 after_trading 后的累计收益）


4.1.0
==================

**[For 开发/运行策略的用户]**

- 移除了回测报告中的 Excel 文件，所有信息均可在 csv 文件中找到
- 使用 IDE 编写策略的用户可通过执行 :code:`from rqalpha.apis import *` 以获得大部分 API 的代码提示
- 修复了若干 4.0.0 版本引入的 bug

**[For Mod 开发者]**

- 下单 API 加入了 "singledispatch" 功能，mod 可为这些 API 针对不同的合约类型注册不同的实现，用法可参考 `sys_mod_accounts.api`_
- :code:`SimulationBroker` 增加 :code:`register_matcher` 方法，mod 可为不同类型的合约注册不同撮合器已实现多样化的撮合逻辑
- 重构 :code:`rqalpha.portfolio.position.Position` 类，自定义的持仓类只要继承该类并重写 :code:`__instrument_types__` 属性便可自动注册持仓类，可参考 `sys_mod_accounts.position_model`_
- 为 :code:`Instrument` 类添加 :code:`account_type` property，Instrument 子类可通过重写该 property 标明该 Instrument 的持仓归属于哪个账户

.. _sys_mod_accounts.api: https://github.com/ricequant/rqalpha/tree/master/rqalpha/mod/rqalpha_mod_sys_accounts/api
.. _sys_mod_accounts.position_model: https://github.com/ricequant/rqalpha/blob/master/rqalpha/mod/rqalpha_mod_sys_accounts/position_model.py

4.0.0
==================


**[For 开发/运行策略的用户]**

对于开发/运行策略的用户，RQAlpha 4.x 版本改动的核心是加强与 `RQDatac`_ 之间的联动，拥有 RQDatac license 的用户可以更及时地更新 bundle，
亦可以在开源的 RQAlpha 框架下直接调用从前在 Ricequant 网站或终端产品中才能使用的扩展 API。

- **新增**

  - 新增集合竞价函数 :code:`open_auction` ，您可以在该函数内发单以实现开盘成交，详见 :ref:`api-base-api`
  - 新增扩展 API 的实现，现在您可以在开源的 rqalpha 框架下直接调用扩展 API，详见 :ref:`api-extend-api`
  - 新增股票下单 API，``order_target_portfolio``，使用该 API 可以根据给定的目标组合仓位批量下单，详见 :ref:`api-base-api-order-api`

- **变更**

  - ``rqalpha update-bundle`` 命令的功能改为使用 RQDatac 更新已存在的数据 bundle，新增 ``rqalpha download-bundle`` 和 ``rqalpha create-bundle`` 命令用于下载和创建 bundle，详见 :ref:`intro-install-get-data`
  - ``line-profiler`` 库不再是 RQAlpha 的硬性依赖，如果您需要性能分析功能，则需要手动安装 ``line-profiler``，详见 :ref:`intro-faq`
  - 配置项中股票和期货验券风控的开关 ``validate_stock_position`` 和 ``validate_future_position`` 移动到了 :code:`rqalpha_mod_sys_accounts`，详见 `rqalpha_mod_sys_accounts`_
  - 传入 ``--report`` 参数后输出的策略报告文件将直接生成于 ``--report`` 参数值给定的目录下，不再在该目录下新建以策略名为名称的文件夹

- **废弃**

  - 不再支持 Python2.7
  - ``context.portfolio.positions`` 可能会在未来版本中废弃，推荐使用 ``get_position`` 和 ``get_positions`` API 获取仓位信息，详见 :ref:`api-position-api`
  - ``context`` 对象的部分老旧属性已移除，如 ``stock_portfolio``、``future_portfolio``、``slippage``、``benchmark``、``margin_rate``、``commission`` 等，详见 :ref:`api-base-types`


**[For Mod 开发者]**

RQAlpha 4.x 相对于 3.x 版本进行了部分重构，重构的核心目标是 Mod 开发者可以更方便地对接不同品种的金融工具。

- :code:`BaseDataSource` 新增 ``register_day_bar_store``、``register_instruments_store``、``register_dividend_store``、``register_split_store``、``register_calendar_store`` 方法，用于在不重载 :code:`DataSource` 的情况下对接更丰富的行情及基础数据
- 移除 ``rqalpha mod install/uninstall`` 命令，您可以使用 ``pip install/uninstall`` 命令替代，详见 :ref:`development-mod`
- :code:`Environment` 移除 ``set_account_model``、``get_account_model`` 方法，默认的 :code:`Account` 类现在可以支持挂载不同类型的金融工具持仓，大多数情况下无需重载 :code:`Account` 类
- :code:`Environment` 移除 ``set_position_model``、``get_position_model`` 方法，重载的 :code:`Position` 类型可以调用 :code:`Portfolio.register_instrument_type` 注册
- 重构了 :code:`AbstractPosition` 接口，现在的 :code:`Position` 对象仅表征单个方向的持仓，而非包含多空两方向的持仓，详见 :ref:`development-basic-concept`
- 移除了 :code:`BenchmarkProvider` 接口，基准相关的逻辑转移到 :code:`rqalpha_mod_sys_analyser` 内部
- :code:`BaseDataSource` 使用的 bundle 格式由 bcolz 替换为 hdf5
- 移除 Mod: ``rqalpha_mod_sys_funcat``、``rqalpha_mod_sys_benchmark``
- :code:`Instrument` 新增 ``calc_cash_occupation`` 方法，该方法被风控等模块用于计算订单需要占用的资金量，对接新品种的金融工具应重载该方法
- 移除了以下冗余的 logger 对象：``user_detail_log``、``basic_system_log``、``std_log``

.. _RQDatac: https://www.ricequant.com/welcome/rqdata
.. _rqalpha_mod_sys_accounts: https://github.com/ricequant/rqalpha/tree/master/rqalpha/mod/rqalpha_mod_sys_accounts


3.4.4
==================

- **修复**

  - 修复 ``rqalpha mod install/uninstall`` 命令与 pip 19.3.1 的兼容性问题

- **变更**

  - :code:`history_bars` 取不到行情时返回空 ndarray 而非 None


3.4.2
==================

- **变更**

  - 移除代码中硬编码的期货交易时间、佣金费率等信息，期货新品种上市不再需要更新 RQAlpha 版本，只需更新 bundle 数据（:ref:`intro-install-get-data`）
  - 变更 :code:`rqalpha.data` 的目录结构
  - :code:`rqalpha.utils.get_trading_period` 和 :code:`rqalpha.utils.is_night_trading` 函数变更为 :code:`DataProxy` 的方法
  - 调整下载 bundle 的 URL

- **新增**

  - :code:`Instrument` 对象新增交易时间相关的 :code:`trading_hours` 和 :code:`trade_at_night` property


3.4.1
==================

- **新增**

  - 对期货 SS, EB 的支持

- **变更**

  - 调整下载 bundle 的 URL，提高 bundle 下载速度

- **修复**

  - 股票/期货上市首日调用 pnl 相关属性抛出异常的问题
  - 股票股权登记日和分红到账日间隔多个交易日时分红计算错误的问题


3.4.0
==================

- **新增**

  - 股票下单 API 加入资金不足时自动转为使用所有剩余资金下单的功能，见 `rqalpha_mod_sys_accounts <https://github.com/ricequant/rqalpha/tree/master/rqalpha/mod/rqalpha_mod_sys_accounts>`_

- **变更**

  - 重构 :code:`rqalpha_mod_sys_accounts` 中的账户、持仓类，主要变化如下：

    - 持仓类拆分为两层，核心同时兼容期货和股票的逻辑，上层兼容绝大部分旧有 API
    - 期货保证金的计算逻辑改为跟随行情变化的动态保证金、不再维护持仓序列
    - 新增 :code:`position_pnl` 昨仓盈亏、:code:`trading_pnl` 交易盈亏字段
    - 删除 :code:`holding_pnl` 持仓盈亏、:code:`realized_pnl` 实现盈亏字段
    - 降低账户类和持仓类之间的耦合程度

  - 去掉配置项 :code:`base.resume_mode` 和 :code:`extra.force_run_init_when_pt_resume`，相关判断移交给 :code:`PersistProvider` 实现
  - 去掉 :code:`Booking` 类，相关逻辑合并至持仓类


3.3.3
==================

- **新增**

  - 对期货 NR、UR、RR 的支持

- **修复**

  - Python2.7 环境下依赖的 numpy 版本不正确的问题
  - 进程启动后初次触发 settlement 事件时框架内部时间可能不正确的问题
  - 期货下单 API 未拒绝不足一手的下单请求的问题


3.3.2
==================

- **新增**

  - :code:`SelfTradeValidator` 模块，用于拦截策略可能产生自成交的订单
  - :code:`buy_close`、:code:`sell_close` API 将订单拆分成多个时给出 WARNING 提示
  - 对股票更换代码这一行为的支持
  - 对期货 CJ 品种的支持


- **变更**

  - 不再支持 Python3.4


- **修复**

  - :code:`Booking` 持久化逻辑错误的问题
  - 指数的 :code:`Bar` 对象获取 :code:`limit_up`、:code:`limit_down` 字段报错的问题
  - 策略订阅的合约交易时间与基准合约交易时间不一致会导致模拟交易报错退出的问题
  - 股票在同一个交易日出现多次分红时计算有误的问题
  - :code:`order_value` 等 API 在市价单时计算下单量有误的问题
  - 信号模式下仍然会拦截在标的涨跌停时下出的订单


3.3.1
==================

- **新增**

  - 对期货 SP, EG 品种的支持。
  - 加入 python3.7 环境下的自动化测试。
  - 使用 :code:`run_func` 运行的策略不再需要显式地执行 :code:`from rqalpha.api import *`。
  - :code:`update-bundle` 命令增加中断重试功能。
  - 增加 :code:`MinuteBarObject` 对象，当分钟线数据不包含涨跌停价时该对象的涨跌停字段改为从日线获取。


- **变更**

  - 年化（如收益率）的计算改为使用交易日而非是自然日。
  - 基准收益率不再使用全仓买入基准合约模拟，改为直接使用前复权价格序列计算。
  - 策略使用 :code:`subscribe_event` 注册的回调函数改为接收两个参数 :code:`context`, :code:`event`。
  - 重构了 :code:`Booking` 的计算逻辑，增加了 :code:`trading_pnl`, :code:`position_pnl` 两个字段。
  - 抽离 :code:`risk.py` 为 `rqrisk <https://github.com/ricequant/rqrisk>`_ 项目。
  - :code:`order_value` 等使用价值计算股数的下单 API 计算股数时增加对税费的考虑（即计算包含税费的情况下花费一定数量的现金可以交易多少合约）。


- **修复**

  - 净值为负的情况下 :code:`Portfolio` 年化收益率计算有误的问题。
  - :code:`Portfolio` 对象不存在的情况下某些 API 的报错信息不明确的问题。
  - :code:`RunInfo` 对象中的 :code:`commission_multiplier` 字段不正确的问题。
  - 期货 tick 回测/模拟交易下滑点计算报错的问题。
  - 模拟交易和实盘中调用 :code:`submit_order` 发送代码中包含 "88" 的股票订单报错的问题。
  - 限价单 round price 的精度问题。
  - 策略使用 :code:`subscribe_event` 注册的回调函数和框架内部逻辑触发顺序不可控的问题。
  - 回测和模拟交易中股票市价单冻结和解冻的资金可能出现不一致的问题。


3.2.0
==================

- **配置和命令**

  - :code:`rqalpha run` 命令增加参数 :code:`-mk/--market`，用来标识策略交易标的所在的市场，如 cn、hk 等。
  - :code:`rqalpha update_bundle` 更改为 :code:`rqalpha update-bundle`。

- **接口和 Mod**

  - 增加新接口 :code:`AbstractTransactionCostDecider`，在 :code:`Environment` 中注册该接口的实现可以自定义不同合约品种、不同市场的税费计算逻辑。
  - 增加新 Mod :code:`sys_transaction_cost` 实现上述接口，抽离了原 :code:`sys_simulation` Mod 中的税费计算逻辑，并加入了对港股税费计算的支持。
  - 移除 :code:`sys_booking` Mod，booking 相关逻辑移入框架中，:code:`Booking` 与 :code:`Portfolio` 类地位相当。
  - 移除 :code:`sys_stock_realtime` Mod，该 Mod 被移到了单独的仓库 `rqalpha-mod-stock-realtime <https://github.com/ricequant/rqalpha-mod-stock-realtime>`_ ，不再与框架一同维护。
  - 移除 :code:`sys_stock_incremental` Mod，该 Mod 被移到了单独的仓库 `rqalpha-mod-incremental <https://github.com/ricequant/rqalpha-mod-incremental>`_ ，不再与框架一同维护。


- **类型和 Api**

  - 增加 :code:`SimulationBooking` 类，实现了 :code:`Booking` 类相同的方法，用于在回测和模拟交易中兼容实盘 :code:`Booking` 相关的 Api。
  - 增加 Api :code:`get_position` 和 :code:`get_positions`，用来获取策略持仓的 :code:`BookingPosition` 对象。
  - 增加 Api :code:`subscribe_event`，策略可以通过该 Api 注册回调函数，订阅框架内部事件。
  - :code:`DEFAULT_ACCOUNT_TYPE` 枚举类增加债券 :code:`BOND` 类型。
  - :code:`history_bars` 在 :code:`before_trading` 中调用时可以取到当日日线数据。
  - 重构 :code:`Instrument` 类，该类所需的字段现在以 property 的形式写明，方便对 Instrument 对象的调用及对接第三方数据源。
  - :code:`Instrument` 类型新增字段 :code:`market_tplus`，用来标识合约对平仓时间的限制，例如有 T+1 限制的 A 股该字段值为1，港股为 0。


- **逻辑**

  - 更改 Benchmark 的买入逻辑，不再对买入数量进行取整，避免初始资金较小时 Benchmark 空仓的问题。
  - 修正画图时最大回撤的计算逻辑。
  - 修正年化收益的计算逻辑，年化的天数的计算使用 :code:`start_date`、:code:`end_date`，而非根据交易日历调整后的日期。
  - 下单冻结资金时考虑税费。
  - 前端风控验资时考虑税费。
  - 修复了 :code:`before_trading` 中更新订阅池会可能会导致开盘收到错误 tick 的 Bug。
  - 修复 beta 值为 0 时 plot result 出错的问题。
  - 重构 A 股 T+1 的相关逻辑，移除 hard code。
  - 滑点计算增加对涨跌停价的判断，现在有涨跌停价的合约滑点不会超出涨跌停价的范围。
  - 修复在取不到行情时下单可能会抛出 RuntimeError 的 Bug。


- **依赖**

  - 在 Python2.7 和 Python3.4 环境中限制 Matplotlib 的版本。
  - 移除了测试用例对 Pandas 的版本依赖。
  - 不再限制 Pandas 的版本上限。
  - 移除对 colorama 库的依赖。
  - 限制 click 库的版本下限为 7.0。


- **其他**

  - 加入对期货 TS 品种的支持。
  - 模拟交易和实盘中支持持久化自定义类型（可被 pickle 的自定义类型）。
  - 增加了单元测试框架并添加了少量测试用例。

3.1.2
==================

- 修复上个版本打包时包含异常文件的问题。

3.1.1
==================

- 修复 :code:`rqalpha mod uninstall` 命令不兼容 pip 10.0 以上版本的bug。
- 不再限制 logbook 库的版本上限。
- python 2.7/3.5/3.6 环境下不再限制 bcolz 的版本上限。

3.1.0
==================

- Api

  - 增加 :code:`symbol(order_book_id, split=", ")` 扩展Api，用于获取合约简称。
  - 修改 :code:`current_snapshot(id_or_symbol)`，该 Api 支持在 before_trading/after_trading 中调用。
  - 修改 :code:`history_bars`，增加对 :code:`frequency` 参数的检查。
  - 修正 :code:`order(order_book_id, quantity, price=None, style=None)` 函数期货下单的逻辑。
  - 修改股票下单接口，允许一次性申报卖出非100股整倍数的股票。
  - 修改下单接口，当因参数检查或前端风控等原因创建订单失败时，接口返回 None 或空 list，并打印 warn。


- 接口

  - :code:`AbstractDataSource` 接口增加 :code:`get_tick_size(instrument)` 方法，:code:`BaseDataSource` 实现了该方法。
  - :code:`AbstractDataSource` 接口增加 :code:`history_ticks(instrument, count, fields, dt)` 方法，支持 tick 级别策略运行的 DataSource 应实现该方法。
  - 增加通用下单接口 :code:`submit_order(id_or_ins, amount, side, price=None, position_effect=None)`，策略可以通过该接口自由选择参数下单。


- 类

  - :code:`Instrument` 类新增 :code:`tick_size()` 方法。
  - :code:`PersistHelper` 类新增 :code:`unregister(key)` 方法，可以调用该方法注销已经注册了持久化服务的模块。
  - 新增 :code:`TickObject` 类，替代原 :code:`Tick` 类和 :code:`SnapshotObject` 类。可通过 :code:`TickObject` 对象的 asks, bids, ask_vols, bid_bols 四个属性获取买卖报盘。

- 配置

  - 增加 :code:`base.round_price` 参数，开启后现价单价格会被调整为最小价格变动单位的整倍数，对应的命令行参数为 :code:`--round-price`。
  - :code:`sys_simulation Mod` 增加滑点模型 :code:`slippage_model` 参数，滑点不再限制为价格的比率，亦可使用基于最小价格变动单位的滑点模型，甚至加载自定义的滑点模型。
  - :code:`sys_simulation Mod` 增加股票最小手续费 :code:`stock_min_commission` 参数，用于控制回测和模拟交易中单笔股票交易收取的最小手续费，对应的命令行参数为 :code:`--stock-min-commission 5`
  - :code:`sys_account Mod` 增加 :code:`future_forced_liquidation` 参数，开启后期货账户在爆仓时会被强平。

- 其他

  - Fix `Issue 224 <https://github.com/ricequant/rqalpha/issues/224>`_ ， 解决了展示图像时图像不能被保存的问题。
  - 策略运行失败时 return code 为 1。
  - 开启 :code:`force_run_init_when_pt_resume` 参数时，策略启动前将会清空 universe。
  - 移除对 `better-exceptions <https://github.com/Qix-/better-exceptions>`_ 库的依赖，可以通过安装并设置环境变量的方式获得更详细的错误栈。
  - 修复 :code:`StockPosition` 类中股票卖空买回时计算平均开仓价格错误的 bug。
  - 修复画图时最大回撤计算错误的 bug。
  - 重构 :code:`Executor`，现在 EventSource 不再需要发出 SETTLEMENT 事件，框架会在第二个交易日 BEFORE_TRAINDG 事件前先发出 SETTLEMENT 事件，如果 EventSource 未发出 BEFORE_TRAINDG 事件，该事件会在第一个行情事件到来时被框架发出。
  - 加入新 Mod :code:`rqalpha_mod_sys_incremental`，启用该 Mod 可以增量运行回测，方便长期跟踪策略而不必反复运行跑过的日期，详情参考文档 `sys_incremental Mod README <https://github.com/ricequant/rqalpha/blob/master/rqalpha/mod/rqalpha_mod_sys_incremental/README.rst>`_。
  - 加入新 Mod :code:`rqalpha_mod_sys_booking`，该 Mod 用于从外部加载仓位作为实盘交易的初始仓位，详情参考文档 `sys_booking Mod README <https://github.com/ricequant/rqalpha/blob/master/rqalpha/mod/rqalpha_mod_sys_booking/README.rst>`_。

3.0.10
==================

- 支持期货合约：苹果（AP）、棉纱（CY）、原油（SC）
- 限制 :code:`better-exceptions`、:code:`bcolz` 库的版本
- 支持 pip 10.x
- 修复 tick 回测中夜盘前 before_trading 无法获取白天数据的问题
- 当 :code:`force_run_init_when_pt_resume` 开启时会清空 persist 的 universe
- 增加资金风控中对佣金的考虑
- 修复文档中若干 typo

3.0.9
==================

- 限制 pandas 的版本为 0.18 ~ 0.20 ，因为 0.21 和 matplotlib 有些不兼容。

3.0.8
==================

- 修复 :code:`rqalpha run --config` 参数
- 增加 ON_NORMAL_EXIT 的持久化模式，在 RQAlpha 成功运行完毕后进行 persist 。可以在盘后快速地根据昨日持久化数据继续运行回测来增量回测。
- 增加 :code:`rqalpha run --logger` 参数可以单独设置特定的 logger 的 level
- 增加 persist_provider 的检查
- 修复 :code:`get_prev_close`
- 打印 mod 的启动状态信息，方便 debug
- 增加 :code:`is_valid_price` 工具函数来判断价格是否有效
- 修复期货账户因为保证金变化导致total_value计算错误
- 重构股票账户 :code:`last_price` 更新
- 修复期货下单拒单是错误信息typo
- 当启动LIVE_TRADING模式的时候，跳过simulation_mod的初始化
- 增加 :code:`rqalpha run --position` 来设置初始仓位的功能
-

3.0.6
==================

- import 修改相对引用为绝对引用
- 重构配置文件读取功能，分为默认配置，用户配置，项目配置
- 重构 `main()` 的 `tear_down` 的调用
- get_previous_trading_date(date, n=1) 增加参数 n
- 增加公募基金数据处理相关逻辑
- 修改 `mod.tear_down` ，如果单个 mod 在 tear_down 抛异常后，不影响其他 mod 继续 tear_down
- scheduler bugfix
- 处理 persist 遇到的异常
- 修复 order get_state / set_state 缺失 transaction_cost, avg_price
- 修复 mod_sys_stock_realtime

3.0.2
==================

- 取消在股票下单函数中对 `order_book_id` 类型的检查，现在您可以交易 `ETF`, `LOF`, `FenjiMu`, `FenjiA`, `FenjiB`, `INDX` 了
- Merge `PR 170 <https://github.com/ricequant/rqalpha/pull/170>`_ 解决自定义 `volume limit` 时显示数值不正确的问题。
- Fix `Issue 148 <https://github.com/ricequant/rqalpha/issues/148>`_ `get_dividend()方法返回的类型是numpy.ndarray，而非pandas.DataFrame`
- Fix `Issue 169 <https://github.com/ricequant/rqalpha/issues/169>`_ 执行 `rqalpha mod install ctp==0.2.0dev0` 时错误的记录了库信息的问题
- Fix `Issue 158 <https://github.com/ricequant/rqalpha/issues/158>`_ 多次循环 `run_file` / `run_code` 时导致的内存泄漏的问题
- Enhance `Issue 166 <https://github.com/ricequant/rqalpha/issues/166>`_ 启动参数支持 `--no-stock-t1` 来屏蔽股票 T + 1 导致今仓的限制
- 性能提升: 使用 `bisect_right` 代替 `searchsorted`

3.0.0
==================

**[For 开发/运行策略的用户]**

3.x 相比 2.x 进行了如下更改，如果您升级到 3.x 版本，请务必阅读以下内容，保证您的策略可以顺利启动和执行:

- 命令行参数做出如下调整

  - 不再使用 :code:`-sc/--stock-starting-cash` 参数
  - 不再使用 :code:`-fc/--future-starting-cash` 参数
  - 不再使用 :code:`-i/--init-cash` 参数
  - 不再使用 :code:`-s/--security` 参数
  - 不再使用 :code:`-k/--kind` 参数
  - 不再使用 :code:`--strategy-type` 参数
  - **使用** :code:`--account` 来替代，具体用法如下

.. code-block:: bash

  # 策略通过命令行运行，设置可交易类型是股票，起始资金为 10000
  $ rqalpha run --account stock 10000
  # 策略通过命令行运行，设置可交易类型为期货，起始资金为 50000
  $ rqalpha run --account future 50000
  # 策略通过命令行运行，设置可交易类型为期货和股票，起始资金分别为 股票 10000, 期货 50000
  $ rqalpha run --account stock 10000 --account future 50000
  # 如果您通过 Mod 扩展，自定义了一种可交易类型(假设是huobi)，您也可以增加对于火币的支持和起始资金设置
  $ rqalpha run --account stock 10000 --account future 50000 --account huobi 20000

- 相应，如果您通过 :code:`run_file | run_code | run_func` 来启动策略，配置文件及配置信息也做了对应的调整:

  - 不再使用 :code:`base.stock_starting_cash`
  - 不再使用 :code:`base.future_starting_cash`
  - 不再使用 :code:`base.securities`
  - **使用** :code:`base.accounts` 来替代，具体用法如下:

.. code-block:: python

  # 策略通过配置，设置可交易类型是股票，起始资金为 10000
  config = {
    "base": {
      "start_date": "...",
      "end_date": "...",
      "frequency": "...",
      "matching_type": "...",
      "benchmark": "...",
      "accounts": {
        "stock": 10000
      }
    }
  }
  # 策略通过配置，设置可交易类型是期货，起始资金为 50000
  config = {
    "base": {
      "start_date": "...",
      "end_date": "...",
      "frequency": "...",
      "matching_type": "...",
      "benchmark": "...",
      "accounts": {
        "future": 50000
      }
    }
  }
  # 策略通过配置，设置可交易类型为期货和股票，起始资金分别为 股票 10000, 期货 50000
  config = {
    "base": {
      "start_date": "...",
      "end_date": "...",
      "frequency": "...",
      "matching_type": "...",
      "benchmark": "...",
      "accounts": {
        "stock": 10000,
        "future": 50000
      }
    }
  }
  # 如果您通过 Mod 扩展，自定义了一种可交易类型(假设是huobi)，您也可以增加对于火币的支持和起始资金设置
  config = {
    "base": {
      "start_date": "...",
      "end_date": "...",
      "frequency": "...",
      "matching_type": "...",
      "benchmark": "...",
      "accounts": {
        "stock": 10000,
        "future": 50000,
        "huobi": 20000
      }
    }
  }



**[For Mod developer]**

本次更新可能导致已实现 Mod 无法正常使用，请按照文档升级您的 Mod，或者使用 2.2.x 版本 RQAlpha

在通过 Mod 扩展 RQAlpha 的时候，由于 RQAlpha 直接定义了 `Account` 和 `Position` 相关的 Model, 增加新的 `account` 和 `position` 变得非常的困难，想扩展更多类型是一件很麻烦的事情，因此我们决定重构该模块从而解决这些问题。

详情请查看: https://github.com/ricequant/rqalpha/issues/160

主要进行如下更改:

- 增加 :code:`AbstractAccount` 和 :code:`AbstractPosition`, 用户可以基于该抽象类进行扩展。
- :code:`const.ACCOUNT_TYPE` 修改为 :code:`const.DEFAULT_ACCOUNT_TYPE`，并且不再直接使用，您可以通过 :code:`Environment.get_instance().account_type_dict` 来获取包括 Mod 注入的账户类型。
- 原先所有使用 `ACCOUNT_TYPE` 作为 key 的地方，不再使用 Enum 类型作为 Key, 而是修改为对应 Enum 的 name 作为key。比如说原本使用 :code:`portfolio.accounts[ACCOUNT_TYPE.STOCK]` 更改为 :code:`portfolio.accounts['STOCK']`
- :code:`Environment` 提供 :code:`set_account_model` | :code:`get_account_model` | :code:`set_position_model` | :code:`get_position_model` API 来注入 自定义Model。
- :code:`Environment` 提供 :code:`set_smart_order` API 来注入自定义账户类型的智能下单函数，从而通过通用的 :code:`order` | :code:`order_to` API 便可以交易对应自定义账户类型。
- RQAlpha 将已有的 AccountModel, PositionModel 和 API 抽离至 `rqalpha_mod_sys_accounts` 中，通过如下方式注入:

.. code-block:: python

  from .account_model import *
  from .position_model import *
  from .api import api_future, api_stock


  class AccountMod(AbstractMod):

      def start_up(self, env, mod_config):

          # 注入 Account
          env.set_account_model(DEFAULT_ACCOUNT_TYPE.STOCK.name, StockAccount)
          env.set_account_model(DEFAULT_ACCOUNT_TYPE.FUTURE.name, FutureAccount)
          env.set_account_model(DEFAULT_ACCOUNT_TYPE.BENCHMARK.name, BenchmarkAccount)

          # 注入 Position
          env.set_position_model(DEFAULT_ACCOUNT_TYPE.STOCK.name, StockPosition)
          env.set_position_model(DEFAULT_ACCOUNT_TYPE.FUTURE.name, FuturePosition)
          env.set_position_model(DEFAULT_ACCOUNT_TYPE.BENCHMARK.name, StockPosition)

          # 注入 API
          if DEFAULT_ACCOUNT_TYPE.FUTURE.name in env.config.base.accounts:
              # 注入期货API
              for export_name in api_future.__all__:
                  export_as_api(getattr(api_future, export_name))
              # 注入 smart order
              env.set_smart_order(DEFAULT_ACCOUNT_TYPE.FUTURE.name, api_future.smart_order)
          if DEFAULT_ACCOUNT_TYPE.STOCK.name in env.config.base.accounts:
              # 注入股票API
              for export_name in api_stock.__all__:
                  export_as_api(getattr(api_stock, export_name))
              # 注入 smart order
              env.set_smart_order(DEFAULT_ACCOUNT_TYPE.STOCK.name, api_stock.smart_order)

      def tear_down(self, code, exception=None):
          pass


2.2.7
==================

- 解决当存在无效 Mod 时，RQAlpha 崩溃无法启动的问题
- 修复期货下单函数默认 style 为 None 导致报错退出的问题

2.2.5
==================

- 增加 IPython Magic 方便在 IPython 中运行回测 `run-rqalpha-in-ipython.ipynb <https://github.com/ricequant/rqalpha/blob/master/docs/source/notebooks/run-rqalpha-in-ipython.ipynb>`_ 。运行完回测后，会将所有的 mod 的输出结果保存在 results 变量中，并且会将回测报告存储在 report 对象中。
- 修复系统异常、用户异常的区分判断
- 增加 :code:`--source-code` 参数可以直接在命令行中传入策略源代码进行回测，这个选项目前主要给 IPython 使用。
- 对于 :code:`history_bars` 当 fields 为 None 的时候，指定为 ["datetime", "open", "high", "low", "close", "volume"] 。
- 重构 rqalpha_mod_sys_funcat 的数据获取
- 修复 order 的 set_state 的 bug
- 优化分红计算
- 提取 inject_mod_commands 给 click 参数注入

.. code-block:: python

  # 加载 rqalpha 插件
  %load_ext rqalpha

  # 运行回测
  %% rqalpha -s 20160101 -e 20170101 -sc 100000

2.2.4
==================

- 所有的下单函数进行了扩展，扩展如下:

.. code-block:: python

  # 以 order_shares 举例，其他的下单函数同理。
  # 原本的下单方式: 以 200 元的价格下单 100 股 000001.XSHE
  order_shares("000001.XSHE", 100, style=LimitOrder(200))
  # 下单的如下方式都OK:
  order_shares("000001.XSHE", 100, 200)
  order_shares("000001.XSHE", 100, LimitOrder(200))
  order_shares("000001.XSHE", 100, price=200)
  order_shares("000001.XSHE", 100, style=LimitOrder(200))

- :code:`buy_close` 和 :code:`sell_close` API 增加 :code:`close_today` 参数，现在您现在可以指定发平今单了。
- Breaking Change: 原本期货中的 :code:`buy_close` 和 :code:`sell_close` API 返回的 :code:`Order` 对象。但实际交易过程中，涉及到昨仓今仓的时候，可能会存在发单被拒单的情况，RQAlpha 进行平昨/平今智能拆单的处理，因此在一些情况下会生成多个订单，对应也会返回一个订单列表。期货平仓更新的内容请参考 `Issue 116 <https://github.com/ricequant/rqalpha/issues/116>`_
- Breaking Change: 取消 :code:`Order` | :code:`Trade` 对应的 :code:`__from_create__` 函数中 :code:`calendar_dt` 和 :code:`trading_dt` 的传入，对接第三方交易源，构建订单和成交的 Mod 可能会产生影响，需要进行修改.

.. code-block:: python

  # 原先的构建方式
  Order.__from_create__(
    calendar_dt,
    trading_dt,
    order_book_id,
    amount,
    side,
    style,
    position_effect
  )
  #修改为
  Order.__from_create__(
    order_book_id,
    amount,
    side,
    style,
    position_effect
  )

- `iPython` 更新至 6.0 版本以后不再支持 `Python 2.x` 导致在 `Python 2.x` 下安装RQAlpha 因为 `line-profiler` 依赖 `iPython` 的缘故而报错。目前增加了在 `Python 2.x` 下依赖 `iPython 5.3.0` 版本解决此问题。
- 不再提供 `rqalpha-cmd` 命令的扩展和注入，目前只有一个 entry point: `rqalpha` 第三方 Mod 可以扩展 `rqalpha` 命令。
- 增加 :code:`from rqalpha import subscribe_event` 来支持事件订阅(暂时不增加到API中，您如果想在策略里使用，也需要主动 import 该函数), 如下示例所示:

.. code-block:: python

  from rqalpha.api import *
  from rqalpha import subscribe_event


  def on_trade_handler(event):
      trade = event.trade
      order = event.order
      account = event.account
      logger.info("*" * 10 + "Trade Handler" + "*" * 10)
      logger.info(trade)
      logger.info(order)
      logger.info(account)


  def on_order_handler(event):
      order = event.order
      logger.info("*" * 10 + "Order Handler" + "*" * 10)
      logger.info(order)


  def init(context):
      logger.info("init")
      context.s1 = "000001.XSHE"
      update_universe(context.s1)
      context.fired = False
      subscribe_event(EVENT.TRADE, on_trade_handler)
      subscribe_event(EVENT.ORDER_CREATION_PASS, on_order_handler)


  def before_trading(context):
      pass


  def handle_bar(context, bar_dict):
      if not context.fired:
          order_percent(context.s1, 1)
          context.fired = True

  # rqalpha run -f ./rqalpha/examples/subscribe_event.py -s 2016-06-01 -e 2016-12-01 --stock-starting-cash 100000 --benchmark 000300.XSHG

- `sys_stock_realtime` 提供了一个行情下载服务，启动该服务，会实时往 redis 中写入全市场股票行情数据。多个 RQAlpha 可以连接该 redis 获取实时盘口数据，就不需要重复获取数据。详情参考文档 `sys stock realtime mod README <https://github.com/ricequant/rqalpha/blob/master/rqalpha/mod/rqalpha_mod_sys_stock_realtime/README.rst>`_
- 解决期货策略持仓到交割导致可用资金计算不准确的问题
- 解决 `--plot` 时候会报错退出的问题


2.2.2
==================

- 增加 :code:`run_file` | :code:`run_code` | :code:`run_func` API, 详情请参见 `多种方式运行策略 <http://rqalpha.io/zh_CN/latest/intro/run_algorithm.html>`_
- Breaking Change: 更改 :code:`AbstractStrategyLoader:load` 函数的传入参数，现在不需要 :code:`strategy` 了。
- 增加 :code:`UserFuncStrategyLoader` 类
- 根据 `Issue 116 <https://github.com/ricequant/rqalpha/issues/116>`_ 增加如下内容:

  - :code:`POSITION_EFFECT` 增加 :code:`CLOSE_TODAY` 类型
  - 增加调仓函数 :code:`order(order_book_id, quantity, price=None)` API

    - 如果不传入 price 则认为执行的是 MarketOrder 类型订单，否则下 LimitOrder 订单
    - 期货

      - quantity > 0: 往 BUY 方向调仓 quantity 手
      - quantity < 0: 往 SELL 方向调仓 quantity 手

    - 股票

      - 相当于 order_shares 函数

  - 增加调仓函数 :code:`order_to(order_book_id, quantity, price=None)` API

    - 基本逻辑和 :code:`order` 函数一致
    - 区别在于 quantity 表示调仓对应的最终仓位

  - 现有所有下单函数，增加 `price` option，具体行为和 :code:`order` | :code:`order_to` 一致

- Fix bug in :code:`all_instruments` `PR 123 <https://github.com/ricequant/rqalpha/pull/123>`_
- Fix "运行不满一天的情况下 sys_analyser 报 KeyError" `PR 118 <https://github.com/ricequant/rqalpha/pull/118>`_
- sys_analyser 生成 report 对应的字段进行调整，具体调整内容请查看 commit `d9d19f <https://github.com/ricequant/rqalpha/commit/f6e4c24fde2f086cc09b45b2cc4d2cfe0cd9d19f>`_

2.2.0
==================

- 增加 :code:`order` 和 :code:`order_to` 高阶下单函数
- 更新数据源，现在使用原始数据和复权因子的方式进行回测
- 不再使用 `ruamel.yaml` 该库在某些情况下无法正确解析 yml 配置文件
- 解决 `six` 库依赖多次引用导致安装出错的问题
- 解决 :code:`rqalpha run` 的时候指定 :code:`-st` | :code:`--kind` 时报错的问题
- :code:`--security` / :code:`-st` 现在支持多种模式，可以使用 :code:`-st stock -st future` 也可以使用 :code:`-st stock_future` 来设置security
- 更新 BarDictPriceBoard `Issue 115 <https://github.com/ricequant/rqalpha/issues/115>`_
- 解决 :code:`print(context.portfolio)` 时因为调用了 `abandon property` 会报 warning 的问题 `Issue 114 <https://github.com/ricequant/rqalpha/issues/114>`_
- 解决 :code:`rqalpha mod install xx` 不存在的 Mod 也会导致 mod_config.yml 更新的问题 `Issue 111 <https://github.com/ricequant/rqalpha/issues/111>`_
- 解决 :code:`rqalpha plot` 无法画图的问题 `Issue 109 <https://github.com/ricequant/rqalpha/issues/109>`_

2.1.4
==================

- 解决 history_bars 在 before_trading 获取的是未来数据的问题
- 解决 before_trading 获取结算价是当前交易日结算价的问题
- 增加 RQAlpha 向前兼容(0.3.x) `Issue 100 <https://github.com/ricequant/rqalpha/issues/100>`_
- 期货增加强平机制: 及当前账户权益<=0时，清空仓位，资金置0 `Issue 108 <https://github.com/ricequant/rqalpha/issues/108>`_
- 解决回测时只有一个交易日时，只有回测数据显示的问题

2.1.3
==================

- Fix `Issue 101 <https://github.com/ricequant/rqalpha/issues/101>`_
- Fix `Issue 105 <https://github.com/ricequant/rqalpha/issues/105>`_
- 解决运行 RQAlpha 时缺少 `six` | `requests` 库依赖的问题
- 解决安装RQAlpha时在某些情况下报错的问题
- 解决第三方 Mod 安装后配置文件路径有误的问题
- 现在可以通过 `rqalpha mod install -e .` 的方式来安装依赖 Mod 了
- 现在运行策略时会检测当前目录是否存在 `config.yml` 或者 `config.json` 来作为配置文件
- 解决股票下单就存在 `position` 的问题，现在只有成交后才会产生 `position` 了。
- 修复 `portfolio` 和 `future_account` 计算逻辑的一些问题
- 修复 `transaction_cost` 在某个 position 清空以后计算不准确的问题
- 在信号模式下 `price_limit` 表示是否输出涨跌停买入/卖出的报警信息，但不会阻止其买入/卖出

2.1.2
==================

- 提供 :code:`from rqalpha import cli` 方便第三方 Mod 扩展 `rqalpha` command
- :code:`history_bars` 增加 :code:`include_now` option
- Fix `Issue 90 <https://github.com/ricequant/rqalpha/issues/90>`_
- Fix `Issue 94 <https://github.com/ricequant/rqalpha/issues/94>`_

2.1.0
==================

- Fix `Issue 87 <https://github.com/ricequant/rqalpha/issues/87>`_
- Fix `Issue 89 <https://github.com/ricequant/rqalpha/pull/89>`_
- Fix 无法通过 :code:`env.config.mod` 获取全部 `mod` 的配置信息
- 增加 :code:`context.config` 来获取配置信息
- 提供 :code:`from rqalpha import export_as_api` 接口，方便扩展自定义 API

2.0.9
==================

- Fix `Issue 79 <https://github.com/ricequant/rqalpha/issues/79>`_
- Fix `Issue 82 <https://github.com/ricequant/rqalpha/issues/82>`_
- Fix :code:`rqalpha cmd` 失效

2.0.8
==================

- Fix `Issue 81 <https://github.com/ricequant/rqalpha/issues/81>`_
- 解决 `mod_config.yml` 文件解析出错以后，所有的命令报错的问题
- 默认在 Python 2.x 下 `sys.setdefaultencoding("utf-8")`
- 优化 `UNIVERSE_CHANGED` 事件，现在只有在universe真正变化时才触发

2.0.7
==================

- Fix `Issue 78 <https://github.com/ricequant/rqalpha/issues/78>`_
- `is_st_stock` | `is_suspended` 支持 `count` 参数
- 解决大量 Python 2.x 下中文乱码问题

2.0.6
==================

- 解决在 Python 2.x 下安装 RQAlpha 提示 `requirements-py2.txt Not Found` 的问题
- 解决 `Benchmark` 无法显示的问题
- 解决 `rqalpha mod list` 显示不正确的问题
- 现在可以通过配置 `base.extra_vars` 向策略中预定义变量了。用法如下:

.. code-block:: python3

    from rqalpha import run

    config = {
      "base": {
        "strategy_file": "strategy.py",
        "start_date": "2016-06-01",
        "end_date": "2016-07-01",
        "stock_starting_cash":100000,
        "benchmark": '000300.XSHG'
      },
      "extra":{
        "context_vars":{
          "short":5,
          "middle":10,
          "long":21
        }
      }
    }

    result_dict = run(config)

    # 以下是策略代码:

    def handle_bar(context):
        print(context.short)    # 5
        print(context.middle)   # 10
        print(context.long)     # 21

2.0.1
==================

- 修改配置的读取方式，不再从 `~/.rqalpha/config.yml` 读取自定义配置信息，而是默认从当前路径读取 `config.yml`，如果没找到，则会读取系统默认配置信息
- 现在不再对自定义信息进行版本检查
- :code:`rqalpha generate_config` 现在会生成包含所有默认系统配置信息的 `config.yml` 文件。
- :code:`RUN_TYPE` 增加 :code:`LIVE_TRADING`
- 修复 :code:`history_bars` 获取日期错误产生的问题
- 修复执行 :code:`context.run_info` 会报错的问题
- 修复持久化报错的问题
- 增加 Order Persist 相关内容


2.0.0
==================

2.0.0 详细修改内容请访问：`RQAlpha 2.0.0 <https://github.com/ricequant/rqalpha/issues/65>`_

**Portfolio/Account/Position 相关**

- 重新定义了 :code:`Portfolio`, :code:`Account` 和 :code:`Position` 的角色和关系
- 删除大部分累计计算的属性，重新实现股票和期货的计算逻辑
- 现在只有在 :code:`Portfolio` 层级进行净值/份额的计算，Account级别不再进行净值/份额/收益/相关的计算
- 账户的恢复和初始化现在只需要 :code:`total_cash`, :code:`positions` 和 :code:`backward_trade_set` 即可完成
- 精简 :code:`Position` 的初始化，可以从 :code:`real_broker` 直接进行恢复
- :code:`Account` 提供 :code:`fast_forward` 函数，账户现在可以从任意时刻通过 :code:`orders` 和 :code:`trades` 快速前进至最新状态
- 如果存在 Benchmark， 则创建一个 :code:`benchmark_portfolio`, 其包含一个 :code:`benchmark_account`
- 策略在调用 :code:`context.portfolio.positions[some_security]` 时候，如果 position 不存在，不再每次都创建临时仓位，而是会缓存，从而提高回测速度和性能
- 不再使用 :code:`clone` 方法
- 不再使用 :code:`PortfolioProxy` 和 :code:`PositionProxy`

**Event 相关**

- 规范 Event 的生成和相应逻辑, 使用 Event object 来替换原来的 Enum
- 抽离事件执行相关逻辑为 :code:`Executor` 模块

**Mod 相关**

- 规范化 Mod 命名规则，需要以 `rqalpha_mod_xxx` 作为 Mod 依赖库命名
- 抽离 :code:`slippage` 相关业务逻辑至 :code:`simulation mod`
- 抽离 :code:`commission` 相关业务逻辑至 :code:`simulation mod`
- 抽离 :code:`tax` 相关业务逻辑至 :code:`simulation mod`
- `rqalpha mod list` 命令现在可以格式化显示 Mod 当前的状态了

**Environment 和 ExecutionContext 相关**

- 现在 :code:`ExecutionContext` 只负责上下文相关的内容，不再可以通过 :code:`ExecutionContext` 访问其他成员变量。
- 扩展了 :code:`Environment` 的功能，RQAlpha 及 Mod 均可以直接通过 :code:`Environment.get_instance()` 来获取到环境中核心模块的引用
- :code:`Environment` 还提供了很多常用的方法，具体请直接参考代码

**配置及参数相关**

- 重构了配置相关的内容，`~/.rqalpha/config.yml` 现在类似于 Sublime/Atom 的用户配置文件，用于覆盖默认配置信息，因此只需要增加自定义配置项即可，不需要全部的配置内容都存在
- 将Mod自己的默认配置从配置文件中删除，放在Mod中自行管理和维护
- 独立存在 `~/.rqalpha/.mod_conifg.yml`, 提供 `rqalpha mod install/uninstall/enable/disable/list` 命令，RQAlpha 会通过该配置文件来对Mod进行管理。
- 抽离 :code:`rqalpha run` 的参数，将其中属于 `Mod` 的参数全部删除，取代之为Mod提供了参数注入机制，所以现在 `Mod` 可以自行决定是否要注入参数或者命令来扩展 RQAlpha 的功能
- 提供了 :code:`rqalpha-cmd` 命令，`Mod` 推荐在该命令下注入自己的命令来实现功能扩展
- 不再使用 `--strategy-type`， 改为使用 `--security` 选项
- `--output-file` | `--report` | `--plot` | `--plot-save`参数 转移至 `sys_analyser` Mod 中
- `plot` | `report` 命令，转移至 `sys_analyser` Mod 中
- `--signal` | `--slippage` | `--commission-multiplier` | `--matching-type` | `--rid` 转移至 `sys_simulation` Mod 中

**Risk 计算**

- 修复 `tracking error <https://www.ricequant.com/api/python/chn#backtest-results-factors>`_ 计算错误
- 修改 `sharpe <https://www.ricequant.com/api/python/chn#backtest-results-risk-adjusted-returns>`_ , `sortino <https://www.ricequant.com/api/python/chn#backtest-results-risk-adjusted-returns>`_ , `information ratio <https://www.ricequant.com/api/python/chn#backtest-results-risk-adjusted-returns>`_ , `alpha <https://www.ricequant.com/api/python/chn#backtest-results-returns>`_ 计算逻辑。参考 `晨星 <https://gladmainnew.morningstar.com/directhelp/Methodology_StDev_Sharpe.pdf>`_ 的方法, 先计算单日级别指标, 再进行年化。与原本直接基于年化值计算相比, 在分析时间较短的情况下, 新的指标计算结果会系统性低于原指标结果。
- 引入单日无风险利率作为中间变量计算上述指标。单日无风险利率为通过 `中国债券信息网 <http://yield.chinabond.com.cn/cbweb-mn/yield_main>`_ 获取得到对应期限的年化国债到期收益率除以244得到
- 修改指标说明若干

**其他**

- 修改了 :code:`Order` 和 :code:`Trade` 的字段和函数，使其更通用
- 为 :code:`RqAttrDict` 类增加 :code:`update` 方法，现在支持动态更新了
- :code:`arg_checker` 增加 :code:`is_greater_or_equal_than` 和 :code:`is_less_or_equal_than` 函数
- 删除 :code:`DEFAULT_FUTURE_INFO` 变量，现在可以直接通过 :code:`data_proxy` 获取相关数据
- 通过 `better_exceptions <https://github.com/Qix-/better-exceptions>`_ 提供更好的错误堆栈提示体验
- 对字符串的处理进行了优化，现在可以正确在 Python2.x/3.x 下显示中文了
- 修复 :code:`update_bundle` 直接在代码中调用会报错的问题
- 增加对于下单量为0的订单过滤，不再会创建订单，也不再会输出警报日志
- 增加 :code:`is_suspended` 和 :code:`is_st_stock` API 的支持

0.3.14
==================

- Hotfix :code:`UnboundLocalError: local variable 'signature' referenced before assignment`

0.3.13
==================

- 增加股票裸做空的配置参数 :code:`--short-stock`
- :code:`POSITION_EFFECT` 增加 :code:`CLOSE_TODAY`
- :code:`ExecutionContext` 增加 :code:`get_current_close_price` :code:`get_future_commission_info`  :code:`get_future_margin` :code:`get_future_info` 函数
- 增加 :code:`RQInvalidArgument` 来处理用户策略代码异常的问题
- 现在可以正确提示期货主力连续合约和指数连续合约在回测和模拟中的报错信息了
- 现在以 :code:`handle_tick(context, tick)` 的方式支持tick级别的API支持(未来可能会修改)
- 现在回测时的 :code:`before_trading` 函数输出的时间提前到开盘前半小时

0.3.12
==================

- 优化 `setup.py` 脚本，只有在 python 2 环境下才安装兼容性依赖库
- 增加 :code:`rqalpha install/uninstall/list/enable/disable` 命令
- 增加 :code:`EVENT.POST_SYSTEM_RESTORED` 事件
- 增加 净值和份额的支持，现在的收益和Analyser的计算都是基于净值了。
- 在 AnalyserMod 输出的 Trade 中增加 :code:`side` 和 :code:`position_effect`
- 修复 :code:`total_orders` 计算错误
- 修复 :code:`inpsect.signature` 在 python 2.x 报错的问题。

0.3.11
==================

- 更新本地化翻译，修改系统提示，支持多语言
- 增加 :code:`--locale` 默认为 :code:`cn` (中文), 支持 :code:`cn | en` (中文 | 英文)
- 修复 :code:`main.run` 返回值中 :code:`stock_position` 为 :code:`None` 的问题
- 修复 Windows Python 2.7 下中文显示乱码的问题

0.3.10
==================

- 增加 :code:`config.yml` 的版本号检查及相关流程
- 增加 :code:`plot` 关于中文字体的校验，如果系统没有中文字体，则显示英文字段
- 修正 :code:`Benchmark` 在不设置时某些情况下会导致运行失败的错误
- 修正 :code:`inspect.unwrap` 在 Python 2.7 下不支持的兼容性问题
- 修正 :code:`numpy` 在某些平台下没有 `float128` 引起的报错问题

0.3.9
==================

- 增加 :code:`--disable-user-system-log` 参数，可以独立关闭回测过程中因策略而产生的系统日志
- :code:`--log-level` 现在可以正确区分不同类型的日志，同时增加 :code:`none` 类型，用来关闭全部日志信息。
- 在不指定配置文件的情况下，默认会调用 :code:`~/.rqalpha/config.yml` 文件
- 支持 :code:`rqalpha generate_config` 命令来获取默认配置文件
- 指定策略类型不再使用 :code:`--kind` 参数，替换为 :code:`--strategy-type` 和配置文件呼应
- 重构 :code:`events.py`，现在可以更好的支持基于事件的模块编写了
- 将风险指标计算独立成 :code:`analyser` Mod
- 将事前风控相关内容独立成 :code:`risk_manager` Mod
- 将 `回测` 和 `实盘模拟` 相关功能独立成 :code:`simulation` Mod

0.3.8
==================

- 增加几个 technical analysis 的 examples 和自动化测试
- 修复一些在 Python 2 下运行的 bug

0.3.7
==================

- 增加 :code:`-mc` / :code:`--mod-config` 参数来传递参数到 mod 中
- 增加了 simple_stock_realtime_trade, progressive_output_csv，funcat_api 几个 DEMO mod 供开发者参考开发自己的 mod
- :code:`update_bundle` 移到 :code:`main.py` 中，方便直接从代码中调用 :code:`update_bundle`
- 增加了一些自动化的测试用例

0.3.6
==================

- support auto test with Travis [python 2.7 3.4 3.5 3.6]
- :code:`rqalpha.run` 现在支持直接传入 :code:`source_code` 了
- 支持 :code:`rqalpha.update_bundle` 函数

0.3.5
==================

- 增加 :code:`from rqalpha import run` 接口，现在可以很方便的直接在程序中调用RQAlpha 回测了。

0.3.4
==================

- 本地化模块更具有扩展性
- 修改 :code:`rqalpha update_bundle` 的目录结构，现在是在指定目录下生成一个 bundle 文件，而不再会直接删除当前文件夹内容了。

0.3.3
==================

- 解决 :code:`rqalpha examples -d .` 无样例策略生成的问题

0.3.2
==================

- 解决 Windows 10 下 matplotlib 中文字体显示乱码的问题
- 解决 Windows 下 set_locale error 的问题

0.3.1
==================

- 增加 Python 2 的支持

0.3.0
==================

- 支持多周期回测扩展(虽然只有日线数据，但是结构上是支持不同周期的回测和实盘的)
- 支持期货策略
- 支持混合策略(股票和期货混合)
- 支持多种参数配置方式
- 抽离接口层，数据源、事件源、撮合引擎、下单模块全部可以替换或扩展。
- 完善事件定义，采取 pub/sub 模式，可以非常简答的在 RQAlpha 中添加 hook。
- 增加 Mod 机制，极大的增加了 RQAlpha 的扩展性，使其可以轻松完成程序化交易过程中所产生的的特定需求。

0.0.53
==================

- 完善了回测结果显示
- 修正了 Risk 计算和 Benchmark 计算


0.0.20
==================

- 增加会回测进度显示开关
- 完善了回测结果显示

0.0.19
==================

- 在 :code:`handle_bar` 前用当前的数据更新 portfolio 和 position，因为 ricequant.com 是这样做的。

0.0.18
==================

- 修复了分红计算

0.0.16
==================

- 用户可以通过 context 设置 slippage/commission/benchmark
- 增加了 scheduler

0.0.15
==================

- 修复 history 在 before_trading 调用
- 增加 api 的 phase 检查

0.0.14
==================

- 修改支持 python2

0.0.12
==================

- 修正了 Risk 计算，使用合理的年化收益计算方法
- 格式化代码符合 pep8
- 更新 requirements.txt


0.0.9
==================

- 增加了数据下载
- 修正了 Risk 计算
- 增加了 instrument
- 增加了 position 的 :code:`market_value` 和 :code:`value_percent`


0.0.2
==================

- 增加了日线回测
- 去掉了涨跌停检查
- 增加了分红处理
- 运行参数如下:

.. code-block:: python3

  # 生成sample策略
  rqalpha generate_examples -d ./

  # 运行回测
  rqalpha run -f examples/simple_macd.py -s 2013-01-01 -e 2015-01-04 -o /tmp/a.pkl

0.0.1
==================

- 搭建基本的框架，增加基本的 unittest
