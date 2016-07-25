# -*- coding: utf-8 -*-

import sys

from logbook import Logger, StreamHandler, StderrHandler
from logbook.more import ColorizedStderrHandler

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


# handler = StreamHandler(sys.stdout)
handler = ColorizedStderrHandler()
handler.formatter = user_log_formatter
handler.push_application()


user_log = Logger("user_log")


def user_print(*args, **kwargs):
    sep = kwargs.get("sep", " ")
    end = kwargs.get("end", "")

    message = sep.join(map(str, args)) + end

    user_log.info(message)
