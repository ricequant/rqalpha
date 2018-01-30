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

import click
from rqalpha import cli
from rqalpha.data.base_data_source import BaseDataSource
from rqalpha.utils.config import parse_config
from rqalpha.utils.logger import system_log


cli_prefix = "mod__sys_stock_realtime__"

__config__ = {
    "priority": 200,
    "persist_path": "./persist/strategy/",
    "fps": 3,
    "redis_uri": None,
}


cli.commands['run'].params.append(
    click.Option(
        ('--redis-uri', cli_prefix + 'redis_uri'),
        type=click.STRING,
        help="[sys_stock_realtime] market data redis uri",
    )
)


@cli.command()
@click.argument('redis_url', required=True)
def quotation_server(redis_url):
    """
    [sys_stock_realtime] quotation service, download market data into redis

    Multiple RQAlpha instance can use single market data service.
    """
    import redis
    import time
    import json

    from .utils import get_realtime_quotes

    redis_client = redis.from_url(redis_url)

    from rqalpha.data.data_proxy import DataProxy
    # 通过 parse_config 函数 获取 默认 data_bundle 的配置
    # 由于 parse_config 会进行配置检查，如果没有设置 account 会提示报错，因此随意设置一个股票初始资金，来保证正确获取默认参数配置
    config = parse_config({
        'base': {
            'accounts': {
                'stock': 10000
            }
        }
    })

    data_source = BaseDataSource(config.base.data_bundle_path)
    data_proxy = DataProxy(data_source)

    order_book_id_list = sorted(ins.order_book_id for ins in data_proxy.all_instruments("CS"))

    def record_market_data(total_df):
        for order_book_id, item in total_df.iterrows():
            redis_client[order_book_id] = json.dumps(item.to_dict())

    retry_cnt = 0
    while True:
        try:
            total_df = get_realtime_quotes(order_book_id_list, include_limit=True)
        except (OSError, IOError) as e:
            system_log.exception("get_realtime_quotes socket error. retry {} {}", retry_cnt, e)
            time.sleep(retry_cnt * 2)
            retry_cnt += 1
            continue
        system_log.info("Fetching snapshots, size {}", len(total_df))
        record_market_data(total_df)
        time.sleep(1)
        retry_cnt = 0


def load_mod():
    from .mod import RealtimeTradeMod
    return RealtimeTradeMod()
