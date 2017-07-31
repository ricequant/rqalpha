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

import os.path
from gettext import NullTranslations, translation

from rqalpha.utils.logger import system_log
from rqalpha.utils.py2 import to_utf8


class Localization(object):

    def __init__(self, trans=None):
        self.trans = NullTranslations() if trans is None else trans

    def set_locale(self, locales, trans_dir=None):
        if locales[0] is None or "en" in locales[0].lower():
            self.trans = NullTranslations()
            return
        if "cn" in locales[0].lower():
            locales = ["zh_Hans_CN"]
        try:
            if trans_dir is None:
                trans_dir = os.path.join(
                    os.path.dirname(
                        os.path.abspath(
                            __file__,
                        ),
                    ),
                    "translations"
                )
            self.trans = translation(
                domain="messages",
                localedir=trans_dir,
                languages=locales,
            )
        except Exception as e:
            system_log.debug(e)
            self.trans = NullTranslations()


localization = Localization()


def gettext(message):
    trans_txt = localization.trans.gettext(message)
    return to_utf8(trans_txt)
