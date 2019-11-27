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


from rqalpha.const import RUN_TYPE
from rqalpha.events import EVENT
from rqalpha.interface import AbstractMod
from rqalpha.utils.exception import patch_user_exc
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.logger import system_log


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
            if config.base.run_type == RUN_TYPE.BACKTEST:
                msg = _(u"benchmark {benchmark} has been de_listed on {end_date}").format(
                    benchmark=bechmark_order_book_id,
                    end_date=end_date)
            else:
                msg = _(u"the target {benchmark} will be delisted in the short term. "
                        u"please choose a sustainable target.").format(
                    benchmark=bechmark_order_book_id)
            raise patch_user_exc(ValueError(msg))
