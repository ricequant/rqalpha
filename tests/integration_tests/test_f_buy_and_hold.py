from rqalpha.utils.testing import integration_test

from rqalpha.apis import subscribe, buy_open, logger


def test_f_buy_and_hold(result_file):
    def init(context):
        context.s1 = "IF88"
        subscribe(context.s1)
        logger.info("Interested in: " + str(context.s1))

    def handle_bar(context, bar_dict):
        buy_open(context.s1, 1)

    config = {
        "base": {
            "start_date": "2015-01-09",
            "end_date": "2015-03-09",
            "frequency": "1d",
            "matching_type": "current_bar",
            "benchmark": None,
            "accounts": {
                "future": 1000000
            }
        },
        "extra": {
            "log_level": "error",
        }
    }

    integration_test(result_file, config=config, init=init, handle_bar=handle_bar)
