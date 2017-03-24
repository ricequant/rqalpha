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
from rqalpha.__main__ import cli


__config__ = {
    "plot": None,
    "plot_save_file": None,
    "priority": -9999,
}


def load_mod():
    from .mod import PlotMod
    return PlotMod()


"""
注入 --plot option
可以通过 `rqalpha run --plot` 的方式支持回测的时候显示进度条
"""
cli_prefix = "mod__sys_plot__"

cli.commands['run'].params.append(
    click.Option(
        ('-p', '--plot/--no-plot', cli_prefix + 'plot'),
        default=None,
        help="[sys_plot]plot result"
    )
)
cli.commands['run'].params.append(
    click.Option(
        ('--plot-save', cli_prefix + 'plot_save_file'),
        default=None,
        help="[sys_plot]save plot to file"
    )
)


@cli.command()
@click.argument('result_dict_file', type=click.Path(exists=True), required=True)
@click.option('--show/--hide', 'is_show', default=True)
@click.option('--plot-save', 'plot_save_file', default=None, type=click.Path(), help="save plot result to file")
def plot(result_dict_file, is_show, plot_save_file):
    """
    [sys_plot]draw result DataFrame
    """
    import pandas as pd
    from .plot import plot_result

    result_dict = pd.read_pickle(result_dict_file)
    if is_show:
        plot_result(result_dict)
    if plot_save_file:
        plot_result(result_dict, show_windows=False, savefile=plot_save_file)
