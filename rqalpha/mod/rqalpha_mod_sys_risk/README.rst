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
        # 检查可平仓位是否充足
        "validate_position": True,
    }

您可以通过如下方式来修改模块的配置信息，从而选择开启/关闭风控模块对应的风控项

..  code-block:: python

    from rqalpha import run
    config = {
        "base": {
            "strategy_file": "strategy.py",
            "start_date": "2015-01-09",
            "end_date": "2015-03-09",
            "frequency": "1d",
            "accounts": {
                "stock": 100000
            }
        }
        "mod": {
            "sys_risk": {
                "enabled": True,
                # 关闭仓位是否充足相关的风控判断
                "validate_position": False,
            }
        }
    }
    run(config)
