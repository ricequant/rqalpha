import os
import pickle
import time
from types import SimpleNamespace

import pytest

from rqalpha.data import bundle


def test_write_instruments_removes_expired_temp_files_before_writing(
    monkeypatch, tmp_path
):
    stale_tmp_path = tmp_path / "instruments.pk.tmp.previous"
    another_stale_tmp_path = tmp_path / "instruments.pk.tmp.interrupted"
    recent_tmp_path = tmp_path / "instruments.pk.tmp.current"
    unrelated_tmp_path = tmp_path / "other.pk.tmp.previous"
    for path in (stale_tmp_path, another_stale_tmp_path, recent_tmp_path, unrelated_tmp_path):
        path.write_bytes(b"tmp")

    stale_time = time.time() - 2 * 24 * 60 * 60
    os.utime(str(stale_tmp_path), (stale_time, stale_time))
    os.utime(str(another_stale_tmp_path), (stale_time, stale_time))
    os.utime(str(unrelated_tmp_path), (stale_time, stale_time))

    original_dump = bundle.pickle.dump

    def checked_dump(*args, **kwargs):
        assert not stale_tmp_path.exists()
        assert not another_stale_tmp_path.exists()
        assert recent_tmp_path.exists()
        assert unrelated_tmp_path.exists()
        return original_dump(*args, **kwargs)

    monkeypatch.setattr(bundle.pickle, "dump", checked_dump)

    instrument = SimpleNamespace(order_book_id="000001.XSHE")
    bundle.write_instruments(str(tmp_path), [instrument])

    assert not stale_tmp_path.exists()
    assert not another_stale_tmp_path.exists()
    assert recent_tmp_path.exists()
    assert unrelated_tmp_path.exists()
    with open(str(tmp_path / "instruments.pk"), "rb") as input_file:
        assert pickle.load(input_file) == [instrument.__dict__]


@pytest.mark.parametrize("instruments", [None, []])
def test_write_instruments_rejects_empty_instruments(tmp_path, instruments):
    with pytest.raises(RuntimeError, match="Invalid instruments list!"):
        bundle.write_instruments(str(tmp_path), instruments)

    assert not list(tmp_path.iterdir())


def test_write_instruments_removes_temp_file_when_serialization_fails(monkeypatch, tmp_path):
    target_path = tmp_path / "instruments.pk"
    target_path.write_bytes(b"previous instruments")

    def raise_serialization_error(*args, **kwargs):
        raise ValueError("serialization failed")

    monkeypatch.setattr(bundle.pickle, "dump", raise_serialization_error)

    with pytest.raises(ValueError, match="serialization failed"):
        bundle.write_instruments(
            str(tmp_path), [SimpleNamespace(order_book_id="000001.XSHE")]
        )

    assert target_path.read_bytes() == b"previous instruments"
    assert not list(tmp_path.glob("instruments.pk.tmp.*"))


def test_write_instruments_removes_temp_file_when_replace_fails(monkeypatch, tmp_path):
    target_path = tmp_path / "instruments.pk"
    target_path.write_bytes(b"previous instruments")

    def raise_replace_error(*args, **kwargs):
        raise OSError("replace failed")

    monkeypatch.setattr(bundle.os, "replace", raise_replace_error)

    with pytest.raises(OSError, match="replace failed"):
        bundle.write_instruments(
            str(tmp_path), [SimpleNamespace(order_book_id="000001.XSHE")]
        )

    assert target_path.read_bytes() == b"previous instruments"
    assert not list(tmp_path.glob("instruments.pk.tmp.*"))
