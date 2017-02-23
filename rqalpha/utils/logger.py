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

import logbook
from logbook import Logger
from logbook.more import ColorizedStderrHandler


logbook.set_datetime_format("local")


# patch warn
logbook.base._level_names[logbook.base.WARNING] = 'WARN'


__all__ = [
    "user_log",
    "system_log",
]


DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.00"


def user_std_handler_log_formatter(record, handler):
    from ..execution_context import ExecutionContext

    try:
        dt = ExecutionContext.get_current_calendar_dt().strftime(DATETIME_FORMAT)
    except Exception:
        dt = "0000-00-00"

    log = "{dt} {level} {msg}".format(
        dt=dt,
        level=record.level_name,
        msg=record.message,
    )
    return log


user_std_handler = ColorizedStderrHandler(bubble=True)
user_std_handler.formatter = user_std_handler_log_formatter


def formatter_builder(tag):
    def formatter(record, handler):
        log = "[{formatter_tag}] [{time}] {level}: {msg}".format(
            formatter_tag=tag,
            level=record.level_name,
            msg=record.message,
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
user_detail_log.handlers.append(ColorizedStderrHandler(bubble=True))

# 系统日志
system_log = Logger("system_log")
system_log.handlers.append(ColorizedStderrHandler(bubble=True))

# 标准输出日志
std_log = Logger("std_log")
std_log.handlers.append(ColorizedStderrHandler(bubble=True))


def user_print(*args, **kwargs):
    sep = kwargs.get("sep", " ")
    end = kwargs.get("end", "")

    message = sep.join(map(str, args)) + end

    user_log.info(message)
