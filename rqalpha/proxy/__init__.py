# -*- coding: utf-8 -*-
#
# Copyright 2016 Ricequant, Inc
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


class PositionsProxy:
    def __init__(self, postions):
        self._postions = postions
        self.__class__.__repr__ = postions.__repr__

    def __repr__(self):
        return str([order_book_id for order_book_id in self.keys()])

    def __getitem__(self, name):
        position = self._postions[name]
        return position._clone()

    def __iter__(self):
        for key in self.keys():
            yield key

    def __len__(self):
        return len(self._postions)

    def items(self):
        for key, value in sorted(self._postions.items()):
            yield key, value._clone()

    def keys(self):
        return sorted(self._postions.keys())

    def __setattr__(self, name, value):
        if name not in ["_postions"]:
            raise AttributeError("{} can not modify to {}".format(name, value))
        super().__setattr__(name, value)


class PortfolioProxy:
    def __init__(self, portfolio):
        self._portfolio = portfolio
        self.__class__.__repr__ = portfolio.__repr__

        self.positions = PositionsProxy(portfolio.positions)

    def __getattr__(self, name):
        return getattr(self._portfolio, name)

    def __setattr__(self, name, value):
        if name not in ["_portfolio", "_positions_proxy", "positions"]:
            raise AttributeError("{} can not modify to {}".format(name, value))
        super().__setattr__(name, value)
