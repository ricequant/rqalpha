===============================
sys_funcat Mod
===============================

该模块为 RQAlpha 带来了通达信公式的方式写策略。

启用该 Mod ，会自动将 Funcat_ 注入 API 到 RQAlpha 中。

开启或关闭 Mod
===============================

.. code-block:: bash

    # 启用 Funcat API Mod
    $ rqalpha mod enable sys_funcat

    # 关闭 Funcat API Mod
    $ rqalpha mod disable sys_funcat


API样例
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


.. _Funcat: https://github.com/cedricporter/funcat
