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


@click.group()
@click.option('-v', '--verbose', count=True)
@click.pass_context
def cmd_cli(ctx, verbose):
    ctx.obj["VERBOSE"] = verbose


def entry_point():
    from rqalpha.utils.config import get_default_config_path
    get_default_config_path()

    # 获取 Mod 中的命令
    # noinspection PyUnresolvedReferences
    from .mod import SYSTEM_MOD_LIST
    mod_lib_prefix = "rqalpha.mod.rqalpha_mod_"
    from .utils.package_helper import import_mod
    for sys_mod in SYSTEM_MOD_LIST:
        import_mod(mod_lib_prefix + sys_mod)

    # 获取第三方包中的命令
    from pkgutil import iter_modules
    for package in iter_modules():
        if "rqalpha_mod_" in package[1]:
            import_mod(package[1])

    cmd_cli(obj={})
