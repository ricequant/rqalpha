import pytest
import os
import shutil
from tempfile import TemporaryDirectory

from rqalpha.utils.testing.integration import assert_result
from rqalpha import run_func


@pytest.fixture
def result_file(request, testcase_name):
    return os.path.join(os.path.dirname(request.path), "outs", f"{testcase_name}.txt")


@pytest.fixture
def future_info_file():
    return os.path.join(os.path.dirname(__file__), "resources", "future_info.json")


@pytest.fixture
def run_and_assert_result(result_file, future_info_file):
    def _do(reload_futures_info=False, **kwargs):
        if reload_futures_info:
            conf = kwargs.get("config") or {}
            base = conf.get("base") or {}
            bundle_path = base.get("data_bundle_path") or os.path.join(os.path.expanduser("~/.rqalpha"), "bundle")
            with TemporaryDirectory() as tmp_bundle:
                for f in os.listdir(bundle_path):
                    src = os.path.join(bundle_path, f)
                    if not f.startswith(".") and os.path.isfile(src) and f != "future_info.json":
                        shutil.copy2(src, os.path.join(tmp_bundle, f))
                shutil.copy2(future_info_file, os.path.join(tmp_bundle, "future_info.json"))
                base["data_bundle_path"] = tmp_bundle
                conf["base"] = base
                kwargs["config"] = conf
                result = run_func(**kwargs) 
        else:
            result = run_func(**kwargs)
        assert_result(result, result_file)
    return _do


@pytest.fixture
def resources_path(testcase_name):
    return os.path.join(os.path.dirname(__file__), "resources", testcase_name)