.. _development-event-source:

==================
扩展事件源
==================

了解事件，首先要从 RQAlpha 的事件驱动说起。

RQAlpha 大部分的组件是以 :code:`add_listener` 的方式进行事件的注册。举例来说:

*   当Bar数据生成，则会触发 :code:`EVENT.BAR` 事件，那么用户的 :code:`handle_bar` 相关的代码注册了该事件则会立即执行。
*   当订单成交，则会触发 :code:`EVENT.TRADE` 事件，那么系统的账户模块因为注册了该事件，就可以立即计算成交以后的收益和资金变化。
*   当订单下单，则会触发 :code:`EVENT.ORDER_PENDING_NEW` 事件，前端风控模块注册了该事件，则可以立即对该订单进行审核，如果不满足风控要求，则直接指定执行 :code:`order._cancel(some_reason)` 来保证有问题的订单不会进入实际下单环节。

程序化交易中很多需求，都可以通过注册事件的方式无缝插入到 RQAlpha 中进行扩展。

事件源分类
==================

*   SystemEvent: 系统事件源

    *   POST_SYSTEM_INIT: 系统初始化后触发
    *   POST_USER_INIT: 策略的 :code:`init` 函数执行后触发
    *   POST_SYSTEM_RESTORED: 在实盘时，你可能需要在此事件后根据其他信息源对系统状态进行调整

*   MarketEvent: 市场及数据事件源

    *   POST_UNIVERSE_CHANGED: 策略证券池发生变化后触发
    *   PRE_BEFORE_TRADING: 执行 :code:`before_trading` 函数前触发
    *   BEFORE_TRADING: 该事件会触发策略的 :code:`before_trading` 函数
    *   POST_BEFORE_TRADING: 执行 :code:`before_trading` 函数后触发
    *   PRE_BAR: 执行 :code:`handle_bar` 函数前触发
    *   BAR: 该事件会触发策略的 :code:`handle_bar` 函数
    *   POST_BAR: 执行 :code:`handle_bar` 函数后触发
    *   PRE_TICK: 执行 :code:`handle_tick` 前触发
    *   TICK: 该事件会触发策略的 :code:`handle_tick` 函数
    *   POST_TICK: 执行 :code:`handle_tick` 后触发
    *   PRE_SCHEDULED: 在 :code:`scheduler` 执行前触发
    *   POST_SCHEDULED: 在 :code:`scheduler` 执行后触发
    *   PRE_AFTER_TRADING: 执行 :code:`after_trading` 函数前触发
    *   AFTER_TRADING: 该事件会触发策略的 :code:`after_trading` 函数
    *   POST_AFTER_TRADING: 执行 :code:`after_trading` 函数后触发
    *   PRE_SETTLEMENT: 结算前触发该事件
    *   SETTLEMENT: 触发结算事件
    *   POST_SETTLEMENT: 结算后触发该事件

*   OrderEvent: 交易事件源

    *   ORDER_PENDING_NEW: 创建订单
    *   ORDER_CREATION_PASS: 创建订单成功
    *   ORDER_CREATION_REJECT: 创建订单失败
    *   ORDER_PENDING_CANCEL: 创建撤单
    *   ORDER_CANCELLATION_PASS: 撤销订单成功
    *   ORDER_CANCELLATION_REJECT: 撤销订单失败
    *   ORDER_UNSOLICITED_UPDATE: 订单状态更新
    *   TRADE: 成交

事件源的订阅及使用
==================

我们可以订阅需要的事件源，从而在该事件发生时实现指定需求。

下面以最简单的 Mod - ProgressMod 为例，介绍事件源的订阅和使用。

ProgressMod 需要实现的需求非常的简单：在命令行输出目前回测的进度条。

.. image:: https://raw.githubusercontent.com/ricequant/rq-resource/master/rqalpha/progress_bar.png


首先定义一个 ProgressMod 类，继承与接口类 :class:`~AbstractMod`

.. code-block:: python3

    from rqalpha.interface import AbstractMod

    class ProgressMod(AbstractMod):

        def __init__(self):
            pass

        def start_up(self, env, mod_config):
            """
            RQAlpha 在系统启动时会调用此接口；在此接口中，可以通过调用 ``env`` 的相应方法来覆盖系统默认组件。

            :param env: 系统环境
            :type env: :class:`~Environment`
            :param mod_config: 模块配置参数
            """
            pass

        def tear_down(self, success, exception=None):
            """
            RQAlpha 在系统退出前会调用此接口。

            :param code: 退出代码
            :type code: rqalpha.const.EXIT_CODE
            :param exception: 如果在策略执行过程中出现错误，此对象为相应的异常对象
            """
            pass


我们将需求进行分拆:

*   在回测开始时初始化进度条
*   在回测每日交易结束后更新进度条
*   在回测结束后，终止进度条

为了实现以上需求，我们需要注册两个事件:

*   :code:`EVENT.POST_SYSTEM_INIT` 系统初始化后
*   :code:`EVENT.POST_AFTER_TRADING` 交易结束后

进度条相关 我们使用 :code:`click` 库来实现，具体 API 这里不详细展开。

接下来，我们在 :code:`start_up` 函数中进行事件注册，并定义 :code:`_init` 和 :code:`_tick` 函数来响应事件。

.. code-block:: python3

    from rqalpha.interface import AbstractMod

    class ProgressMod(AbstractMod):

        def __init__(self):
            self._env = None

        def start_up(self, env, mod_config):
            self._env = env
            env.event_bus.add_listener(EVENT.POST_AFTER_TRADING, self._tick)
            env.event_bus.add_listener(EVENT.POST_SYSTEM_INIT, self._init)

        def tear_down(self, success, exception=None):
            pass

        def _init(self, event):
            pass

        def _tick(self, event):
            pass

在 :code:`_init` 函数中，初始化 :code:`progressBar`，进度条的长度为回测的总时长

.. code-block:: python

    def _init(self):
        trading_length = len(self._env.config.base.trading_calendar)
        self.progress_bar = click.progressbar(length=trading_length, show_eta=False)

在 :code:`_tick` 函数中，更新进度条

.. code-block:: python

    def _tick(self, event):
        self.progress_bar.update(1)

在 :code:`tear_down` 函数中，终止进度条

.. code-block:: python

    def tear_down(self, success, exception=None):
        self.progress_bar.render_finish()

至此，我们就完成了整个 ProgressMod 的编写

.. code-block:: python3

    import click

    from rqalpha.interface import AbstractMod
    from rqalpha.core.events import EVENT


    class ProgressMod(AbstractMod):
        def __init__(self):
            self._env = None
            self.progress_bar = None

        def start_up(self, env, mod_config):
            self._env = env
            env.event_bus.add_listener(EVENT.POST_AFTER_TRADING, self._tick)
            env.event_bus.add_listener(EVENT.POST_SYSTEM_INIT, self._init)

        def _init(self, event):
            trading_length = len(self._env.config.base.trading_calendar)
            self.progress_bar = click.progressbar(length=trading_length, show_eta=False)

        def _tick(self, event):
            self.progress_bar.update(1)

        def tear_down(self, success, exception=None):
            self.progress_bar.render_finish()

最后，我们添加默认的载入函数 :code:`load_mod`，一个完整的进度条的Mod就完成了

.. code-block:: python3

    import click

    from rqalpha.interface import AbstractMod
    from rqalpha.events import EVENT


    class ProgressMod(AbstractMod):
        def __init__(self):
            self._env = None
            self.progress_bar = None

        def start_up(self, env, mod_config):
            self._env = env
            env.event_bus.add_listener(EVENT.POST_AFTER_TRADING, self._tick)
            env.event_bus.add_listener(EVENT.POST_SYSTEM_INIT, self._init)

        def _init(self, event):
            trading_length = len(self._env.config.base.trading_calendar)
            self.progress_bar = click.progressbar(length=trading_length, show_eta=False)

        def _tick(self, event):
            self.progress_bar.update(1)

        def tear_down(self, success, exception=None):
            self.progress_bar.render_finish()


    def load_mod():
        return ProgressMod()


事件源的扩展
==================

上一节讲的是如何订阅事件源，那么如何发布事件呢？其实也很简单，只需要通过 :code:`publish_event` 就可以进行事件的发布。

RQAlpha 整个回测模块是通过 :code:`rqalpha_mod_sys_simulation` 实现的，其中定义了基于Bar回测的 :code:`event_source` 和 :code:`simulation_broker`， 其中包含了 MarketEvent 和 OrderEvent 大部分事件源的定义和发布。

我们简单来分析一下日线回测 :code:`simulation_event_source` 中 MaketEvent 相关事件的触发流程。

.. code-block:: python3

    class SimulationEventSource(AbstractEventSource):

        ...

        def events(self, start_date, end_date, frequency):
            # 根据起始日期和结束日期，获取所有的交易日，然后再循环获取每一个交易日
            for day in self._env.data_proxy.get_trading_dates(start_date, end_date):
                date = day.to_pydatetime()
                dt_before_trading = date.replace(hour=0, minute=0)
                dt_bar = date.replace(hour=15, minute=0)
                dt_after_trading = date.replace(hour=15, minute=30)
                dt_settlement = date.replace(hour=17, minute=0)

                yield Event(EVENT.BEFORE_TRADING, calendar_dt=dt_before_trading, trading_dt=dt_before_trading)
                yield Event(EVENT.BAR, calendar_dt=dt_bar, trading_dt=dt_bar)

                yield Event(EVENT.AFTER_TRADING, calendar_dt=dt_after_trading, trading_dt=dt_after_trading)
                yield Event(EVENT.SETTLEMENT, calendar_dt=dt_settlement, trading_dt=dt_settlement)

:code:`event` 函数是一个generator, 在 rqalpha_mod_sys_simulation 中主要返回 :code:`BEFORE_TRADING`, :code:`BAR`, :code:`AFTER_TRADING` 和 :code:`SETTLEMENT` 事件。RQAlpha 在接受到对应的事件后，会自动的进行相应的 `publish_event` 操作，并且会自动 publish 相关的 `PRE_` 和 `POST_` 事件。

而在 :code:`simulation_broker` 中可以看到，当被调用 `cancel_order` 时，会模拟撤单的执行流程，分别触发 :code:`ORDER_PENDING_CANCEL` && :code:`ORDER_CANCELLATION_PASS` 事件，并将 :code:`account` 和 :code:`order` 传递给回调函数，使其可以获取其可能需要到的数据。

.. code-block:: python3

    class SimulationBroker(AbstractBroker, Persistable):

        def cancel_order(self, order):
            account = self._get_account_for(order.order_book_id)

            self._env.event_bus.publish_event(Event(EVENT.ORDER_PENDING_CANCEL, account=account, order=order))

            order._mark_cancelled(_("{order_id} order has been cancelled by user.").format(order_id=order.order_id))

            self._env.event_bus.publish_event(Event(EVENT.ORDER_CANCELLATION_PASS, account=account, order=order))

            # account.on_order_cancellation_pass(order)
            try:
                self._open_orders.remove((account, order))
            except ValueError:
                try:
                    self._delayed_orders.remove((account, order))
                except ValueError:
                    pass

如果想查看详细的事件源相关的内容，建议直接阅读 `rqalpha_mod_sys_simulation` 源码，您会发现，扩展事件源比想象中要简单。

您也可以基于 `rqalpha_mod_sys_simulation` 扩展一个自定义的回测引擎，实现您特定的回测需求。

