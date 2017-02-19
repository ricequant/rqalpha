#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Hua Liang[Stupid ET] <et@everet.org>
#


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
        from funcat.data.rqalpha_backend import RQAlphaDataBackend

        from rqalpha.api.api_base import register_api

        for name in dir(funcat):
            obj = getattr(funcat, name)
            if getattr(obj, "__module__", "").startswith("funcat"):
                register_api(name, obj)

        funcat.set_data_backend(RQAlphaDataBackend())

    def tear_down(self, code, exception=None):
        pass
