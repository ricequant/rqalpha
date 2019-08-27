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
import codecs


class ShareTransformationStore(object):
    def __init__(self, f):
        with codecs.open(f, 'r', encoding="utf-8") as store:
            self._share_transformation = json.load(store)

    def get_share_transformation(self, order_book_id):
        try:
            transformation_data = self._share_transformation[order_book_id]
        except KeyError:
            return
        return transformation_data["successor"], transformation_data["share_conversion_ratio"]
