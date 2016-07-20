# -*- coding: utf-8 -*-

import sys
import os
import shutil
import datetime
import tempfile
import tarfile

import click
import requests
from six import exec_, print_

from . import StrategyExecutor
from . import api
from .data import LocalDataProxy
from .logger import user_log
from .trading_params import TradingParams
from .utils.click_helper import Date
from .utils import dummy_func


@click.group()
@click.option('-v', '--verbose', count=True)
@click.pass_context
def cli(ctx, verbose):
    ctx.obj["VERBOSE"] = verbose


def entry_point():
    cli(obj={})


@cli.command()
@click.option('-d', '--data-bundle-path', default=os.path.expanduser("~/.rqalpha"), type=click.Path())
def update_bundle(data_bundle_path):
    """update data bundle, download if not found"""
    day = datetime.date.today() - datetime.timedelta(days=1)
    tmp = os.path.join(tempfile.gettempdir(), 'rq.bundle')

    while True:
        url = 'http://7xjci3.com1.z0.glb.clouddn.com/bundles/rqbundle_%04d%02d%02d.tar.bz2' % (day.year, day.month, day.day)
        print_('try {} ...'.format(url))
        r = requests.get(url, stream=True)
        if r.status_code != 200:
            day = day - datetime.timedelta(days=1)
            continue

        out = open(tmp, 'wb')
        total_length = int(r.headers.get('content-length'))

        with click.progressbar(length=total_length, label='downloading ...') as bar:
            for data in r.iter_content(chunk_size=8192):
                bar.update(len(data))
                out.write(data)

        out.close()
        break

    shutil.rmtree(data_bundle_path, ignore_errors=True)
    os.mkdir(data_bundle_path)
    tar = tarfile.open(tmp, 'r:bz2')
    tar.extractall(data_bundle_path)
    os.remove(tmp)


@cli.command()
@click.option('-f', '--strategy-file', type=click.Path(exists=True), required=True)
@click.option('-s', '--start-date', type=Date(), required=True)
@click.option('-e', '--end-date', type=Date(), required=True)
@click.option('-o', '--output-file', type=click.Path(writable=True))
@click.option('--draw-result/--no-draw-result', default=True)
@click.option('-d', '--data-bundle-path', default=os.path.expanduser("~/.rqalpha"), type=click.Path())
def run(strategy_file, start_date, end_date, output_file, draw_result, data_bundle_path):
    '''run strategy from file
    '''
    if not os.path.exists(data_bundle_path):
        print_("data bundle not found. Run `%s update_bundle` to download data bundle." % sys.argv[0])
        return

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
    scope = {
        "logger": user_log,
        "print": print_,
    }
    scope.update({export_name: getattr(api, export_name) for export_name in api.__all__})
    code = compile(source_code, strategy_filename, 'exec')
    exec_(code, scope)

    try:
        data_proxy = LocalDataProxy(data_bundle_path)
    except FileNotFoundError:
        print_("data bundle might crash. Run `%s update_bundle` to redownload data bundle." % sys.argv[0])
        sys.exit()

    trading_cal = data_proxy.get_trading_dates(start_date, end_date)
    trading_params = TradingParams(trading_cal, start_date=start_date.date(), end_date=end_date.date())

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
