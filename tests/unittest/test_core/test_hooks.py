from datetime import date
from functools import partial
from pathlib import Path
from textwrap import dedent
from types import SimpleNamespace

import pandas as pd
import pytest
from mypy import api as mypy_api

from rqalpha.core.events import EVENT, Event, EventBus
from rqalpha.core.hooks import HookRegistry, HookSpec, Notify, Waterfall
from rqalpha.environment import Environment
from rqalpha.main import AVAILABLE_DATA_RANGE, _adjust_start_date, cleanup_resources
from rqalpha.utils import RqAttrDict
from rqalpha.utils.exception import is_user_exc


@pytest.mark.parametrize("callbacks, expected", [
    pytest.param([], 2, id="empty"),
    pytest.param([
        lambda value, offset, *, scale: (value + offset) * scale,
        lambda value, offset, *, scale: (value - offset) * scale,
    ], 68, id="chain-with-context"),
    pytest.param([
        lambda value, offset, *, scale: None,
        lambda value, offset, *, scale: 7 if value is None else -1,
    ], 7, id="none-is-a-result"),
])
def test_waterfall(callbacks, expected):
    # Given 有序回调，When 执行，Then 逐级传递结果并透传上下文，空流水线保留初值。
    hook = Waterfall()
    for callback in callbacks:
        hook.register(callback)
    assert hook.apply(2, 3, scale=4) == expected


@pytest.mark.parametrize("factory, user", [
    pytest.param(Waterfall, False, id="waterfall"),
    pytest.param(Notify, False, id="notify-internal"),
    pytest.param(Notify, True, id="notify-user"),
])
def test_registration_lifecycle(factory, user):
    # Given 重复注册，When 注销或清空后重新注册，Then 只影响对应注册且注销可重复执行。
    hook = factory()
    register = partial(hook.register, user=True) if user else hook.register
    calls = []

    def callback(value):
        calls.append("same")

    dispose_first = register(callback)
    register(lambda value: calls.append("middle"))
    dispose_last = register(callback)
    hook.apply(None)
    assert calls == ["same", "middle", "same"]

    calls.clear()
    dispose_last()
    dispose_last()
    hook.apply(None)
    assert calls == ["same", "middle"]

    calls.clear()
    hook.clear()
    hook.clear()
    hook.apply(None)
    assert calls == []
    register(callback)
    dispose_first()
    dispose_first()
    hook.apply(None)
    assert calls == ["same"]


def test_registry_shares_registrations_only_for_the_same_spec_and_registry():
    # Given 同名不同类型的扩展点，When 注册和调用，Then 同一 spec 共享回调，其他扩展点和运行隔离。
    registry = HookRegistry()
    spec = HookSpec("shared_name", Waterfall)
    notify_spec = HookSpec("shared_name", Notify)
    registry.hook(spec).register(lambda value: value + 1)
    notified = []
    registry.hook(notify_spec).register(notified.append)

    assert registry.hook(spec).apply(2) == 3
    registry.hook(notify_spec).apply("message")
    assert notified == ["message"]
    assert HookRegistry().hook(spec).apply(2) == 2


def test_event_dispatch_order_and_isolation():
    # Given 两阶段及不同类型监听器，When 发布事件，Then 按类型派发，真值仅短路内部阶段。
    bus = EventBus(HookRegistry())
    calls = []

    def listener(name, result=None):
        def callback(event):
            event.value += 1
            calls.append(name)
            return result
        return callback

    bus.add_listener("custom.event", listener("custom"))
    # 用户监听器即使先注册，也要在内部阶段之后执行。
    bus.add_listener(EVENT.BAR, listener("user_first", True), user=True)
    bus.add_listener(EVENT.BAR, listener("user_second"), user=True)
    bus.prepend_listener(EVENT.BAR, listener("user_prepend"), user=True)
    bus.add_listener(EVENT.BAR, listener("internal_stop", "truthy"))
    bus.add_listener(EVENT.BAR, listener("internal_skipped"))
    bus.prepend_listener(EVENT.BAR, listener("internal_prepend_first"))
    bus.prepend_listener(EVENT.BAR, listener("internal_prepend_second"))

    bus.publish_event(Event(EVENT.TICK, value=0))
    assert calls == []
    event = Event(EVENT.BAR, value=0)
    bus.publish_event(event)
    assert event.value == 6
    assert calls == [
        "internal_prepend_second", "internal_prepend_first", "internal_stop",
        "user_prepend", "user_first", "user_second",
    ]
    calls.clear()
    bus.publish_event(Event("custom.event", value=0))
    assert calls == ["custom"]


def test_event_bus_keeps_live_registration_in_both_phases():
    # Given 监听器执行时追加监听器，When 发布旧事件，Then 新监听器参与本次派发。
    bus = EventBus(HookRegistry())
    calls = []

    def internal(event):
        calls.append("internal")
        bus.add_listener(EVENT.BAR, lambda event: calls.append("late_internal"))
        bus.add_listener(EVENT.BAR, lambda event: calls.append("user_from_internal"), user=True)

    def user(event):
        calls.append("user")
        bus.add_listener(EVENT.BAR, lambda event: calls.append("late_user"), user=True)

    bus.add_listener(EVENT.BAR, internal)
    bus.add_listener(EVENT.BAR, user, user=True)
    bus.publish_event(Event(EVENT.BAR))
    assert calls == ["internal", "late_internal", "user", "user_from_internal", "late_user"]


@pytest.mark.parametrize("mode", ["waterfall", "internal", "user"])
def test_callback_error_stops_dispatch(mode):
    # Given 回调失败，When 派发，Then 原异常向外传播，后续回调（包括用户阶段）不执行。
    calls = []
    error = ValueError("callback failed")

    def fail(value):
        calls.append("fail")
        raise error

    if mode == "waterfall":
        hook = Waterfall()
        register, dispatch = hook.register, partial(hook.apply, None)
    else:
        bus = EventBus(HookRegistry())
        register = partial(bus.add_listener, EVENT.BAR, user=mode == "user")
        dispatch = partial(bus.publish_event, Event(EVENT.BAR))
        if mode == "internal":
            bus.add_listener(EVENT.BAR, lambda event: calls.append("unexpected_user"), user=True)
    register(fail)
    register(lambda value: calls.append("unexpected"))

    with pytest.raises(ValueError) as caught:
        dispatch()
    assert caught.value is error
    assert calls == ["fail"]


def test_cleanup_resources_clears_hooks_and_events(monkeypatch):
    # Given 环境同时持有新 hook 和旧事件，When 结束清理，Then 调用方仍持有的实例也不再触发回调。
    monkeypatch.setattr(Environment, "_env", None)
    env = Environment(RqAttrDict({"base": {"start_date": date(2024, 1, 1)}}), rqdatac_init=False)
    calls = []
    hook = env.hook_registry.hook(AVAILABLE_DATA_RANGE)
    dispose = hook.register(lambda current, frequency: (date(2024, 1, 2), current[1]))
    env.event_bus.add_listener(EVENT.BAR, lambda event: calls.append("internal"))
    env.event_bus.add_listener(EVENT.BAR, lambda event: calls.append("user"), user=True)
    initial = (date(2024, 1, 1), date(2024, 1, 5))
    try:
        assert hook.apply(initial, "1d") == (date(2024, 1, 2), date(2024, 1, 5))
        env.event_bus.publish_event(Event(EVENT.BAR))
        assert calls == ["internal", "user"]

        cleanup_resources(env)
        dispose()
        assert hook.apply(initial, "1d") == initial
        env.event_bus.publish_event(Event(EVENT.BAR))
        assert calls == ["internal", "user"]
    finally:
        cleanup_resources(env)


def test_hooks_preserve_callback_and_apply_signatures(tmp_path):
    # Given 真实扩展点的正反例，When 执行 mypy，Then 正例通过且每处预期类型错误都被检出。
    sample = tmp_path / "hook_signatures.py"
    # 样本仅用于静态检查；类型化参数替代无关的回调实现。
    sample.write_text(dedent("""\
        from __future__ import annotations
        from datetime import date
        from typing import Callable, Optional
        from typing_extensions import assert_type
        from rqalpha.core.hooks import HookRegistry, HookSpec, Notify, Waterfall
        from rqalpha.main import AVAILABLE_DATA_RANGE, DateRange

        def check_signatures(
            restrict: Callable[[DateRange, str], DateRange],
            wrong_frequency: Callable[[DateRange, int], DateRange],
            wrong_return: Callable[[DateRange, str], str],
            missing_frequency: Callable[[DateRange], DateRange],
            extra_argument: Callable[[DateRange, str, int], DateRange],
            on_message: Callable[[str], Optional[bool]],
            on_number: Callable[[int], Optional[bool]],
            wrong_notify_return: Callable[[str], str],
        ) -> None:
            registry = HookRegistry()
            hook = registry.hook(AVAILABLE_DATA_RANGE)
            initial = (date(2024, 1, 1), date(2024, 1, 5))
            assert_type(hook, Waterfall[[str], DateRange])
            assert_type(hook.register(restrict), Callable[[], None])
            assert_type(hook.apply(initial, "1d"), DateRange)

            spec: HookSpec[Notify[str]] = HookSpec("message", Notify)
            notify = registry.hook(spec)
            assert_type(notify, Notify[str])
            assert_type(notify.register(on_message, user=True), Callable[[], None])
            notify.prepend(on_message)
            assert_type(notify.apply("message"), None)

            # warn_unused_ignores 防止类型约束退化为 Any 后负例悄悄通过。
            hook.register(wrong_frequency)  # type: ignore[arg-type]
            hook.register(wrong_return)  # type: ignore[arg-type]
            hook.register(missing_frequency)  # type: ignore[arg-type]
            hook.register(extra_argument)  # type: ignore[arg-type]
            hook.apply("invalid", "1d")  # type: ignore[arg-type]
            hook.apply(initial, 1)  # type: ignore[arg-type]
            hook.apply(initial)  # type: ignore[call-arg]
            hook.apply(initial, "1d", extra=True)  # type: ignore[call-arg]
            notify.register(on_number)  # type: ignore[arg-type]
            notify.register(wrong_notify_return)  # type: ignore[arg-type]
            notify.prepend(on_number, user=True)  # type: ignore[arg-type]
            notify.apply(1)  # type: ignore[arg-type]
    """), encoding="utf-8")
    config = tmp_path / "mypy.ini"
    config.write_text(
        "[mypy]\n"
        f"mypy_path = {Path(__file__).resolve().parents[3]}\n"
        "follow_imports = silent\n"
        "ignore_missing_imports = True\n"
        "warn_unused_ignores = True\n"
    )
    stdout, stderr, status = mypy_api.run([
        "--config-file", str(config),
        "--cache-dir", str(tmp_path / "mypy-cache"),
        "--no-incremental", str(sample),
    ])
    assert status == 0, stdout + stderr
