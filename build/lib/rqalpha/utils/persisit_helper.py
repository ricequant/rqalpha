# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。

import hashlib
from collections import OrderedDict

from rqalpha.const import PERSIST_MODE
from rqalpha.core.events import EVENT
from rqalpha.utils.logger import system_log


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
            event_bus.add_listener(EVENT.DO_RESTORE, self.restore)

    def persist(self, *_):
        for key, obj in self._objects.items():
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

    def restore(self, event):
        key = getattr(event, "key", None)
        if key:
            return self._restore_obj(key, self._objects[key])

        ret = {key: self._restore_obj(key, obj) for key, obj in self._objects.items()}
        return ret

    def _restore_obj(self, key, obj):
        state = self._persist_provider.load(key)
        system_log.debug('restore {} with state = {}', key, state)
        if not state:
            return False
        try:
            obj.set_state(state)
        except Exception:
            system_log.exception('restore failed: key={} state={}'.format(key, state))
        return True
