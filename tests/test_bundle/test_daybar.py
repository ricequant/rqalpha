import datetime
from types import SimpleNamespace

import h5py
import numpy as np
import pandas as pd

from rqalpha.data.bundle import daybar
from rqalpha.utils.datetime_func import convert_date_to_int


def _instrument(order_book_id, de_listed_date="0000-00-00"):
    return SimpleNamespace(order_book_id=order_book_id, de_listed_date=de_listed_date)


def _as_date(value):
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    return pd.Timestamp(value).date()


def _price_frame(rows):
    df = pd.DataFrame.from_records(
        [
            {
                "order_book_id": order_book_id,
                "date": pd.Timestamp(date),
                **values,
            }
            for order_book_id, date, values in rows
        ]
    )
    return df.set_index(["order_book_id", "date"]).sort_index()


def _bar_array(rows):
    return np.array(
        [
            (convert_date_to_int(pd.Timestamp(date)), open_, close_)
            for date, open_, close_ in rows
        ],
        dtype=[("datetime", "i8"), ("open", "f8"), ("close", "f8")],
    )


def _write_bars(file_path, order_book_id, rows):
    with h5py.File(str(file_path), "w") as h5:
        h5.create_dataset(order_book_id, data=_bar_array(rows))


class FakeRqdatac(object):
    def __init__(self, instruments, price_frames=None):
        self._instruments = instruments
        self._price_frames = list(price_frames or [])
        self.get_price_calls = []
        self.instruments_calls = []
        self.get_previous_trading_date_calls = []
        self.get_next_trading_date_calls = []
        self.is_trading_date_calls = []

    def instruments(self, order_book_ids, market=None):
        self.instruments_calls.append(
            {
                "order_book_ids": order_book_ids,
                "market": market,
            }
        )
        if isinstance(order_book_ids, str):
            order_book_ids = [order_book_ids]

        result = []
        for order_book_id in order_book_ids:
            instruments = self._instruments[order_book_id]
            if isinstance(instruments, list):
                result.extend(instruments)
            else:
                result.append(instruments)
        return result

    def get_price(self, order_book_ids, start_date, end_date, frequency, **kwargs):
        self.get_price_calls.append(
            {
                "order_book_ids": order_book_ids,
                "start_date": start_date,
                "end_date": end_date,
                "frequency": frequency,
                "kwargs": kwargs,
            }
        )
        if self._price_frames:
            return self._price_frames.pop(0)
        return pd.DataFrame()

    def get_previous_trading_date(self, trading_date):
        self.get_previous_trading_date_calls.append(trading_date)
        return _as_date(trading_date) - datetime.timedelta(days=1)

    def get_next_trading_date(self, trading_date):
        self.get_next_trading_date_calls.append(trading_date)
        return _as_date(trading_date) + datetime.timedelta(days=1)

    def is_trading_date(self, trading_date):
        self.is_trading_date_calls.append(trading_date)
        return True


def test_generate_daybar_task_writes_transformed_datasets(monkeypatch, tmp_path):
    file_path = tmp_path / "stocks.h5"
    fake_rqdatac = FakeRqdatac(
        {
            "000001.XSHE": _instrument("000001.XSHE"),
            "000002.XSHE": _instrument("000002.XSHE"),
        },
        [
            _price_frame(
                [
                    ("000001.XSHE", "2020-01-02", {"open": 10.0, "close": 11.0, "volume": 100.0}),
                    ("000001.XSHE", "2020-01-03", {"open": 12.0, "close": 13.0, "volume": 200.0}),
                    ("000002.XSHE", "2020-01-02", {"open": 20.0, "close": 21.0, "volume": 300.0}),
                ]
            )
        ],
    )
    monkeypatch.setattr(daybar, "rqdatac", fake_rqdatac)

    task = daybar.GenerateDayBarTask(
        ["000001.XSHE", "000002.XSHE"],
        str(file_path),
        ["open", "close"],
    )

    assert task.total_steps == 2
    assert list(task()) == [2]

    assert fake_rqdatac.get_price_calls == [
        {
            "order_book_ids": ["000001.XSHE", "000002.XSHE"],
            "start_date": daybar.START_DATE,
            "end_date": daybar.END_DATE,
            "frequency": "1d",
            "kwargs": {
                "adjust_type": "none",
                "fields": ["open", "close"],
                "expect_df": True,
                "market": "cn",
            },
        }
    ]

    with h5py.File(str(file_path), "r") as h5:
        assert sorted(h5.keys()) == ["000001.XSHE", "000002.XSHE"]

        stock_data = h5["000001.XSHE"][:]
        assert stock_data.dtype.names == ("datetime", "open", "close")
        assert stock_data["datetime"].tolist() == [
            convert_date_to_int(pd.Timestamp("2020-01-02")),
            convert_date_to_int(pd.Timestamp("2020-01-03")),
        ]
        assert stock_data["open"].tolist() == [10.0, 12.0]
        assert stock_data["close"].tolist() == [11.0, 13.0]

        another_stock_data = h5["000002.XSHE"][:]
        assert another_stock_data.dtype.names == ("datetime", "open", "close")
        assert another_stock_data["open"].tolist() == [20.0]


def test_update_daybar_task_recreates_file_when_existing_fields_do_not_match(monkeypatch, tmp_path):
    file_path = tmp_path / "stocks.h5"
    with h5py.File(str(file_path), "w") as h5:
        h5.create_dataset(
            "000001.XSHE",
            data=np.array(
                [(convert_date_to_int(pd.Timestamp("2020-01-02")), 10.0)],
                dtype=[("datetime", "i8"), ("open", "f8")],
            ),
        )

    fake_rqdatac = FakeRqdatac(
        {"000001.XSHE": _instrument("000001.XSHE")},
        [
            _price_frame(
                [
                    ("000001.XSHE", "2020-01-03", {"open": 12.0, "close": 13.0}),
                ]
            )
        ],
    )
    monkeypatch.setattr(daybar, "rqdatac", fake_rqdatac)

    task = daybar.UpdateDayBarTask(["000001.XSHE"], str(file_path), ["open", "close"])

    assert list(task()) == [1]
    assert fake_rqdatac.get_price_calls[0]["start_date"] == daybar.START_DATE

    with h5py.File(str(file_path), "r") as h5:
        data = h5["000001.XSHE"][:]
        assert data.dtype.names == ("datetime", "open", "close")
        assert data["datetime"].tolist() == [convert_date_to_int(pd.Timestamp("2020-01-03"))]
        assert data["open"].tolist() == [12.0]
        assert data["close"].tolist() == [13.0]


def test_update_daybar_task_appends_incremental_rows(monkeypatch, tmp_path):
    file_path = tmp_path / "stocks.h5"
    _write_bars(file_path, "000001.XSHE", [("2020-01-02", 10.0, 11.0)])

    fake_rqdatac = FakeRqdatac(
        {"000001.XSHE": _instrument("000001.XSHE")},
        [
            _price_frame(
                [
                    ("000001.XSHE", "2020-01-02", {"open": 90.0, "close": 91.0}),
                    ("000001.XSHE", "2020-01-03", {"open": 12.0, "close": 13.0}),
                ]
            )
        ],
    )
    monkeypatch.setattr(daybar, "rqdatac", fake_rqdatac)

    task = daybar.UpdateDayBarTask(["000001.XSHE"], str(file_path), ["open", "close"])

    assert list(task()) == [1]
    assert fake_rqdatac.get_price_calls[0]["start_date"] == datetime.date(2020, 1, 3)

    with h5py.File(str(file_path), "r") as h5:
        data = h5["000001.XSHE"][:]
        assert data["datetime"].tolist() == [
            convert_date_to_int(pd.Timestamp("2020-01-02")),
            convert_date_to_int(pd.Timestamp("2020-01-03")),
        ]
        assert data["open"].tolist() == [10.0, 12.0]
        assert data["close"].tolist() == [11.0, 13.0]


def test_update_daybar_task_skips_delisted_instrument_when_already_complete(monkeypatch, tmp_path):
    file_path = tmp_path / "stocks.h5"
    _write_bars(file_path, "000001.XSHE", [("2020-01-02", 10.0, 11.0)])

    fake_rqdatac = FakeRqdatac(
        {"000001.XSHE": _instrument("000001.XSHE", "2020-01-03")},
    )
    monkeypatch.setattr(daybar, "rqdatac", fake_rqdatac)

    task = daybar.UpdateDayBarTask(["000001.XSHE"], str(file_path), ["open", "close"])

    assert list(task()) == [1]
    assert fake_rqdatac.get_price_calls == []

    with h5py.File(str(file_path), "r") as h5:
        data = h5["000001.XSHE"][:]
        assert data["datetime"].tolist() == [convert_date_to_int(pd.Timestamp("2020-01-02"))]
        assert data["open"].tolist() == [10.0]
        assert data["close"].tolist() == [11.0]


def test_get_de_listed_date_prefers_active_reused_instrument(monkeypatch, tmp_path):
    fake_rqdatac = FakeRqdatac(
        {
            "000001.XSHE": [
                _instrument("000001.XSHE", "2018-01-01"),
                _instrument("000001.XSHE", "0000-00-00"),
            ],
            "000002.XSHE": [
                _instrument("000002.XSHE", "2018-01-01"),
                _instrument("000002.XSHE", "2020-01-01"),
            ],
        }
    )
    monkeypatch.setattr(daybar, "rqdatac", fake_rqdatac)

    task = daybar.UpdateDayBarTask(
        ["000001.XSHE", "000002.XSHE"],
        str(tmp_path / "stocks.h5"),
        ["open", "close"],
    )

    assert task._get_de_listed_date("000001.XSHE") == "0000-00-00"
    assert task._get_de_listed_date("000002.XSHE") == "2020-01-01"
