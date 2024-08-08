import os
from typing import Generator, Any, Optional, Callable, Tuple
import queue
import multiprocessing

import click

from concurrent.futures import _base
# noinspection PyUnresolvedReferences
from concurrent.futures.process import ProcessPoolExecutor, _ExceptionWithTraceback, _ResultItem


def _process_worker(call_queue, result_queue, progress_queue, initializer, initargs):
    error = None
    if initializer is not None:
        try:
            initializer(*initargs)
        except BaseException:
            _base.LOGGER.critical('Exception in initializer:', exc_info=True)
            return
    while True:
        call_item = call_queue.get(block=True)
        if call_item is None:
            result_queue.put(os.getpid())
            return
        try:
            r = call_item.fn(*call_item.args, **call_item.kwargs)
            if isinstance(call_item.fn, ProgressedTask):
                for step in r:
                    if isinstance(step, int):
                        progress_queue.put(step)
                    elif isinstance(step, tuple): # 部分 task 报错时会返回一个 tuple
                        error = step
                r = None
            else:
                progress_queue.put(1)
        except BaseException as e:
            exc = _ExceptionWithTraceback(e, e.__traceback__)
            result_queue.put(_ResultItem(call_item.work_id, exception=exc))
        else:
            if error:
                result_queue.put(_ResultItem(call_item.work_id, result=error))
                error = None
            else:
                result_queue.put(_ResultItem(call_item.work_id, result=r))


class ProgressedProcessPoolExecutor(ProcessPoolExecutor):
    def __init__(self, max_workers: Optional[int] = None, initializer: Optional[Callable] = None, initargs: Optional[tuple] = ()):
        super(ProgressedProcessPoolExecutor, self).__init__(max_workers)
        self._initializer = initializer
        self._initargs = initargs
        self._progress_queue = multiprocessing.Queue()
        self._futures = []
        self._total_steps = 0

    def _adjust_process_count(self):
        # noinspection PyUnresolvedReferences
        for _ in range(len(self._processes), self._max_workers):
            self._spawn_process()

    def _spawn_process(self):
        p = multiprocessing.Process(
            target=_process_worker,
            args=(self._call_queue, self._result_queue, self._progress_queue, self._initializer, self._initargs)
        )
        p.start()
        # noinspection PyUnresolvedReferences
        self._processes[p.pid] = p

    def submit(self, fn, *args, **kwargs):
        if isinstance(fn, ProgressedTask):
            # noinspection PyUnresolvedReferences
            self._total_steps += fn.total_steps
        else:
            self._total_steps += 1
        f = super(ProgressedProcessPoolExecutor, self).submit(fn, *args, **kwargs)
        self._futures.append(f)
        return f

    def shutdown(self, wait=True):
        if not wait:
            return super(ProgressedProcessPoolExecutor, self).shutdown(wait)
        progress_bar = click.progressbar(length=self._total_steps, show_eta=False)
        finish = False
        while True:
            for fut in self._futures:
                if fut.running():
                    break
            else:
                finish = True
            while True:
                try:
                    step = self._progress_queue.get(timeout=0.5)
                except queue.Empty:
                    break
                else:
                    progress_bar.update(step)

            if finish:
                break

        progress_bar.render_finish()
        super(ProgressedProcessPoolExecutor, self).shutdown(True)
        for fut in self._futures:
            if fut.exception():
                raise fut.exception()


class ProgressedTask:
    @property
    def total_steps(self) -> int:
        raise NotImplementedError

    def __call__(self, *args: Any, **kwargs: Any) -> Generator:
        raise NotImplementedError
