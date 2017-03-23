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
from rqalpha import cmd_cli

from .mod import PlotMod


cli_prefix = "mod__sys_plot__"


def load_mod():
    return PlotMod()


def cli_injection(cli):
    """
    注入 --plot option
    可以通过 `rqalpha run --plot` 的方式支持回测的时候显示进度条
    """
    cli.commands['run'].params.append(
        click.Option(('-p', '--plot/--no-plot', cli_prefix + 'plot'),
                     default=None,
                     help="[Plot]plot result")
    )
    cli.commands['run'].params.append(
        click.Option(('--plot-save', cli_prefix + 'plot_save_file'),
                     default=None,
                     help="[Plot]save plot to file"
                     )
    )


@cmd_cli.command()
def plot():
    print("This is plot command injection test")


__config__ = {
    "plot": None,
    "plot_save_file": None,
    "priority": -9999,
}
