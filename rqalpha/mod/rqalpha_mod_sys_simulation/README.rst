===============================
sys_simulation Mod
===============================

RQAlpha 回测 Mod，启用该模块开启回测功能。

该模块是系统模块，不可删除

开启或关闭策略回测/模拟 Mod
===============================

..  code-block:: bash

    # 关闭策略回测/模拟 Mod
    $ rqalpha mod disable sys_simulation

    # 启用策略回测/模拟 Mod
    $ rqalpha mod enable sys_simulation

模块配置项
===============================

您可以通过直接修改 `sys_simulation` Mod 的配置信息来更改默认配置项

默认配置项如下:

..  code-block:: python

    {
        # 是否开启信号模式
        "signal": False,
        # 启用的回测引擎，目前支持 `current_bar` (当前Bar收盘价撮合) 和 `next_bar` (下一个Bar开盘价撮合)
        "matching_type": "current_bar",
        # 设置滑点
        "slippage": 0,
        # 设置手续费乘数，默认为1
        "commission_multiplier": 1,
        # price_limit: 在处于涨跌停时，无法买进/卖出，默认开启【在 Signal 模式下，不再禁止买进/卖出，如果开启，则给出警告提示。】
        "price_limit": True,
        # 是否有成交量限制
        "volume_limit": True,
        # 按照当前成交量的百分比进行撮合
        "volume_percent": 0.25,
    }

您可以通过如下方式来修改模块的配置信息，比如下面的示例中介绍了如何设置滑点

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
            "sys_simulation": {
                "enabled": True,
                "slippage": 0.01
            }
        }
    }
    run(config)

扩展命令
===============================

在启用该 Mod 的情况下，您可以使用如下功能:

*   :code:`rqalpha run` 命令增加 :code:`--signal` 选项，您可以指定使用信号方式来直接按照下单价格成交，从而屏蔽订单细节。
*   :code:`rqalpha run` 命令增加 :code:`--slippage` / :code:`-sp` 选项，您可以指定成交所产生的滑点，目前支持按照当前价格的百分比的方式计算滑点。
*   :code:`rqalpha run` 命令增加 :code:`--commission-multiplier` / :code:`--cm` 选项，您可以指定手续费乘数
*   :code:`rqalpha run` 命令增加 :code:`--matching-type` / :code:`--mt` 选项，您可以指定撮合的锚定价格及对应的方式
