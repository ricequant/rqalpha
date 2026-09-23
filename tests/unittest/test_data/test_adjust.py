# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。

import datetime

import numpy as np
import pytest

from rqalpha.data.base_data_source.adjust import adjust_bars, adjust_rate, factor_for_date


EX_FACTOR_DTYPE = np.dtype([("start_date", "u8"), ("ex_cum_factor", "f8")])
BAR_DTYPE = np.dtype([
    ("datetime", "u8"), ("open", "f8"), ("high", "f8"), ("low", "f8"),
    ("close", "f8"), ("volume", "f8"), ("total_turnover", "f8"),
])


def date_int(date_str):
    """'2021-06-01' -> 20210601000000（与 bar 的 datetime 编码一致）"""
    return np.uint64(int(date_str.replace("-", "")) * 10 ** 6)


# 与 get_ex_cum_factor 的输出一致：首行为 (0, 1.0)，其后是各除权日的累计因子
EX_FACTORS = np.array([
    (0, 1.),
    (date_int("2021-06-01"), 1.1),
    (date_int("2021-10-08"), 1.3),
], dtype=EX_FACTOR_DTYPE)

BAR_DATES = [datetime.date(2021, 5, 6), datetime.date(2021, 6, 1), datetime.date(2021, 6, 2)]
# (datetime, open, high, low, close, volume, total_turnover)
BARS = np.array([
    (date_int("2021-05-06"), 9.9, 10.5, 9.8, 10., 1000., 10000.),
    (date_int("2021-06-01"), 10.9, 11.5, 10.8, 11., 2000., 22000.),
    (date_int("2021-06-02"), 11.9, 12.5, 11.8, 12., 3000., 36000.),
], dtype=BAR_DTYPE)


def test_factor_for_date():
    assert factor_for_date(EX_FACTORS, datetime.date(2021, 5, 31)) == 1.
    # 除权日当天起用新的累计因子；因子表末尾之后沿用最后一个因子
    assert factor_for_date(EX_FACTORS, datetime.date(2021, 6, 1)) == pytest.approx(1.1)
    assert factor_for_date(EX_FACTORS, datetime.date(2021, 10, 9)) == pytest.approx(1.3)
    # 只取日期部分：datetime 与 bar 的 uint64 时间戳都接受
    assert factor_for_date(EX_FACTORS, datetime.datetime(2021, 6, 1, 9, 31)) == pytest.approx(1.1)
    assert factor_for_date(EX_FACTORS, np.uint64(20210601103000)) == pytest.approx(1.1)
    # 没有因子表时不复权
    assert factor_for_date(None, datetime.date(2021, 6, 1)) == 1.
    assert factor_for_date(np.array([], dtype=EX_FACTOR_DTYPE), datetime.date(2021, 6, 1)) == 1.


def test_adjust_rate():
    # 没有因子表，或 adjust_type 为 none 时不复权
    assert adjust_rate(EX_FACTORS, datetime.date(2021, 6, 1), "none", datetime.date(2021, 5, 6)) == 1.
    assert adjust_rate(None, datetime.date(2021, 6, 1), "pre", datetime.date(2021, 5, 6)) == 1.
    # post 以 1 为基准，pre 以 adjust_orig 为基准
    assert adjust_rate(EX_FACTORS, datetime.date(2021, 10, 11), "post", None) == pytest.approx(1.3)
    adjust_orig = datetime.date(2021, 6, 2)
    assert adjust_rate(EX_FACTORS, adjust_orig, "pre", adjust_orig) == pytest.approx(1.)
    assert adjust_rate(EX_FACTORS, datetime.date(2021, 5, 6), "pre", adjust_orig) == pytest.approx(1. / 1.1)


@pytest.mark.parametrize("adjust_type,adjust_orig", [("pre", datetime.date(2021, 6, 2)), ("post", None)])
def test_adjust_rate_matches_adjust_bars(adjust_type, adjust_orig):
    """数据源在 history_bars 之外拼接数据，依赖「adjust_rate 与 adjust_bars 口径一致」这一契约"""
    for i, bar_date in enumerate(BAR_DATES):
        rate = adjust_rate(EX_FACTORS, bar_date, adjust_type, adjust_orig)
        adjusted = adjust_bars(BARS[i:i + 1], EX_FACTORS, ["close", "volume"], adjust_type, adjust_orig)
        assert adjusted[0]["close"] == pytest.approx(BARS[i]["close"] * rate)
        assert adjusted[0]["volume"] == pytest.approx(BARS[i]["volume"] / rate)


def test_adjust_bars_pre():
    raw = BARS.copy()
    # 以 2021-06-02 为复权起点：价格等比缩放，成交量反向缩放，入参不被修改
    adjusted = adjust_bars(raw, EX_FACTORS, None, "pre", datetime.date(2021, 6, 2))
    assert [float(x) for x in adjusted["close"]] == pytest.approx([10. / 1.1, 11., 12.])
    assert [float(x) for x in adjusted["volume"]] == pytest.approx([1000. * 1.1, 2000., 3000.])
    assert np.array_equal(raw, BARS)

    # 跨除权日：除权日当天的那根 bar 用新的累计因子
    adjusted = adjust_bars(BARS[:2], EX_FACTORS, None, "pre", BAR_DATES[0])
    assert [float(x) for x in adjusted["close"]] == pytest.approx([10., 11. * 1.1])


def test_adjust_bars_post():
    adjusted = adjust_bars(BARS, EX_FACTORS, None, "post", None)
    assert [float(x) for x in adjusted["close"]] == pytest.approx([10., 11. * 1.1, 12. * 1.1])
    assert [float(x) for x in adjusted["volume"]] == pytest.approx([1000., 2000. / 1.1, 3000. / 1.1])

    # 区间内因子没有变化时，价格量都不变
    assert np.array_equal(adjust_bars(BARS[:1], EX_FACTORS, None, "post", None), BARS[:1])


def test_adjust_bars_fields_and_no_factors():
    # fields 为 str 时只调整该字段
    adjusted = adjust_bars(BARS, EX_FACTORS, "close", "post", None)
    assert [float(x) for x in adjusted["close"]] == pytest.approx([10., 11. * 1.1, 12. * 1.1])
    assert np.array_equal(adjusted["volume"], BARS["volume"])
    assert np.array_equal(adjusted["open"], BARS["open"])

    adjusted = adjust_bars(BARS, EX_FACTORS, "volume", "post", None)
    assert [float(x) for x in adjusted["volume"]] == pytest.approx([1000., 2000. / 1.1, 3000. / 1.1])
    assert np.array_equal(adjusted["close"], BARS["close"])

    # fields 为 list/None 时，不需要复权的字段保持原值
    for fields in (None, ["close", "volume", "total_turnover"]):
        adjusted = adjust_bars(BARS, EX_FACTORS, fields, "post", None)
        assert np.array_equal(adjusted["total_turnover"], BARS["total_turnover"])
        assert np.array_equal(adjusted["datetime"], BARS["datetime"])

    # 没有因子表、或 bars 为空时原样返回
    assert adjust_bars(BARS, None, None, "pre", BAR_DATES[0]) is BARS
    empty = BARS[0:0]
    assert adjust_bars(empty, EX_FACTORS, None, "pre", BAR_DATES[0]) is empty
