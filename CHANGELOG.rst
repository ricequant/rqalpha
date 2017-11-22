==================
CHANGELOG
==================

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
- 重构股票账户:code:`last_price`更新
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
