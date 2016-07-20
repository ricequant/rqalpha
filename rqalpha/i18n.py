# -*- coding: utf-8 -*-

import os.path
from gettext import NullTranslations, translation


translation_dir = os.path.join(
    os.path.dirname(
        os.path.abspath(
            __file__,
        ),
    ),
    "translations"
)
current_translation = NullTranslations()


def set_locale(locales):
    global current_translation
    current_translation = translation(
        domain="rqalpha",
        localedir=translation_dir,
        languages=locales,
    )


def gettext(message):
    return current_translation.gettext(message)
