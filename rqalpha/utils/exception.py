# -*- coding: utf-8 -*-
#
# Copyright 2017 Ricequant, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import six

from rqalpha import const


class CustomError(object):
    def __init__(self):
        self.stacks = []
        self.msg = None
        self.exc_type = None
        self.exc_val = None
        self.exc_tb = None
        self.error_type = const.EXC_TYPE.NOTSET
        self.max_exc_var_len = 160

    def set_exc(self, exc_type, exc_val, exc_tb):
        self.exc_type = exc_type
        self.exc_val = exc_val
        self.exc_tb = exc_tb

    def set_msg(self, msg):
        self.msg = msg

    def add_stack_info(self, filename, lineno, func_name, code, local_variables={}):
        self.stacks.append((filename, lineno, func_name, code, local_variables))

    @property
    def stacks_length(self):
        return len(self.stacks)

    def __repr__(self):
        if len(self.stacks) == 0:
            return self.msg

        def _repr(v):
            try:
                var_str = repr(v)
                if len(var_str) > self.max_exc_var_len:
                    var_str = var_str[:self.max_exc_var_len] + " ..."
                return var_str
            except Exception:
                return 'UNREPRESENTABLE VALUE'

        content = ["Traceback (most recent call last):"]
        for filename, lineno, func_name, code, local_variables in self.stacks:
            content.append('  File %s, line %s in %s' % (filename, lineno, func_name))
            content.append('    %s' % (code, ))
            for k, v in six.iteritems(local_variables):
                content.append('    --> %s = %s' % (k, _repr(v)))
            content.append('')
        content.append("%s: %s" % (self.exc_type.__name__, self.msg))

        return "\n".join(content)


class CustomException(Exception):
    def __init__(self, error):
        self.error = error


EXC_EXT_NAME = "ricequant_exc"


def patch_user_exc(exc_val, force=False):
    exc_from_type = getattr(exc_val, EXC_EXT_NAME, const.EXC_TYPE.NOTSET)
    if exc_from_type == const.EXC_TYPE.NOTSET or force:
        setattr(exc_val, EXC_EXT_NAME, const.EXC_TYPE.USER_EXC)
    return exc_val


def patch_system_exc(exc_val, force=False):
    exc_from_type = getattr(exc_val, EXC_EXT_NAME, const.EXC_TYPE.NOTSET)
    if exc_from_type == const.EXC_TYPE.NOTSET or force:
        setattr(exc_val, EXC_EXT_NAME, const.EXC_TYPE.SYSTEM_EXC)
    return exc_val


def get_exc_from_type(exc_val):
    exc_from_type = getattr(exc_val, EXC_EXT_NAME, const.EXC_TYPE.NOTSET)
    return exc_from_type


def is_system_exc(exc_val):
    return get_exc_from_type(exc_val) == const.EXC_TYPE.SYSTEM_EXC


def is_user_exc(exc_val):
    return get_exc_from_type(exc_val) == const.EXC_TYPE.USER_EXC


class ModifyExceptionFromType(object):
    def __init__(self, exc_from_type, force=False):
        self.exc_from_type = exc_from_type
        self.force = force

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None:
            exc_from_type = getattr(exc_val, EXC_EXT_NAME, const.EXC_TYPE.NOTSET)
            if self.force or exc_from_type == const.EXC_TYPE.NOTSET:
                setattr(exc_val, EXC_EXT_NAME, self.exc_from_type)


class RQUserError(Exception):
    ricequant_exc = const.EXC_TYPE.USER_EXC
    pass


class RQInvalidArgument(RQUserError):
    pass


class RQTypeError(RQUserError):
    pass
