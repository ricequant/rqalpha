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
        # 检查限价单价格是否合法
        "validate_price": True,
        # 检查标的证券是否可以交易
        "validate_is_trading": True,
        # 检查可用资金是否充足
        "validate_cash": True,
        # 检查是否存在自成交的风险
        "validate_self_trade": False,
    }

