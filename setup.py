#!/usr/bin/env python
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


from setuptools import setup, find_packages

from pip.req import parse_requirements


setup(
    name='rqalpha',
    version='0.0.72',
    description='Ricequant Backtest Engine',
    packages=find_packages(exclude=[]),
    author='ricequant',
    author_email='public@ricequant.com',
    package_data={'': ['*.*']},
    url='https://github.com/ricequant/rqalpha',
    install_requires=[str(ir.req) for ir in parse_requirements("requirements.txt", session=False)],
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "rqalpha = rqalpha.__main__:entry_point",
        ]
    },
)
