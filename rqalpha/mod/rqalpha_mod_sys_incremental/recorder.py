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

import abc
import csv
import os

from six import with_metaclass


class Recorder(with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def append_trade(self, trade):
        raise NotImplementedError

    @abc.abstractmethod
    def append_portfolio(self, dt, portfolio, benchmark_portfolio):
        raise NotImplementedError

    def flush(self):
        pass

    def close(self):
        pass


class CsvRecorder(Recorder):
    '''
    CSV 存储 trade 和 投资组合收益，根据 trade 可以恢复出 positions ，所以不需要存储 positions
    TODO: 重跑时避免重复存储
    '''
    TRADE_CSV_HEADER = [
        "exec_id",
        "order_id",
        "order_book_id",
        "datetime",
        "last_price",
        "last_quantity",
        "transaction_cost",
        "side",
        "position_effect",
    ]

    PORTFOLIO_CSV_HEADER = [
        "datetime",
        "portfolio_value",
        "market_value",
        "cash",
        "daily_pnl",
        "daily_returns",
        "total_returns",
    ]

    def __init__(self, csv_folder):
        self._file_list = []
        self._pending_tasks = []
        self._trade_writer = self._create_writer(os.path.join(csv_folder, "trade.csv"), self.TRADE_CSV_HEADER)
        self._portfolio_writer = self._create_writer(os.path.join(csv_folder, "portfolio.csv"), self.PORTFOLIO_CSV_HEADER)
        self._bm_portfolio_writer = self._create_writer(os.path.join(csv_folder, "bm_portfolio.csv"), self.PORTFOLIO_CSV_HEADER)

    def _create_writer(self, path, header):
        is_file_exist = os.path.exists(path)
        csv_file = open(path, "a")
        self._file_list.append(csv_file)
        writer = csv.DictWriter(csv_file, fieldnames=header)
        if not is_file_exist:
            writer.writeheader()

        return writer

    def append_trade(self, trade):
        self._pending_tasks.append((self._trade_writer, {key: getattr(trade, key) for key in self.TRADE_CSV_HEADER}))

    def _portfolio2dict(self, dt, portfolio):
        dic = {key: getattr(portfolio, key) for key in self.PORTFOLIO_CSV_HEADER if key != "datetime"}
        dic["datetime"] = dt
        return dic

    def append_portfolio(self, dt, portfolio, benchmark_portfolio):
        self._pending_tasks.append((self._portfolio_writer, self._portfolio2dict(dt, portfolio)))
        if benchmark_portfolio is not None:
            self._pending_tasks.append((self._bm_portfolio_writer, self._portfolio2dict(dt, benchmark_portfolio)))

    def flush(self):
        # TODO: use writerows
        for writer, data in self._pending_tasks:
            writer.writerow(data)

    def close(self):
        for csv_file in self._file_list:
            csv_file.close()


# TODO: add mongodb recorder, etc...