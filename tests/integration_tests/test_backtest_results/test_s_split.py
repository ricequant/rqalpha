from rqalpha.apis import get_position

from datetime import date
 

def test_s_split(run_and_assert_result):
    def init(context):
        context.s1 = "688550.XSHG"

    def handle_bar(context, bar_dict):
        position = get_position(context.s1)
        if context.now.date() <= date(2024, 6, 13):
            assert position.quantity == 1445
        else:
            assert position.quantity == 1879

    config = {
        "base": {
            "start_date": "2024-06-10",
            "end_date": "2024-06-20",
            "frequency": "1d",
            "init_positions": "688550.XSHG:1445",
            "accounts": {
                "stock": 1000000,
            }
        },
        "extra": {
            "log_level": "error",
        }
    }

    run_and_assert_result(config=config, init=init, handle_bar=handle_bar)