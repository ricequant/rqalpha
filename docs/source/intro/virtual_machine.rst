.. _intro-virtual-machine:

========================================
开箱即用虚拟机
========================================

为了您方便快速上手 RQAlpha，免去开发环境的安装和配置，我们为您提供了一个虚拟机镜像文件。该虚拟机已经安装了最新版本的 RQAlpha 及其他依赖组件。

使用虚拟机
------------------------------------------------------

此处附上使用 VirtualBox 使用本镜像的简单教程

*   访问 `VirtualBox 官网`_ 下载 VirtualBox。

*   下载 `RQAlpha 开箱即用虚拟机镜像`_ 。

*   在 VirtualBox 中选择 "导入虚拟电脑"， 选择刚刚下载的 .ova 文件。

*   点击 继续，进行虚拟机的一些设置，亦可维持默认。

*   点击 导入，坐等几分钟。

*   选择刚刚创建好的虚拟机，点击启动。

.. image:: https://raw.githubusercontent.com/ricequant/rq-resource/master/rqalpha/virtualBox_1.png

*   选中创建好的虚拟机，点击 "启动"

*   虚拟机的默认用户密码为: rqalpha

.. _VirtualBox 官网: https://www.virtualbox.org/wiki/Downloads

.. _RQAlpha 开箱即用虚拟机镜像: https://pan.baidu.com/s/1htvAEmK


在终端运行 RQAlpha
------------------------------------------------------


在您成功创建虚拟机并运行后，您可以按照以下步骤快速运行 RQAlpha

打开终端并在终端输入如下命令以进入事先创建好的虚拟环境

..  code-block:: bash

    source activate py3

在终端输入如下命令以启动 RQAlpha，并运行 :ref:`intro-examples` 中的 :ref:`intro-examples-buy-and-hold` 进行回测。

.. code-block:: bash

    rqalpha run -f ~/examples/buy_and_hold.py -s 2017-01-01 -e 2017-12-31 --account stock 100000 --benchmark 000300.XSHG --plot


其他命令
------------------------------------------------------

更新 RQAlpha 版本

.. code-block:: bash

    source activate py3
    pip install -U rqalpha

在 RQAlpha 所在虚拟环境中安装其他依赖（以 funcat 为例）

.. code-block:: bash

    source activate py3
    pip install funcat

