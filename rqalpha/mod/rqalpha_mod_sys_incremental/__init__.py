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
    "csv_output_folder": None,
    "use_disk_persist": True,
    "use_csv_feeds_record": True,
}


def load_mod():
    from .mod import IncrementalMod
    return IncrementalMod()


cli_prefix = "mod__sys_incremental__"

cli.commands['run'].params.append(
    click.Option(
        ("--persist-folder", cli_prefix + "persist_folder"),
        help="[sys_incremental] persist folder"
    )
)

