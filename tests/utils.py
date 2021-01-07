import collections
from copy import deepcopy

from six import iteritems


def deep_update(from_dict, to_dict):
    for (key, value) in from_dict.items():
        if (key in to_dict.keys() and
                isinstance(to_dict[key], collections.Mapping) and
                isinstance(value, collections.Mapping)):
            deep_update(value, to_dict[key])
        else:
            to_dict[key] = value


def make_test_strategy_decorator(default_config, strategies_list):
    def as_test_strategy(custom_config=None):
        def strategy_decorator(func):
            strategy_components = func()
            if not isinstance(strategy_components, tuple):
                strategy_components = (strategy_components, )
            strategy = {c.__name__: c for c in strategy_components}
            config = deepcopy(default_config)
            if custom_config:
                deep_update(custom_config, config)
            strategy["config"] = config
            strategy["name"] = func.__name__
            strategies_list.append(strategy)
        return strategy_decorator
    return as_test_strategy


def assert_order(order, **kwargs):
    for field, value in iteritems(kwargs):
        assert getattr(order, field) == value, "order.{} is wrong, {} != {}".format(field, getattr(order, field), value)
