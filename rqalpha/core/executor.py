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

from datetime import datetime

from rqalpha.events import EVENT, Event
from rqalpha.utils.rq_json import convert_dict_to_json, convert_json_to_dict

PRE_BEFORE_TRADING = Event(EVENT.PRE_BEFORE_TRADING)
POST_BEFORE_TRADING = Event(EVENT.POST_BEFORE_TRADING)
PRE_BAR = Event(EVENT.PRE_BAR)
POST_BAR = Event(EVENT.POST_BAR)
PRE_TICK = Event(EVENT.PRE_TICK)
POST_TICK = Event(EVENT.POST_TICK)
PRE_AFTER_TRADING = Event(EVENT.PRE_AFTER_TRADING)
POST_AFTER_TRADING = Event(EVENT.POST_AFTER_TRADING)
PRE_SETTLEMENT = Event(EVENT.PRE_SETTLEMENT)
POST_SETTLEMENT = Event(EVENT.POST_SETTLEMENT)


class Executor(object):
    def __init__(self, env):
        self._env = env
        self._last_before_trading = None

    def get_state(self):
        return convert_dict_to_json({"last_before_trading": self._last_before_trading}).encode('utf-8')

    def set_state(self, state):
        self._last_before_trading = convert_json_to_dict(state.decode('utf-8')).get("last_before_trading")

    def run(self, bar_dict):

        def update_time(e):
            self._env.calendar_dt = e.calendar_dt
            self._env.trading_dt = e.trading_dt

        def publish_settlement(e=None):
            if e:
                previous_trading_date = self._env.data_proxy.get_previous_trading_date(e.trading_dt).date()
                if self._env.trading_dt.date() != previous_trading_date:
                    self._env.trading_dt = datetime.combine(previous_trading_date, self._env.trading_dt.time())
                    self._env.calendar_dt = datetime.combine(previous_trading_date, self._env.calendar_dt.time())

            event_bus.publish_event(PRE_SETTLEMENT)
            event_bus.publish_event(Event(EVENT.SETTLEMENT))
            event_bus.publish_event(POST_SETTLEMENT)

        def check_before_trading(e):
            if self._last_before_trading == event.trading_dt.date():
                return False

            if self._env.config.extra.is_hold:
                return False

            if self._last_before_trading:
                # don't publish settlement on first day
                publish_settlement(e)

            self._last_before_trading = e.trading_dt.date()
            update_time(e)
            event_bus.publish_event(PRE_BEFORE_TRADING)
            event_bus.publish_event(Event(EVENT.BEFORE_TRADING, calendar_dt=e.calendar_dt, trading_dt=e.trading_dt))
            event_bus.publish_event(POST_BEFORE_TRADING)

            return True

        PRE_BAR.bar_dict = bar_dict
        POST_BAR.bar_dict = bar_dict

        start_date = self._env.config.base.start_date
        end_date = self._env.config.base.end_date
        frequency = self._env.config.base.frequency
        event_bus = self._env.event_bus

        for event in self._env.event_source.events(start_date, end_date, frequency):
            if event.event_type == EVENT.TICK:
                if check_before_trading(event):
                    continue
                update_time(event)
                event_bus.publish_event(PRE_TICK)
                event_bus.publish_event(event)
                event_bus.publish_event(POST_TICK)

            elif event.event_type == EVENT.BAR:
                if check_before_trading(event):
                    continue
                update_time(event)

                bar_dict.update_dt(event.calendar_dt)
                event_bus.publish_event(PRE_BAR)
                event.bar_dict = bar_dict
                event_bus.publish_event(event)
                event_bus.publish_event(POST_BAR)

            elif event.event_type == EVENT.BEFORE_TRADING:
                check_before_trading(event)

            elif event.event_type == EVENT.AFTER_TRADING:
                update_time(event)
                event_bus.publish_event(PRE_AFTER_TRADING)
                event_bus.publish_event(event)
                event_bus.publish_event(POST_AFTER_TRADING)

            else:
                event_bus.publish_event(event)

        # publish settlement after last day
        publish_settlement()
