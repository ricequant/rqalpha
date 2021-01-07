# -*- coding: utf-8 -*-
# 版权所有 2020 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），您可以在以下位置获得 Apache 2.0 许可的副本：
#         http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。
import os
import shutil
import tarfile
import tempfile
import time
import datetime
import dateutil
from six.moves.urllib.parse import urlparse

import click
import requests
import six

from rqalpha.utils.i18n import gettext as _

from rqalpha.cmds.entry import cli
from rqalpha.utils import init_rqdatac_env


@cli.command()
@click.option('-d', '--data-bundle-path', default=os.path.expanduser('~/.rqalpha'), type=click.Path(file_okay=False))
@click.option("rqdatac_uri", '--rqdatac', '--rqdatac-uri', default=None,
              help='rqdatac uri, eg user:password or tcp://user:password@ip:port')
@click.option('--compression', default=False, is_flag=True, help='enable compression to reduce file size')
@click.option('-c', '--concurrency', type=click.INT, default=1)
def create_bundle(data_bundle_path, rqdatac_uri, compression, concurrency):
    """create bundle using rqdatac"""
    try:
        import rqdatac
    except ImportError:
        click.echo(_(
            'rqdatac is required to create bundle. '
            'you can visit https://www.ricequant.com/welcome/rqdata to get rqdatac, '
            'or use "rqalpha download-bundle" to download monthly updated bundle.'
        ))
        return 1

    try:
        init_rqdatac_env(rqdatac_uri)
        rqdatac.init()
    except ValueError as e:
        click.echo(_('rqdatac init failed with error: {}').format(e))
        return 1

    os.makedirs(os.path.join(data_bundle_path, 'bundle'), exist_ok=True)
    from rqalpha.data.bundle import update_bundle as update_bundle_
    update_bundle_(os.path.join(data_bundle_path, 'bundle'), True, compression, concurrency)


@cli.command()
@click.option('-d', '--data-bundle-path', default=os.path.expanduser('~/.rqalpha'), type=click.Path(file_okay=False))
@click.option("rqdatac_uri", '--rqdatac', '--rqdatac-uri', default=None,
              help='rqdatac uri, eg user:password or tcp://user:password@ip:port')
@click.option('--compression', default=False, type=click.BOOL, help='enable compression to reduce file size')
@click.option('-c', '--concurrency', type=click.INT, default=1)
def update_bundle(data_bundle_path, rqdatac_uri, compression, concurrency):
    """update bundle using rqdatac"""
    try:
        import rqdatac
    except ImportError:
        click.echo(_(
            'rqdatac is required to update bundle. '
            'you can visit https://www.ricequant.com/welcome/rqdata to get rqdatac, '
            'or use "rqalpha download-bundle" to download monthly updated bundle.'
        ))
        return 1

    try:
        init_rqdatac_env(rqdatac_uri)
        rqdatac.init()
    except ValueError as e:
        click.echo(_('rqdatac init failed with error: {}').format(e))
        return 1

    if not os.path.exists(os.path.join(data_bundle_path, 'bundle')):
        click.echo(_('bundle not exist, use "rqalpha create-bundle" command instead'))
        return 1

    from rqalpha.data.bundle import update_bundle as update_bundle_
    update_bundle_(os.path.join(data_bundle_path, 'bundle'), False, compression, concurrency)


@cli.command()
@click.option('-d', '--data-bundle-path', default=os.path.expanduser('~/.rqalpha'), type=click.Path(file_okay=False))
@click.option('--confirm', default=True, is_flag=True)
def download_bundle(data_bundle_path, confirm):
    """download bundle (monthly updated)"""
    default_bundle_path = os.path.abspath(os.path.expanduser('~/.rqalpha/bundle'))
    if data_bundle_path is None:
        data_bundle_path = default_bundle_path
    else:
        data_bundle_path = os.path.abspath(os.path.join(data_bundle_path, './bundle/'))
    if (confirm and os.path.exists(data_bundle_path) and data_bundle_path != default_bundle_path and
            os.listdir(data_bundle_path)):
        click.confirm(_(u"""
    [WARNING]
    Target bundle path {data_bundle_path} is not empty.
    The content of this folder will be REMOVED before updating.
    Are you sure to continue?""").format(data_bundle_path=data_bundle_path), abort=True)

    tmp = os.path.join(tempfile.gettempdir(), 'rq.bundle')
    url, total_length = get_exactly_url()

    with open(tmp, 'wb') as out:
        download(out, total_length, url)

    shutil.rmtree(data_bundle_path, ignore_errors=True)
    os.makedirs(data_bundle_path)
    tar = tarfile.open(tmp, 'r:bz2')
    tar.extractall(data_bundle_path)
    tar.close()
    os.remove(tmp)
    six.print_(_(u"Data bundle download successfully in {bundle_path}").format(bundle_path=data_bundle_path))


CDN_URL = 'http://bundle.assets.ricequant.com/bundles_v4/rqbundle_%04d%02d.tar.bz2'


def get_exactly_url():
    day = datetime.date.today()
    proxy_uri = os.environ.get('RQALPHA_PROXY')
    while True:  # get exact url
        url = CDN_URL % (day.year, day.month)
        six.print_(_(u"try {} ...").format(url))
        r = requests.get(url, stream=True, proxies={'http': proxy_uri, 'https': proxy_uri})
        if r.status_code == 200:
            return url, int(r.headers.get('content-length'))

        day -= dateutil.relativedelta.relativedelta(months=1)


def download(out, total_length, url):
    retry_interval = 3
    retry_times = 5
    proxy_uri = os.environ.get('RQALPHA_PROXY')
    with click.progressbar(length=total_length, label=_(u"downloading ...")) as bar:
        for i in range(retry_times):
            try:
                headers = {'Range': "bytes={}-".format(bar.pos)}
                r = requests.get(url, headers=headers, stream=True, timeout=10, proxies={'http': proxy_uri,
                                                                                         'https': proxy_uri})
                for data in r.iter_content(chunk_size=8192):
                    bar.update(len(data))
                    out.write(data)

                if total_length == bar.pos:
                    return True  # Download complete . exit
            except requests.exceptions.RequestException:
                if i < retry_times - 1:
                    six.print_(_("\nDownload failed, retry in {} seconds.".format(retry_interval)))
                    time.sleep(retry_interval)
                else:
                    raise
