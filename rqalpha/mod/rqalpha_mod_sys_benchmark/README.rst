===============================
sys_benchmark Mod
===============================

RQAlpha 基准 Mod，为回测和模拟交易提供了以单一标的收盘价作为基准的具体实现

开启或关闭基准 Mod
===============================

..  code-block:: bash

    # 关闭账户 Mod
    $ rqalpha mod disable sys_benchmark

    # 启用账户 Mod
    $ rqalpha mod enable sys_benchmark


模块配置项
===============================

基准 Mod 的可用配置项如下：

.. code-block:: python

    {
        # 作为基准的标的代码
        "order_book_id": None
    }
