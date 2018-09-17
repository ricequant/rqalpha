# -*- coding: utf-8 -*-
#
# Copyright 2017 Ricequant, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import datetime
import logbook
from logbook import Logger
from logbook.more import ColorizedStderrHandler

from rqalpha.utils.py2 import to_utf8, from_utf8

logbook.set_datetime_format("local")


# patch warn
logbook.base._level_names[logbook.base.WARNING] = 'WARN'


__all__ = [
    "user_log",
    "system_log",
]


DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"


def user_std_handler_log_formatter(record, handler):
    from rqalpha.environment import Environment
    try:
        dt = Environment.get_instance().calendar_dt.strftime(DATETIME_FORMAT)
    except Exception:
        dt = datetime.now().strftime(DATETIME_FORMAT)

    log = "{dt} {level} {msg}".format(
        dt=dt,
        level=record.level_name,
        msg=to_utf8(record.message),
    )
    return log


user_std_handler = ColorizedStderrHandler(bubble=True)
user_std_handler.formatter = user_std_handler_log_formatter


def formatter_builder(tag):
    def formatter(record, handler):

        log = "[{formatter_tag}] [{time}] {level}: {msg}".format(
            formatter_tag=tag,
            level=record.level_name,
            msg=to_utf8(record.message),
            time=record.time,
        )

        if record.formatted_exception:
            log += "\n" + record.formatted_exception
        return log
    return formatter


# loggers
# 用户代码logger日志
user_log = Logger("user_log")
# 给用户看的系统日志
user_system_log = Logger("user_system_log")

# 用于用户异常的详细日志打印
user_detail_log = Logger("user_detail_log")
# user_detail_log.handlers.append(ColorizedStderrHandler(bubble=True))

# 系统日志
system_log = Logger("system_log")
basic_system_log = Logger("basic_system_log")

# 标准输出日志
std_log = Logger("std_log")


def init_logger():
    system_log.handlers = [ColorizedStderrHandler(bubble=True)]
    basic_system_log.handlers = [ColorizedStderrHandler(bubble=True)]
    std_log.handlers = [ColorizedStderrHandler(bubble=True)]
    user_log.handlers = []
    user_system_log.handlers = []


def user_print(*args, **kwargs):
    sep = kwargs.get("sep", " ")
    end = kwargs.get("end", "")

    message = sep.join(map(str, args)) + end

    user_log.info(message)


init_logger()
