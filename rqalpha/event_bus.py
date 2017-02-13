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

from collections import defaultdict


class EventBus(object):
    def __init__(self):
        self._listeners = defaultdict(list)

    def add_listener(self, event, listener):
        self._listeners[event].append(listener)

    def prepend_listener(self, event, listener):
        self._listeners[event].insert(0, listener)

    def publish_event(self, event, *args, **kwargs):
        for l in self._listeners[event]:
            l(*args, **kwargs)
