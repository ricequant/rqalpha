===============================
sys_funcat Mod
===============================

该模块为 RQAlpha 带来了通达信公式的方式写策略。

启用该 Mod ，会自动将 funcat_ 注入 API 到 RQAlpha 中。

该 mod 依赖 funcat_ ，使用前需要安装依赖库：

.. code-block:: bash

    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple funcat


开启或关闭 Mod
===============================

.. code-block:: bash

    # 启用 funcat API Mod
    $ rqalpha mod enable sys_funcat

    # 关闭 funcat API Mod
    $ rqalpha mod disable sys_funcat


常用API定义
===============================

行情变量
------------------

* 开盘价：:code:`OPEN` :code:`O`
* 收盘价：:code:`CLOSE` :code:`C`
* 最高价：:code:`HIGH` :code:`H`
* 最低价：:code:`LOW` :code:`L`
* 成交量：:code:`VOLUME` :code:`V`


工具函数
------------------

* n天前的数据：REF

:code:`REF(C, 10)  # 10天前的收盘价`

* 金叉判断：CROSS

:code:`CROSS(MA(C, 5), MA(C, 10))  # 5日均线上穿10日均线`

* 两个序列取最小值：MIN

:code:`MIN(O, C)  # K线实体的最低价`

* 两个序列取最大值：MAX

:code:`MAX(O, C)  # K线实体的最高价`

* n天都满足条件：EVERY

:code:`EVERY(C > MA(C, 5), 10)  # 最近10天收盘价都大于5日均线`

* n天内满足条件的天数：COUNT

:code:`COUNT(C > O, 10)  # 最近10天收阳线的天数`

* n天内最大值：HHV

:code:`HHV(MAX(O, C), 60)  # 最近60天K线实体的最高价`

* n天内最小值：LLV

:code:`LLV(MIN(O, C), 60)  # 最近60天K线实体的最低价`

* 求和n日数据 SUM

:code:`SUM(C, 10)  # 求和10天的收盘价`

* 求绝对值 ABS

:code:`ABS(C - O)`


API样例策略
===============================

.. code-block:: python

    from rqalpha.api import *


    def init(context):
	context.s1 = "600275.XSHG"


    def handle_bar(context, bar_dict):
	S(context.s1)
	# 自己实现 DMA指标（Different of Moving Average）
	M1 = 5
	M2 = 89
	M3 = 36

	DDD = MA(CLOSE, M1) - MA(CLOSE, M2)
	AMA = MA(DDD, M3)

	cur_position = context.portfolio.positions[context.s1].quantity

	if DDD < AMA and cur_position > 0:
	    order_target_percent(context.s1, 0)

	if (HHV(MAX(O, C), 50) / LLV(MIN(O, C), 50) < 2
	    and CROSS(DDD, AMA) and cur_position == 0):
	    order_target_percent(context.s1, 1)


更多 API 介绍
===============================

请见 funcat_ 。


.. _funcat: https://github.com/cedricporter/funcat
