===============================
sys_transaction_cost Mod
===============================

RQAlpha 交易税费 Mod，实现了不同市场不同交易标的的税费计算逻辑

开启或关闭交易税费 Mod
===============================

..  code-block:: bash

    # 关闭账户 Mod
    $ rqalpha mod disable sys_transaction_cost

    # 启用账户 Mod
    $ rqalpha mod enable sys_transaction_cost


模块配置项
===============================

交易税费 Mod 的可用配置项如下：

.. code-block:: python

    {
        # A股最小手续费
        "cn_stock_min_commission": 5,
        # 港股最小手续费
        "hk_stock_min_commission": 50,
        # 设置手续费乘数，默认为1
        "commission_multiplier": 1,
    }


