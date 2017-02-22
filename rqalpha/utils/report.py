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

import os

import six
import pandas as pd


def generate_report(result_dict, target_report_csv_path):
    from six import StringIO

    output_path = os.path.join(target_report_csv_path, result_dict["summary"]["strategy_name"])
    try:
        os.mkdir(output_path)
    except:
        pass

    xlsx_writer = pd.ExcelWriter(os.path.join(output_path, "report.xlsx"), engine='xlsxwriter')

    # summary.csv
    csv_txt = StringIO()
    summary = result_dict["summary"]
    csv_txt.write(u"\n".join(sorted("{},{}".format(key, value) for key, value in six.iteritems(summary))))
    df = pd.DataFrame(data=[{"val": val} for val in summary.values()], index=summary.keys()).sort_index()
    df.to_excel(xlsx_writer, sheet_name="summary")

    with open(os.path.join(output_path, "summary.csv"), 'w') as csvfile:
        csvfile.write(csv_txt.getvalue())

    for name in ["total_portfolios", "stock_portfolios", "future_portfolios",
                 "stock_positions", "future_positions", "trades"]:
        try:
            df = result_dict[name]
        except KeyError:
            continue

        # replace all date in dataframe as string
        if df.index.name == "date":
            df = df.reset_index()
            df["date"] = df["date"].apply(lambda x: x.strftime("%Y-%m-%d"))
            df = df.set_index("date")

        csv_txt = StringIO()
        csv_txt.write(df.to_csv(encoding='utf-8'))

        df.to_excel(xlsx_writer, sheet_name=name)

        with open(os.path.join(output_path, "{}.csv".format(name)), 'w') as csvfile:
            csvfile.write(csv_txt.getvalue())

    # report.xls <--- 所有sheet的汇总
    xlsx_writer.save()
