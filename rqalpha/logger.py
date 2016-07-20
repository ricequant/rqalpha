# -*- coding: utf-8 -*-

import sys

from logbook import Logger, StreamHandler, StderrHandler

from .utils import ExecutionContext


__all__ = [
    "user_log",
]


def user_log_formatter(record, handler):
    return "[{dt}] {level}: {msg}".format(
        dt=ExecutionContext.get_current_dt(),
        level=record.level_name,
        msg=record.message,
    )


handler = StreamHandler(sys.stdout)
handler.formatter = user_log_formatter
handler.push_application()


user_log = Logger("user_log")
