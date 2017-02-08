.. _development-basic-concept:

==================
Basic Concept
==================

Interface
==================

..  module:: rqalpha.interface
    :synopsis: 接口

我们将重要模块进行了抽离，使得通过 Mod 来替换核心组件成为了可能。

*   策略加载器:

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

Mod
------------------

..  autoclass:: AbstractMod
    :members:

PersistProvider
------------------

..  autoclass:: AbstractPersistProvider
    :members:
















