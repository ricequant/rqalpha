import multiprocessing
import queue
from multiprocessing.sharedctypes import Synchronized
from typing import Any, List, Optional

from rqalpha.utils.logger import system_log


START_DATE = 20050104
END_DATE = 29991231


STOCK_FIELDS = ['open', 'close', 'high', 'low', 'prev_close', 'limit_up', 'limit_down', 'volume', 'total_turnover']
INDEX_FIELDS = ['open', 'close', 'high', 'low', 'prev_close', 'volume', 'total_turnover']
FUTURES_FIELDS = STOCK_FIELDS + ['settlement', 'prev_settlement', 'open_interest']
FUND_FIELDS = STOCK_FIELDS


sval: Optional[Synchronized] = None
error_queue: Optional[Any] = None


def set_sval(value: Synchronized) -> None:
    global sval
    sval = value


def bind_error_list(value: Any) -> None:
    global error_queue
    error_queue = value


def reset_error_list() -> Any:
    global error_queue
    error_queue = multiprocessing.Queue()
    return error_queue


def get_error_list() -> List[str]:
    if error_queue is None:
        return []

    errors = []
    while True:
        try:
            errors.append(error_queue.get(timeout=0.1))
        except queue.Empty:
            break
    return errors


def mark_update_failed(message: Optional[str] = None) -> None:
    if sval is not None:
        sval.value = False

    if message is not None and error_queue is not None:
        error_queue.put(str(message))


def log_and_mark_error(error_message: str):
    system_log.error(error_message)
    mark_update_failed(error_message)
