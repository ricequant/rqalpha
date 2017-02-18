.. _development-mod:

====================================
RQAlpha 扩展 - Mod
====================================

目前内置了几个简单的 mod 示例，在 `rqalpha/mod/` 目录下面。

一个最简单的 mod 示例：


.. code-block:: python3

    from rqalpha.interface import AbstractMod
    from rqalpha.utils.logger import system_log


    class HelloWorldMod(AbstractMod):
        def start_up(self, env, mod_config):
            system_log.info("HelloWorldMod.start")

        def tear_down(self, success, exception=None):
            system_log.info("HelloWorldMod.tear")


    def load_mod():
        return HelloWorldMod()
