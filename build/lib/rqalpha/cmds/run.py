# -*- coding: utf-8 -*-
# 版权所有 2021 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），您可以在以下位置获得 Apache 2.0 许可的副本：
#         http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。

import os

import click

from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.click_helper import Date
from rqalpha.utils.config import parse_config

from .entry import cli


@cli.command(help=_("Run a strategy"))
@click.help_option('-h', '--help')
# -- Base Configuration
@click.option('-d', '--data-bundle-path', 'base__data_bundle_path', type=click.Path(exists=True))
@click.option('-f', '--strategy-file', 'base__strategy_file', type=click.Path(exists=True))
@click.option('-s', '--start-date', 'base__start_date', type=Date())
@click.option('-e', '--end-date', 'base__end_date', type=Date())
@click.option('-mm', '--margin-multiplier', 'base__margin_multiplier', type=click.FLOAT)
@click.option('-a', '--account', 'base__accounts', nargs=2, multiple=True,
              help="set account type with starting cash, eg: -a stock 1000000 -a future 1000000")
@click.option('--position', 'base__init_positions', type=click.STRING, help="set init position")
@click.option('-fq', '--frequency', 'base__frequency', type=click.Choice(['1d', '1m', 'tick']))
@click.option('-rt', '--run-type', 'base__run_type', type=click.Choice(['b', 'p', 'r']), default="b")
@click.option('-rp', '--round-price', 'base__round_price', is_flag=True)
@click.option('--source-code', 'base__source_code')
@click.option('--rqdatac', '--rqdatac-uri', 'base__rqdatac_uri', default=None,
              help='rqdatac uri, eg user:password or or license:xxxxxxx or tcp://user:password@ip:port')
# -- Extra Configuration
@click.option('-l', '--log-level', 'extra__log_level', type=click.Choice(['verbose', 'debug', 'info', 'error', 'none']))
@click.option('--logger', 'extra__logger', nargs=2, multiple=True, help='config logger, e.g. --logger system_log debug')
@click.option('--locale', 'extra__locale', type=click.Choice(['cn', 'en']), default=None)
@click.option('--extra-vars', 'extra__context_vars', type=click.STRING, help="override context vars")
@click.option("--enable-profiler", "extra__enable_profiler", is_flag=True, default=None,
              help="add line profiler to profile your strategy")
@click.option('--config', 'config_path', type=click.STRING, help="config file path")
# -- Mod Configuration
@click.option('-mc', '--mod-config', 'mod_configs', nargs=2, multiple=True, type=click.STRING, help="mod extra config")
# for compatible
@click.option('--resume', 'base__resume_mode', is_flag=True, help="[DEPRECATED] --resume is deprecated")
def run(**kwargs):
    config_path = kwargs.get('config_path', None)
    if config_path is not None:
        config_path = os.path.abspath(config_path)
        kwargs.pop('config_path')
    if not kwargs.get('base__securities', None):
        kwargs.pop('base__securities', None)

    from rqalpha import main
    source_code = kwargs.get("base__source_code")
    cfg = parse_config(kwargs, config_path=config_path, click_type=True, source_code=source_code)
    source_code = cfg.base.source_code
    results = main.run(cfg, source_code=source_code)

    # store results into ipython when running in ipython
    from rqalpha.utils import is_run_from_ipython
    if results is not None and is_run_from_ipython():
        import IPython
        from rqalpha.utils import RqAttrDict
        ipy = IPython.get_ipython()
        report = results.get("sys_analyser", {})
        ipy.user_global_ns["results"] = results
        ipy.user_global_ns["report"] = RqAttrDict(report)

    if results is None:
        return 1


def inject_run_param(param: click.Parameter):
    cli.commands["run"].params.append(param)
