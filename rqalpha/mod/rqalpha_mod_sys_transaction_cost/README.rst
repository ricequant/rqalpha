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
        # 股票最小手续费，单位元；cn_stock_min_commission 是兼容旧配置的废弃字段
        "stock_min_commission": 5,
        "cn_stock_min_commission": None,
        # 佣金倍率，即在默认的手续费率基础上按该倍数进行调整，股票的默认佣金为万八，期货默认佣金因合约而异
        "commission_multiplier": None,
        "stock_commission_multiplier": 1,
        "futures_commission_multiplier": 1,
        # ETF 最终佣金费率和最低佣金。None 表示逐字段继承股票的有效配置，0 是有效的显式值
        "etf_commission": {
            "default": {
                "commission_rate": None,
                "min_commission": None,
            },
            "subtypes": {
                "bond": {
                    "commission_rate": None,
                    "min_commission": None,
                },
                "money": {
                    "commission_rate": None,
                    "min_commission": None,
                },
            },
        },
        # 印花倍率，即在默认的印花税基础上按该倍数进行调整，股票默认印花税为千分之一，单边收取
        "tax_multiplier": 1,
    }


ETF 佣金配置
===============================

``etf_commission`` 按字段使用以下优先级解析：

``subtypes.bond / subtypes.money > default > 股票有效配置``

其中股票有效佣金率为 ``0.0008 * stock_commission_multiplier``，股票有效最低佣金优先使用非空的
``cn_stock_min_commission``，否则使用 ``stock_min_commission``。``None`` 表示继续继承下一层，``0`` 表示明确配置为零。

ETF 子类型根据合约的 ``fund_type`` 确定：

- ``Bond``、``BondIndex``、``ShortBond`` 使用 ``bond`` 配置；
- ``Money`` 使用 ``money`` 配置；
- ``Stock``、``Hybrid``、``StockIndex``、``Related``、``QDII``、``Other`` 使用 ``default`` 配置。

只有在设置了 subtype 专属值时，旧 bundle 或自定义数据源中缺失、无法识别的 ``fund_type`` 才会报错；
未设置 subtype 专属值时仍使用 ``default``，从而兼容旧数据。ETF 买卖均不收取股票印花税。

不会新增 ETF 专用命令行参数。可以使用通用 ``-mc/--mod-config`` 覆盖 default 或 subtype，例如：

.. code-block:: bash

    rqalpha run -mc sys_transaction_cost.etf_commission.default.commission_rate 0.0001
    rqalpha run -mc sys_transaction_cost.etf_commission.subtypes.bond.commission_rate 0.00002
