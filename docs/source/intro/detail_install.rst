.. _intro-detail-install:

=====================
Anaconda 虚拟环境搭建
=====================

Anaconda 是一个用于科学计算的 Python 发行版，支持 Linux, Mac, Windows, 包含了众多流行的科学计算、数据分析的 Python 包。

Anaconda 环境包含了常用的 Python 科学计算库及依赖关系，而 RQAlpha 有很多模块是依赖于这些科学计算库的，因此下载 Anaconda 可以轻松搭建出一个强大的 Python 量化研发的基础环境。

.. note::

    安装 Anaconda 比较简单，只需要去 `Anaconda 官网`_ 下载对应操作系统版本的安装包进行安装即可。

当安装成功后，执行如下命令来查看是否安装成功:

.. code-block:: bash

    conda -V

For GNU/Linux
------------------------------------

如果您使用 GNU/Linux 系统，可以使用如下方式进行 Anaconda 环境（基于 **Python 3**）的安装，下面以 CentOS 为例:

.. code-block:: bash

    # 首先从 Anaconda 官网下载 anaconda Linux 64Bit 版本命令行安装包

    $ wget https://repo.anaconda.com/archive/Anaconda3-2020.02-Linux-x86_64.sh

    # 修改权限让脚本可以运行
    $ chmod +x Anaconda3-2020.02-Linux-x86_64.sh

    # 运行该安装脚本
    $ ./Anaconda3-2020.02-Linux-x86_64.sh

    # 剩下就是一路Yes或者Enter好了...

    Welcome to Anaconda3 4.2.0 (by Continuum Analytics, Inc.)


    In order to continue the installation process, please review the license

    agreement.

    Please, press ENTER to continue
    >>>

    # 重新加载一下 bash 就可以使用 `conda` 命令了
    $ source ~/.bashrc

    #然后尝试一下运行 `conda -V` 命令行看是否已经安装成功，如果返回对应的版本信息，则说明安装成功。

    $ conda -V
    conda 4.2.13

    #设置matplotlib的backend（没有图形化界面的情况下）
    $ echo "backend: Agg" > ~/.config/matplotlib/matplotlibrc

安装中文字体: 将 :code:`WenQuanYi Micro Hei.ttf` 放到 :code:`/usr/share/fonts/chinese`

在执行以下命令如出现问题，请参考 :ref:`FAQ-chinese-fonts-mac`

.. code-block:: bash

    mkdir /usr/share/fonts/chinese
    cd /usr/share/fonts/chinese
    wget https://static.ricequant.com/data/WenQuanYi%20Micro%20Hei.ttf
    fc-cache -fv
    fc-list
    rm -rf ~/.cache/matplotlib
    rm -rf ~/.fontconfig


.. _`Anaconda 官网`: https://www.anaconda.com/distribution/


conda 虚拟环境
------------------------------------

*   构建 conda 虚拟环境

我们强烈建议您去创建并使用Python虚拟环境，因为这样才能让您的开发环境更加独立，不会因为安装不同的包而出现问题，造成运行失败等。

目前流行的Python虚拟环境有两种：:code:`conda` 和 :code:`pyenv`, 由于大部分的量化开发都是基于 Anaconda 的 python 技术栈，因此我们建议您使用 conda 作为默认的虚拟环境开发。

以下有几个常用的虚拟环境命令可以使用:



.. code-block:: bash

    # 创建 conda 虚拟环境（ :code:`env_name` 是您希望创建的虚拟环境名）
    $ conda create --name env_name python=3.6

    # 如您想创建一个名为rqalpha的虚拟环境
    $ conda create --name rqalpha python=3.6

    # 使用 conda 虚拟环境
    $ source activate env_name
    # 如果是 Windows 环境下 直接执行 activcate
    $ activate env_name

    # 退出 conda 虚拟环境
    $ source deactivate env_name
    # 如果是 Windows 环境下 直接执行 deactivate
    $ deactivate env_name

    # 删除 conda 虚拟环境
    $ conda-env remove --name env_name

