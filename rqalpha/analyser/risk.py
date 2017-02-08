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

from ..utils.repr import dict_repr


class Risk:

    __repr__ = dict_repr

    def __init__(self):
        self.volatility = .0
        self.alpha = .0
        self.beta = .0
        self.sharpe = .0
        self.sortino = .0
        self.information_ratio = .0
        self.max_drawdown = .0
        self.tracking_error = .0
        self.downside_risk = .0

    def _clone(self):
        c = type('RiskClone', (), {})()
        c.volatility = self.volatility
        c.alpha = self.alpha
        c.beta = self.beta
        c.sharpe = self.sharpe
        c.sortino = self.sortino
        c.information_ratio = self.information_ratio
        c.max_drawdown = self.max_drawdown
        c.tracking_error = self.tracking_error
        c.downside_risk = self.downside_risk
        return c

    def __to_dict__(self):
        risk_dict = {
            'volatility': self.volatility,
            'alpha': self.alpha,
            'beta': self.beta,
            'sharpe': self.sharpe,
            'sortino': self.sortino,
            'information_ratio': self.information_ratio,
            'max_drawdown': self.max_drawdown,
            'tracking_error': self.tracking_error,
            'downside_risk': self.downside_risk
        }
        return risk_dict

    @classmethod
    def __from_dict__(cls, risk_dict):
        risk = cls()
        risk.volatility = risk_dict['volatility']
        risk.alpha = risk_dict['alpha']
        risk.beta = risk_dict['beta']
        risk.sharpe = risk_dict['sharpe']
        risk.sortino = risk_dict['sortino']
        risk.information_ratio = risk_dict['information_ratio']
        risk.max_drawdown = risk_dict['max_drawdown']
        risk.tracking_error = risk_dict['tracking_error']
        risk.downside_risk = risk_dict['downside_risk']
        return risk
