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
from .data import LocalDataProxy
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
@click.option('--draw-result/--no-draw-result', default=True)
@click.option('-d', '--data-bundle-path', default=os.path.expanduser("~/.rqbacktest"), type=click.Path(exists=True))
def run(strategy_file, start_date, end_date, output_file, draw_result, data_bundle_path):
    '''run strategy from file
    '''
    with open(strategy_file) as f:
        source_code = f.read()

    results_df = run_strategy(source_code, strategy_file, start_date, end_date, data_bundle_path)

    if output_file is not None:
        results_df.to_pickle(output_file)

    if draw_result:
        import matplotlib
        import matplotlib.pyplot as plt
        plt.style.use('ggplot')

        f, ax = plt.subplots(num=strategy_file, figsize=(16, 8))

        ax.get_xaxis().set_minor_locator(matplotlib.ticker.AutoMinorLocator())
        ax.get_yaxis().set_minor_locator(matplotlib.ticker.AutoMinorLocator())
        ax.grid(b=True, which='minor', linewidth=.2)
        ax.grid(b=True, which='major', linewidth=1)

        ax.plot(results_df["total_returns"], label="strategy", alpha=1, linewidth=2, color="#aa4643")
        ax.plot(results_df["benchmark_total_returns"], label="benchmark", alpha=1, linewidth=2, color="#4572a7")

        plt.legend()
        plt.show()


@cli.command()
@click.option('-d', '--directory', default="./", type=click.Path(), required=True)
def generate_examples(directory):
    '''generate example strategies to target folder
    '''
    source_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "examples")

    shutil.copytree(source_dir, os.path.join(directory, "examples"))


def run_strategy(source_code, strategy_filename, start_date, end_date, data_bundle_path):
    dummy_func = lambda *args, **kwargs: None
    scope = {
        "logger": user_log,
    }
    scope.update(api.__dict__)
    code = compile(source_code, strategy_filename, 'exec')
    exec_(code, scope)

    data_proxy = LocalDataProxy(data_bundle_path)

    trading_cal = data_proxy.get_trading_dates(start_date, end_date)
    trading_params = TradingParams(trading_cal)

    executor = StrategyExecutor(
        init=scope.get("init", dummy_func),
        before_trading=scope.get("before_trading", dummy_func),
        handle_bar=scope.get("handle_bar", dummy_func),

        trading_params=trading_params,
        data_proxy=data_proxy,
    )

    results_df = executor.execute()

    return results_df


if __name__ == '__main__':
    entry_point()
