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

以独立 Pypi 包作为 Mod
================================

RQAlpha 支持安装、卸载、启用、停止第三方Mod。

.. code-block:: bash

    # 以名为 "xxx" 的 Mod 为例，介绍RQAlpha 第三方Mod的使用

    # 安装
    $ rqalpha install xxx

    # 卸载
    $ rqalpha uninstall xxx

    # 启用
    $ rqalpha enable xxx

    # 关闭
    $ rqalpha disable xxx

如果您希望发布自己的Mod并被 RQAlpha 的用户使用，只需要遵循简单的约定即可。

下面为一个 RQAlpha Mod 的模板:

.. code-block:: python3

    from rqalpha.interface import AbstractMod


    class XXXMod(AbstractMod):
        def __init__(self):
            pass

        def start_up(self, env, mod_config):
            pass

        def tear_down(self, code, exception=None):
            pass


    def load_mod():
        return XXXMod()


    __mod_config__ = """
      param1: "111"
      param2: "222"
    """

约定如下：

1.  需要定义并实现 :code:`load_mod` 函数, 其返回值为对应的继承自 :code:`AbstractMod` 的类，并且 :code:`load_mod` 所在文件必须按照 :code:`rqalpha_mod_xxx` 规则进行命名。
2.  如果有自定义参数的话，需要实现 :code:`__mod_config__` 变量，其为字符串，配置的具体格式为 `yaml` 格式(支持注释)。RQAlpha 会自动将其扩展到默认配置项中。
3.  当写好 Mod 以后，需要发布到 Pypi 仓库中，并且包名需要如下格式: :code:`rqalpha-mod-xxx`，一下的 setup.py 文件可作参考。

.. code-block:: python3

    from pip.req import parse_requirements

    from setuptools import (
        find_packages,
        setup,
    )

    setup(
        name='rqalpha-mod-xxx',
        version="0.1.0",
        description='RQAlpha Mod XXX',
        packages=find_packages(exclude=[]),
        author='',
        author_email='',
        license='Apache License v2',
        package_data={'': ['*.*']},
        url='',
        install_requires=[str(ir.req) for ir in parse_requirements("requirements.txt", session=False)],
        zip_safe=False,
        classifiers=[
            'Programming Language :: Python',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: Unix',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
        ],
    )

按此编写好 Mod 并发布到 Pypi 上以后，就可以直接使用RQAlpha的命令来安装和启用该Mod了。

如果您希望更多人使用您的Mod，您也可以联系我们，我们审核通过后，会在 RQAlpha 项目介绍和文档中增加您的Mod的介绍和推荐。