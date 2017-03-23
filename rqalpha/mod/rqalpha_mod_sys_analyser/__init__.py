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

__config__ = {
    "record": True,
    "output_file": None,
    "report_save_path": None,
}


def load_mod():
    from .mod import AnalyserMod
    return AnalyserMod()


def cli_injection(cli):
    """
    注入 --progress option
    可以通过 `rqalpha run --progress` 的方式支持回测的时候显示进度条
    """
    cli.commands['run'].params.append(
        click.Option(
            ('--report', 'mod__sys_analyser__report_save_path'),
            type=click.Path(writable=True),
            help="[sys_analyser]save report"
        )
    )
    cli.commands['run'].params.append(
        click.Option(
            ('-o', '--output-file', 'mod__sys_analyser__output_file'),
            type=click.Path(writable=True),
            help="[sys_analyser]output result pickle file"
        )
    )
