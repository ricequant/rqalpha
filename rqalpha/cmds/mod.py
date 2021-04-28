# -*- coding: utf-8 -*-
# 版权所有 2020 深圳米筐科技有限公司（下称“米筐科技”）
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
from importlib import import_module

import six
import click

from rqalpha.utils.config import dump_config
from .entry import cli


@cli.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.help_option('-h', '--help')
@click.argument('cmd', nargs=1, type=click.Choice(['list', 'enable', 'disable']))
@click.argument('params', nargs=-1)
def mod(cmd, params):
    """
    Mod management command

    rqalpha mod list \n
    rqalpha mod enable xxx \n
    rqalpha mod disable xxx \n

    """
    def list(params):
        """
        List all mod configuration
        """
        from tabulate import tabulate
        from rqalpha.utils.config import get_mod_conf

        mod_config = get_mod_conf()
        table = []

        for mod_name, mod in mod_config['mod'].items():
            table.append([
                mod_name,
                ("enabled" if mod['enabled'] else "disabled")
            ])

        headers = [
            "name",
            "status"
        ]

        six.print_(tabulate(table, headers=headers, tablefmt="psql"))
        six.print_("You can use `rqalpha mod list/enable/disable` to manage your mods")

    def change_mod_status(mod_list, enabled):
        for mod_name in mod_list:
            if "rqalpha_mod_" in mod_name:
                mod_name = mod_name.replace("rqalpha_mod_", "")

            # check whether is installed
            module_name = "rqalpha_mod_" + mod_name
            if module_name.startswith("rqalpha_mod_sys_"):
                module_name = "rqalpha.mod." + module_name

            try:
                import_module(module_name)
            except ImportError:
                print("can not find mod [{}], ignored".format(mod_name))
                continue

            from rqalpha.utils.config import user_mod_conf_path, load_yaml
            user_conf = load_yaml(user_mod_conf_path()) if os.path.exists(user_mod_conf_path()) else {'mod': {}}
            user_conf['mod'].setdefault(mod_name, {'enabled': enabled})['enabled'] = enabled
            dump_config(user_mod_conf_path(), user_conf)

    def enable(params):
        """
        enable mod
        """
        mod_list = params
        change_mod_status(mod_list, True)

    def disable(params):
        """
        disable mod
        """
        mod_list = params
        change_mod_status(mod_list, False)

    locals()[cmd](params)


def _detect_package_name_from_dir(params):
    setup_path = os.path.join(os.path.abspath(params[-1]), 'setup.py')
    if not os.path.exists(setup_path):
        return None
    return os.path.split(os.path.dirname(setup_path))[1]
