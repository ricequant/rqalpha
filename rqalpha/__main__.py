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

import errno
import os
import shutil
import six
import click
from importlib import import_module

from rqalpha.utils.click_helper import Date
from rqalpha.utils.config import parse_config, dump_config

CONTEXT_SETTINGS = {
    'default_map': {
        'run': {
        }
    }
}


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option('-v', '--verbose', count=True)
@click.help_option('-h', '--help')
@click.pass_context
def cli(ctx, verbose):
    ctx.obj["VERBOSE"] = verbose


def inject_mod_commands():
    from rqalpha.utils.config import get_mod_conf
    from rqalpha.mod import SYSTEM_MOD_LIST
    from rqalpha.utils.package_helper import import_mod
    mod_config = get_mod_conf()

    for mod_name, config in six.iteritems(mod_config['mod']):
        if 'lib' in config:
            lib_name = config["lib"]
        else:
            lib_name = "rqalpha_mod_{}".format(mod_name)
        if not config['enabled']:
            continue
        try:
            if mod_name in SYSTEM_MOD_LIST:
                # inject system mod
                import_mod("rqalpha.mod." + lib_name)
            else:
                # inject third part mod
                import_mod(lib_name)
        except Exception as e:
            pass


def entry_point():
    inject_mod_commands()

    cli(obj={})


@cli.command()
@click.option('-d', '--data-bundle-path', default=os.path.expanduser('~/.rqalpha'), type=click.Path(file_okay=False))
@click.option('--locale', 'locale', type=click.STRING, default="zh_Hans_CN")
def update_bundle(data_bundle_path, locale):
    """
    Sync Data Bundle
    """
    from rqalpha import main
    main.update_bundle(data_bundle_path, locale)


@cli.command()
@click.help_option('-h', '--help')
# -- Base Configuration
@click.option('-d', '--data-bundle-path', 'base__data_bundle_path', type=click.Path(exists=True))
@click.option('-f', '--strategy-file', 'base__strategy_file', type=click.Path(exists=True))
@click.option('-s', '--start-date', 'base__start_date', type=Date())
@click.option('-e', '--end-date', 'base__end_date', type=Date())
@click.option('-bm', '--benchmark', 'base__benchmark', type=click.STRING, default=None)
@click.option('-mm', '--margin-multiplier', 'base__margin_multiplier', type=click.FLOAT)
@click.option('-a', '--account', 'base__accounts', nargs=2, multiple=True, help="set account type with starting cash")
@click.option('--position', 'base__init_positions', type=click.STRING, help="set init position")
@click.option('-fq', '--frequency', 'base__frequency', type=click.Choice(['1d', '1m', 'tick']))
@click.option('-rt', '--run-type', 'base__run_type', type=click.Choice(['b', 'p', 'r']), default="b")
@click.option('--resume', 'base__resume_mode', is_flag=True)
@click.option('--source-code', 'base__source_code')
# -- Extra Configuration
@click.option('-l', '--log-level', 'extra__log_level', type=click.Choice(['verbose', 'debug', 'info', 'error', 'none']))
@click.option('--disable-user-system-log', 'extra__user_system_log_disabled', is_flag=True, help='disable user system log stdout')
@click.option('--disable-user-log', 'extra__user_log_disabled', is_flag=True, help='disable user log stdout')
@click.option('--logger', 'extra__logger', nargs=2, multiple=True, help='config logger, e.g. --logger system_log debug')
@click.option('--locale', 'extra__locale', type=click.Choice(['cn', 'en']), default="cn")
@click.option('--extra-vars', 'extra__context_vars', type=click.STRING, help="override context vars")
@click.option("--enable-profiler", "extra__enable_profiler", is_flag=True, help="add line profiler to profile your strategy")
@click.option("--dividend-reinvestment", "extra__dividend_reinvestment", is_flag=True, help="enable dividend reinvestment")
@click.option('--config', 'config_path', type=click.STRING, help="config file path")
# -- Mod Configuration
@click.option('-mc', '--mod-config', 'mod_configs', nargs=2, multiple=True, type=click.STRING, help="mod extra config")
def run(**kwargs):
    """
    Start to run a strategy
    """
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
            six.print_("Folder examples is exists.")


@cli.command()
@click.option('-v', '--verbose', is_flag=True)
def version(**kwargs):
    """
    Output Version Info
    """
    from rqalpha import version_info
    six.print_("Current Version: ", version_info)


@cli.command()
@click.option('-d', '--directory', default="./", type=click.Path(), required=True)
def generate_config(directory):
    """
    Generate default config file
    """
    default_config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.yml")
    target_config_path = os.path.abspath(os.path.join(directory, 'config.yml'))
    shutil.copy(default_config, target_config_path)
    six.print_("Config file has been generated in", target_config_path)


# For Mod Cli

@cli.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.help_option('-h', '--help')
@click.argument('cmd', nargs=1, type=click.Choice(['list', 'enable', 'disable', 'install', 'uninstall']))
@click.argument('params', nargs=-1)
def mod(cmd, params):
    """
    Mod management command

    rqalpha mod list \n
    rqalpha mod install xxx \n
    rqalpha mod uninstall xxx \n
    rqalpha mod enable xxx \n
    rqalpha mod disable xxx \n

    """
    def list(params):
        """
        List all mod configuration
        """
        from colorama import init, Fore
        from tabulate import tabulate
        from rqalpha.utils.config import get_mod_conf
        init()

        mod_config = get_mod_conf()
        table = []

        for mod_name, mod in six.iteritems(mod_config['mod']):
            table.append([
                Fore.RESET + mod_name,
                (Fore.GREEN + "enabled" if mod['enabled'] else Fore.RED + "disabled") + Fore.RESET
            ])

        headers = [
            Fore.CYAN + "name",
            Fore.CYAN + "status" + Fore.RESET
        ]

        six.print_(tabulate(table, headers=headers, tablefmt="psql"))
        six.print_(Fore.LIGHTYELLOW_EX + "You can use `rqalpha mod list/install/uninstall/enable/disable` to manage your mods")

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
            if mod_name.startswith("rqalpha_mod_sys_"):
                six.print_('System Mod can not be installed or uninstalled')
                return
            if "rqalpha_mod_" in mod_name:
                lib_name = mod_name
            else:
                lib_name = "rqalpha_mod_" + mod_name
            params[mod_name_index] = lib_name

        # Install Mod
        installed_result = pip_main(params)

        # Export config
        from rqalpha.utils.config import load_yaml, user_mod_conf_path
        user_conf = load_yaml(user_mod_conf_path()) if os.path.exists(user_mod_conf_path()) else {'mod': {}}

        if installed_result == 0:
            # 如果为0，则说明安装成功
            if len(mod_list) == 0:
                """
                主要是方便 `pip install -e .` 这种方式 本地调试 Mod 使用，需要满足以下条件:
                1.  `rqalpha mod install -e .` 命令是在对应 自定义 Mod 的根目录下
                2.  该 Mod 必须包含 `setup.py` 文件（否则也不能正常的 `pip install -e .` 来安装）
                3.  该 Mod 包名必须按照 RQAlpha 的规范来命名，具体规则如下
                    *   必须以 `rqalpha-mod-` 来开头，比如 `rqalpha-mod-xxx-yyy`
                    *   对应import的库名必须要 `rqalpha_mod_` 来开头，并且需要和包名后半部分一致，但是 `-` 需要替换为 `_`, 比如 `rqalpha_mod_xxx_yyy`
                """
                mod_name = _detect_package_name_from_dir()
                mod_name = mod_name.replace("-", "_").replace("rqalpha_mod_", "")
                mod_list.append(mod_name)

            for mod_name in mod_list:
                if "rqalpha_mod_" in mod_name:
                    mod_name = mod_name.replace("rqalpha_mod_", "")
                if "==" in mod_name:
                    mod_name = mod_name.split('==')[0]
                user_conf['mod'][mod_name] = {}
                user_conf['mod'][mod_name]['enabled'] = False

            dump_config(user_mod_conf_path(), user_conf)

        return installed_result

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
            if mod_name.startswith("rqalpha_mod_sys_"):
                six.print_('System Mod can not be installed or uninstalled')
                return
            if "rqalpha_mod_" in mod_name:
                lib_name = mod_name
            else:
                lib_name = "rqalpha_mod_" + mod_name
            params[mod_name_index] = lib_name

        # Uninstall Mod
        uninstalled_result = pip_main(params)
        # Remove Mod Config
        from rqalpha.utils.config import user_mod_conf_path, load_yaml
        user_conf = load_yaml(user_mod_conf_path()) if os.path.exists(user_mod_conf_path()) else {'mod': {}}

        for mod_name in mod_list:
            if "rqalpha_mod_" in mod_name:
                mod_name = mod_name.replace("rqalpha_mod_", "")

            del user_conf['mod'][mod_name]

        dump_config(user_mod_conf_path(), user_conf)
        return uninstalled_result

    def enable(params):
        """
        enable mod
        """
        mod_name = params[0]
        if "rqalpha_mod_" in mod_name:
            mod_name = mod_name.replace("rqalpha_mod_", "")

        # check whether is installed
        module_name = "rqalpha_mod_" + mod_name
        if module_name.startswith("rqalpha_mod_sys_"):
            module_name = "rqalpha.mod." + module_name
        try:
            import_module(module_name)
        except ImportError:
            installed_result = install([module_name])
            if installed_result != 0:
                return

        from rqalpha.utils.config import user_mod_conf_path, load_yaml
        user_conf = load_yaml(user_mod_conf_path()) if os.path.exists(user_mod_conf_path()) else {'mod': {}}

        try:
            user_conf['mod'][mod_name]['enabled'] = True
        except KeyError:
            user_conf['mod'][mod_name] = {'enabled': True}

        dump_config(user_mod_conf_path(), user_conf)

    def disable(params):
        """
        disable mod
        """
        mod_name = params[0]

        if "rqalpha_mod_" in mod_name:
            mod_name = mod_name.replace("rqalpha_mod_", "")

        from rqalpha.utils.config import user_mod_conf_path, load_yaml
        user_conf = load_yaml(user_mod_conf_path()) if os.path.exists(user_mod_conf_path()) else {'mod': {}}

        try:
            user_conf['mod'][mod_name]['enabled'] = False
        except KeyError:
            user_conf['mod'][mod_name] = {'enabled': False}

        dump_config(user_mod_conf_path(), user_conf)

    locals()[cmd](params)


def _detect_package_name_from_dir():
    setup_path = os.path.join(os.path.abspath('.'), 'setup.py')
    if not os.path.exists(setup_path):
        return None
    return os.path.split(os.path.dirname(setup_path))[1]


if __name__ == '__main__':
    entry_point()
