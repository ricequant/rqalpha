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


from rqalpha.interface import AbstractMod
from rqalpha.model.base_position import Positions

from .booking_account import BookingAccount
from .booking_position import BookingPosition

# import api
from . import api_booking


class BookingMod(AbstractMod):

    def start_up(self, env, mod_config):
        if env.config.base.init_positions:
            raise RuntimeError("RQAlpha recieve init positions. rqalpha_mod_sys_booking do not support init_positions")

        # TODO: load pos/trade from pms
        self.booking_account = BookingAccount(register_event=True)

    def tear_down(self, code, exception=None):
        pass
