# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。

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
    # 基准 order_book_id
    "benchmark": {}
}


def load_mod():
    from .mod import AnalyserMod
    return AnalyserMod()


"""
--report
--output-file

"""
cli_prefix = "mod__sys_analyser__"

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
cli.commands["run"].params.append(
    click.Option(
        ("-bm", "--benchmark", cli_prefix + "benchmark"),
        type=click.STRING,
        help="[sys_analyser] order_book_id of benchmark"
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
