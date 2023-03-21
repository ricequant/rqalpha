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
        # 股票最小手续费，单位元
        "cn_stock_min_commission": 5,
        # 佣金倍率，即在默认的手续费率基础上按该倍数进行调整，股票的默认佣金为万八，期货默认佣金因合约而异
        "commission_multiplier": None,
        "stock_commission_multiplier": 1,
        "futures_commission_multiplier": 1,
        # 印花倍率，即在默认的印花税基础上按该倍数进行调整，股票默认印花税为千分之一，单边收取
        "tax_multiplier": 1,
    }


