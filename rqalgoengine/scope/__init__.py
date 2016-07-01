# -*- coding: utf-8 -*-
from functools import wraps
from collections import Iterable

import pandas as pd
import six

from . import api
from ..utils import ExecutionContext


__all__ = [
    "export_as_api",
]


def export_as_api(func):
    """
    Mark the object (usually class or function) that it should be exported to
    the global scope of the user strategy
    """
    @wraps(func)
    def api_func(*args, **kwargs):
        return getattr(ExecutionContext.get_strategy(), func.__name__)(*args, **kwargs)

    setattr(api, func.__name__, api_func)
    api.__all__.append(func.__name__)

    return func
