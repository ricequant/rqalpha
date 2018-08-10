#!/usr/bin/env python
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

import platform
from os.path import dirname, join
try:
    from pip._internal.req import parse_requirements
except ImportError:
    from pip.req import parse_requirements

from setuptools import find_packages, setup


def update_requirements(from_reqs, to_reqs):
    from_req_dict = {req.name: req for req in from_reqs}
    from_req_dict.update({req.name: req for req in to_reqs})
    return from_req_dict.values()


with open(join(dirname(__file__), 'rqalpha/VERSION.txt'), 'rb') as f:
    version = f.read().decode('ascii').strip()

requirements = parse_requirements("requirements.txt", session=False)

python_version = platform.python_version()
if python_version.startswith("2"):
    requirements = update_requirements(requirements, parse_requirements("requirements-py2.txt", session=False))
elif python_version.startswith("3.4"):
    requirements = update_requirements(requirements, parse_requirements("requirements-py34.txt", session=False))

req_strs = [str(ir.req) for ir in requirements]


setup(
    name='rqalpha',
    version=version,
    description='Ricequant Algorithm Trading System',
    packages=find_packages(exclude=[]),
    author='ricequant',
    author_email='public@ricequant.com',
    license='Apache License v2',
    package_data={'': ['*.*']},
    url='https://github.com/ricequant/rqalpha',
    install_requires=req_strs,
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "rqalpha = rqalpha.__main__:entry_point"
        ]
    },
    classifiers=[
        'Programming Language :: Python',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: Unix',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
