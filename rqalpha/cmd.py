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
import yaml


@click.group()
@click.option('-v', '--verbose', count=True)
@click.pass_context
def cmd_cli(ctx, verbose):
    ctx.obj["VERBOSE"] = verbose


def entry_point():
    import six
    from rqalpha.mod import SYSTEM_MOD_LIST
    from rqalpha.utils.config import get_mod_config_path, load_mod_config
    from rqalpha.utils.package_helper import import_mod
    mod_config_path = get_mod_config_path()
    mod_config = load_mod_config(mod_config_path, loader=yaml.Loader)

    for mod_name, config in six.iteritems(mod_config['mod']):
        lib_name = "rqalpha_mod_{}".format(mod_name)
        if not config['enabled']:
            continue
        if mod_name in SYSTEM_MOD_LIST:
            # inject system mod
            import_mod("rqalpha.mod." + lib_name)
        else:
            # inject third part mod
            import_mod(lib_name)

    cmd_cli(obj={})
