===============================
sys_incremental Mod
===============================

RQAlpha 增量运行 Mod

启用该 Mod 后，可以增量运行回测，方便长期跟踪策略而不必反复运行跑过的日期。

可以每天根据当日数据只运行当天的回测，节约计算资源，方便跟踪大量的策略。

该模块是系统模块，不可删除

开启或关闭增量运行 Mod
===============================

..  code-block:: bash

    # 关闭增量运行 Mod
    $ rqalpha mod disable sys_incremental

    # 启用增量运行 Mod
    $ rqalpha mod enable sys_incremental

模块配置项
===============================

..  code-block:: python

    {
        # 持久化数据输出文件夹
        "persist_folder": "./strategy_persist",
        # 是否启动磁盘存储 persist 功能
        "use_disk_persist": True,
        # 是否启用 csv 保存 feeds 功能
        "use_csv_feeds_record": True,
    }

您可以通过如下方式来修改模块的配置信息，从而选择开启/关闭风控模块对应的风控项

..  code-block:: bash

    rqalpha run -f ~/strategy.py -s 2017-10-01 -e 2017-11-23 --account stock 100000 -l verbose --persist-folder ~/strategy-persist/strategy-1/
