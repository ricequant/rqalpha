import pickle

import h5py
import numpy as np
import pandas as pd
import pytest

from rqalpha.data.bundle import daybar_checker
from rqalpha.utils.datetime_func import convert_date_to_date_int, convert_date_to_int


@pytest.fixture(autouse=True)
def identity_gettext(monkeypatch):
    monkeypatch.setattr(daybar_checker, "_", lambda message: message)


def _date_int(date):
    return convert_date_to_date_int(pd.Timestamp(date))


def _datetime_int(date):
    return convert_date_to_int(pd.Timestamp(date))


def _instrument(order_book_id, listed_date="2020-01-02", de_listed_date="0000-00-00"):
    return {
        "order_book_id": order_book_id,
        "listed_date": listed_date,
        "de_listed_date": de_listed_date,
    }


def _daybar_array(dates):
    return np.array(
        [(_datetime_int(date),) for date in dates],
        dtype=[("datetime", "i8")],
    )


def _write_h5(base_path, file_name, datasets):
    with h5py.File(str(base_path / file_name), "w") as h5:
        for order_book_id, dates in datasets.items():
            if dates == "missing_datetime":
                h5.create_dataset(order_book_id, data=np.array([(1.0,)], dtype=[("open", "f8")]))
            elif dates == "empty":
                h5.create_dataset(order_book_id, data=np.array([], dtype=[("datetime", "i8")]))
            else:
                h5.create_dataset(order_book_id, data=_daybar_array(dates))


def _write_base_bundle(tmp_path, instruments, daybar_datasets, trading_dates=None):
    base_path = tmp_path / "bundle"
    base_path.mkdir()

    if trading_dates is None:
        trading_dates = ["2020-01-02", "2020-01-03", "2020-01-06"]
    np.save(str(base_path / "trading_dates.npy"), np.array([_date_int(d) for d in trading_dates], dtype=np.int64))

    with open(str(base_path / "instruments.pk"), "wb") as f:
        pickle.dump(instruments, f)

    for file_name in daybar_checker.DAYBAR_FILE_LIST:
        _write_h5(base_path, file_name, daybar_datasets.get(file_name, {}))
    return base_path


def _valid_instruments():
    return [
        _instrument("000001.XSHE"),
        _instrument("000300.XSHG"),
        _instrument("IF2001"),
        _instrument("510050.XSHG"),
    ]


def _valid_daybar_datasets():
    dates = ["2020-01-02", "2020-01-03", "2020-01-06"]
    return {
        "stocks.h5": {"000001.XSHE": dates},
        "indexes.h5": {"000300.XSHG": dates},
        "futures.h5": {"IF2001": dates},
        "funds.h5": {"510050.XSHG": dates},
    }


def test_check_daybar_reports_missing_bundle_directory(tmp_path, capsys):
    daybar_checker.check_daybar(str(tmp_path))

    output = capsys.readouterr().out
    assert "Directory not found:" in output
    assert str(tmp_path / "bundle") in output


def test_check_daybar_reports_missing_base_files(tmp_path, capsys):
    (tmp_path / "bundle").mkdir()

    daybar_checker.check_daybar(str(tmp_path))

    output = capsys.readouterr().out
    assert "trading_dates.npy or instruments.pk is missing" in output
    assert str(tmp_path / "bundle") in output


def test_check_daybar_reports_missing_daybar_files(tmp_path, capsys):
    base_path = tmp_path / "bundle"
    base_path.mkdir()
    np.save(str(base_path / "trading_dates.npy"), np.array([_date_int("2020-01-02")], dtype=np.int64))
    with open(str(base_path / "instruments.pk"), "wb") as f:
        pickle.dump([_instrument("000001.XSHE")], f)

    daybar_checker.check_daybar(str(tmp_path))

    output = capsys.readouterr().out
    assert "Missing files in directory" in output
    assert "stocks.h5,indexes.h5,futures.h5,funds.h5" in output


def test_check_daybar_reports_good_bundle(tmp_path, capsys):
    _write_base_bundle(tmp_path, _valid_instruments(), _valid_daybar_datasets())

    daybar_checker.check_daybar(str(tmp_path))

    output = capsys.readouterr().out
    assert output == "Detection complete: daybar data quality is good!\n"


def test_check_daybar_reports_missing_dates_and_unknown_order_book_ids(tmp_path, capsys):
    datasets = _valid_daybar_datasets()
    datasets["stocks.h5"] = {
        "000001.XSHE": ["2020-01-02", "2020-01-06"],
        "UNKNOWN.XSHE": ["2020-01-02", "2020-01-03", "2020-01-06"],
    }
    _write_base_bundle(tmp_path, _valid_instruments(), datasets)

    daybar_checker.check_daybar(str(tmp_path))

    output = capsys.readouterr().out
    assert "Detection complete: a total of 1 files have issues" in output
    assert "stocks.h5(total of 2 anomaly):" in output
    assert "000001.XSHE" in output
    assert "UNKNOWN.XSHE" in output


def test_check_daybar_accepts_future_continuous_contract_starting_after_listed_date(tmp_path, capsys):
    instruments = [
        _instrument("000001.XSHE"),
        _instrument("000300.XSHG"),
        _instrument("IF888"),
        _instrument("510050.XSHG"),
    ]
    datasets = _valid_daybar_datasets()
    datasets["futures.h5"] = {
        "IF888": ["2020-01-03", "2020-01-06"],
    }
    _write_base_bundle(tmp_path, instruments, datasets)

    daybar_checker.check_daybar(str(tmp_path))

    output = capsys.readouterr().out
    assert output == "Detection complete: daybar data quality is good!\n"


def test_check_daybar_reports_file_without_valid_dataset(tmp_path, capsys):
    datasets = _valid_daybar_datasets()
    datasets["stocks.h5"] = {
        "000001.XSHE": "missing_datetime",
        "000002.XSHE": "empty",
    }
    _write_base_bundle(tmp_path, _valid_instruments(), datasets)

    daybar_checker.check_daybar(str(tmp_path))

    output = capsys.readouterr().out
    assert "Detection complete: a total of 1 files have issues" in output
    assert "does not contain any valid dataset" in output
    assert "stocks.h5" in output
