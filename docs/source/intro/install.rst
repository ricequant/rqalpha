.. _intro-install:

==================
安装指南
==================

安装前
==================

..  image:: https://img.shields.io/pypi/pyversions/rqalpha.svg
    :target: https://pypi.python.org/pypi/rqalpha
    :alt: Python Version Support

.. note::

    *   我们强烈建议您使用虚拟环境安装RQAlpha，以避免因为环境问题出现安装失败。虚拟环境的使用请参考：:ref:`intro-detail-install`
    *   如果安装过程中遇到了问题，先阅读该文档下面的 「FAQ」 章节来尝试着解决
    *   如果执行 :code:`pip install` 安装依赖库网络速度比较慢的话，推荐使用 :code:`pip install -i https://pypi.douban.com/simple` 国内镜像来加速


安装
==================

.. code-block:: bash

    $ pip install -i https://pypi.douban.com/simple rqalpha

查看 RQAlpha 是否安装成功可以通过如下方式:

.. code-block:: bash

    $ rqalpha version

.. _intro-install-get-data:

获取回测数据
==================

RiceQuant 免费提供日级别的股票、常用指数、场内基金和期货数据供回测使用。数据每个月月初更新，可以通过以下命令来下载:

.. code-block:: bash

    $ rqalpha download-bundle

.. note::

    Mac OS下执行 :code:`download-bundle` 出现问题，请参考：:ref:`FAQ-download-bundle-mac`

bundle 默认存放在 :code:`~/.rqalpha` 下，您也可以指定 bundle 的存放位置，

.. code-block:: bash

    $ rqalpha download-bundle -d target_bundle_path

如果您使用了指定路径来存放 bundle，那么执行程序的时候也同样需要指定对应的 bundle 路径。

.. code-block:: bash

    $ rqalpha run -d target_bundle_path .....


回测数据的更新
==================
您也可以使用 `RQDatac`_ 在每日盘后即时更新回测数据，更新命令如下：

.. code-block:: bash

    $ rqalpha update-bundle

.. note::

    您需要先安装 `RQDatac`_ 包、获取 `RQDatac`_ 的使用权限，并使用 Ricequant 提供的配置脚本将您的 `RQDatac`_ license 配置到系统环境变量中。请参考: https://www.ricequant.com/welcome/trial/rqdata-cloud


.. _intro-config:

获取配置文件
==================

如果运行 RQAlpha 时不指定配置文件，会在 :code:`~/.rqalpha/` 文件夹下创建 :code:`config.yml` 文件作为默认配置文件。

如果您想要直接获得一份配置文件，也可以通过如下命令来获得。

.. code-block:: bash

    $ rqalpha generate-config

.. _intro-faq:

FAQ
==================

1.  line-profiler 相关问题
------------------------------------------------------
RQAlpha 的性能分析功能依赖于 :code:`line_profiler` 包；通过 :code:`pip` 安装 RQAlpha 时，默认并不会附带安装 :code:`line_profiler`；
如果您需要使用性能分析功能，请使用 :code:`pip install rqalpha[profiler]` 方式安装 RQAlpha。

在windows上，建议您访问 http://www.lfd.uci.edu/~gohlke/pythonlibs/#line_profiler 下载 :code:`line_profiler` 直接进行安装。

在windows上，通过 :code:`pip` 安装 :code:`line-profiler` 需要安装 :code:`Visual C++ Compiler`。
请访问 https://wiki.python.org/moin/WindowsCompilers 根据自己的机器环境和Python版本选择安装对应的编译工具。


2.  Matplotlib 相关问题
------------------------------------------------------

1.  运行回测时，matplotlib 报错怎么办？:code:`RuntimeError: Python is not installed as a framework`:

解决方案：创建文件 :code:`~/.matplotlib/matplotlibrc`，并加入代码 :code:`backend: TkAgg`

2.  在 Python 3.6 下没有任何报错，但是就是没有plot输出:

解决方案：创建文件 :code:`~/.matplotlib/matplotlibrc`，并加入代码 :code:`backend: TkAgg`

3.  在Windows运行报 :code:`Error on import matplotlib.pyplot`:

解决方案: 请访问 `Error on import matplotlib.pyplot (on Anaconda3 for Windows 10 Home 64-bit PC) <http://stackoverflow.com/questions/34004063/error-on-import-matplotlib-pyplot-on-anaconda3-for-windows-10-home-64-bit-pc>`_ 解决。


.. _FAQ-download-bundle-mac:

3.  Mac OS 获取回测数据相关问题
------------------------------------------------------

1.  Finder中查看数据存放位置：

Mac OS下默认关闭显示隐藏文件，如想在Finder中查看bundle，您需要打开显示隐藏文件：

.. code-block:: bash

    $ defaults write com.apple.finder AppleShowAllFiles -boolean true ; killall Finder

.. _FAQ-chinese-fonts-mac:

4.  Mac 下安装中文字体相关问题：
------------------------------------------------------

1.  出现 :code:`Operation not permitted`:

因为Mac OS 10.11 EI Capitan 后加入rootless机制，对系统的读写有了更严格的限制，在创建目录环节会出现“Operation not permitted”

您可以通过关闭rootless来解决这个问题。

请重启按住 :code:`command + R` ，进入恢复模式，打开Terminal：

.. code-block:: bash

    $ csrutil disable

2.  出现 :code:`command not found`:

Mac 下默认并没有安装很多命令，我们可以通过homebrew安装，如没有安装homebrew，请参考：

在Terminal下输入：

.. code-block:: bash

    ruby -e "$(curl --insecure -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)”

按照系统提示输入密码

:code:`wget` 命令没有安装：

.. code-block:: bash

   $ brew install wget

:code:`fc--cache` 命令没有安装：

.. code-block:: bash

    $ brew install fontconfig

.. _FAQ-examples-path:

5.  策略样例路径相关问题：
------------------------------------------------------

执行 :code:`pip install rqalpha` 后虽然会默认保存examples到python环境中，但路径相对复杂，我们建议您将examples目录重新保存到您认为方便的地方。


.. _RQDatac: https://www.ricequant.com/welcome/rqdata