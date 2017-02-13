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
from .logger import system_log

translation_dir = os.path.join(
    os.path.dirname(
        os.path.abspath(
            __file__,
        ),
    ),
    "translations"
)
current_translation = NullTranslations()


def set_locale(locales, trans_dir=translation_dir):
    global current_translation

    try:
        current_translation = translation(
            domain="messages",
            localedir=trans_dir,
            languages=locales,
        )
    except Exception as e:
        system_log.debug(e)
        current_translation = NullTranslations()


def gettext(message):
    return current_translation.gettext(message)
