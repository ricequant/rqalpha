===============================
RQAlpha SYS_stock_realtime Mod
===============================

使用该Mod可以接收实时行情进行触发。用于 RQAlpha 实时模拟交易，实盘交易。

这个是一个初级的DEMO。

使用:code:`--run-type`或者:code:`-rt`为:code:`p`(PaperTrading)，就可以激活改 mod。

.. code-block:: bash

    rqalpha run -fq 1m -rt p -f ~/tmp/test_a.py -sc 100000 -l verbose -mc sys_stock_realtime.enabled True
