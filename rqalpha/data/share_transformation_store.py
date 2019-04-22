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

import json

from rqalpha.utils.logger import system_log

DEFAULT_SHARE_TRANSFORMATION = {
  "000024.XSHE": {
    "successor": "001979.XSHE",
    "effective_date": 1451433600000,
    "share_conversion_ratio": 1.6008,
    "predecessor_delisted": True,
    "discretionary_execution": False,
    "predecessor_delisted_date": 1451433600000,
    "event": "merge"
  },
  "600005.XSHG": {
    "successor": "600019.XSHG",
    "effective_date": 1487030400000,
    "share_conversion_ratio": 0.56,
    "predecessor_delisted": True,
    "discretionary_execution": False,
    "predecessor_delisted_date": 1487030400000,
    "event": "merge"
  },
  "601299.XSHG": {
    "successor": "601766.XSHG",
    "effective_date": 1432080000000,
    "share_conversion_ratio": 1.1,
    "predecessor_delisted": True,
    "discretionary_execution": False,
    "predecessor_delisted_date": 1432080000000,
    "event": "merge"
  },
  "601313.XSHG": {
    "successor": "601360.XSHG",
    "effective_date": 1519603200000,
    "share_conversion_ratio": 1.0,
    "predecessor_delisted": True,
    "discretionary_execution": False,
    "predecessor_delisted_date": 1519603200000,
    "event": "code_change"
  }
}


class ShareTransformationStore(object):
    def __init__(self, f):
        try:
            with open(f, 'r', encoding="utf-8") as store:
                self._share_transformation = json.load(store)
        except FileNotFoundError:
            # only for compatibility with the old bundle
            system_log.warning("{} not found, use default data which may be out-of-date".format(f))
            self._share_transformation = DEFAULT_SHARE_TRANSFORMATION

    def get_share_transformation(self):
        return self._share_transformation
