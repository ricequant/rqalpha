"""供框架与 Mod 协作的类型化扩展点。

调用方在模块级声明共享的 HookSpec，Mod 通常在 start_up 中注册回调。调用方需显式执行 apply。例如：

    ADJUST: "HookSpec[Waterfall[[int], int]]" = HookSpec("my_mod.adjust", Waterfall)

    def add(value: int, delta: int) -> int:
        return value + delta

    hook = env.hook_registry.hook(ADJUST)
    hook.register(add)
    result = hook.apply(10, 2)  # 12
    
类型注解供静态检查器验证签名，不进行运行时签名检查。
"""

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
    """兼容旧事件的两阶段通知：先内部回调，再用户回调。

    内部回调返回真值只会停止内部阶段，用户阶段忽略返回值。
    追加到当前阶段的回调可参与本次通知。
    """

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
    """按注册顺序传递结果：callback(current, *args, **kwargs) -> T。

    每个回调接收上一步的结果，额外参数原样透传；None 也作为普通结果传递。
    回调应始终返回约定类型的值；异常直接传播，后续回调不再执行。
    """

    def apply(self, initial: T, /, *args: P.args, **kwargs: P.kwargs) -> T:
        value = initial
        for reg in self._callbacks:
            value = reg.callback(value, *args, **kwargs)
        return value


# more hook types in the future:
#   FirstResult: (*args) -> Optional[R]，返回首个结果
#       - 事前风控
#       - Portfolio 工厂的扩展
#       - 汇率等数据的注入
#   Wrapper: func -> func，动态注册装饰器
#   Dispatch: 替代现有的 instype_dispatch，实现 Mod 基于品种扩展执行逻辑
#   Collect：收集回调的结果
#       - Mod 贡献 RunInfo 中提供的信息
#       - Mod 贡献回测结果

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
