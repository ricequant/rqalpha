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
def assert_order():
    def _assert_order(order, **kwargs):
        for field, value in kwargs.items():
            assert getattr(order, field) == value, "order.{} is wrong, {} != {}".format(field, getattr(order, field), value)
    return _assert_order
