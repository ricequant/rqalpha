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

import six
import hashlib
from collections import OrderedDict

import jsonpickle

from rqalpha.events import EVENT
from rqalpha.const import PERSIST_MODE
from rqalpha.utils.logger import system_log


class CoreObjectsPersistProxy(object):
    def __init__(self, scheduler):
        self._objects = {'scheduler': scheduler}

    def get_state(self):
        result = {}
        for key, obj in six.iteritems(self._objects):
            state = obj.get_state()
            if state is not None:
                result[key] = state

        return jsonpickle.dumps(result).encode('utf-8')

    def set_state(self, state):
        state = jsonpickle.loads(state.decode('utf-8'))
        for key, value in six.iteritems(state):
            try:
                self._objects[key].set_state(value)
            except KeyError:
                system_log.warn('core object state for {} ignored'.format(key))


class PersistHelper(object):
    def __init__(self, persist_provider, event_bus, persist_mode):
        self._objects = OrderedDict()
        self._last_state = {}
        self._persist_provider = persist_provider
        if persist_mode == PERSIST_MODE.REAL_TIME:
            event_bus.add_listener(EVENT.POST_BEFORE_TRADING, self.persist)
            event_bus.add_listener(EVENT.POST_AFTER_TRADING, self.persist)
            event_bus.add_listener(EVENT.POST_BAR, self.persist)
            event_bus.add_listener(EVENT.DO_PERSIST, self.persist)
            event_bus.add_listener(EVENT.POST_SETTLEMENT, self.persist)

    def persist(self, *args):
        for key, obj in six.iteritems(self._objects):
            try:
                state = obj.get_state()
                if not state:
                    continue
                md5 = hashlib.md5(state).hexdigest()
                if self._last_state.get(key) == md5:
                    continue
                self._persist_provider.store(key, state)
            except Exception as e:
                system_log.exception("PersistHelper.persist fail")
            else:
                self._last_state[key] = md5

    def register(self, key, obj):
        if key in self._objects:
            raise RuntimeError('duplicated persist key found: {}'.format(key))
        self._objects[key] = obj

    def unregister(self, key):
        if key in self._objects:
            del self._objects[key]
            return True
        return False

    def restore(self):
        for key, obj in six.iteritems(self._objects):
            state = self._persist_provider.load(key)
            system_log.debug('restore {} with state = {}', key, state)
            if not state:
                continue
            obj.set_state(state)
