===============================
sys_incremental Mod
===============================

RQAlpha 增量运行 Mod

启用该 Mod 后，可以增量运行回测，方便长期跟踪策略而不必反复运行跑过的日期。

可以每天根据当日数据只运行当天的回测，节约计算资源，方便跟踪大量的策略。

目前自带两种持久化模式，可以通过 CsvRecorder 将状态持久化到磁盘上，或者通过 MongodbRecorder 将状态保存在数据库。

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
        "strategy_id": "1",
        # 是否启用 csv 保存 feeds 功能，可以设置为 MongodbRecorder
        "recorder": "CsvRecorder",
        # 持久化数据输出文件夹
        "persist_folder": None,
        # mongodb
        "mongo_url": "mongodb://localhost",
        "mongo_dbname": "rqalpha_records",
    }

运行
===============================

使用默认的文件持久化

..  code-block:: bash

    rqalpha run -f ~/strategy.py -s 2017-09-01 -e 2017-10-01 --account stock 100000 -l verbose --persist-folder ~/strategy-persist/strategy-1/
    # 接着上次运行继续增量运行回测
    # 此时传入的 account 信息会被持久化的数据覆盖
    rqalpha run -f ~/strategy.py -s 2017-10-02 -e 2017-11-01 --account stock 100000 -l verbose --persist-folder ~/strategy-persist/strategy-1/

使用数据库持久化

..  code-block:: bash

    rqalpha run -f ~/strategy.py -s 2017-10-16 -e 2017-10-20 --account stock 100000 --recorder MongodbRecorder --mongo-url mongodb://localhost --strategy-id 1
    # 接着上次运行继续增量运行回测
    # 此时传入的 account 信息会被持久化的数据覆盖
    rqalpha run -f ~/strategy.py -s 2017-10-21 -e 2017-10-30 --account stock 100000 --recorder MongodbRecorder --mongo-url mongodb://localhost --strategy-id 1

数据分析
===============================

读取 csv

..  code-block:: python

    import pandas as pd

    portfolio_df = pd.read_csv("~/strategy-persist/strategy-1/portfolio.csv")
    bm_portfolio_df = pd.read_csv("~/strategy-persist/strategy-1/bm_portfolio.csv")
    trade_df = pd.read_csv("~/strategy-persist/strategy-1/trade.csv")

读取 mongodb

..  code-block:: python

    import pandas as pd
    import pymongo

    db = pymongo.MongoClient(mongo_url)["rqalpha_records"]
    pd.DataFrame(db["portfolio"].find_one({"strategy_id": '1'}, {"data": 1, "_id": 0})["data"])
    pd.DataFrame(list(db["trade"].find({"strategy_id": '1'}, {"_id": 0})))