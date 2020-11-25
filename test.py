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


import pickle
import sys
import os
import csv
from datetime import datetime
from typing import Optional, Tuple

from six import iteritems
import pandas as pd
import numpy as np
import coverage

from rqalpha import run, run_func
from rqalpha.utils.config import set_locale
from rqalpha.utils.logger import system_log

TEST_DIR = os.path.abspath("./tests/")
TEST_OUT = os.path.abspath("./tests/outs/")

pd.set_option("display.width", 160)

set_locale("zh_Hans_CN")


def run_tests(file_path=None):
    tests = {f.replace(".py", ""): f for f in (
        (file_path, ) if file_path else (f for f in os.listdir(TEST_DIR) if f.find("test") == 0)
    )}
    error_map = {}
    for name, filename in tests.items():
        try:
            result_data = run_test(filename)
            if result_data is not None:
                error_map[name] = result_data
        except Exception as e:
            error_map[name] = e
    for filename, result_data in iteritems(error_map):
        print(u"*" * 20, u"[{}]did not pass!".format(filename), u"*" * 20)
        if isinstance(result_data, Exception):
            system_log.error(result_data)
        else:
            _, __, result = result_data
            print(result.all())
    print(u"=" * 40)
    print("[{}|{}] strategies has been passed!".format(len(tests) - len(error_map), len(tests)))
    return len(error_map)


def run_test(filename):
    # type: (str) -> Optional[Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]
    config = {"base": {"strategy_file": os.path.join(TEST_DIR, filename)}}
    print(u"Start test: " + str(config["base"]["strategy_file"]))
    result_dict = run(config)["sys_analyser"]

    # del df['positions']

    old_pickle_file = os.path.join(TEST_OUT, filename.replace(".py", ".pkl"))

    if not os.path.exists(old_pickle_file):
        if not os.path.exists(TEST_OUT):
            os.makedirs(TEST_OUT)
        pickle.dump(result_dict, open(old_pickle_file, "wb"), protocol=2)
        return
    else:
        old_result_dict = pd.read_pickle(old_pickle_file)

        # 比较 portfolios
        old_df = old_result_dict["portfolio"].replace([np.nan, np.inf, -np.inf], 0).round(0)
        df = result_dict["portfolio"].replace([np.nan, np.inf, -np.inf], 0).round(0)
        try:
            del old_df["dividend_receivable"]
            del df["dividend_receivable"]
        except:
            pass

        result = df.eq(old_df)
        if not result.all().all():
            return df, old_df, result

        # 比较 summary
        old_df = (
            pd.DataFrame(
                data=[{"val": val} for val in old_result_dict["summary"].values()],
                index=old_result_dict["summary"].keys(),
            )
            .sort_index()
            .T.fillna(0)
        )
        df = (
            pd.DataFrame(
                data=[{"val": val} for val in result_dict["summary"].values()],
                index=result_dict["summary"].keys(),
            )
            .sort_index()
            .T.fillna(0)
        )
        try:
            del old_df["daily_pnl"]
            del old_df["daily_returns"]
            del old_df["dividend_receivable"]
            del old_df["strategy_file"]
            del df["strategy_file"]
        except:
            pass
        try:
            del old_df["strategy_file"]
            del df["strategy_file"]
        except:
            pass
        result = df.eq(old_df)
        if not result.all().all():
            return old_result_dict, result_dict, result


def is_enable_coverage():
    return os.environ.get("COVERAGE") == "enabled"


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


def test_strategy():
    run_tests()


def write_csv(path, fields):
    old_test_times = []
    if not os.path.exists(path):
        with open(path, "w") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fields)
            writer.writeheader()
    with open(path) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            old_test_times.append(row)

    if performance_path is not None:
        if (
            0 < len(old_test_times) < 5
            and time_spend
            > float(sum(float(i["time_spend"]) for i in old_test_times))
            / len(old_test_times)
            * 1.1
        ):
            print(
                "Average time of last 5 runs:",
                float(sum(float(i["time_spend"]) for i in old_test_times))
                / len(old_test_times),
            )
            print("Now time spend:", time_spend)
            raise RuntimeError("Performance regresses!")
        elif (
            len(old_test_times) >= 5
            and time_spend
            > float(sum(float(i["time_spend"]) for i in old_test_times[-5:])) / 5 * 1.1
        ):
            print(
                "Average time of last 5 runs:",
                float(sum(float(i["time_spend"]) for i in old_test_times[-5:])) / 5,
            )
            print("Now time spend:", time_spend)
            raise RuntimeError("Performance regresses!")
        else:
            with open(path, "a") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=fields)
                writer.writerow({"date_time": end_time, "time_spend": time_spend})


def run_unit_tests():
    from unittest import TextTestRunner

    from tests.unittest import load_tests

    result = TextTestRunner(verbosity=2).run(load_tests())
    if not result.wasSuccessful():
        raise RuntimeError("Unittest failed.")


if __name__ == "__main__":
    if is_enable_coverage():
        print("enable coverage")
        cov = coverage.Coverage()
        cov.start()

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

        elif sys.argv[1] == "strategy":
            test_strategy()
            end_time = datetime.now()

        elif sys.argv[1] == "performance":
            # test_api()
            test_strategy()
            end_time = datetime.now()
            performance_path = sys.argv[2]
            time_spend = (end_time - start_time).total_seconds()
            write_csv(performance_path, field_names)

        elif sys.argv[1] == "unittest":
            run_unit_tests()
            end_time = datetime.now()

        else:
            target_file = sys.argv[1]
            run_tests(target_file)
            end_time = datetime.now()

    else:
        run_unit_tests()
        test_api()
        error_count = run_tests()
        end_time = datetime.now()
        if error_count == 0:
            time_csv_file_path = os.path.join(TEST_OUT, "time.csv")
            time_spend = (end_time - start_time).total_seconds()
            write_csv(time_csv_file_path, field_names)

        else:
            print("Failed!")
            sys.exit(-1)
    if is_enable_coverage():
        cov.stop()
        cov.save()
        cov.html_report()

    print("Total Spend: ", end_time - start_time)
