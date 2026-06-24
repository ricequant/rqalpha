from multiprocessing.sharedctypes import Synchronized
from typing import Optional


START_DATE = 20050104
END_DATE = 29991231


STOCK_FIELDS = ['open', 'close', 'high', 'low', 'prev_close', 'limit_up', 'limit_down', 'volume', 'total_turnover']
INDEX_FIELDS = ['open', 'close', 'high', 'low', 'prev_close', 'volume', 'total_turnover']
FUTURES_FIELDS = STOCK_FIELDS + ['settlement', 'prev_settlement', 'open_interest']
FUND_FIELDS = STOCK_FIELDS


sval: Optional[Synchronized] = None


def set_sval(value: Synchronized) -> None:
    global sval
    sval = value


def mark_update_failed() -> None:
    if sval is not None:
        sval.value = False
