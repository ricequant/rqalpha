# -*- coding: utf-8 -*-
from contextlib import contextmanager


class ContextStack(object):

    def __init__(self):
        self.stack = []

    def push(self, obj):
        self.stack.append(obj)

    def pop(self):
        try:
            return self.stack.pop()
        except IndexError:
            raise RuntimeError("stack is empty")

    @contextmanager
    def pushed(self, obj):
        self.push(obj)
        try:
            yield self
        finally:
            self.pop()

    @property
    def top(self):
        try:
            return self.stack[-1]
        except IndexError:
            raise RuntimeError("stack is empty")


class ExecutionContext(object):
    stack = ContextStack()

    def __init__(self, strategy):
        self.strategy = strategy

    def _push(self):
        self.stack.push(self)

    def _pop(self):
        popped = self.stack.pop()
        if popped is not self:
            raise RuntimeError("Popped wrong context")
        return self

    def __enter__(self):
        self._push()
        return self

    def __exit__(self, _type, _value, _tb):
        """
        Restore the algo instance stored in __enter__.
        """
        self._pop()

    @classmethod
    def get_active(cls):
        return cls.stack.top

    @classmethod
    def get_strategy(cls):
        return cls.get_active().strategy

    @classmethod
    def get_bridge(cls):
        return cls.get_strategy().converter
