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
import os
import shutil
import tarfile
import tempfile
import time
import datetime

import click
import requests
import six

from rqalpha.utils.config import set_locale
from rqalpha.utils.i18n import gettext as _

CDN_URL = 'http://bundle.assets.ricequant.com/bundles_v3/rqbundle_%04d%02d%02d.tar.bz2'


def get_exactly_url():
    day = datetime.date.today()
    while True:  # get exactly url
        url = CDN_URL % (day.year, day.month, day.day)
        six.print_(_(u"try {} ...").format(url))
        r = requests.get(url, stream=True)
        if r.status_code != 200:
            day = day - datetime.timedelta(days=1)
            continue
        break
    total_length = int(r.headers.get('content-length'))
    return url, total_length


def download(out, total_length, url):
    retry_interval = 3
    retry_times = 5
    with click.progressbar(length=total_length, label=_(u"downloading ...")) as bar:
        for i in range(retry_times):
            try:
                headers = {'Range': "bytes={}-".format(bar.pos), }
                r = requests.get(url, headers=headers, stream=True, timeout=10)
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


def update_bundle(data_bundle_path=None, locale="zh_Hans_CN", confirm=True):
    set_locale(locale)
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
