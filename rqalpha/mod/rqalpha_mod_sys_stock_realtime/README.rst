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

使用方式
===============================

在启动该 Mod 的情况下，

使用 :code:`--run-type` 或者 :code:`-rt` 为 :code:`p` (PaperTrading)，就可以激活改 mod。

.. code-block:: bash

    rqalpha run -fq 1m -rt p -f ~/tmp/test_a.py -sc 100000 -l verbose -mc sys_stock_realtime.enabled True
