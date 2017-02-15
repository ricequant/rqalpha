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


def deep_update(from_dict, to_dict):
    for (key, value) in from_dict.items():
        if key in to_dict.keys() and \
                isinstance(to_dict[key], dict) and \
                isinstance(value, dict):
            deep_update(value, to_dict[key])
        else:
            to_dict[key] = value
