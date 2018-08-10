===============================
sys_booking Mod
===============================

RQAlpha 仓位加载 Mod

该 Mod 用于从外部加载仓位，使得策略可以在某一份已经存在的仓位（Booking）的基础上进行交易。

该 Mod 中留有未实现的方法，需要对接 Booking 持久化方案后方可使用。

该模块是系统模块，不可删除

开启或关闭策略仓位 Mod
===============================

..  code-block:: bash

    # 关闭
    $ rqalpha mod disable sys_booking

    # 启用
    $ rqalpha mod enable sys_booking
