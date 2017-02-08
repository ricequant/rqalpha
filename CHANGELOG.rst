0.0.53
==================

- 完善了回测结果显示
- 修正了Risk计算和Benchmark计算


0.0.20
==================

- 增加会回测进度显示开关
- 完善了回测结果显示

0.0.19
==================

- 在handle_bar前用当前的数据更新portfolio和position，因为ricequant.com是这样做的。

0.0.18
==================

- 修复了分红计算

0.0.16
==================

- 用户可以通过context设置slippage/commission/benchmark
- 增加了scheduler

0.0.15
==================

- 修复history在before_trading调用
- 增加api的phase检查

0.0.14
==================

- 修改支持python2

0.0.12
==================

- 修正了Risk计算，使用合理的年化收益计算方法
- 格式化代码符合pep8
- 更新requirements.txt


0.0.9
==================

- 增加了数据下载
- 修正了Risk计算
- 增加了instrument
- 增加了position的 `market_value` 和 `value_percent`


0.0.2
==================

- 增加了日线回测
- 去掉了涨跌停检查
- 增加了分红处理
- 运行参数如下:

::

  # 生成sample策略
  rqalpha generate_examples -d ./

  # 运行回测
  rqalpha run -f examples/simple_macd.py -s 2013-01-01 -e 2015-01-04 -o /tmp/a.pkl

0.0.1
==================

- 搭建基本的框架，增加基本的unittest