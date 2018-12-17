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
    "order_book_id": None
}


def load_mod():
    from .mod import BenchmarkMod
    return BenchmarkMod()


cli_prefix = "mod__sys_benchmark__"

cli.commands["run"].params.append(
    click.Option(
        ("-bm", "--benchmark", cli_prefix + "order_book_id"),
        type=click.STRING,
        help="[sys_benchmark] order_book_id of benchmark"
    )
)
