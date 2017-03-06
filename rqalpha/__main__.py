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
import errno
import os
import shutil
import ruamel.yaml as yaml
from importlib import import_module

from .utils.click_helper import Date
from .utils.config import parse_config, get_default_config_path, load_config, dump_config


@click.group()
@click.option('-v', '--verbose', count=True)
@click.pass_context
def cli(ctx, verbose):
    ctx.obj["VERBOSE"] = verbose


def entry_point():
    cli(obj={})


@cli.command()
@click.option('-d', '--data-bundle-path', default=os.path.expanduser("~/.rqalpha"), type=click.Path(file_okay=False))
@click.option('--locale', 'locale', type=click.STRING, default="zh_Hans_CN")
def update_bundle(data_bundle_path, locale):
    """
    Sync Data Bundle
    """
    from . import main
    main.update_bundle(data_bundle_path, locale)


@cli.command()
@click.help_option('-h', '--help')
# -- Base Configuration
@click.option('-d', '--data-bundle-path', 'base__data_bundle_path', type=click.Path(exists=True))
@click.option('-f', '--strategy-file', 'base__strategy_file', type=click.Path(exists=True))
@click.option('-s', '--start-date', 'base__start_date', type=Date())
@click.option('-e', '--end-date', 'base__end_date', type=Date())
@click.option('-r', '--rid', 'base__run_id', type=click.STRING)
@click.option('-sc', '--stock-starting-cash', 'base__stock_starting_cash', type=click.FLOAT)
@click.option('-fc', '--future-starting-cash', 'base__future_starting_cash', type=click.FLOAT)
@click.option('-bm', '--benchmark', 'base__benchmark', type=click.STRING, default=None)
@click.option('-sp', '--slippage', 'base__slippage', type=click.FLOAT)
@click.option('-cm', '--commission-multiplier', 'base__commission_multiplier', type=click.FLOAT)
@click.option('-mm', '--margin-multiplier', 'base__margin_multiplier', type=click.FLOAT)
@click.option('-st', '--strategy-type', 'base__strategy_type', type=click.Choice(['stock', 'future', 'stock_future']))
@click.option('-fq', '--frequency', 'base__frequency', type=click.Choice(['1d', '1m']))
@click.option('-me', '--match-engine', 'base__matching_type', type=click.Choice(['current_bar', 'next_bar']))
@click.option('-rt', '--run-type', 'base__run_type', type=click.Choice(['b', 'p']), default="b")
@click.option('--resume', 'base__resume_mode', is_flag=True)
@click.option('--handle-split/--not-handle-split', 'base__handle_split', default=None, help="handle split")
# -- Extra Configuration
@click.option('-l', '--log-level', 'extra__log_level', type=click.Choice(['verbose', 'debug', 'info', 'error', 'none']))
@click.option('--locale', 'extra__locale', type=click.Choice(['cn', 'en']), default="cn")
@click.option('--disable-user-system-log', 'extra__user_system_log_disabled', is_flag=True, help='disable user system log')
@click.option('--extra-vars', 'extra__context_vars', type=click.STRING, help="override context vars")
@click.option("--enable-profiler", "extra__enable_profiler", is_flag=True,
              help="add line profiler to profile your strategy")
@click.option('--config', 'config_path', type=click.STRING, help="config file path")
# -- Mod Configuration
@click.option('-mc', '--mod-config', 'mod_configs', nargs=2, multiple=True, type=click.STRING, help="mod extra config")
@click.option('-p', '--plot/--no-plot', 'mod__analyser__plot', default=None, help="plot result")
@click.option('--plot-save', 'mod__analyser__plot_save_file', default=None, help="save plot to file")
@click.option('--report', 'mod__analyser__report_save_path', type=click.Path(writable=True), help="save report")
@click.option('-o', '--output-file', 'mod__analyser__output_file', type=click.Path(writable=True),
              help="output result pickle file")
@click.option('--progress/--no-progress', 'mod__progress__enabled', default=None, help="show progress bar")
@click.option('--short-stock', 'mod__risk_manager__short_stock', is_flag=True, help="enable stock shorting")
# -- DEPRECATED ARGS && WILL BE REMOVED AFTER VERSION 1.0.0
@click.option('-i', '--init-cash', 'base__stock_starting_cash', type=click.FLOAT)
@click.option('-k', '--kind', 'base__strategy_type', type=click.Choice(['stock', 'future', 'stock_future']))
def run(**kwargs):
    """
    Start to run a strategy
    """
    config_path = kwargs.get('config_path', None)
    if config_path is not None:
        config_path = os.path.abspath(config_path)

    from . import main
    main.run(parse_config(kwargs, config_path))


@cli.command()
@click.option('-d', '--directory', default="./", type=click.Path(), required=True)
def examples(directory):
    """
    Generate example strategies to target folder
    """
    source_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "examples")

    try:
        shutil.copytree(source_dir, os.path.join(directory, "examples"))
    except OSError as e:
        if e.errno == errno.EEXIST:
            print("Folder examples is exists.")


@cli.command()
@click.argument('result_dict_file', type=click.Path(exists=True), required=True)
@click.option('--show/--hide', 'is_show', default=True)
@click.option('--plot-save', 'plot_save_file', default=None, type=click.Path(), help="save plot result to file")
def plot(result_dict_file, is_show, plot_save_file):
    """
    Draw result DataFrame
    """
    import pandas as pd
    from rqalpha.plot import plot_result

    result_dict = pd.read_pickle(result_dict_file)
    if is_show:
        plot_result(result_dict)
    if plot_save_file:
        plot_result(result_dict, show_windows=False, savefile=plot_save_file)


@cli.command()
@click.argument('result_pickle_file_path', type=click.Path(exists=True), required=True)
@click.argument('target_report_csv_path', type=click.Path(exists=True, writable=True), required=True)
def report(result_pickle_file_path, target_report_csv_path):
    """
    Generate report from backtest output file
    """
    import pandas as pd
    result_dict = pd.read_pickle(result_pickle_file_path)

    from rqalpha.utils.report import generate_report
    generate_report(result_dict, target_report_csv_path)


@cli.command()
@click.option('-v', '--verbose', is_flag=True)
def version(**kwargs):
    """
    Output Version Info
    """
    from rqalpha import version_info
    print("Current Version: ", version_info)


@cli.command()
@click.option('-d', '--directory', default="./", type=click.Path(), required=True)
def generate_config(directory):
    """
    Generate default config file
    """
    default_config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config_template.yml")
    target_config_path = os.path.abspath(os.path.join(directory, 'config.yml'))
    shutil.copy(default_config, target_config_path)
    print("Config file has been generated in", target_config_path)


# For Mod Cli

system_mod = [
    'simulation',
    'funcat_api',
    'progress',
    'simple_stock_realtime_trade',
    'progressive_output_csv',
    'risk_manager',
    'analyser',
]


@cli.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('params', nargs=-1)
def install(params):
    """
    Install third-party Mod
    """
    from pip import main as pip_main
    from pip.commands.install import InstallCommand

    params = [param for param in params]

    options, mod_list = InstallCommand().parse_args(params)

    params = ["install"] + params

    for mod_name in mod_list:
        mod_name_index = params.index(mod_name)
        if mod_name in system_mod:
            print('System Mod can not be installed or uninstalled')
            return
        if "rqalpha_mod_" in mod_name:
            lib_name = mod_name
            mod_name = lib_name.replace("rqalpha_mod_", "")
        else:
            lib_name = "rqalpha_mod_" + mod_name
        params[mod_name_index] = lib_name

    # Install Mod
    pip_main(params)

    # Export config
    config_path = get_default_config_path()
    config = load_config(config_path, loader=yaml.RoundTripLoader)

    for mod_name in mod_list:
        if "rqalpha_mod_" in mod_name:
            lib_name = mod_name
            mod_name = lib_name.replace("rqalpha_mod_", "")
        else:
            lib_name = "rqalpha_mod_" + mod_name

        mod = import_module(lib_name)

        mod_config = yaml.load(mod.__mod_config__, yaml.RoundTripLoader)

        config['mod'][mod_name] = mod_config
        config['mod'][mod_name]['lib'] = lib_name
        config['mod'][mod_name]['enabled'] = False
        config['mod'][mod_name]['priority'] = 1000

    dump_config(config_path, config)


@cli.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument('params', nargs=-1)
def uninstall(params):
    """
    Uninstall third-party Mod
    """
    from pip import main as pip_main
    from pip.commands.uninstall import UninstallCommand

    params = [param for param in params]

    options, mod_list = UninstallCommand().parse_args(params)

    params = ["uninstall"] + params

    for mod_name in mod_list:
        mod_name_index = params.index(mod_name)
        if mod_name in system_mod:
            print('System Mod can not be installed or uninstalled')
            return
        if "rqalpha_mod_" in mod_name:
            lib_name = mod_name
            mod_name = lib_name.replace("rqalpha_mod_", "")
        else:
            lib_name = "rqalpha_mod_" + mod_name
        params[mod_name_index] = lib_name

    # Uninstall Mod
    pip_main(params)

    # Remove Mod Config
    config_path = get_default_config_path()
    config = load_config(config_path, loader=yaml.RoundTripLoader)

    for mod_name in mod_list:
        if "rqalpha_mod_" in mod_name:
            mod_name = mod_name.replace("rqalpha_mod_", "")

        del config['mod'][mod_name]

    dump_config(config_path, config)


@cli.command()
def list():
    """
    List all mod configuration
    """
    config_path = get_default_config_path()
    config = load_config(config_path, loader=yaml.RoundTripLoader)

    print(yaml.dump(config['mod'], Dumper=yaml.RoundTripDumper))


@cli.command()
@click.argument('mod_name')
def enable(mod_name):
    """
    enable mod
    """
    if mod_name not in system_mod and "rqalpha_mod_" in mod_name:
        mod_name = mod_name.replace("rqalpha_mod_", "")

    config_path = get_default_config_path()
    config = load_config(config_path, loader=yaml.RoundTripLoader)

    try:
        config['mod'][mod_name]['enabled'] = True
        dump_config(config_path, config)
    except Exception as e:
        pass


@cli.command()
@click.argument('mod_name')
def disable(mod_name):
    """
    disable mod
    """
    if mod_name not in system_mod and "rqalpha_mod_" in mod_name:
        mod_name = mod_name.replace("rqalpha_mod_", "")

    config_path = get_default_config_path()
    config = load_config(config_path, loader=yaml.RoundTripLoader)

    try:
        config['mod'][mod_name]['enabled'] = False
        dump_config(config_path, config)
    except Exception as e:
        pass


if __name__ == '__main__':
    entry_point()
