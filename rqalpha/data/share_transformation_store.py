# -*- coding: utf-8 -*-
#
# Copyright 2019 Ricequant, Inc
#
# * Commercial Usage: please contact public@ricequant.com
# * Non-Commercial Usage:
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

import json
import six

from rqalpha.utils.logger import system_log

DEFAULT_SHARE_TRANSFORMATION = {
    '000022.XSHE': {
        'successor': '001872.XSHE',
        'effective_date': '2018-12-26',
        'share_conversion_ratio': 1.0,
        'predecessor_delisted': True,
        'discretionary_execution': False,
        'predecessor_delisted_date': '2018-12-26',
        'event': 'code_change'
    },
    '000024.XSHE': {
        'successor': '001979.XSHE',
        'effective_date': '2015-12-30',
        'share_conversion_ratio': 1.6008,
        'predecessor_delisted': True,
        'discretionary_execution': False,
        'predecessor_delisted_date': '2015-12-30',
        'event': 'merge'
    },
    '600005.XSHG': {
        'successor': '600019.XSHG',
        'effective_date': '2017-02-14',
        'share_conversion_ratio': 0.56,
        'predecessor_delisted': True,
        'discretionary_execution': False,
        'predecessor_delisted_date': '2017-02-14',
        'event': 'merge'
    },
    '601299.XSHG': {
        'successor': '601766.XSHG',
        'effective_date': '2015-05-20',
        'share_conversion_ratio': 1.1,
        'predecessor_delisted': True,
        'discretionary_execution': False,
        'predecessor_delisted_date': '2015-05-20',
        'event': 'merge'
    },
    '601313.XSHG': {
        'successor': '601360.XSHG',
        'effective_date': '2018-02-26',
        'share_conversion_ratio': 1.0,
        'predecessor_delisted': True,
        'discretionary_execution': False,
        'predecessor_delisted_date': '2018-02-26',
        'event': 'code_change'
    }
}


if six.PY2:
    # FileNotFoundError is only available since Python 3.3
    FileNotFoundError = IOError
    from io import open


class ShareTransformationStore(object):
    def __init__(self, f):
        try:
            with open(f, 'r', encoding="utf-8") as store:
                self._share_transformation = json.load(store)
        except FileNotFoundError:
            # only for compatibility with the old bundle
            system_log.warning("{} not found, use default data which may be out-of-date".format(f))
            self._share_transformation = DEFAULT_SHARE_TRANSFORMATION

    def get_share_transformation(self, order_book_id):
        try:
            transformation_data = self._share_transformation[order_book_id]
        except KeyError:
            return
        return transformation_data["successor"], transformation_data["share_conversion_ratio"]
