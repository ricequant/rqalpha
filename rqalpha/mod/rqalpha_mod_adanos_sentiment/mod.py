# -*- coding: utf-8 -*-

import os
from collections.abc import Iterable

import requests

from rqalpha.const import EXECUTION_PHASE
from rqalpha.core.execution_context import ExecutionContext
from rqalpha.interface import AbstractMod


ADANOS_SOURCES = {"reddit", "x", "news", "polymarket"}


class AdanosSentimentMod(AbstractMod):
    def __init__(self):
        self._api_key = ""
        self._base_url = "https://api.adanos.org"
        self._source = "reddit"
        self._timeout = 10
        self._inject_api()

    def start_up(self, env, mod_config):
        self._api_key = (mod_config.api_key or os.getenv("ADANOS_API_KEY", "")).strip()
        self._base_url = mod_config.base_url.rstrip("/")
        self._source = self._normalize_source(mod_config.source)
        self._timeout = mod_config.timeout

    def tear_down(self, code, exception=None):
        pass

    def get_sentiment(self, order_book_id, source=None, days=7):
        source = self._normalize_source(source or self._source)
        ticker = self._normalize_order_book_id(order_book_id)
        return self._request_json(
            path="/{}/stocks/v1/stock/{}".format(source, ticker),
            params={"days": days},
        )

    def compare_sentiment(self, order_book_ids, source=None, days=7):
        source = self._normalize_source(source or self._source)
        tickers = ",".join(
            self._normalize_order_book_id(order_book_id)
            for order_book_id in self._as_order_book_id_list(order_book_ids)
        )
        if not tickers:
            raise ValueError("order_book_ids must contain at least one symbol")
        return self._request_json(
            path="/{}/stocks/v1/compare".format(source),
            params={"tickers": tickers, "days": days},
        )

    def _inject_api(self):
        from rqalpha.api import export_as_api

        @export_as_api
        @ExecutionContext.enforce_phase(
            EXECUTION_PHASE.ON_INIT,
            EXECUTION_PHASE.BEFORE_TRADING,
            EXECUTION_PHASE.ON_BAR,
            EXECUTION_PHASE.ON_TICK,
            EXECUTION_PHASE.AFTER_TRADING,
            EXECUTION_PHASE.SCHEDULED,
        )
        def adanos_sentiment(order_book_id, source=None, days=7):
            return self.get_sentiment(order_book_id, source=source, days=days)

        @export_as_api
        @ExecutionContext.enforce_phase(
            EXECUTION_PHASE.ON_INIT,
            EXECUTION_PHASE.BEFORE_TRADING,
            EXECUTION_PHASE.ON_BAR,
            EXECUTION_PHASE.ON_TICK,
            EXECUTION_PHASE.AFTER_TRADING,
            EXECUTION_PHASE.SCHEDULED,
        )
        def adanos_sentiment_compare(order_book_ids, source=None, days=7):
            return self.compare_sentiment(order_book_ids, source=source, days=days)

    def _request_json(self, path, params):
        api_key = self._api_key
        if not api_key:
            raise ValueError("Please set mod.api_key or ADANOS_API_KEY")

        response = requests.get(
            "{}{}".format(self._base_url, path),
            params=params,
            headers={"X-API-Key": api_key, "Accept": "application/json"},
            timeout=self._timeout,
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _normalize_source(source):
        source = source.strip().lower()
        if source not in ADANOS_SOURCES:
            raise ValueError("source must be one of: reddit, x, news, polymarket")
        return source

    @staticmethod
    def _normalize_order_book_id(order_book_id):
        symbol = str(order_book_id).strip().split(".", 1)[0].upper()
        if not symbol:
            raise ValueError("order_book_id must not be empty")
        return symbol

    @staticmethod
    def _as_order_book_id_list(order_book_ids):
        if isinstance(order_book_ids, str):
            return [item.strip() for item in order_book_ids.split(",") if item.strip()]
        if isinstance(order_book_ids, Iterable):
            return list(order_book_ids)
        raise TypeError("order_book_ids must be a string or iterable")
