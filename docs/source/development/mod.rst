.. _development-mod:

====================================
RQAlpha 扩展 - Mod
====================================

目前内置了几个简单的 mod 示例，在 `rqalpha/mod/` 目录下面。


Hello World
===============

我们在 `rqalpha/mod/` 下面创建一个 `hello_world` 文件夹。进入 `hello_world` 文件夹，创建 `__init__.py` ，填入以下代码：

.. code-block:: python3

    from rqalpha.interface import AbstractMod


    class HelloWorldMod(AbstractMod):
        def start_up(self, env, mod_config):
            print(">>> HelloWorldMod.start")

        def tear_down(self, success, exception=None):
            print(">>> HelloWorldMod.tear")


    def load_mod():
        return HelloWorldMod()


于是我们的第一个 Mod 就写好了，现在我们需要修改配置，以让我们的 mod 生效，我们创建一个新的配置文件，在 mod 下面

.. code-block:: yaml

    mod:
      hello_world:
        lib: 'rqalpha.mod.hello_world'
        enabled: true
        priority: 100


然后运行命令，就会输出一下内容

.. code-block:: bash

    $ rqalpha run -f rqalpha/examples/buy_and_hold.py -sc 100000
    >>> HelloWorldMod.start
    >>> HelloWorldMod.tear
