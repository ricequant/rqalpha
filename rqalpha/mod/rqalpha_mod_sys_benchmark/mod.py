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
from rqalpha.utils.logger import system_log
from rqalpha.utils.exception import patch_user_exc
from rqalpha.utils.i18n import gettext as _
from rqalpha.const import RUN_TYPE
from rqalpha.events import EVENT


class BenchmarkMod(AbstractMod):
    def start_up(self, env, mod_config):

        # forward compatible
        try:
            order_book_id = mod_config.order_book_id or env.config.base.benchmark
        except AttributeError:
            order_book_id = None

        if not order_book_id:
            system_log.info("No order_book_id set, BenchmarkMod disabled.")
            return

        env.event_bus.add_listener(EVENT.POST_SYSTEM_INIT, lambda e: self._validate_benchmark(order_book_id, env))

        if env.config.base.run_type == RUN_TYPE.BACKTEST:
            from .benchmark_provider import BackTestPriceSeriesBenchmarkProvider as BTProvider
            env.set_benchmark_provider(BTProvider(order_book_id))
        else:
            from .benchmark_provider import RealTimePriceSeriesBenchmarkProvider as RTProvider
            env.set_benchmark_provider(RTProvider(order_book_id))

    def tear_down(self, code, exception=None):
        pass

    @staticmethod
    def _validate_benchmark(bechmark_order_book_id, env):
        instrument = env.data_proxy.instruments(bechmark_order_book_id)
        if instrument is None:
            raise patch_user_exc(ValueError(_(u"invalid benchmark {}").format(bechmark_order_book_id)))

        if instrument.order_book_id == "000300.XSHG":
            # 000300.XSHG 数据进行了补齐，因此认为只要benchmark设置了000300.XSHG，就存在数据，不受限于上市日期。
            return

        config = env.config
        start_date = config.base.start_date
        end_date = config.base.end_date
        if instrument.listed_date.date() > start_date:
            raise patch_user_exc(ValueError(
                _(u"benchmark {benchmark} has not been listed on {start_date}").format(benchmark=bechmark_order_book_id,
                                                                                       start_date=start_date)))
        if instrument.de_listed_date.date() < end_date:
            raise patch_user_exc(ValueError(
                _(u"benchmark {benchmark} has been de_listed on {end_date}").format(benchmark=bechmark_order_book_id,
                                                                                    end_date=end_date)))
