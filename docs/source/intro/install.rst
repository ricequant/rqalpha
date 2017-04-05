.. _intro-install:

==================
安装指南
==================

安装前
==================

**我们强烈建议您如果安装过程中遇到了问题，先阅读该文档下面的 「FAQ」 章节来尝试着解决**

..  image:: https://img.shields.io/pypi/pyversions/rqalpha.svg
    :target: https://pypi.python.org/pypi/rqalpha
    :alt: Python Version Support

注: 我们尽量保证 Python 2.7 的兼容，但如果没有特殊的需求，尽量使用 Python 3.4+

为了避免一些安装问题，建议您先升级您的 pip 和 setuptools :

.. code-block:: bash

    $ pip install -U pip setuptools

bcolz 是 RQAlpha 的依赖库，因为其编译时间较长，并且中间比较容易失败，建议先单独安装 bcolz 库，安装好以后再安装 RQAlpha。如果在安装的过程中出现问题，请参考 「FAQ」 章节。

Windows 环境下因为默认没有安装 `Visual C++ Compiler`, 需要自行下载并安装 `visual-cpp-build-tools`，如果觉得麻烦，也可以直接去 http://www.lfd.uci.edu/~gohlke/pythonlibs/#bcolz 下载相应版本的 :code:`bcolz wheel` 包，直接安装编译后的 bcolz 版本。

.. code-block:: bash

    $ pip install cython
    $ pip install bcolz

安装
==================

.. code-block:: bash

    $ pip install rqalpha

如果执行 :code:`pip install` 安装依赖库网络速度比较慢的话，推荐使用国内镜像来进行加速:

.. code-block:: bash

    $ pip install -i https://pypi.tuna.tsinghua.edu.cn/simple rqalpha

查看 RQAlpha 是否安装成功可以通过如下方式:

.. code-block:: bash

    $ rqalpha version

.. _intro-install-get-data:

获取回测数据
==================

RiceQuant 免费提供日级别的股票和期货数据供回测使用，可以通过以下命令来进行每日数据的增量更新:

.. code-block:: bash

    $ rqalpha update_bundle

bundle 默认存放在 :code:`~/.rqalpha` 下，您也可以指定 bundle 的存放位置，

.. code-block:: bash

    $ rqalpha update_bundle -d target_bundle_path

如果您使用了指定路径来存放 bundle，那么执行程序的时候也同样需要指定对应的 bundle 路径。

.. code-block:: bash

    $ rqalpha run -d target_bundle_path .....

详细参数配置请查看 :ref:`api-config`

获取配置文件
==================

如果运行 RQAlpha 时不指定配置文件，会在 :code:`~/.rqalpha/` 文件夹下创建 :code:`config.yml` 文件作为默认配置文件。

如果您想要直接获得一份配置文件，也可以通过如下命令来获得。

.. code-block:: bash

    $ rqalpha generate_config

FAQ
==================

1.  Bcolz 相关问题
    
    请首先 `pip install cython` 来安装cython

    `bcolz` 安装大部分问题都来自于没有安装 `Visual C++ Compiler`，建议您无论如何先成功安装 `Visual C++ Compiler`， 访问 https://wiki.python.org/moin/WindowsCompilers 根据自己的机器环境和Python版本选择安装对应的编译工具。

    不进行编译安装，访问 http://www.lfd.uci.edu/~gohlke/pythonlibs/#bcolz 下载 :code:`bcolz` 直接进行安装。

2.  Matplotlib 相关问题

    1.  运行回测时，matplotlib 报错怎么办？:code:`RuntimeError: Python is not installed as a framework`:

    解决方案：创建文件 :code:`~/.matplotlib/matplotlibrc`，并加入代码 :code:`backend: TkAgg`
    
    2.  在 Python 3.6 下没有任何报错，但是就是没有plot输出:

    解决方案：创建文件 :code:`~/.matplotlib/matplotlibrc`，并加入代码 :code:`backend: TkAgg`

    3.  在Windows运行报 :code:`Error on import matplotlib.pyplot`:

    解决方案: 请访问 `Error on import matplotlib.pyplot (on Anaconda3 for Windows 10 Home 64-bit PC) <http://stackoverflow.com/questions/34004063/error-on-import-matplotlib-pyplot-on-anaconda3-for-windows-10-home-64-bit-pc>`_ 解决。

3.  Python 2.7 在 Windows 下产生中文乱码的问题

    RQAlpha 运行在 Windows(Python 2.x) 可能会遇到中文乱码的问题，这个并不是RQAlpha的问题，而是由于 Windows 的 cmd 本身是 `gbk` 编码而产生的，具体的解决方案可以参考 [Windows(Python 2.x) 命令行下输出日志中文乱码的问题](https://github.com/ricequant/rqalpha/issues/80)