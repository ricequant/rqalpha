#!/usr/bin/env python

from setuptools import setup, find_packages

from pip.req import parse_requirements


setup(
    name='rqalpha',
    version='0.0.16',
    description='Ricequant Backtest Engine',
    packages=find_packages(exclude=[]),
    author='ricequant',
    author_email='public@ricequant.com',
    url='https://github.com/ricequant/rqalpha',
    install_requires=[str(ir.req) for ir in parse_requirements("requirements.txt", session=False)],
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "rqalpha = rqalpha.__main__:entry_point",
        ]
    },

)
