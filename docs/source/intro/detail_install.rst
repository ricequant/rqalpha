.. _intro-detail-install:

==================
详细环境搭建
==================

Anaconda
====================================

安装
------------------------------------

**如果您已经安装好了 Anaconda 环境，可以跳过这个环节**

Anaconda 是一个用于科学计算的 Python 发行版，支持 Linux, Mac, Windows, 包含了众多流行的科学计算、数据分析的 Python 包。

Anaconda 环境包含了常用的 Python 科学计算库及依赖关系，而 RQAlpha 有很多模块是依赖于这些科学计算库的，因此下载 Anaconda 可以轻松搭建出一个强大的 Python 量化研发的基础环境。

安装 Anaconda 需要新下载最新的安装包。我们建议您下载最新的 Python 3.5 Anaconda 安装包，具体地址如下:

1.  官方下载：https://www.continuum.io/downloads  （我们不是特别建议，因为官方下载的速度较慢，但是如果您非常认可官方的可信度可以考虑...）
2.  清华的官方镜像下载：https://mirrors.tuna.tsinghua.edu.cn/anaconda/archive/  ，找最新的anaconda版本下载即可

For CentOS
------------------------------------

首先从清华的官方镜像下载 anaconda Linux64版本

.. code-block:: bash

    wget https://mirrors.tuna.tsinghua.edu.cn/anaconda/archive/Anaconda3-4.2.0-Linux-x86_64.sh

修改权限让脚本可以运行

.. code-block:: bash

    chmod +x Anaconda3-4.2.0-Linux-x86_64.sh

运行该安装脚本

.. code-block:: bash

    ./Anaconda3-4.2.0-Linux-x86_64.sh

剩下就是一路Yes或者Enter好了...

.. code-block:: bash

    Welcome to Anaconda3 4.2.0 (by Continuum Analytics, Inc.)


    In order to continue the installation process, please review the license

    agreement.

    Please, press ENTER to continue
    >>>

重新加载一下 bash 就可以使用 `conda` 命令了

.. code-block:: bash

    source ~/.bashrc

然后尝试一下运行 `conda -V` 命令行看是否已经安装成功，如果返回对应的版本信息，则说明安装成功。

.. code-block:: bash

    conda -V

设置matplotlib的backend（没有图形化界面的情况下）

.. code-block:: bash

echo "backend: Agg" > ~/.config/matplotlib/matplotlibrc

安装中文字体: 将 WenQuanYi Micro Hei.ttf 放到 /usr/share/fonts/chinese

.. code-block:: bash

    mkdir /usr/share/fonts/chinese
    cd /usr/share/fonts/chinese
    wget https://static.ricequant.com/data/WenQuanYi%20Micro%20Hei.ttf
    fc-cache -fv
    fc-list
    rm -rf ~/.cache/matplotlib
    rm -rf ~/.fontconfig


更改 Anaconda 源，提高下载速度
------------------------------------

conda 官方的服务器在国外，因此国内的网络环境使用 `conda` 可能会比较慢，建议您根据自己的网络环境选择是否更换 `conda` 源。

清华大学提供了Anaconda的仓库镜像，我们只需要配置Anaconda的配置文件，添加清华的镜像源，然后将其设置为第一搜索渠道即可：
运行以下命令行:

..  code-block:: bash

    conda config --add channels 'https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/'
    conda config --set show_channel_urls yes

设置好源后，就可以使用 `conda install 【包名】` 安装需要的 Python 库了。大部分情况下，建议使用 `conda` 来安装 Python 数据分析相关的库，因为 conda 做了很多的优化和版本依赖关系的管理。如果没有相关的库，则使用 `pip install 【包名】` 的方式来安装。

conda 虚拟环境
------------------------------------

*   构建 conda 虚拟环境

我们强烈建议您去创建并使用Python虚拟环境，因为这样才能让您的开发环境更加独立，不会因为安装不同的包而出现问题，造成运行失败等。

目前流行的Python虚拟环境有两种：conda 和 pyenv, 由于大部分的量化开发都是基于 Anaconda 的 python 技术栈，因此我们建议您使用 conda 作为默认的虚拟环境开发。

一下有几个常用的虚拟环境命令可以使用:

*   创建 conda 虚拟环境

.. code-block:: bash

    conda create --name env_name python=3.5

*   使用 conda 虚拟环境

.. code-block:: bash

    source activate env_name

*   退出 conda 虚拟环境

.. code-block:: bash

    source deactivate env_name

*   删除 conda 虚拟环境

    conda-env remove --name env_name

注意: **Windows下无需加上 source**

安装 RQAlpha
====================================

RQAlpha 的相关安装 请参考 :ref:`intro-install`

.. _intro-detail-install-talib:

安装 TA-Lib
====================================

您可以使用PyPI安装:

.. code-block:: bash

    $ pip install TA-Lib

如果发现无法通过 pip 安装，请访问 https://mrjbq7.github.io/ta-lib/install.html 解决。

对于 Windows 用户，如果编译困难，可以根据您本地的Python版本下载指定的whl包，然后 `pip install TA_Lib-0.4.9-cp27-none-win_amd64.whl` 来完成安装。
