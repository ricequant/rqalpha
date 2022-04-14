from rqalpha import run_file


if __name__ == '__main__':
    config = {
        "base": {
            "start_date": "2018-01-01",
            "end_date": "2018-12-31",
            "benchmark": "000300.XSHG",
            "accounts": {
                "stock": 100000
            }
        },
        "extra": {
            "log_level": "verbose",
        },
        "mod": {
            "sys_analyser": {
                "enabled": True,
                "plot": True
            }
        }
    }

    strategy_file_path = "./strategy.py"

    run_file(strategy_file_path, config=config)


