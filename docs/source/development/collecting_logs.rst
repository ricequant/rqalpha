.. _development-collection-logs:

==================
收集策略日志
==================

RQAlpha 采用 `logbook`_ 作为默认的日志模块，开发者可以通过在 mod 中为 logger 添加 handler 实现自定义的日志收集。

.. _`logbook`: https://logbook.readthedocs.io/en/stable/


Mod 示例
==================

首先要做的是实现 `handler`_ 对象，此处实现的 handler 对象接受 :code:`send_log_handler` 函数作为参数，该函数会在打印日志的时候被调用。

formatter 使用了 :code:`rqalpha.utils.logger.user_std_handler_log_formatter`，该 formatter 在输出策略日志的时候会选用策略运行的时间而非物理时间作为日志的时间戳。

.. _`handler`: https://logbook.readthedocs.io/en/stable/quickstart.html#handlers

.. code-block:: python

    from logbook.handlers import Handler, StringFormatterHandlerMixin
    from logbook.base import NOTSET

    from rqalpha.environment import Environment
    from rqalpha.utils.logger import user_std_handler_log_formatter


    class LogHandler(Handler, StringFormatterHandlerMixin):
        def __init__(self, send_log_handler, level=NOTSET, format_string=None, filter=None, bubble=False):
            Handler.__init__(self, level, filter, bubble)
            StringFormatterHandlerMixin.__init__(self, format_string)
            self.send_log_handler = send_log_handler
            self.formatter = user_std_handler_log_formatter

        def _write(self, level_name, item):
            dt = Environment.get_instance().calendar_dt
            self.send_log_handler(dt, item, level_name)

        def emit(self, record):
            msg = self.format(record)
            self.lock.acquire()
            try:
                self._write(record.level_name, msg)
            finally:
                self.lock.release()


Mod 的实现如下，该 Mod 所做的所有工作仅仅是初始化了 :code:`LogHandler` 对象并将其传给 user_log 和 user_system_logger。另外需要实现 :code:`_send_log` 方法，将日志送往需要的去处。


.. code-block:: python

    from rqalpha.interface import AbstractMod
    from rqalpha.utils.logger import user_system_log, user_log


    class CustomLogHandlerMod(AbstractMod):
        def _send_log(self, dt, text, log_tag):
            # TODO
            pass

        def start_up(self, env, mod_config):
            user_log.handlers.append(LogHandler(self._send_log, bubble=True))
            user_system_log.handlers.append(LogHandler(self._send_log, bubble=True))

        def tear_down(self, code, exception=None):
            pass


    def load_mod():
        return CustomLogHandlerMod()
