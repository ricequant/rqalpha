.. _development-basic-concept:

==================
基本概念
==================

接口
==================

..  module:: rqalpha.interface
    :synopsis: 接口

我们将重要模块进行了抽离，使得通过 Mod 来替换核心组件成为了可能。

*   策略加载模块(AbstractStrategyLoader): 加载策略，并将策略运行所需要的域环境传递给策略执行代码，可以通过扩展策略加载器来实现自定义策略源、自定义API载入等功能。
*   事件生成模块(AbstractEventSource): 无论是回测还是实盘，都需要基于数据源生成对应的事件，而事件生成模块主要负责生成策略执行相应的事件。
*   数据源模块(AbstractDataSource): 日线数据、分钟线数据、财务数据、债务数据等等都可以通过该模块进行扩展和使用。
*   券商代理模块(AbstractBroker): 用户的所有下单、账户、撮合逻辑其实都来自于券商+交易所，即使是回测，也实际是一个回测模拟交易所。因此可以通过扩展该模块来自定义Broker，也可以通过该模块扩展实盘交易等。

.. image:: https://raw.githubusercontent.com/ricequant/rq-resource/master/rqalpha/RQAlpha_structure.png

详细的 RQAlpha 结构图请查看 `Processon RQAlpha Structure`_

Account
------------------

.. autoclass:: AbstractAccount
    :members:

Position
------------------

.. autoclass:: AbstractPosition
    :members:

StrategyLoader
------------------

..  autoclass:: AbstractStrategyLoader
    :members:


EventSource
------------------

..  autoclass:: AbstractEventSource
    :members:

DataSource
------------------

..  autoclass:: AbstractDataSource
    :members:

Broker
------------------

..  autoclass:: AbstractBroker
    :members:

PriceBoarder
------------------

..  autoclass:: AbstractPriceBoard
    :members:

Mod
------------------

..  autoclass:: AbstractMod
    :members:

PersistProvider
------------------

..  autoclass:: AbstractPersistProvider
    :members:


.. _Processon RQAlpha Structure: https://www.processon.com/view/link/58aa9809e4b07158582ebf13
