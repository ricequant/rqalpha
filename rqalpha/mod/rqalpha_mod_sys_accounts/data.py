# -*- coding: utf-8 -*-
# 版权所有 2020 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），
#         您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、
#         本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，
#         否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。

import os
import json
import codecs
from datetime import date
from typing import Tuple, Optional, Sequence, Set, List

from h5py import File

from rqalpha.environment import Environment
from rqalpha.utils import open_h5
from rqalpha.utils.typing import DateLike
from rqalpha.utils.datetime_func import convert_date_to_date_int
from rqalpha.utils.functools import lru_cache


@lru_cache(None)
def _all_share_transformations():
    bundle_path = Environment.get_instance().config.base.data_bundle_path
    with codecs.open(os.path.join(bundle_path, "share_transformation.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def get_share_transformation(order_book_id):
    # type: (str) -> Optional[Tuple[str, float]]
    """
    获取股票转换信息
    :param order_book_id: 合约代码
    :return: (successor, conversion_ratio), (转换后的合约代码，换股倍率)
    """
    try:
        transformation_data = _all_share_transformations()[order_book_id]
    except KeyError:
        return
    return transformation_data["successor"], transformation_data["share_conversion_ratio"]


@lru_cache(None)
def _st_stock_file():
    # type: () -> File
    bundle_path = Environment.get_instance().config.base.data_bundle_path
    return open_h5(os.path.join(bundle_path, "st_stock_days.h5"), mode="r")


@lru_cache(2048)
def get_st_stock_days(order_book_id):
    # type: (str) -> Set
    try:
        days = _st_stock_file()[order_book_id][:]
    except KeyError:
        return set()
    else:
        return set(days.tolist())


def is_st_stock(order_book_id, dates):
    # type: (str, Sequence[DateLike]) -> List[bool]
    date_set = get_st_stock_days(order_book_id)
    if not date_set:
        return [False] * len(dates)
    return [convert_date_to_date_int(d) in date_set for d in dates]
