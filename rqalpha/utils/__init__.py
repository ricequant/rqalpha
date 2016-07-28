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


from six import iteritems

from .context import ExecutionContext


def memoize(function):
    memo = {}
    function.__memo__ = memo

    def wrapper(*args, **kwargs):
        key = "#".join([str(arg) for arg in args] + ["%s:%s" % (k, v) for k, v in iteritems(kwargs)])
        if key in memo:
            return memo[key]
        else:
            rv = function(*args, **kwargs)
            memo[key] = rv
            return rv

    return wrapper


def dummy_func(*args, **kwargs):
    return None
