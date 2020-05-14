.. _development-mod:

====================================
Mod
====================================

创建您的第一个Mod
================================

每一个Mod都遵循扩展事件源的细则，通过对接接口即可实现各种逻辑的组合，而 Mod 接口是扩展事件源的标准格式，下面我们将创建一个最简单的Mod帮助大家理解。

.. warning:: 在克隆RQAlpha的时候发现我们有一些系统集成的 Mod 在 RQAlpha 里，这是为了大家可以能更好了解Mod逻辑，但是在开发Mod的过程里我们不建议您在原有的 RQAlpha 项目中做更改，而是将 Mod 以独立的项目进行开发。


Mod开发环境搭建
----------------

首先我们创建独立的开发虚拟环境：

.. code-block:: bash

    $ conda create rqalpha-mod-hello

在虚拟环境下将 RQAlpha 安装好：

如有问题请参考：:ref:`intro-install`

创建Mod项目
-----------------

我们以 `rqalpha-mod-hello <https://github.com/johnsonchak/rqalpha-mod-hello>`_ 项目为例，介绍如何实现一个简单的 Mod

项目结构:

.. code-block:: bash

    rqalpha-mod-hello
    ├── __init__.py
    ├── requirements.txt
    ├── README.rst
    ├── setup.py
    └── rqalpha_mod_hello
        ├── __init__.py
        └── mod.py

假设在新的环境中已经可以成功运行 RQAlpha ，便按照Mod的标准命名格式创建项目 :code:`rqalpha-mod-hello`。进入 :code:`rqalpha-mod-hello` 文件夹，创建 :code:`__init__.py`，填入以下代码：

.. code-block:: python3

    __config__ = {
        "url": None,

    }

    def load_mod():
        from .mod import HelloWorldMod
        return HelloWorldMod()

创建 :code:`mod.py` ，填入以下代码：

.. code-block:: python3

    from rqalpha.interface import AbstractMod


    class HelloWorldMod(AbstractMod):
        def start_up(self, env, mod_config):
            print(">>> HelloWorldMod.start_up")

        def tear_down(self, success, exception=None):
            print(">>> HelloWorldMod.tear_down")

我们第一个 Mod 就写好了，接下来我们需要写一个 :code:`setup.py` 以便我们以PyPI的形式发布以及安装。

PyPI方式安装Mod
------------------------

在项目 :code:`rqalpha-mod-hello` 下新建 :code:`setup.py` ，按照以下格式填入代码。

.. code-block:: python3


    #from pip.req import parse_requirements 这样的话如果pip版本较高会报错
    try: # for pip >= 10
        from pip._internal.req import parse_requirements
    except ImportError: # for pip <= 9.0.3
        from pip.req import parse_requirements

    from setuptools import (
        find_packages,
        setup,
    )

    setup(
        name='rqalpha-mod-hello',     #mod名
        version="0.1.0",
        description='RQAlpha Mod to say hello',
        packages=find_packages(exclude=[]),
        author='your name',
        author_email='your email address',
        license='Apache License v2',
        package_data={'': ['*.*']},
        url='https://github.com/johnsonchak/rqalpha-mod-hello',
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

在完成 :code:`setup.py` 文件的同时需要为Mod添加版本信息 :code:`VERSION.txt` 以及运行所需环境说明文件 :code:`requirements.txt` :

完成以后即可在命令进入Mod项目的 :code:`setup.py` 所在路径下进行安装:

.. code-block:: bash

    $ pip install -e .

.. note::

    .. code-block:: bash

        $ pip install -e .

    会扫描当前目录下的 :code:`setup.py` 文件执行安装，同时直接修改项目内文件就可以实现修改对应Mod。


激活以及使用Mod
--------------------

激活并查看我们安装的mod：

.. code-block:: bash

    $ rqalpha mod enable hello
    $ rqalpha mod list

.. image:: https://raw.githubusercontent.com/ricequant/rq-resource/master/rqalpha/mod-install-success.png


运行RQAlpha即可看到如下：

.. image:: https://raw.githubusercontent.com/ricequant/rq-resource/master/rqalpha/mod-run-success.png

.. note::

    至此，完成了第一个Mod的创建以及安装，如您想与RQAlpha用户分享自己的Mod，您需要遵守一些发布格式，以便他人进行管理及使用。

    :ref:`development-release-mod`


扩展 RQAlpha API
================================

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
            from rqalpha.api import register_api
            for name in dir(funcat):
                obj = getattr(funcat, name)
                if getattr(obj, "__module__", "").startswith("funcat"):
                    register_api(name, obj)

        def tear_down(self, code, exception=None):
            pass

.. _development-release-mod:

发布独立 Pypi 包作为 Mod
================================

RQAlpha 支持安装、卸载、启用、停止第三方Mod。

.. code-block:: bash

    # 以名为 "xxx" 的 Mod 为例，介绍RQAlpha 第三方Mod的使用

    # 启用
    $ rqalpha mod enable xxx

    # 关闭
    $ rqalpha mod disable xxx

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
3.  当写好 Mod 以后，需要发布到 Pypi 仓库中，并且包名需要如下格式: :code:`rqalpha-mod-xxx`，以下的 setup.py 文件可作参考。

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
            'Programming Language :: Python :: 3.6',
        ],
    )

按此编写好 Mod 并发布到 Pypi 上以后，就可以直接使用RQAlpha的命令来安装和启用该Mod了。

如您不熟悉PyPI发布的流程，请参考官方文档：https://packaging.python.org/distributing/


如果您希望更多人使用您的Mod，您也可以联系我们，我们审核通过后，会在 RQAlpha 项目介绍和文档中增加您的Mod的介绍和推荐。