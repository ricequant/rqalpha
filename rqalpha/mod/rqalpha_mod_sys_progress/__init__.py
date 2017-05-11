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

import click
from rqalpha import cli


__config__ = {
    "show": False
}


def load_mod():
    from .mod import ProgressMod
    return ProgressMod()


"""
注入 --progress option
可以通过 `rqalpha run --progress` 的方式支持回测的时候显示进度条
"""
cli_prefix = "mod__sys_progress__"
cli.commands['run'].params.append(
    click.Option(
        ("--progress", cli_prefix + "show"),
        is_flag=True,
        help="[sys_progress]show progress bar"
    )
)

