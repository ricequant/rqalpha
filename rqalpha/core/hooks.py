from dataclasses import dataclass
from typing import Any, Callable, Generic, Optional, Type, TypeVar, cast, List

from rqalpha.utils.typing import ParamSpec, Concatenate


__all__ = [
    'Hook', 
    'Notify', 
    'Waterfall', 
    'HookSpec', 
    'HookRegistry'
]


C = TypeVar('C', bound=Callable)
P = ParamSpec('P')
T = TypeVar('T')


@dataclass(eq=False)
class _Registration(Generic[C]):
    # 严格按对象 id 判重，防止注册重复 callback 后注销时错误定位对象
    callback: C


class Hook(Generic[C]):
    def __init__(self) -> None:
        self._callbacks: List[_Registration[C]] = []

    def register(self, callback: C) -> Callable[[], None]:
        return self._do_register(self._callbacks, callback)

    def clear(self) -> None:
        self._callbacks.clear()

    @classmethod
    def _do_register(
        cls, 
        callbacks: List[_Registration[C]], 
        callback: C, 
        insert_func: Callable[[List[_Registration[C]], _Registration[C]], Any] = list.append
    ) -> Callable[[], None]:
        reg = _Registration(callback)
        insert_func(callbacks, reg)

        def _unreg():
            try:
                callbacks.remove(reg)
            except ValueError:
                pass

        return _unreg


insert_0 = lambda lst, item: lst.insert(0, item)


class Notify(Generic[T], Hook[Callable[[T], Optional[bool]]]):
    def __init__(self) -> None:
        super().__init__()
        self._user_callbacks: List[_Registration[Callable[[T], Optional[bool]]]] = []

    def register(self, callback: Callable[[T], Optional[bool]], user: bool = False) -> Callable[[], None]:
        if user:
            return self._do_register(self._user_callbacks, callback)
        else:
            return super().register(callback)

    def prepend(self, callback: Callable[[T], Optional[bool]], user: bool = False) -> None:
        if user:
            self._do_register(self._user_callbacks, callback, insert_0)
        else:
            self._do_register(self._callbacks, callback, insert_0)

    def apply(self, value: T) -> None:
        for reg in self._callbacks:
            if reg.callback(value):
                break
        for reg in self._user_callbacks:
            reg.callback(value)

    def clear(self) -> None:
        super().clear()
        self._user_callbacks.clear()


class Waterfall(Generic[P, T], Hook[Callable[Concatenate[T, P], T]]):
    def apply(self, initial: T, /, *args: P.args, **kwargs: P.kwargs) -> T:
        value = initial
        for reg in self._callbacks:
            value = reg.callback(value, *args, **kwargs)
        return value


# more hook types in the future:
#   FirstResult: (*args) -> Optional[R]，返回首个结果
#   Wrapper: func -> func，动态注册装饰器


H = TypeVar('H', bound=Hook)


@dataclass(frozen=True, eq=False)
class HookSpec(Generic[H]):
    name: str
    factory: Type[H]


class HookRegistry:
    def __init__(self) -> None:
        self._hooks: dict[HookSpec, Hook] = {}

    def hook(self, spec: HookSpec[H]) -> H:
        if spec not in self._hooks:
            self._hooks[spec] = spec.factory()
        return cast(H, self._hooks[spec])

    def clear(self):
        for hook in self._hooks.values():
            hook.clear()
        self._hooks.clear()