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

from . import api_base, api_future, api_stock
from ..const import ACCOUNT_TYPE


def get_apis(account_list):
    apis = {name: getattr(api_base, name) for name in api_base.__all__}
    for account_type in account_list:
        if account_type == ACCOUNT_TYPE.STOCK:
            apis.update((name, getattr(api_stock, name)) for name in api_stock.__all__)
        elif account_type == ACCOUNT_TYPE.FUTURE:
            apis.update((name, getattr(api_future, name)) for name in api_future.__all__)
    return apis
