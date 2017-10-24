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

    *   我们强烈建议您使用虚拟环境安装RQAlpha，以避免因为环境问题出现安装失败。虚拟环境的使用请参考：:ref:`intro-detail-create-env`
    *   如果安装过程中遇到了问题，先阅读该文档下面的 「FAQ」 章节来尝试着解决
    *   如果执行 :code:`pip install` 安装依赖库网络速度比较慢的话，推荐使用 :code:`pip install -i https://pypi.tuna.tsinghua.edu.cn/simple` 国内镜像来加速

*   更新您的 pip 和 setuptools :

.. code-block:: bash

    $ pip install -U pip setuptools cython -i https://pypi.tuna.tsinghua.edu.cn/simple

*   安装 bcolz

bcolz 是 RQAlpha 的依赖库，因为其编译时间较长，并且中间比较容易失败，建议先单独安装 bcolz 库，安装过程比较慢，请耐心等待。

.. code-block:: bash

    $ pip install bcolz -i https://pypi.tuna.tsinghua.edu.cn/simple

如果在安装的过程中出现问题，请参考 :ref:`intro-faq` 章节。

.. note::

       Windows 环境下因为默认没有安装 `Visual C++ Compiler`, 需要自行下载并安装 `visual-cpp-build-tools`，如果觉得麻烦，也可以直接去 http://www.lfd.uci.edu/~gohlke/pythonlibs/#bcolz 下载相应版本的 :code:`bcolz wheel` 包，直接安装编译后的 bcolz 版本。

       除了 bcolz 库以外，line-profiler 安装时也同样需要 C++ 编译器，如果出现安装失败，也可以前往 http://www.lfd.uci.edu/~gohlke/pythonlibs/#line_profiler 下载相应的版本 :code:`line-profiler wheel` 包来进行安装。

       Mac OS 环境下默认没有安装`X-code`，需要自行运行安装以添加一个轻量级的C/C++ clang编译器，可在Terminal下输入：

        .. code-block:: bash

            $ xcode-select --install

        .. code-block:: bash

            $ pip install cython
            $ pip install bcolz

安装
==================

.. code-block:: bash

    $ pip install -i https://pypi.tuna.tsinghua.edu.cn/simple rqalpha

查看 RQAlpha 是否安装成功可以通过如下方式:

.. code-block:: bash

    $ rqalpha version

.. _intro-install-get-data:

获取回测数据
==================

RiceQuant 免费提供日级别的股票和期货数据供回测使用，可以通过以下命令来进行每日数据的增量更新:

.. note::

    Mac OS下执行 :code:`update_bundle` 出现问题，请参考：:ref:`FAQ-update-bundle-mac`

.. code-block:: bash

    $ rqalpha update_bundle


bundle 默认存放在 :code:`~/.rqalpha` 下，您也可以指定 bundle 的存放位置，

.. code-block:: bash

    $ rqalpha update_bundle -d target_bundle_path

如果您使用了指定路径来存放 bundle，那么执行程序的时候也同样需要指定对应的 bundle 路径。

.. code-block:: bash

    $ rqalpha run -d target_bundle_path .....

.. _intro-config:

获取配置文件
==================

如果运行 RQAlpha 时不指定配置文件，会在 :code:`~/.rqalpha/` 文件夹下创建 :code:`config.yml` 文件作为默认配置文件。

如果您想要直接获得一份配置文件，也可以通过如下命令来获得。

.. code-block:: bash

    $ rqalpha generate_config

.. _intro-faq:

FAQ
==================

1.  Bcolz 相关问题
------------------------------------------------------
    
请首先 `pip install cython` 来安装cython

`bcolz` 安装大部分问题都来自于没有安装 `Visual C++ Compiler`，建议您无论如何先成功安装 `Visual C++ Compiler`， 访问 https://wiki.python.org/moin/WindowsCompilers 根据自己的机器环境和Python版本选择安装对应的编译工具。

不进行编译安装，访问 http://www.lfd.uci.edu/~gohlke/pythonlibs/#bcolz 下载 :code:`bcolz` 直接进行安装。

如果您按照 :ref:`intro-detail-install` 进行环境搭建并安装了 `anaconda` 您可以使用如下方式进行免编译安装

.. code-block:: bash

    $ conda install bcolz -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/


2.  Matplotlib 相关问题
------------------------------------------------------

1.  运行回测时，matplotlib 报错怎么办？:code:`RuntimeError: Python is not installed as a framework`:

解决方案：创建文件 :code:`~/.matplotlib/matplotlibrc`，并加入代码 :code:`backend: TkAgg`

2.  在 Python 3.6 下没有任何报错，但是就是没有plot输出:

解决方案：创建文件 :code:`~/.matplotlib/matplotlibrc`，并加入代码 :code:`backend: TkAgg`

3.  在Windows运行报 :code:`Error on import matplotlib.pyplot`:

解决方案: 请访问 `Error on import matplotlib.pyplot (on Anaconda3 for Windows 10 Home 64-bit PC) <http://stackoverflow.com/questions/34004063/error-on-import-matplotlib-pyplot-on-anaconda3-for-windows-10-home-64-bit-pc>`_ 解决。

3.  Python 2.7 在 Windows 下产生中文乱码的问题
------------------------------------------------------

RQAlpha 运行在 Windows(Python 2.x) 可能会遇到中文乱码的问题，这个并不是RQAlpha的问题，而是由于 Windows 的 cmd 本身是 `gbk` 编码而产生的，具体的解决方案可以参考 [Windows(Python 2.x) 命令行下输出日志中文乱码的问题](https://github.com/ricequant/rqalpha/issues/80)

.. _FAQ-update-bundle-mac:

4.  Mac OS 获取回测数据相关问题
------------------------------------------------------

1.  Finder中查看数据存放位置：

Mac OS下默认关闭显示隐藏文件，如想在Finder中查看bundle，您需要打开显示隐藏文件：

.. code-block:: bash

    $ defaults write com.apple.finder AppleShowAllFiles -boolean true ; killall Finder

.. _FAQ-chinese-fonts-mac:

5.  Mac 下安装中文字体相关问题：
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

6.  策略样例以及数据路径相关问题：
------------------------------------------------------

1.策略样例存储路径：

执行 :code:`pip install rqalpha` 后虽然会默认保存examples到python环境中，但路径相对复杂，我们建议您将examples目录重新保存到您认为方便的地方。

2.数据存储的路径：

如您没有指定路径，则会在您执行 :code:`rqalpha update_bundle` 的当前目录创建 :code:`/.rqalpha/bundle` 的文件夹.您可以在命令行内查看路径。
