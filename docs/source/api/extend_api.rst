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


..  module:: rqalpha.api

get_price - 合约历史数据
------------------------------------------------------

.. autofunction:: get_price


get_split - 拆分数据
------------------------------------------------------

.. autofunction:: get_split


index_components - 指数成分股
------------------------------------------------------

.. autofunction:: index_components


index_weights - 指数成分股权重
--------------------------------------------------------

.. autofunction:: index_weights


futures.get_dominant/get_dominant_future - 期货主力合约
--------------------------------------------------------

.. autofunction:: get_dominant_future


get_securities_margin - 融资融券信息
------------------------------------------------------

.. autofunction:: get_securities_margin


get_shares - 流通股信息
------------------------------------------------------

.. autofunction:: get_shares


get_turnover_rate - 历史换手率
------------------------------------------------------

.. autofunction:: get_turnover_rate


concept - 概念股列表
--------------------------------------------------------

.. autofunction:: concept
