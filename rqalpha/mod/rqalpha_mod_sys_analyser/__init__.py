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
    # 当不输出csv/pickle/plot 等内容时，可以通过 record 来决定是否执行该 Mod 的计算逻辑
    "record": True,
    # 如果指定路径，则输出计算后的 pickle 文件
    "output_file": None,
    # 如果指定路径，则输出 report csv 文件
    "report_save_path": None,
    # 画图
    'plot': False,
    # 如果指定路径，则输出 plot 对应的图片文件
    'plot_save_file': None,
}


def load_mod():
    from .mod import AnalyserMod
    return AnalyserMod()


"""
--report
--output-file

"""
cli.commands['run'].params.append(
    click.Option(
        ('--report', 'mod__sys_analyser__report_save_path'),
        type=click.Path(writable=True),
        help="[sys_analyser] save report"
    )
)
cli.commands['run'].params.append(
    click.Option(
        ('-o', '--output-file', 'mod__sys_analyser__output_file'),
        type=click.Path(writable=True),
        help="[sys_analyser] output result pickle file"
    )
)
cli.commands['run'].params.append(
    click.Option(
        ('-p', '--plot/--no-plot', 'mod__sys_analyser__plot'),
        default=None,
        help="[sys_analyser] plot result"
    )
)
cli.commands['run'].params.append(
    click.Option(
        ('--plot-save', 'mod__sys_analyser__plot_save_file'),
        default=None,
        help="[sys_analyser] save plot to file"
    )
)


@cli.command()
@click.argument('result_pickle_file_path', type=click.Path(exists=True), required=True)
@click.option('--show/--hide', 'show', default=True)
@click.option('--plot-save', 'plot_save_file', default=None, type=click.Path(), help="save plot result to file")
def plot(result_pickle_file_path, show, plot_save_file):
    """
    [sys_analyser] draw result DataFrame
    """
    import pandas as pd
    from .plot import plot_result

    result_dict = pd.read_pickle(result_pickle_file_path)
    plot_result(result_dict, show, plot_save_file)


@cli.command()
@click.argument('result_pickle_file_path', type=click.Path(exists=True), required=True)
@click.argument('target_report_csv_path', type=click.Path(exists=True, writable=True), required=True)
def report(result_pickle_file_path, target_report_csv_path):
    """
    [sys_analyser] Generate report from backtest output file
    """
    import pandas as pd
    result_dict = pd.read_pickle(result_pickle_file_path)

    from .report import generate_report
    generate_report(result_dict, target_report_csv_path)
