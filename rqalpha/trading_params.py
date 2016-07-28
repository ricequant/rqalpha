# -*- coding: utf-8 -*-
#
# Copyright 2016 Ricequant, Inc
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


import pytz
import pandas as pd


class TradingParams(object):
    def __init__(self, trading_calendar, **kwargs):
        assert isinstance(trading_calendar, pd.Index)
        self.trading_calendar = trading_calendar
        self.timezone = kwargs.get("timezone", pytz.utc)
        self.benchmark = kwargs.get("benchmark", "000300.XSHG")
        self.frequency = kwargs.get("frequency", "1d")

        self.start_date = kwargs.get("start_date", self.trading_calendar[0].date())
        self.end_date = kwargs.get("end_date", self.trading_calendar[-1].date())

        self.init_cash = kwargs.get("init_cash", 100000)

        self.show_progress = kwargs.get("show_progress", False)
