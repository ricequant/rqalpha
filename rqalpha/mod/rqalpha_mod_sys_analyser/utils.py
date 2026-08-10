import re
import pandas as pd


EQUITIES_OID_RE = re.compile(r"^(?:\d{6}\.(?:XSHE|XSHG|BJSE)|\d{5}\.XHKG)$")


def _all_trades_are_equities(trades: pd.DataFrame) -> bool:
    if trades.empty or "order_book_id" not in trades.columns:
        return False
    return trades["order_book_id"].map(lambda oid: isinstance(oid, str) and EQUITIES_OID_RE.match(oid) is not None).all()
