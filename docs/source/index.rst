
===============================
RQAlpha |version| Documentation
===============================

..  image:: https://img.shields.io/travis/ricequant/rqalpha/master.svg
    :target: https://travis-ci.org/ricequant/rqalpha/branches
    :alt: Build

..  image:: https://coveralls.io/repos/github/ricequant/rqalpha/badge.svg?branch=master
    :target: https://coveralls.io/github/ricequant/rqalpha?branch=master

..  image:: https://readthedocs.org/projects/rqalpha/badge/?version=stable
    :target: http://rqalpha.readthedocs.io/zh_CN/stable/?badge=stable
    :alt: Documentation Status

..  image:: https://img.shields.io/pypi/v/rqalpha.svg
    :target: https://pypi.python.org/pypi/rqalpha
    :alt: PyPI Version

..  image:: https://img.shields.io/pypi/l/rqalpha.svg
    :target: https://opensource.org/licenses/Apache-2.0
    :alt: License

..  image:: https://img.shields.io/pypi/pyversions/rqalpha.svg
    :target: https://pypi.python.org/pypi/rqalpha
    :alt: Python Version Support


RQAlpha 从数据获取、算法交易、回测引擎，实盘模拟，实盘交易到数据分析，为程序化交易者提供了全套解决方案。RQAlpha 具有灵活的配置方式，强大的扩展性，用户可以非常容易地定制专属于自己的程序化交易系统。

RQAlpha 所有的策略都可以直接在 `Ricequant`_ 上进行回测和实盘模拟，并且可以通过微信和邮件实时推送您的交易信号。

`Ricequant`_ 是一个开放的量化算法交易社区，为程序化交易者提供免费的回测和实盘模拟环境，并且会不间断举行实盘资金投入的量化比赛。


Getting Help
==================

关于RQAlpha的任何问题可以通过以下途径来获取帮助

*  查看 :doc:`FAQ <faq>` 页面找寻常见问题及解答
*  可以通过 :ref:`genindex` 或者 :ref:`search` 来查找特定问题
*  在 `github issue page`_ 中提交issue
*  RQAlpha 交流群「487188429」

Quick Guide
==================

.. toctree::
    :caption: Quick Guide
    :hidden:

    intro/overview
    intro/install
    intro/detail_install
    intro/tutorial
    intro/examples

:doc:`intro/overview`
    了解RQAlpha

:doc:`intro/install`
    安装RQAlpha

:doc:`intro/detail_install`
    如果对Python并不熟悉的话，我们提供了整套开发环境的详细安装教程

:doc:`intro/tutorial`
    使用RQAlpha

:doc:`intro/examples`
    通过RQAlpha运行的策略示例


RQAlpha API
==================

.. toctree::
    :caption: API
    :hidden:

    api/config
    api/base_api
    api/extend_api

:doc:`api/config`
    启动 RQAlpha 参数配置

:doc:`api/base_api`
    基础API(期货股票公用API)

:doc:`api/extend_api`
    扩展API(开源版暂不支持，可以通过Ricequant平台或者商业版使用)


Development
==================

.. toctree::
    :caption: Development
    :hidden:

    development/make_contribute
    development/basic_concept
    development/mod

:doc:`development/make_contribute`
    如何加入 RQAlpha 的开发

:doc:`development/basic_concept`
    基本概念

:doc:`development/mod`
    基于Mod来开发和扩展RQAlpha

Extra
==================

.. toctree::
    :caption: Extra
    :hidden:

    faq
    history
    todo

:doc:`faq`
    FAQ

:doc:`history`
    更新日志

:doc:`todo`
    TODO

.. _github issue page: https://github.com/ricequant/rqalpha/issues
.. _Ricequant: https://www.ricequant.com/algorithms

