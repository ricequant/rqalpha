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


# TODO use nametuple to reduce memory


class Trade(object):

    def __init__(self, date, order_book_id, price, amount, order_id, commission=0., tax=0.):
        self.date = date
        self.order_book_id = order_book_id
        self.price = price
        self.amount = amount
        self.order_id = order_id
        self.commission = commission
        self.tax = tax

    def __repr__(self):
        return "Trade({0})".format(self.__dict__)
