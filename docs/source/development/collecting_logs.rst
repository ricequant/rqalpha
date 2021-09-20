.. _development-collection-logs:

==================
收集策略日志
==================

RQAlpha 采用 `logbook`_ 作为默认的日志模块，开发者可以通过在 mod 中为 logger 添加 handler 实现自定义的日志收集。

.. _`logbook`: https://logbook.readthedocs.io/en/stable/


也可以使用第三方 mod `rqalpha-mod-log <https://pypi.org/project/rqalpha-mod-log/>`_