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

import simplejson as json
import datetime

from rqalpha import const


def convert_dict_to_json(dict_obj):
    dict_obj = json.dumps(dict_obj, default=custom_encode)
    return dict_obj


def convert_json_to_dict(json_str):
    dict_obj = json.loads(json_str, object_hook=custom_decode)
    return dict_obj


def custom_encode(obj):
    if isinstance(obj, datetime.datetime):
        obj = {"__datetime__": True, "as_str": obj.strftime("%Y%m%dT%H:%M:%S.%f")}
    elif isinstance(obj, datetime.date):
        obj = {"__date__": True, "as_str": obj.strftime("%Y%m%d")}
    elif isinstance(obj, const.CustomEnum):
        obj = {"__enum__": True, "as_str": str(obj)}
    else:
        raise TypeError(
            "Unserializable object {} of type {}".format(obj, type(obj))
        )
    return obj


def custom_decode(obj):
    if "__datetime__" in obj:
        obj = datetime.datetime.strptime(obj["as_str"], "%Y%m%dT%H:%M:%S.%f")
    elif "__date__" in obj:
        obj = datetime.datetime.strptime(obj["as_str"], "%Y%m%d").date()
    elif "__enum__" in obj:
        [e, v] = obj["as_str"].split(".")
        obj = getattr(getattr(const, e), v)
    return obj
