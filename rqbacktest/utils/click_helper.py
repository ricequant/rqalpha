# -*- coding: utf-8 -*-

import datetime

import click
import pandas as pd


class Date(click.ParamType):
    def __init__(self, tz=None):
        self.tz = tz

    def convert(self, value, param, ctx):
        return pd.Timestamp(value, self.tz)

    @property
    def name(self):
        return type(self).__name__.upper()
