import pytest
import os
import shutil
from tempfile import TemporaryDirectory

from rqalpha.utils.testing.integration import assert_result
from rqalpha import run_func


@pytest.fixture
def result_file(request, testcase_name):
    return os.path.join(os.path.dirname(request.path), "outs", f"{testcase_name}.txt")


@pytest.fixture(scope="session")
def bundle_path():
    with TemporaryDirectory() as tmp_bundle:
        bundle = os.path.join(os.path.expanduser("~/.rqalpha"), "bundle")
        for f in os.listdir(bundle):
            src = os.path.join(bundle, f)
            if not f.startswith(".") and os.path.isfile(src) and f != "future_info.json":
                os.symlink(src, os.path.join(tmp_bundle, f))
        future_info_file = os.path.join(os.path.dirname(__file__), "resources", "future_info.json")
        os.symlink(future_info_file, os.path.join(tmp_bundle, "future_info.json"))
        yield tmp_bundle


@pytest.fixture
def run_and_assert_result(result_file, bundle_path):
    def _do(**kwargs):
        conf = kwargs.get("config") or {}
        base = conf.get("base") or {}
        base["data_bundle_path"] = bundle_path
        conf["base"] = base
        kwargs["config"] = conf
        result = run_func(**kwargs)
        assert_result(result, result_file)
    return _do


@pytest.fixture
def resources_path(testcase_name):
    return os.path.join(os.path.dirname(__file__), "resources", testcase_name)