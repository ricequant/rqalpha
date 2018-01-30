#!/usr/bin/env python
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


import pickle
import sys
from datetime import datetime
import os
import csv

from six import iteritems
import pandas as pd
import numpy as np
import coverage

from rqalpha import run
from rqalpha.utils.logger import system_log

TEST_DIR = os.path.abspath("./tests/")
TEST_OUT = os.path.abspath("./tests/outs/")

pd.set_option("display.width", 160)


def run_tests(file_path=None):
    if file_path is not None:
        files = [file_path]
    else:
        files = [f for f in os.listdir(TEST_DIR) if f.find("test") == 0]
    error_map = {}
    for filename in files:
        try:
            r, result_data = run_test(filename)
            if r is not None:
                error_map[filename.replace(".py", "")] = result_data
        except Exception as e:
            system_log.exception()
            error_map[filename.replace(".py", "")] = e
    for filename, result_data in iteritems(error_map):
        print(u"*" * 20, u"[{}]did not pass!".format(filename), u"*" * 20)
        if isinstance(result_data, Exception):
            system_log.error(result_data)
        else:
            df, old_df, result = result_data
            # print("+" * 10, "old test Dataframe: ", "+" * 10)
            # print(old_df.drop(result.columns[result.all()], axis=1))
            # print("+" * 10, "new test Dataframe: ", "+" * 10)
            # print(df.drop(result.columns[result.all()], axis=1))
            print(result.all())
    print(u"=" * 40)
    print(u"[{}|{}] strategies has been passed!".format(len(files) - len(error_map), len(files)))
    return len(error_map)


def run_test(filename):
    config = {
        "base": {
            "strategy_file": os.path.join(TEST_DIR, filename)
        }
    }
    print(u"Start test: " + str(config["base"]["strategy_file"]))
    result_dict = run(config)['sys_analyser']
    df = result_dict["portfolio"]
    # del df['positions']

    old_pickle_file = os.path.join(TEST_OUT, filename.replace(".py", ".pkl"))

    if not os.path.exists(old_pickle_file):
        if not os.path.exists(TEST_OUT):
            os.makedirs(TEST_OUT)
        pickle.dump(result_dict, open(old_pickle_file, "wb"), protocol=2)
        return None, None
    else:
        old_result_dict = pd.read_pickle(old_pickle_file)

        # 比较 portfolios
        old_df = old_result_dict["portfolio"]
        old_df = old_df.fillna(0)
        old_df = old_df.replace([np.inf, -np.inf], 0)
        df = df.fillna(0)
        df = df.replace([np.inf, -np.inf], 0)
        # del old_df["trades"]
        # del df["trades"]
        try:
            del old_df["dividend_receivable"]
            del df["dividend_receivable"]
        except:
            pass

        df = df.round(0)
        old_df = old_df.round(0)

        result = df.eq(old_df)
        if not result.all().all():
            return result.all(), (df, old_df, result)

        # 比较 summary
        old_df = pd.DataFrame(data=[{"val": val} for val in old_result_dict["summary"].values()],
                              index=old_result_dict["summary"].keys()).sort_index().T.fillna(0)
        df = pd.DataFrame(data=[{"val": val} for val in result_dict["summary"].values()],
                          index=result_dict["summary"].keys()).sort_index().T.fillna(0)
        try:
            del old_df['daily_pnl']
            del old_df['daily_returns']
            del old_df['dividend_receivable']
            del old_df['strategy_file']
            del df['strategy_file']
        except:
            pass
        try:
            del old_df['strategy_file']
            del df['strategy_file']
        except:
            pass
        result = df.eq(old_df)
        if not result.all().all():
            return result.all(), (old_result_dict, result_dict, result)

        return None, None


def is_enable_coverage():
    return os.environ.get('COVERAGE') == "enabled"


def test_api():
    # FIXME: Error msg is hard to understand @zjuguxi
    # return

    print(u"Testing API......")
    from rqalpha import run

    from tests.api.test_api_base import (
        test_get_order_code_new,
        test_get_open_order_code_new,
        test_cancel_order_code_new,
        test_update_universe_code_new,
        test_subscribe_code_new,
        test_unsubscribe_code_new,
        test_get_yield_curve_code_new,
        test_history_bars_code_new,
        test_all_instruments_code_new,
        test_instruments_code_new,
        test_sector_code_new,
        test_industry_code_new,
        test_get_trading_dates_code_new,
        test_get_previous_trading_date_code_new,
        test_get_next_trading_date_code_new,
        test_get_dividend_code_new,
    )

    from tests.api.test_api_stock import (
        test_order_shares_code_new, test_order_lots_code_new,
        test_order_value_code_new,
        test_order_percent_code_new, test_order_target_value_code_new,
    )

    from tests.api.test_api_future import (
        test_buy_open_code_new,
        test_sell_open_code_new,
        test_buy_close_code_new,
        test_sell_close_code_new,
    )

    base_api_config = {
        "base": {
            "start_date": "2016-12-01",
            "end_date": "2016-12-31",
            "frequency": "1d",
            "matching_type": "next_bar",
            "strategy_file": 'rqalpha/__init__.py',
            "accounts": {
                "stock": 1000000
            }
        },
        "extra": {
            "log_level": "error",
        },
        "mod": {
            "sys_progress": {
                "enabled": True,
                "show": True,
            },
        },
    }

    stock_api_config = {
        "base": {
            "start_date": "2016-03-07",
            "end_date": "2016-03-08",
            "frequency": "1d",
            "matching_type": "next_bar",
            "strategy_file": 'rqalpha/__init__.py',
            "accounts": {
                "stock": 100000000
            }
        },
        "extra": {
            "log_level": "error",
        },
        "mod": {
            "sys_progress": {
                "enabled": True,
                "show": True,
            },
        },
    }

    future_api_config = {
        "base": {
            "start_date": "2016-03-07",
            "end_date": "2016-03-08",
            "frequency": "1d",
            "matching_type": "next_bar",
            "strategy_file": 'rqalpha/__init__.py',
            "accounts": {
                "future": 10000000000
            }
        },
        "extra": {
            "log_level": "error",
        },
        "mod": {
            "sys_progress": {
                "enabled": True,
                "show": True,
            },
        },
    }

    # =================== Test Base API ===================
    tasks = []

    tasks.append((base_api_config, test_get_order_code_new, "test_get_order_code_new"))
    tasks.append((base_api_config, test_get_open_order_code_new, "test_get_open_order_code_new"))
    tasks.append((base_api_config, test_cancel_order_code_new, "test_cancel_order_code_new"))
    tasks.append((base_api_config, test_update_universe_code_new, "test_update_universe_code_new"))
    tasks.append((base_api_config, test_subscribe_code_new, "test_subscribe_code_new"))
    tasks.append((base_api_config, test_unsubscribe_code_new, "test_unsubscribe_code_new"))
    tasks.append((base_api_config, test_get_yield_curve_code_new, "test_get_yield_curve_code_new"))
    tasks.append((base_api_config, test_history_bars_code_new, "test_history_bars_code_new"))
    tasks.append((base_api_config, test_all_instruments_code_new, "test_all_instruments_code_new"))
    tasks.append((base_api_config, test_instruments_code_new, "test_instruments_code_new"))
    tasks.append((base_api_config, test_sector_code_new, "test_sector_code_new"))
    tasks.append((base_api_config, test_industry_code_new, "test_industry_code_new"))
    tasks.append((base_api_config, test_get_trading_dates_code_new, "test_get_trading_dates_code_new"))
    tasks.append((base_api_config, test_get_previous_trading_date_code_new, "test_get_previous_trading_date_code_new"))
    tasks.append((base_api_config, test_get_next_trading_date_code_new, "test_get_next_trading_date_code_new"))
    tasks.append((base_api_config, test_get_dividend_code_new, "test_get_dividend_code_new"))

    # =================== Test Stock API ===================
    tasks.append((stock_api_config, test_order_shares_code_new, "test_order_shares_code_new"))
    tasks.append((stock_api_config, test_order_lots_code_new, "test_order_lots_code_new"))
    tasks.append((stock_api_config, test_order_value_code_new, "test_order_value_code_new"))
    tasks.append((stock_api_config, test_order_percent_code_new, "test_order_percent_code_new"))
    tasks.append((stock_api_config, test_order_target_value_code_new, "test_order_target_value_code_new"))

    # =================== Test Future API ===================
    tasks.append((future_api_config, test_buy_open_code_new, "test_buy_open_code_new"))
    tasks.append((future_api_config, test_sell_open_code_new, "test_sell_open_code_new"))
    tasks.append((future_api_config, test_buy_close_code_new, "test_buy_close_code_new"))
    tasks.append((future_api_config, test_sell_close_code_new, "test_sell_close_code_new"))

    for cfg, source_code, name in tasks:
        print("running", name)
        run(cfg, source_code)

    print(u"API test ends.")


def test_strategy():
    run_tests()


def write_csv(path, fields):
    old_test_times = []
    if not os.path.exists(path):
        with open(path, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fields)
            writer.writeheader()
    with open(path) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            old_test_times.append(row)

    if performance_path is None:
        if len(old_test_times) != 0 and time_spend > float(old_test_times[-1]["time_spend"]) * 1.1:
            system_log.error("代码咋写的，太慢了！")
            system_log.error("上次测试用例执行的总时长为：" + old_test_times[-1]["time_spend"])
            system_log.error("本次测试用例执行的总时长增长为: " + str(time_spend))
        else:
            with open(path, 'a') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=fields)
                writer.writerow({'date_time': end_time, 'time_spend': time_spend})
    else:
        if 0 < len(old_test_times) < 5 and time_spend > float(sum(float(i['time_spend']) for i in old_test_times)) / len(old_test_times) * 1.1:
            print('Average time of last 5 runs:', float(sum(float(i['time_spend']) for i in old_test_times))/len(old_test_times))
            print('Now time spend:', time_spend)
            raise RuntimeError('Performance regresses!')
        elif len(old_test_times) >= 5 and time_spend > float(sum(float(i['time_spend']) for i in old_test_times[-5:])) / 5 * 1.1:
            print('Average time of last 5 runs:',
                  float(sum(float(i['time_spend']) for i in old_test_times[-5:])) / 5)
            print('Now time spend:', time_spend)
            raise RuntimeError('Performance regresses!')
        else:
            with open(path, 'a') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=fields)
                writer.writerow({'date_time': end_time, 'time_spend': time_spend})


if __name__ == '__main__':
    if is_enable_coverage():
        print("enable coverage")
        cov = coverage.Coverage()
        cov.start()

    performance_path = None
    field_names = ['date_time', 'time_spend']

    start_time = datetime.now()

    if len(sys.argv) >= 2:
        if sys.argv[1] == 'api':
            test_api()
            end_time = datetime.now()

        elif sys.argv[1] == 'strategy':
            test_strategy()
            end_time = datetime.now()

        elif sys.argv[1] == 'performance':
            test_api()
            test_strategy()
            end_time = datetime.now()
            performance_path = sys.argv[2]
            time_spend = (end_time - start_time).total_seconds()
            write_csv(performance_path, field_names)

        else:
            target_file = sys.argv[1]
            run_tests(target_file)
            end_time = datetime.now()

    else:
        test_api()
        error_count = run_tests()
        end_time = datetime.now()
        if error_count == 0:
            time_csv_file_path = os.path.join(TEST_OUT, "time.csv")
            time_spend = (end_time - start_time).total_seconds()
            write_csv(time_csv_file_path, field_names)

        else:
            print('Failed!')
            sys.exit(-1)
    if is_enable_coverage():
        cov.stop()
        cov.save()
        cov.html_report()

    print("Total Spend: ", end_time - start_time)
