===============================
sys_risk Mod
===============================

RQAlpha 风控 Mod

启用该 Mod 后会对订单进行事前风控校验。

该模块是系统模块，不可删除

开启或关闭风控 Mod
===============================

..  code-block:: bash

    # 关闭风控 Mod
    $ rqalpha mod disable sys_risk

    # 启用风控 Mod
    $ rqalpha mod enable sys_risk

模块配置项
===============================

..  code-block:: python

    {
        # 开启对限价单价格合法性的检查
        "validate_price": True,
        # 开启对标的可交易情况对检查
        "validate_is_trading": True,
        # 开启对可用资金是否足够满足下单要求的检查
        "validate_cash": True,
        # 开启对存在自成交风险的检查
        "validate_self_trade": False,
    }

