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

import click
import pandas as pd


class Date(click.ParamType):
    def __init__(self, tz=None):
        self.tz = tz

    def convert(self, value, param, ctx):
        # return pd.Timestamp(value, self.tz)
        return pd.Timestamp(value)

    @property
    def name(self):
        return type(self).__name__.upper()
