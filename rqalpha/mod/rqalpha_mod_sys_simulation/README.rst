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
        # 开启信号模式：该模式下，所有通过风控的订单将不进行撮合，直接产生交易
        "signal": False,
        # 撮合方式，其中：
        #   日回测的可选值为 "current_bar"|"vwap"（以当前 bar 收盘价｜成交量加权平均价撮合）
        #   分钟回测的可选值有 "current_bar"|"next_bar"|"vwap"（以当前 bar 收盘价｜下一个 bar 的开盘价｜成交量加权平均价撮合)
        #   tick 回测的可选值有 "last"|"best_own"|"best_counterparty"（以最新价｜己方最优价｜对手方最优价撮合）和 "counterparty_offer"（逐档撮合）
        "matching_type": "current_bar",
        # 开启对于处于涨跌停状态的证券的撮合限制
        "price_limit": True,
        # 开启对于对手盘无流动性的证券的撮合限制（仅在 tick 回测下生效）
        "liquidity_limit": False,
        # 开启成交量限制
        #   开启该限制意味着每个 bar 的累计成交量将不会超过该时间段内市场上总成交量的一定比值（volume_percent）
        #   开启该限制意味着每个 tick 的累计成交量将不会超过当前tick与上一个tick的市场总成交量之差的一定比值
        "volume_limit": True,
        # 每个 bar/tick 可成交数量占市场总成交量的比值，在 volume_limit 开启时生效
        "volume_percent": 0.25,
        # 滑点模型，可选值有 "PriceRatioSlippage"（按价格比例设置滑点）和 "TickSizeSlippage"（按跳设置滑点）
        #    亦可自己实现滑点模型，选择自己实现的滑点模型时，此处需传入包含包和模块的完整类路径
        #    滑点模型类需继承自 rqalpha.mod.rqalpha_mod_sys_simulation.slippage.BaseSlippage
        "slippage_model": "PriceRatioSlippage",
        # 设置滑点值，对于 PriceRatioSlippage 表示价格的比例，对于 TickSizeSlippage 表示跳的数量
        "slippage": 0,
        # 开启对于当前 bar 无成交量的标的的撮合限制（仅在日和分钟回测下生效）
        "inactive_limit": True,
        # 账户每日计提的费用，需按照(账户类型，费率)的格式传入，例如[("STOCK", 0.0001), ("FUTURE", 0.0001)]
        "management_fee": [],
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

注意事项
===============================
*   在tick级别回测频率下，开盘集合竞价期间的撮合将无视 matching_type 的设置，一律用last撮合。
*   默认情况下Tick回测使用DefaultTickMatcher，日频和分钟频率回测使用DefaultBarMatcher。