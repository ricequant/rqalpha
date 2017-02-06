.. _intro-install:

==================
安装指南
==================

兼容性
==================

RQAlpha目前只支持 python 3.4 及以上，Python 2 暂不支持。

安装
==================

为了避免一些安装问题，建议您先升级您的 pip 和 setuptools ::

    $ pip install -U pip setuptools

安装 RQAlpha ::

    $ pip install rqalpha

如果执行 `pip install` 安装依赖库网络速度比较慢的话，推荐使用国内镜像来进行加速::

    $ pip install -i http://pypi.douban.com/simple/ --trusted-host pypi.douban.com rqalpha

查看 RQAlpha 是否安装成功可以通过如下方式::

    $ rqalpha version

.. _intro-install-get-data:

获取回测数据
==================

RiceQuant 免费提供日级别的股票和期货数据供回测使用，可以通过以下命令来进行每日数据的增量更新::

    $ rqalpha update_bundle

平台相关的安装问题
==================

在Windows运行报`Error on import matplotlib.pyplot`
------------------------------------------------------

请访问 `Error on import matplotlib.pyplot (on Anaconda3 for Windows 10 Home 64-bit PC) <http://stackoverflow.com/questions/34004063/error-on-import-matplotlib-pyplot-on-anaconda3-for-windows-10-home-64-bit-pc>`_ 解决。

在Windows出现缺失`cl.exe`
----------------------------

请访问 https://wiki.python.org/moin/WindowsCompilers 下载VC并且安装。

出现安装 `bcolz` 编译失败
---------------------------

访问 http://www.lfd.uci.edu/~gohlke/pythonlibs/#bcolz 下载 `bcolz` 安装，之后再安装rqalpha。

安装 `TA-Lib`
------------------

您可以使用PyPI安装::

    $ pip install TA-Lib

如果发现无法通过 pip 安装，请访问 https://mrjbq7.github.io/ta-lib/install.html 解决。

对于 Windows 用户，如果编译困难，可以根据您本地的Python版本下载指定的whl包，然后 `pip install TA_Lib-0.4.9-cp27-none-win_amd64.whl` 来完成安装。

