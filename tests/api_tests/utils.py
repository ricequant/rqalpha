from six import iteritems


def assert_order(order, **kwargs):
    for field, value in iteritems(kwargs):
        assert getattr(order, field) == value, "order.{} is wrong, {} != {}".format(field, getattr(order, field), value)
