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

import six

from rqalpha.interface import AbstractMod
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.exception import patch_user_exc
from rqalpha.const import MATCHING_TYPE, RUN_TYPE

from rqalpha.mod.rqalpha_mod_sys_simulation.simulation_broker import SimulationBroker
from rqalpha.mod.rqalpha_mod_sys_simulation.signal_broker import SignalBroker
from rqalpha.mod.rqalpha_mod_sys_simulation.simulation_event_source import SimulationEventSource


class SimulationMod(AbstractMod):
    def __init__(self):
        pass

    def start_up(self, env, mod_config):

        if env.config.base.run_type == RUN_TYPE.LIVE_TRADING:
            return

        mod_config.matching_type = self.parse_matching_type(mod_config.matching_type)
        if mod_config.commission_multiplier < 0:
            raise patch_user_exc(ValueError(_(u"invalid commission multiplier value: value range is [0, +∞)")))
        if env.config.base.margin_multiplier <= 0:
            raise patch_user_exc(ValueError(_(u"invalid margin multiplier value: value range is (0, +∞]")))

        if env.config.base.frequency == "tick":
            mod_config.volume_limit = False
            if mod_config.matching_type not in [
                MATCHING_TYPE.NEXT_TICK_LAST,
                MATCHING_TYPE.NEXT_TICK_BEST_OWN,
                MATCHING_TYPE.NEXT_TICK_BEST_COUNTERPARTY,
            ]:
                raise RuntimeError(_("Not supported matching type {}").format(mod_config.matching_type))
        else:
            if mod_config.matching_type not in [
                MATCHING_TYPE.NEXT_BAR_OPEN,
                MATCHING_TYPE.CURRENT_BAR_CLOSE,
            ]:
                raise RuntimeError(_("Not supported matching type {}").format(mod_config.matching_type))

        if mod_config.signal:
            env.set_broker(SignalBroker(env, mod_config))
        else:
            env.set_broker(SimulationBroker(env, mod_config))

        event_source = SimulationEventSource(env)
        env.set_event_source(event_source)

    def tear_down(self, code, exception=None):
        pass

    @staticmethod
    def parse_matching_type(me_str):
        assert isinstance(me_str, six.string_types)
        if me_str == "current_bar":
            return MATCHING_TYPE.CURRENT_BAR_CLOSE
        elif me_str == "next_bar":
            return MATCHING_TYPE.NEXT_BAR_OPEN
        elif me_str == "last":
            return MATCHING_TYPE.NEXT_TICK_LAST
        elif me_str == "best_own":
            return MATCHING_TYPE.NEXT_TICK_BEST_OWN
        elif me_str == "best_counterparty":
            return MATCHING_TYPE.NEXT_TICK_BEST_COUNTERPARTY
        else:
            raise NotImplementedError
