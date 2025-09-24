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

import pandas as pd
from numpy import isclose, array
from copy import deepcopy

from rqalpha.apis import *
from rqalpha import run_func
from rqalpha.utils.dict_func import deep_update


__config__ = {
    "base": {
        "start_date": "2024-11-04",
        "end_date": "2024-11-08",
        "frequency": "1d",
        "accounts": {
            "stock": 10000000,
        },
    },
    "extra": {
        "log_level": "error",
    },
    "mod": {
        "sys_analyser": {
            "benchmark": "000300.XSHG:-1,null:2",
        }
    }
}


def _config(c):
    config = deepcopy(__config__)
    deep_update(c, config)
    return config


def test_negative_benchmark():
    def handle_bar(context, _):
        from rqalpha.environment import Environment

        env = Environment.get_instance()
        df = pd.DataFrame(env.mod_dict["sys_analyser"]._total_benchmark_portfolios)
        df['date'] = pd.to_datetime(df['date'])
        benchmark_portfolio = df.set_index('date').sort_index()        

        assert isclose(
            (benchmark_portfolio / benchmark_portfolio.shift(1, fill_value=1) - 1)["unit_net_value"].values, 
            array([-0.01407232, -0.02530206,  0.00501645, -0.03016987,  0.01004613])
        ).all()

    run_func(config=__config__, handle_bar=handle_bar)