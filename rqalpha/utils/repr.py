# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），
#         您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、
#         本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，
#         否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。

import abc


def _repr(cls_name, properties):
    fmt_str = "{}({})".format(cls_name, ", ".join((str(p) + "={}") for p in properties))

    def __repr(inst):
        return fmt_str.format(*(getattr(inst, p, None) for p in properties))
    return __repr


class PropertyReprMeta(abc.ABCMeta):
    # has better performance than property_repr
    def __new__(mcs, *args, **kwargs):
        cls = super(PropertyReprMeta, mcs).__new__(mcs, *args, **kwargs)

        if hasattr(cls, "__repr_properties__"):
            repr_properties = getattr(cls, "__repr_properties__")
        else:
            repr_properties = []
            for c in cls.mro():
                repr_properties.extend(v for v in vars(c) if isinstance(getattr(c, v), property))
        cls.__repr__ = _repr(cls.__name__, repr_properties)
        return cls


def property_repr(inst):
    # return pformat(properties(inst))
    return "%s(%s)" % (inst.__class__.__name__, properties(inst))


def slots_repr(inst):
    # return pformat(slots(inst))
    return "%s(%s)" % (inst.__class__.__name__, slots(inst))


def dict_repr(inst):
    # return pformat(inst.__dict__)
    return "%s(%s)" % (
        inst.__class__.__name__, {k: v for k, v in inst.__dict__.items() if k[0] != "_"})


def properties(inst):
    result = {}
    for cls in inst.__class__.mro():
        abandon_properties = getattr(cls, '__abandon_properties__', [])
        for varname in iter_properties_of_class(cls):
            if varname[0] == "_":
                continue
            if varname in abandon_properties:
                # 如果 设置了 __abandon_properties__ 属性，则过滤其中的property，不输出相关内容
                continue
            # FIXME: 这里getattr在iter_properties_of_class中掉用过了，性能比较差，可以优化
            try:
                tmp = getattr(inst, varname)
            except (AttributeError, RuntimeError, KeyError):
                continue
            if varname == "positions":
                tmp = list(tmp.keys())
            if hasattr(tmp, '__simple_object__'):
                result[varname] = tmp.__simple_object__()
            else:
                result[varname] = tmp
    return result


def slots(inst):
    result = {}
    for slot in inst.__slots__:
        result[slot] = getattr(inst, slot)
    return result


def iter_properties_of_class(cls):
    for varname in vars(cls):
        value = getattr(cls, varname)
        if isinstance(value, property):
            yield varname
