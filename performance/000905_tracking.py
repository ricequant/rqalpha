config = {
    "base": {
        "start_date": "2021-01-01",
        "end_date": "2021-12-31",
        "accounts": {
            "STOCK": 100000000
        }
    },
    "extra": {
        "log_level": "error"
    },
    "mod": {
        "sys_progress": {
            "enabled": True,
            "show": True
        },
        "sys_analyser": {
            "benchmark": "000905.XSHG",
        }
    }
}

INDEX_WEIGHTS = None


def handle_bar(context, _):
    order_target_portfolio(INDEX_WEIGHTS.loc[str(context.now.date())].weight)


if __name__ == "__main__":
    import cProfile

    import rqdatac
    from rqalpha import run_func

    rqdatac.init()

    INDEX_WEIGHTS = rqdatac.index_weights(
        "000905.XSHG",
        start_date=config["base"]["start_date"],
        end_date=config["base"]["end_date"]
    ) * 0.98

    pr = cProfile.Profile()
    pr.enable()
    run_func(config=config, handle_bar=handle_bar)
    pr.disable()
    pr.dump_stats(f"000905_tracking.py.perf")

    """
    Intel(R) Core(TM) i7-4790K CPU @ 4.00GHz

    RQalpha 4.7.2: 622s

    """