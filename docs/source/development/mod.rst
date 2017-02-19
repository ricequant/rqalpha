.. _development-mod:

====================================
RQAlpha 扩展 - Mod
====================================

目前内置了几个简单的 mod 示例，在 :code:`rqalpha/mod/` 目录下面。


Hello World
===============

我们在 :code:`rqalpha/mod/` 下面创建一个 :code:`hello_world` 文件夹。进入 :code:`hello_world` 文件夹，创建 :code:`__init__.py` ，填入以下代码：

.. code-block:: python3

    from rqalpha.interface import AbstractMod


    class HelloWorldMod(AbstractMod):
        def start_up(self, env, mod_config):
            print(">>> HelloWorldMod.start_up")

        def tear_down(self, success, exception=None):
            print(">>> HelloWorldMod.tear_down")


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
    >>> HelloWorldMod.start_up
    >>> HelloWorldMod.tear_down


扩展 RQAlpha API
================
如果你想为 RQAlpha 创建自己的 API，你也可以通过 Mod 来注册新的 API。在内建的 mod 中，有一个 FuncatAPIMod ，将通达信、同花顺的公式表达能力移植到 Python 中，扩展了 RQAlpha 的 API。

其中的关键点，是通过了 :code:`register_api` 来注册 API。

我们只需要实现一个 Mod，然后在 :code:`start_up` 过程中，使用 :code:`register_api` 来注册 API ，既可以达到扩展 RQAlpha API 的功能。

.. code-block:: python3

    class FuncatAPIMod(AbstractMod):
        def start_up(self, env, mod_config):
            try:
                import funcat
            except ImportError:
                print("-" * 50)
                print(">>> Missing funcat. Please run `pip install funcat`")
                print("-" * 50)
                raise

            # change funcat data backend to rqalpha
            from funcat.data.rqalpha_backend import RQAlphaDataBackend
            funcat.set_data_backend(RQAlphaDataBackend())

            # register funcat api into rqalpha
            from rqalpha.api.api_base import register_api
            for name in dir(funcat):
                obj = getattr(funcat, name)
                if getattr(obj, "__module__", "").startswith("funcat"):
                    register_api(name, obj)

        def tear_down(self, code, exception=None):
            pass
