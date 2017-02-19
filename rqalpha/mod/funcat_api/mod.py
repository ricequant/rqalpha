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


from rqalpha.interface import AbstractMod


class FuncatAPIMod(AbstractMod):
    def start_up(self, env, mod_config):
        try:
            import funcat
        except ImportError:
            print("-" * 50)
            print(">>> Missing funcat. Please run `pip install funcat`")
            print("-" * 50)
            raise

        # change funcat data backend to rqalpha
        from funcat.data.rqalpha_backend import RQAlphaDataBackend
        funcat.set_data_backend(RQAlphaDataBackend())

        # register funcat api into rqalpha
        from rqalpha.api.api_base import register_api
        for name in dir(funcat):
            obj = getattr(funcat, name)
            if getattr(obj, "__module__", "").startswith("funcat"):
                register_api(name, obj)

    def tear_down(self, code, exception=None):
        pass
