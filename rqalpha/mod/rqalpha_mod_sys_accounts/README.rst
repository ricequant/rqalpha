===============================
sys_accounts Mod
===============================

RQAlpha 扩展账户 Mod，实现了股票和期货的账户逻辑，提供了股票和期货的专用 API。

开启或关闭账户 Mod
===============================

..  code-block:: bash

    # 关闭账户 Mod
    $ rqalpha mod disable sys_accounts

    # 启用账户 Mod
    $ rqalpha mod enable sys_accounts


模块配置项
===============================

账户 Mod 的可用配置项如下：

..  code-block:: python

    {
        # 是否开启股票 T+1 限制
        "stock_t1": True,
        # 是否开启自动分红再投资
        "dividend_reinvestment": False,
        # 当持仓股票退市时，是否按照退市价格返还现金
        "cash_return_by_stock_delisted": True,
        # 股票下单因资金不足被拒时改为使用全部剩余资金下单
        "auto_switch_order_value": False,
        # 开启对股票仓位是否能满足平仓需求的检查
        "validate_stock_position": True,
        # 开启对期货仓位是否能满足平仓需求的检查
        "validate_future_position": True,
        # 融资利率/年
        "financing_rate": 0.00,
        # 是否开启融资可买入股票的限制
        "financing_stocks_restriction_enabled": False,
        # 逐日盯市结算价: settlement/close
        "futures_settlement_price_type": "close",
    }

