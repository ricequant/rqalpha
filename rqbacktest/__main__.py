# -*- coding: utf-8 -*-

import os
import shutil

import pytz
import click
from six import exec_
import pandas as pd

from .trading_params import TradingParams
from . import api
from .utils.click_helper import Date
from . import StrategyExecutor
from .data import RqDataProxy
from .logger import user_log


@click.group()
@click.option('-v', '--verbose', count=True)
@click.pass_context
def cli(ctx, verbose):
    ctx.obj["VERBOSE"] = verbose


def entry_point():
    cli(obj={})


@cli.command()
@click.option('-f', '--strategy-file', type=click.Path(exists=True), required=True)
@click.option('-s', '--start-date', type=Date(), required=True)
@click.option('-e', '--end-date', type=Date(), required=True)
@click.option('-o', '--output-file', type=click.Path(writable=True))
def run(strategy_file, start_date, end_date, output_file):
    '''run strategy from file
    '''
    import rqdata
    rqdata.init()

    with open(strategy_file) as f:
        source_code = f.read()

    dummy_func = lambda *args, **kwargs: None
    scope = {
        "logger": user_log,
    }
    scope.update(api.__dict__)
    code = compile(source_code, strategy_file, 'exec')
    exec_(code, scope)

    timezone = pytz.utc

    trading_cal = pd.Index(pd.Series(
        rqdata.get_trading_dates("2005-01-01", "2020-01-01")).apply(lambda date: pd.Timestamp(date, tz=timezone)))

    trading_cal = trading_cal[
        (trading_cal >= start_date) & (trading_cal <= end_date)
    ]

    trading_params = TradingParams(trading_cal)
    data_proxy = RqDataProxy()

    executor = StrategyExecutor(
        init=scope.get("init", dummy_func),
        before_trading=scope.get("before_trading", dummy_func),
        handle_bar=scope.get("handle_bar", dummy_func),

        trading_params=trading_params,
        data_proxy=data_proxy,
    )

    results_df = executor.execute()

    if output_file is not None:
        results_df.to_pickle(output_file)


@cli.command()
@click.option('-d', '--directory', default="./", type=click.Path(), required=True)
def generate_examples(directory):
    source_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "examples")

    shutil.copytree(source_dir, os.path.join(directory, "examples"))


if __name__ == '__main__':
    entry_point()
