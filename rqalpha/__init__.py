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

"""
RQAlpha - a Algorithm Trading System
"""

import pkgutil

__all__ = [
    '__version__',
    'version_info'
]

__version__ = pkgutil.get_data(__package__, 'VERSION.txt').decode('ascii').strip()

version_info = tuple(int(v) if v.isdigit() else v
                     for v in __version__.split('.'))

__main_version__ = "%s.%s.x" % (version_info[0], version_info[1])

del pkgutil


def run(config, source_code=None):
    import locale
    import os
    from .utils.cache_control import set_cache_policy, CachePolicy
    from .utils.i18n import localization
    from .utils.config import parse_config
    from . import main

    try:
        if config["base"]["run_type"] == "p":
            set_cache_policy(CachePolicy.MINIMUM)
    except Exception as e:
        pass

    try:
        locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
        locale.setlocale(locale.LC_CTYPE, "en_US.UTF-8")
        os.environ['TZ'] = 'Asia/Shanghai'
        localization.set_locale(["zh_Hans_CN"])
    except Exception as e:
        if os.name != 'nt':
            raise

    return main.run(parse_config(config, click_type=False, source_code=source_code), source_code=source_code)


def update_bundle(data_bundle_path=None, confirm=True):
    from . import main
    main.update_bundle(data_bundle_path, confirm)
