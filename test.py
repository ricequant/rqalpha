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


import sys
import os
from datetime import datetime

import pandas as pd
import pytest

from rqalpha import run_func

TEST_DIR = os.path.abspath("./tests/")
TEST_OUT = os.path.abspath("./tests/outs/")

pd.set_option("display.width", 160)


def test_api(specific_test=None):
    # FIXME: Error msg is hard to understand @zjuguxi
    print(u"Testing API......")

    # from tests.api import test_strategies as test_api_strategies
    # from tests.mod import test_strategies as test_mod_strategies
    from tests.api_tests import strategies

    for strategy in strategies:
        if specific_test and strategy["name"] != specific_test:
            continue
        print("running", strategy["name"])
        run_func(**strategy)

    print(u"API test ends.")


def run_pytest_tests(args):
    retcode = pytest.main(args + [
        os.path.join(TEST_DIR, "unittest"),
        os.path.join(TEST_DIR, "integration_tests"),
    ])
    if retcode != 0:
        raise RuntimeError("Pytest failed.")


if __name__ == "__main__":

    performance_path = None
    field_names = ["date_time", "time_spend"]

    start_time = datetime.now()

    if len(sys.argv) >= 2:
        if sys.argv[1] == "api":
            try:
                test_api(sys.argv[2])
            except IndexError:
                test_api()
            end_time = datetime.now()
        elif sys.argv[1] == "pytest":
            run_pytest_tests(sys.argv[2:])
            end_time = datetime.now()
        else:
            raise ValueError("Invalid argument: {}".format(sys.argv[1]))

    else:
        # TODO: 逐步迁移至 pytest，弃用自定义框架
        run_pytest_tests([])
        test_api()
        end_time = datetime.now()


    print("Total Spend: ", end_time - start_time)
