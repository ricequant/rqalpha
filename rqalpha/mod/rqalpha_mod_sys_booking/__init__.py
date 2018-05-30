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

mod_name = "sys_booking"

__config__ = {
    "priority": 1,
    "booking_id": None,
}


def load_mod():
    from .mod import BookingMod
    return BookingMod()


cli_prefix = "mod__{}__".format(mod_name)


cli.commands['run'].params.append(
    click.Option(
        ("--booking-id", cli_prefix + "booking_id"),
        help="[sys_booking] booking id "
    )
)
