# !usr/bin/env python3
# -*- coding: utf-8 -*-

from logbook.base import NOTSET
from logbook.handlers import Handler, StringFormatterHandlerMixin

from rqalpha.environment import Environment
from rqalpha.interface import AbstractMod
from rqalpha.utils.logger import user_system_log, user_log


class LogHandler(Handler, StringFormatterHandlerMixin):
    def __init__(self, send_log_handler, mod_config, level=NOTSET, format_string=None, filter=None, bubble=False):
        Handler.__init__(self, level, filter, bubble)
        StringFormatterHandlerMixin.__init__(self, format_string)
        self.send_log_handler = send_log_handler
        self.mod_config = mod_config

    def _write(self, level_name, item):
        dt = Environment.get_instance().calendar_dt
        self.send_log_handler(dt, item, level_name, mod_config=self.mod_config)

    def emit(self, record):
        msg = self.format(record)
        self._write(record.level_name, msg)


class CustomLogHandlerMod(AbstractMod):
    def _send_log(self, dt, text, log_tag, mod_config):
        with open(f'{mod_config.log_file}', mode=mod_config.log_mode) as f:
            f.write(f'[{dt}] {log_tag}: {text}\n')

    def start_up(self, env, mod_config):
        user_log.handlers.append(LogHandler(self._send_log, mod_config, bubble=True))
        user_system_log.handlers.append(LogHandler(self._send_log, mod_config, bubble=True))

    def tear_down(self, code, exception=None):
        pass


def load_mod():
    return CustomLogHandlerMod()
