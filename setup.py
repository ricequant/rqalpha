#!/usr/bin/env python

from setuptools import setup, find_packages

from pip.req import parse_requirements


setup(
    name='rqbacktest',
    version='0.0.1',
    description='Python Distribution Utilities',
    packages=find_packages(exclude=[]),
    author='ricequant',
    author_email='public@ricequant.com',
    url='https://www.ricequant.com/',
    install_requires=[str(ir.req) for ir in parse_requirements("requirements.txt", session=False)],
)
