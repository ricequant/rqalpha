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

from collections import defaultdict
from enum import Enum
from typing import Any, Callable, Dict, Hashable, Iterator, List, NamedTuple


HookCallback = Callable[..., Any]


class _CallbackEntry(NamedTuple):
    priority: int
    callback: HookCallback


class HookDispatcher:
    """管理扩展点的回调，并支持按顺序传递处理结果。"""
    def __init__(self):
        self._callbacks: Dict[Hashable, List[_CallbackEntry]] = defaultdict(list)

    def register(
        self,
        point: Hashable,
        callback: HookCallback,
        priority: int = 100,
    ) -> None:
        """注册回调，优先级越小越先执行，同优先级按注册顺序执行。"""
        self._register(point, callback, priority=priority)

    def _register(
        self, point: Hashable, callback: HookCallback, *, priority: int = 100, prepend: bool = False,
    ) -> None:
        """prepend=True 时，插入到相同优先级的回调之前。"""
        if not callable(callback):
            raise TypeError("callback must be callable")

        callbacks = self._callbacks[point]
        entry = _CallbackEntry(priority, callback)

        for index, existing in enumerate(callbacks):
            if existing.priority > priority or (prepend and existing.priority == priority):
                callbacks.insert(index, entry)
                return

        callbacks.append(entry)

    def _iter_callbacks(self, point: Hashable) -> Iterator[HookCallback]:
        for entry in self._callbacks.get(point, ()):
            yield entry.callback

    def apply(self, point: Hashable, value: Any, /, **kwargs: Any) -> Any:
        """
        依次将每个回调的返回值传给下一个回调，无回调时返回原始值。

        None 也作为结果传递，异常直接向外传播。
        执行期间新增的回调从下次调用开始生效。
        """
        callbacks = tuple(self._iter_callbacks(point))

        for callback in callbacks:
            value = callback(value, **kwargs)

        return value


class HOOK(Enum):
    # 回调接收当前日期区间和 frequency 关键字参数，返回调整后的日期区间。
    DATA_AVAILABLE_RANGE = "data_available_range"
