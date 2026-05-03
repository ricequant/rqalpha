# -*- coding: utf-8 -*-

__config__ = {
    "api_key": "",
    "base_url": "https://api.adanos.org",
    "source": "reddit",
    "timeout": 10,
}


def load_mod():
    from .mod import AdanosSentimentMod

    return AdanosSentimentMod()
