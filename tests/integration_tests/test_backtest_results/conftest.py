import pytest
import os

from rqalpha.utils.testing.integration import assert_result
from rqalpha import run_func


@pytest.fixture
def result_file(request, testcase_name):
    return os.path.join(os.path.dirname(request.path), "outs", f"{testcase_name}.txt")


@pytest.fixture
def run_and_assert_result(result_file):
    def _do(**kwargs):
        result = run_func(**kwargs)
        assert_result(result, result_file)
    return _do


@pytest.fixture
def resources_path(testcase_name):
    return os.path.join(os.path.dirname(__file__), "resources", testcase_name)
    