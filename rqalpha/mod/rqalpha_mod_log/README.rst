=======
log Mod
=======

RQAlpha 日志 Mod，实现日志输出


开启或关闭日志 Mod
================

.. code:: bash

   # 关闭日志 Mod
   $ rqalpha mod disable log

   # 启用日志 Mod
   $ rqalpha mod enable log


模块配置项
=========

日志 Mod 的可用配置项如下

.. code:: python

   {
       # 指定日志输出文件
       "log_path": "./log.txt",
       # python open() 方法读写文件的模式
       "log_mode": "a",
   }


拓展命令
=======

在启用该 Mod 的情况下，您可以使用如下功能:

*   :code:`rqalpha run` 命令增加 :code:`--log-file file_path` 选项，您可以将回测中的 log 日志输出到 :code:`file_path` 路径
*   :code:`rqalpha run` 命令增加 :code:`--log-mode log_mode` 选项，也就是 python 内建 :code:`open()` 方法的 mode 参数，决定如何读写输出文件