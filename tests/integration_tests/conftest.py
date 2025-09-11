import pytest
import os


@pytest.fixture
def testcase_name(request):
    if isinstance(request.node.parent, pytest.Class):
        casename = f"{request.node.parent.name}#{request.node.name}"
    else:
        casename = request.node.name

    return f"{os.path.split(request.path)[-1][:-3]}#{casename}"  # type: ignore
