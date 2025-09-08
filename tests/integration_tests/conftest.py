import pytest
import os


@pytest.fixture
def testcase_name(request):
    if isinstance(request.node.parent, pytest.Class):
        casename = f"{request.node.parent.name}#{request.node.name}"
    else:
        casename = request.node.name

    return f"{os.path.split(request.path)[-1][:-3]}#{casename}"  # type: ignore


@pytest.fixture
def result_file(request, testcase_name):
    return os.path.join(os.path.dirname(request.path), "outs", f"{testcase_name}.txt")
