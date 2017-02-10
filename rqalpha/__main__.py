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

import locale
import shutil
import errno
import csv
import os
import click
import tempfile
import tarfile
import datetime
import requests
import pandas as pd
from six import StringIO, iteritems, print_

from .cache_control import set_cache_policy, CachePolicy
from .utils.click_helper import Date
from .utils.i18n import set_locale
from .utils.config import parse_config


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
    day = datetime.date.today()
    tmp = os.path.join(tempfile.gettempdir(), 'rq.bundle')

    while True:
        url = 'http://7xjci3.com1.z0.glb.clouddn.com/bundles_v2/rqbundle_%04d%02d%02d.tar.bz2' % (
        day.year, day.month, day.day)
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
    tar.close()
    os.remove(tmp)


@cli.command()
@click.option('-d', '--data-bundle-path', 'base__data_bundle_path', type=click.Path(exists=True))
@click.option('-f', '--strategy-file', 'base__strategy_file', type=click.Path(exists=True))
@click.option('-s', '--start-date', 'base__start_date', type=Date())
@click.option('-e', '--end-date', 'base__end_date', type=Date())
@click.option('-r', '--rid', 'base__run_id', type=click.STRING)
@click.option('-i', '--init-cash', 'base__stock_starting_cash', type=click.FLOAT)
@click.option('--stock-starting-cash', 'base__stock_starting_cash', type=click.FLOAT)
@click.option('--future-starting-cash', 'base__future_starting_cash', type=click.FLOAT)
@click.option('--benchmark', 'base__benchmark', type=click.STRING, default=None)
@click.option('--slippage', 'base__slippage', type=click.FLOAT)
@click.option('--commission-multiplier', 'base__commission_multiplier', type=click.FLOAT)
@click.option('--margin-multiplier', 'base__margin_multiplier', type=click.FLOAT)
@click.option('--kind', 'base__strategy_type', help="stock/future")
@click.option('--frequency', 'base__frequency', type=click.Choice(['1d', '1m']), help="1d/1m")
@click.option('--match-engine', 'base__matching_type', type=click.Choice(['current_bar', 'next_bar']), help="current_bar/next_bar")
@click.option('--run-type', 'base__run_type', type=click.Choice(['b', 'p']), default="b", help="b/p")
@click.option('--resume', 'base__resume_mode', is_flag=True)
@click.option('--name', 'base__runtime_name')
@click.option('--handle-split/--not-handle-split', 'base__handle_split', default=None, help="handle split")
@click.option('--risk-grid/--no-risk-grid', 'base__cal_risk_grid', default=True)
@click.option('--log-level', 'extra__log_level', type=click.Choice(['verbose', 'debug', 'info']), help="verbose/debug/info")
@click.option('--plot/--no-plot', 'extra__plot', default=None, help="plot result")
@click.option('-o', '--output-file', 'extra__output_file', type=click.Path(writable=True), help="output result pickle file")
@click.option('--fast-match', 'validator__fast_match', is_flag=True)
@click.option('--progress/--no-progress', 'mod__progress__enabled', default=None, help="show progress bar")
@click.option('--extra-vars', 'extra__context_vars', type=click.STRING, help="override context vars")
@click.option('--config', 'config_path', type=click.STRING, help="config file path")
def run(**kwargs):
    if kwargs.get('base__run_type') == 'p':
        set_cache_policy(CachePolicy.MINIMUM)

    locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
    locale.setlocale(locale.LC_CTYPE, "en_US.UTF-8")
    os.environ['TZ'] = 'Asia/Shanghai'
    set_locale(["zh_Hans_CN"])

    config_path = kwargs.get('config_path', None)
    if config_path is not None:
        config_path = os.path.abspath(config_path)

    from . import main
    main.run(parse_config(kwargs, config_path))


@cli.command()
@click.option('-d', '--directory', default="./", type=click.Path(), required=True)
def examples(directory):
    """
    generate example strategies to target folder
    """
    source_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "examples")

    try:
        shutil.copytree(source_dir, os.path.join(directory, "examples"))
    except OSError as e:
        if e.errno == errno.EEXIST:
            print("Folder examples is exists.")


@cli.command()
@click.argument('result-file', type=click.Path(exists=True), required=True)
def plot(result_file):
    """
    draw result DataFrame
    """
    results_df = pd.read_pickle(result_file)
    from .main import plot_result
    plot_result(result_file, results_df)


@cli.command()
@click.argument('result_pickle_file_path', type=click.Path(exists=True), required=True)
@click.argument('target_report_csv_file', type=click.Path(), required=True)
@click.option('-d', '--data-bundle-path', default=os.path.expanduser("~/.rqalpha"), type=click.Path())
def report(result_pickle_file_path, target_report_csv_file, data_bundle_path):
    """
    generate report from backtest output file
    """
    from .data.base_data_source import BaseDataSource
    from .data.data_proxy import DataProxy
    data_proxy = DataProxy(BaseDataSource(data_bundle_path))

    result_df = pd.read_pickle(result_pickle_file_path)

    csv_txt = StringIO()

    # csv_txt.write('Trades\n')
    fieldnames = ['dt', 'order_book_id', 'side', 'amount', 'price', 'cash_amount', 'commission', 'tax']
    writer = csv.DictWriter(csv_txt, fieldnames=fieldnames)
    writer.writeheader()
    # for dt, trades in result_df.trades.iteritems():
    #     for trade in trades:
    #         order = trade['order']
    #         order_book_id = order['order_book_id']
    #         trade['order_book_id'] = order_book_id
    #         instrument = data_proxy.instruments(order_book_id)
    #         trade["order_book_id"] = "{}({})".format(order_book_id, instrument.symbol)
    #         trade['dt'] = trade['dt'].strftime('%Y-%m-%d %H:%M:%S')
    #         trade['side'] = str(order['side']).split('.')[1]
    #         trade['cash_amount'] = trade['price'] * trade['amount']
    #         for key in ['amount', 'price', 'cash_amount', 'commission', 'tax']:
    #             trade[key] = round(trade[key], 2)
    #         trade.pop('order')
    #         trade.pop('trade_id')
    #         writer.writerow(trade)

    csv_txt.write('\nPositions\n')
    fieldnames = ['dt', 'order_book_id', 'market_value', 'quantity']
    writer = csv.DictWriter(csv_txt, fieldnames=fieldnames)
    writer.writeheader()
    for _dt, positions in result_df.positions.iteritems():
        dt = _dt.strftime('%Y-%m-%d %H:%M:%S')
        for order_book_id, position in iteritems(positions):
            instrument = data_proxy.instruments(order_book_id)
            writer.writerow({
                'dt': dt,
                "order_book_id": "{}({})".format(order_book_id, instrument.symbol),
                'market_value': position.market_value,
                'quantity': position.quantity,
            })

    with open(target_report_csv_file, 'w') as csvfile:
        csvfile.write(csv_txt.getvalue())


@cli.command()
@click.option('-v', '--verbose', is_flag=True)
def version(**kwargs):
    """
    Output Version Info
    """
    from rqalpha import version_info
    print("Current Version: ", version_info)

if __name__ == '__main__':
    entry_point()
