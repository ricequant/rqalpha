===============================
sys_stock_realtime Mod
===============================

RQAlpha 接受实时行情并触发事件 Mod

该模块目前只是一个初级的 Demo，用于展示如何接入自有行情进行回测/模拟/实盘

该模块是系统模块，不可删除

开启或关闭 Mod

===============================

..  code-block:: bash

    # 关闭 Mod
    $ rqalpha mod disable sys_stock_realtime

    # 启用 Mod
    $ rqalpha mod enable sys_stock_realtime

使用统一行情服务
===============================
提供一个行情下载服务，启动该服务，会实时往 redis 中写入全市场股票行情数据。多个 RQAlpha 可以连接该 redis 获取实时盘口数据，就不需要重复获取数据。

您本地需要安装 redis 服务，然后将 redis 的 uri 填入到 quotation_server 的参数中，行情服务就会将实时行情数据写入到 redis 中。

.. code-block:: bash

    rqalpha quotation_server redis://localhost/1

使用方式
===============================

在启动该 Mod 的情况下（可以通过 rqalpha mod list 确认是否启动），

使用 :code:`--run-type` 或者 :code:`-rt` 为 :code:`p` (PaperTrading)，就可以激活该 mod。

.. code-block:: bash

    rqalpha run -fq 1m -rt p -f ~/strategy.py --account stock 100000 -l verbose

在启用了 redis 服务后，可以让 rqalpha 连接 redis ，从 redis 读取实时行情数据。只需要增加参数 --redis-uri ，填入启动 quotation_server 的 uri，既可以将两者连通。

.. code-block:: bash

    rqalpha run -fq 1m -rt p -f ~/strategy.py --account stock 100000 -l verbose --redis-uri redis://localhost/1
