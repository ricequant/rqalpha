===============================
sys_booking Mod
===============================

RQAlpha 通用仓位 Mod

该模块是系统模块，不可删除

开启或关闭策略仓位 Mod
===============================

..  code-block:: bash

    # 关闭
    $ rqalpha mod disable sys_booking

    # 启用
    $ rqalpha mod enable sys_booking

模块配置项
===============================

您可以通过直接修改 `sys_booking` Mod 的配置信息来更改默认配置项

默认配置项如下:

..  code-block:: python

    {
        "booking_id": None,
    }

扩展命令
===============================

.. code-block:: bash

   rqalpha run -mc sys_risk.validate_cash False -mc sys_accounts.future_forced_liquidation False