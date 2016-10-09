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


import codecs
import sys
import os
import shutil
import datetime
import tempfile
import tarfile
import errno
import csv

import pandas as pd
import click
import requests
from six import exec_, print_, StringIO, iteritems

from . import StrategyExecutor
from . import api
from .data import LocalDataProxy
from .logger import user_log, user_print
from .trading_params import TradingParams
from .utils.click_helper import Date
from .utils import dummy_func, convert_int_to_date
from .scheduler import Scheduler


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
    tar.close()
    os.remove(tmp)


@cli.command()
@click.option('-f', '--strategy-file', type=click.Path(exists=True), required=True)
@click.option('-s', '--start-date', type=Date(), required=True)
@click.option('-e', '--end-date', type=Date(), required=True)
@click.option('-o', '--output-file', type=click.Path(writable=True))
@click.option('-i', '--init-cash', default=100000, type=click.INT)
@click.option('--plot/--no-plot', default=os.name != "nt", help="plot result")
@click.option('--progress/--no-progress', default=True, help="show progress bar")
@click.option('-d', '--data-bundle-path', default=os.path.expanduser("~/.rqalpha"), type=click.Path())
def run(strategy_file, start_date, end_date, output_file, plot, data_bundle_path, init_cash, progress):
    '''run strategy from file
    '''
    if not os.path.exists(data_bundle_path):
        print_("data bundle not found. Run `%s update_bundle` to download data bundle." % sys.argv[0])
        return

    with codecs.open(strategy_file, encoding="utf-8") as f:
        source_code = f.read()

    results_df = run_strategy(source_code, strategy_file, start_date, end_date,
                              init_cash, data_bundle_path, progress)

    if output_file is not None:
        results_df.to_pickle(output_file)

    if plot:
        show_draw_result(strategy_file, results_df)


@cli.command()
@click.option('-d', '--directory', default="./", type=click.Path(), required=True)
def examples(directory):
    '''generate example strategies to target folder
    '''
    source_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "examples")

    try:
        shutil.copytree(source_dir, os.path.join(directory, "examples"))
    except OSError as e:
        if e.errno == errno.EEXIST:
            print_("Folder examples is exists.")


@cli.command()
@click.argument('result-file', type=click.Path(exists=True), required=True)
def plot(result_file):
    '''draw result DataFrame
    '''
    results_df = pd.read_pickle(result_file)
    show_draw_result(result_file, results_df)


@cli.command()
@click.argument('result', type=click.Path(exists=True), required=True)
@click.argument('csv-file', type=click.Path(), required=True)
@click.option('-d', '--data-bundle-path', default=os.path.expanduser("~/.rqalpha"), type=click.Path())
def report(result, csv_file, data_bundle_path):
    '''generate csv report from backtest output file
    '''
    result_df = pd.read_pickle(result)

    data_proxy = LocalDataProxy(data_bundle_path)

    csv_txt = StringIO()

    csv_txt.write("Trades\n")
    fieldnames = ['date', 'order_book_id', 'amount', 'price', "commission", "tax"]
    writer = csv.DictWriter(csv_txt, fieldnames=fieldnames)
    writer.writeheader()
    for dt, trades in result_df.trades.iteritems():
        for t in trades:
            trade = dict(t.__dict__)
            trade.pop("order_id")
            order_book_id = trade["order_book_id"]
            instrument = data_proxy.instrument(order_book_id)
            trade["order_book_id"] = "{}({})".format(order_book_id, instrument.symbol)
            trade["date"] = trade["date"].strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow(trade)

    csv_txt.write("\nPositions\n")
    fieldnames = ['date', 'order_book_id', 'market_value', 'quantity']
    writer = csv.DictWriter(csv_txt, fieldnames=fieldnames)
    writer.writeheader()
    for _dt, positions in result_df.positions.iteritems():
        dt = _dt.strftime("%Y-%m-%d %H:%M:%S")
        for order_book_id, position in iteritems(positions):
            instrument = data_proxy.instrument(order_book_id)
            writer.writerow({
                "date": dt,
                "order_book_id": "{}({})".format(order_book_id, instrument.symbol),
                "market_value": position.market_value,
                "quantity": position.quantity,
            })

    with open(csv_file, 'w') as csvfile:
        csvfile.write(csv_txt.getvalue())


def run_strategy(source_code, strategy_filename, start_date, end_date,
                 init_cash, data_bundle_path, show_progress):
    scope = {
        "logger": user_log,
        "print": user_print,
    }
    scope.update({export_name: getattr(api, export_name) for export_name in api.__all__})
    code = compile(source_code, strategy_filename, 'exec')
    exec_(code, scope)

    try:
        data_proxy = LocalDataProxy(data_bundle_path)
    except OSError as e:
        if e.errno == errno.EEXIST:
            print_("data bundle might crash. Run `%s update_bundle` to redownload data bundle." % sys.argv[0])
            sys.exit()

    # FIXME set end_date to latest data's date
    dates = data_proxy.last("000001.XSHG", end_date, 10, "1d", "date")
    end_date = min(convert_int_to_date(dates[-1]), end_date)

    trading_cal = data_proxy.get_trading_dates(start_date, end_date)
    Scheduler.set_trading_dates(data_proxy.get_trading_dates(start_date, end_date.date()))
    trading_params = TradingParams(trading_cal, start_date=start_date.date(), end_date=end_date.date(),
                                   init_cash=init_cash, show_progress=show_progress)

    executor = StrategyExecutor(
        init=scope.get("init", dummy_func),
        before_trading=scope.get("before_trading", dummy_func),
        handle_bar=scope.get("handle_bar", dummy_func),

        trading_params=trading_params,
        data_proxy=data_proxy,
    )

    results_df = executor.execute()

    return results_df


def show_draw_result(title, results_df):
    import matplotlib
    from matplotlib import gridspec
    import matplotlib.image as mpimg
    import matplotlib.pyplot as plt
    plt.style.use('ggplot')

    red = "#aa4643"
    blue = "#4572a7"
    black = "#000000"

    figsize = (18, 6)
    f = plt.figure(title, figsize=figsize)
    gs = gridspec.GridSpec(10, 8)

    # draw logo
    ax = plt.subplot(gs[:3, -1:])
    ax.axis("off")
    filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "resource")
    filename = os.path.join(filename, "ricequant-logo.png")
    img = mpimg.imread(filename)
    imgplot = ax.imshow(img, interpolation="nearest")
    ax.autoscale_view()

    # draw risk and portfolio
    series = results_df.iloc[-1]

    font_size = 12
    value_font_size = 11
    label_height, value_height = 0.8, 0.6
    label_height2, value_height2 = 0.35, 0.15

    fig_data = [
        (0.00, label_height, value_height, "Total Returns", "{0:.3%}".format(series.total_returns), red, black),
        (0.15, label_height, value_height, "Annual Returns", "{0:.3%}".format(series.annualized_returns), red, black),
        (0.00, label_height2, value_height2, "Benchmark Total", "{0:.3%}".format(series.benchmark_total_returns), blue, black),
        (0.15, label_height2, value_height2, "Benchmark Annual", "{0:.3%}".format(series.benchmark_annualized_returns), blue, black),

        (0.30, label_height, value_height, "Alpha", "{0:.4}".format(series.alpha), black, black),
        (0.40, label_height, value_height, "Beta", "{0:.4}".format(series.beta), black, black),
        (0.55, label_height, value_height, "Sharpe", "{0:.4}".format(series.sharpe), black, black),
        (0.70, label_height, value_height, "Sortino", "{0:.4}".format(series.sortino), black, black),
        (0.85, label_height, value_height, "Information Ratio", "{0:.4}".format(series.information_rate), black, black),

        (0.30, label_height2, value_height2, "Volatility", "{0:.4}".format(series.volatility), black, black),
        (0.40, label_height2, value_height2, "MaxDrawdown", "{0:.3%}".format(series.max_drawdown), black, black),
        (0.55, label_height2, value_height2, "Tracking Error", "{0:.4}".format(series.tracking_error), black, black),
        (0.70, label_height2, value_height2, "Downside Risk", "{0:.4}".format(series.downside_risk), black, black),
    ]

    ax = plt.subplot(gs[:3, :-1])
    ax.axis("off")
    for x, y1, y2, label, value, label_color, value_color in fig_data:
        ax.text(x, y1, label, color=label_color, fontsize=font_size)
        ax.text(x, y2, value, color=value_color, fontsize=value_font_size)

    # strategy vs benchmark
    ax = plt.subplot(gs[4:, :])

    ax.get_xaxis().set_minor_locator(matplotlib.ticker.AutoMinorLocator())
    ax.get_yaxis().set_minor_locator(matplotlib.ticker.AutoMinorLocator())
    ax.grid(b=True, which='minor', linewidth=.2)
    ax.grid(b=True, which='major', linewidth=1)

    ax.plot(results_df["benchmark_total_returns"], label="benchmark", alpha=1, linewidth=2, color=blue)
    ax.plot(results_df["total_returns"], label="strategy", alpha=1, linewidth=2, color=red)

    # manipulate
    vals = ax.get_yticks()
    ax.set_yticklabels(['{:3.2f}%'.format(x*100) for x in vals])

    leg = plt.legend(loc="upper left")
    leg.get_frame().set_alpha(0.5)

    plt.show()


if __name__ == '__main__':
    entry_point()
