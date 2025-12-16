# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。

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
            return self.msg or ""

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
            for k, v in local_variables.items():
                content.append('    --> %s = %s' % (k, _repr(v)))
            content.append('')
        
        exc_name = self.exc_type.__name__ if self.exc_type else "Exception"
        content.append("%s: %s" % (exc_name, self.msg))

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


class RQApiNotSupportedError(RQUserError):
    pass


class RQDatacVersionTooLow(RuntimeError):
    pass


# ExceptionGroup implementation for compatibility with older Python versions
# Based on Python 3.11's ExceptionGroup behavior
class BaseExceptionGroup(BaseException):
    """A base class for grouping multiple exceptions."""
    
    def __init__(self, message, exceptions):
        if not isinstance(message, str):
            raise TypeError(f"ExceptionGroup message must be a string, not {type(message).__name__}")
        
        if not exceptions:
            raise ValueError("second argument (exceptions) must be a non-empty sequence")
            
        # Convert to list and validate exceptions
        exceptions_list = []
        for exc in exceptions:
            if isinstance(exc, BaseException):
                exceptions_list.append(exc)
            elif isinstance(exc, type) and issubclass(exc, BaseException):
                # Allow exception classes, instantiate them
                exceptions_list.append(exc())
            else:
                raise ValueError(f"Item {exc!r} of second argument is not an exception")
        
        self.message = message
        self.exceptions = tuple(exceptions_list)
        super().__init__(message)
    
    def __str__(self):
        if len(self.exceptions) == 1:
            return f"{self.message} (1 sub-exception)"
        return f"{self.message} ({len(self.exceptions)} sub-exceptions)"
    
    def __repr__(self):
        return f"{self.__class__.__name__}({self.message!r}, {list(self.exceptions)!r})"
    
    def split(self, condition):
        """Split the exception group based on a condition.
        
        Args:
            condition: A callable that takes an exception and returns True/False,
                      or an exception type/tuple of types.
        
        Returns:
            A tuple of (matching_group, non_matching_group).
            Either element can be None if no exceptions match that category.
        """
        if isinstance(condition, type) or (isinstance(condition, tuple) and 
                                         all(isinstance(t, type) for t in condition)):
            # Handle exception type(s)
            def check_condition(exc):
                return isinstance(exc, condition)
        elif callable(condition):
            def check_condition(exc):
                result = condition(exc)
                return bool(result)
        else:
            raise TypeError("condition must be a callable or exception type(s)")
        
        matching = []
        non_matching = []
        
        for exc in self.exceptions:
            if isinstance(exc, BaseExceptionGroup):
                # Recursively split nested groups
                match_group, non_match_group = exc.split(condition)
                if match_group is not None:
                    matching.append(match_group)
                if non_match_group is not None:
                    non_matching.append(non_match_group)
            else:
                if check_condition(exc):
                    matching.append(exc)
                else:
                    non_matching.append(exc)
        
        matching_group = None
        if matching:
            matching_group = self.derive(matching)
            
        non_matching_group = None
        if non_matching:
            non_matching_group = self.derive(non_matching)
            
        return (matching_group, non_matching_group)
    
    def subgroup(self, condition):
        """Return a subgroup containing only exceptions that match the condition."""
        matching_group, _ = self.split(condition)
        return matching_group
    
    def derive(self, exceptions):
        """Create a new exception group with the same message but different exceptions."""
        if not exceptions:
            return None
        return self.__class__(self.message, exceptions)


class ExceptionGroup(BaseExceptionGroup, Exception):
    """An exception group that inherits from Exception."""
    pass


def format_exception_group(exc_group, indent=""):
    """Format an ExceptionGroup for display."""
    if not isinstance(exc_group, BaseExceptionGroup):
        return str(exc_group)
    
    lines = [f"{indent}{exc_group.__class__.__name__}: {exc_group.message}"]
    
    for i, exc in enumerate(exc_group.exceptions):
        is_last = (i == len(exc_group.exceptions) - 1)
        prefix = "└─ " if is_last else "├─ "
        child_indent = "   " if is_last else "│  "
        
        if isinstance(exc, BaseExceptionGroup):
            lines.append(f"{indent}{prefix}{format_exception_group(exc, indent + child_indent)}")
        else:
            exc_str = f"{exc.__class__.__name__}: {exc}"
            lines.append(f"{indent}{prefix}{exc_str}")
    
    return "\n".join(lines)


#  Internal exceptions
class InstrumentNotFound(LookupError):
    pass

