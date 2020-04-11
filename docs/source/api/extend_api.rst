.. _api-extend-api:

==================
扩展 API
==================

扩展 API 是 Ricequant 从众多的数据源中整理、归纳和维护的API。
这些 API 提供的数据大多来自 `RQDatac`_ ，所以调用扩展 API 需要您在环境安装有 `RQDatac`_ 且获得了 `RQDatac`_ 的使用权限，
您可以访问 `Ricequant 官网 <https://www.ricequant.com/welcome/rqdata>`_ 免费申请试用 `RQDatac`_ 及获取 `RQDatac`_ 的文档。
您亦可以在 `Ricequant 在线量化平台 <https://www.ricequant.com/welcome/quant>`_ 中运行策略并免费调用扩展 API。

您也可以通过按照接口规范来进行 API 的扩展。

.. _RQDatac: https://www.ricequant.com/welcome/rqdata


行情
=================

..  module:: rqalpha.api

get_price - 合约历史数据
------------------------------------------------------

.. autofunction:: get_price

get_price_change_rate - 历史涨跌幅
------------------------------------------------------

.. autofunction:: get_price_change_rate


股票
=================

get_split - 拆分数据
------------------------------------------------------

.. autofunction:: get_split

get_securities_margin - 融资融券信息
------------------------------------------------------

.. autofunction:: get_securities_margin

concept - 概念股列表
--------------------------------------------------------

.. autofunction:: concept

get_shares - 流通股信息
------------------------------------------------------

.. autofunction:: get_shares

get_turnover_rate - 历史换手率
------------------------------------------------------

.. autofunction:: get_turnover_rate

get_factor - 因子
------------------------------------------------------

.. autofunction:: get_factor

get_industry - 行业股票列表
------------------------------------------------------
.. autofunction:: get_industry

get_instrument_industry - 股票行业分类
------------------------------------------------------

.. autofunction:: get_instrument_industry

get_stock_connect - 沪深港通持股信息
------------------------------------------------------

.. autofunction:: get_stock_connect

current_performance - 财务快报数据
------------------------------------------------------

.. autofunction:: current_performance


指数
=================

index_components - 指数成分股
------------------------------------------------------

.. autofunction:: index_components


index_weights - 指数成分股权重
--------------------------------------------------------

.. autofunction:: index_weights


期货
=================

..  module:: rqalpha.api.futures

futures.get_dominant - 期货主力合约
------------------------------------------------------

.. autofunction:: get_dominant


futures.get_member_rank - 期货会员持仓等排名
------------------------------------------------------

.. autofunction:: get_member_rank


futures.get_warehouse_stocks - 期货仓单数据
------------------------------------------------------

.. autofunction:: get_warehouse_stocks


宏观经济
=================

..  module:: rqalpha.api.econ


econ.get_reverse_ratio - 存款准备金率
------------------------------------------------------

.. autofunction:: get_reserve_ratio


econ.get_money_supply - 货币供应量
------------------------------------------------------

.. autofunction:: get_money_supply

