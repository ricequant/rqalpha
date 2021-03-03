# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。


import six
from rqalpha.core.events import EVENT
from rqalpha.utils.logger import user_system_log

from rqalpha.interface import AbstractMod
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.exception import patch_user_exc
from rqalpha.const import MATCHING_TYPE, RUN_TYPE

from rqalpha.mod.rqalpha_mod_sys_simulation.simulation_broker import SimulationBroker
from rqalpha.mod.rqalpha_mod_sys_simulation.signal_broker import SignalBroker
from rqalpha.mod.rqalpha_mod_sys_simulation.simulation_event_source import SimulationEventSource


class SimulationMod(AbstractMod):
    def __init__(self):
        self._env = None

    def start_up(self, env, mod_config):
        self._env = env
        if env.config.base.run_type == RUN_TYPE.LIVE_TRADING:
            return

        mod_config.matching_type = self.parse_matching_type(mod_config.matching_type)

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
                MATCHING_TYPE.VWAP,
                MATCHING_TYPE.CURRENT_BAR_CLOSE,
            ]:
                raise RuntimeError(_("Not supported matching type {}").format(mod_config.matching_type))

        if env.config.base.frequency == "1d" and mod_config.matching_type == MATCHING_TYPE.NEXT_BAR_OPEN:
            mod_config.matching_type = MATCHING_TYPE.CURRENT_BAR_CLOSE
            user_system_log.warn(_(u"matching_type = 'next_bar' is abandoned when frequency == '1d',"
                                   u"Current matching_type is 'current_bar'."))

        if mod_config.signal:
            env.set_broker(SignalBroker(env, mod_config))
        else:
            env.set_broker(SimulationBroker(env, mod_config))

        if mod_config.management_fee:
            env.event_bus.add_listener(EVENT.POST_SYSTEM_INIT, self.register_management_fee_calculator)

        event_source = SimulationEventSource(env)
        env.set_event_source(event_source)

    def tear_down(self, code, exception=None):
        pass

    @staticmethod
    def parse_matching_type(me_str):
        assert isinstance(me_str, six.string_types)
        me_str = me_str.lower()
        if me_str == "current_bar":
            return MATCHING_TYPE.CURRENT_BAR_CLOSE
        if me_str == "vwap":
            return MATCHING_TYPE.VWAP
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

    def register_management_fee_calculator(self, event):
        management_fee = self._env.config.mod.sys_simulation.management_fee
        accounts = self._env.portfolio.accounts
        for _account_type, v in management_fee:
            _account_type = _account_type.upper()
            if _account_type not in accounts:
                all_account_type = list(accounts.keys())
                raise ValueError(_("NO account_type = ({}) in {}").format(_account_type, all_account_type))
            accounts[_account_type].set_management_fee_rate(float(v))
