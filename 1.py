import tracemalloc

from rqalpha import run_func
from rqalpha.apis import logger, order_target_portfolio_smart

import rqdatac


__config__ = {
    "base": {
        "start_date": "2026-01-01",
        "end_date": "2026-04-14",
        "accounts": {
            "stock": 10000000
        }
    },
}


def _get_rss_mb():
    with open("/proc/self/status", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("VmRSS:"):
                rss_kb = int(line.split()[1])
                return rss_kb / 1024
    return None


def _log_pre_run_mem():
    rss_mb = _get_rss_mb()
    rss_text = "unavailable" if rss_mb is None else f"{rss_mb:.2f}MB"
    print(f"[mem] pre_run rss={rss_text}", flush=True)


def init(context):
    tracemalloc.start()
    context.counter = -1
    context.mem_day_count = 0
    context.mem_base_rss_mb = None
    context.mem_prev_rss_mb = None

def before_trading(context):
    df = rqdatac.all_instruments("CS", date=context.now)
    context.order_book_ids = df.order_book_id.tolist()


def handle_bar(context, bar_dict):
    context.counter += 1
    if 1 <= context.counter <= 100:
        line = context.counter * 100
        percent = 1 / len(context.order_book_ids)
        dic = {
            order_book_id: percent
            for order_book_id in context.order_book_ids[line: line + 1500]
        }
        order_target_portfolio_smart(dic)


def after_trading(context):
    context.mem_day_count += 1
    rss_mb = _get_rss_mb()
    traced_current_mb, traced_peak_mb = (
        value / 1024 / 1024 for value in tracemalloc.get_traced_memory()
    )

    if rss_mb is None:
        logger.info(
            f"[mem] date={context.now.date()} rss=unavailable "
            f"traced={traced_current_mb:.2f}MB peak={traced_peak_mb:.2f}MB"
        )
        return

    if context.mem_base_rss_mb is None:
        context.mem_base_rss_mb = rss_mb

    delta_from_base_mb = rss_mb - context.mem_base_rss_mb
    delta_from_prev_mb = (
        0.0 if context.mem_prev_rss_mb is None else rss_mb - context.mem_prev_rss_mb
    )
    context.mem_prev_rss_mb = rss_mb

    logger.info(
        f"[mem] day={context.mem_day_count} date={context.now.date()} "
        f"rss={rss_mb:.2f}MB "
        f"delta_from_base={delta_from_base_mb:+.2f}MB "
        f"delta_from_prev={delta_from_prev_mb:+.2f}MB "
        f"traced={traced_current_mb:.2f}MB peak={traced_peak_mb:.2f}MB"
    )


if __name__ == "__main__":
    _log_pre_run_mem()
    run_func(
        config=__config__,
        init=init,
        before_trading=before_trading,
        handle_bar=handle_bar,
        after_trading=after_trading,
    )
