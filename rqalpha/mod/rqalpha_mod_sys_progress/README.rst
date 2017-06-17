===============================
sys_progress Mod
===============================

RQAlpha 控制台进度条 Mod

该 Mod 可以输出当前策略的回测进度。

该模块是系统模块，不可删除

开启或关闭进度条 Mod
===============================

..  code-block:: bash

    # 关闭进度条 Mod
    $ rqalpha mod disable sys_progress

    # 启用进度条 Mod
    $ rqalpha mod enable sys_progress

模块配置项
===============================

您可以通过直接修改 `sys_progress` Mod 的配置信息来选择需要启用的功能。

默认配置项如下：

..  code-block:: python

    {
        "show": False
    }

您可以直接修改模块配置信息来选择开启/关闭对应功能

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
            "sys_progress": {
                "enabled": True,
                "show": True
            }
        }
    }
    run(config)

扩展命令
===============================

在启用该 Mod 的情况下，您可以直接通过 :code:`rqalpha run --progress` 的方式来开启进度条的显示。

..  code-block:: bash

    $ rqalpha run -f strategy.py --progress
