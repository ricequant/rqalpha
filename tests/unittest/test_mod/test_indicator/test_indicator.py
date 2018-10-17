from rqalpha.utils.testing import IndicatorFixture, RQAlphaTestCase


def buy_hys():
    from rqalpha_mod_indicator.indicators import CLOSE
    VAR = CLOSE
    return VAR


class ModIndicatorTestCase(IndicatorFixture, RQAlphaTestCase):
    def __init__(self, *args, **kwargs):
        super(ModIndicatorTestCase, self).__init__(*args, **kwargs)
        import datetime
        # import os
        from rqalpha.const import RUN_TYPE, MARKET

        self.env_config = {
            "base": {
                "start_date": datetime.date(2016, 9, 21),
                "end_date": datetime.date(2016, 10, 21),
                "run_type": RUN_TYPE.BACKTEST,
                "frequency": '1d',
                "market": MARKET.CN,
                # "strategy_file": os.path.abspath(__file__),
            }
        }

    def test_get_indicator(self):
        from rqalpha.data.data_proxy import DataProxy
        from rqalpha.data.base_data_source import BaseDataSource
        from rqalpha.execution_context import ExecutionContext
        from rqalpha.events import EVENT, Event
        from rqalpha.const import EXECUTION_PHASE
        import datetime
        import os

        self.indicator.reg_indicator('buy_hys', buy_hys, '1d', win_size=20)

        mock_event = Event(EVENT.PRE_BEFORE_TRADING)
        self.env.event_bus.publish_event(mock_event)

        order_book_id = '000001.XSHE'

        default_bundle_path = os.path.abspath(os.path.expanduser('~/.rqalpha/bundle'))
        self.env.set_data_source(BaseDataSource(default_bundle_path))
        self.env.set_data_proxy(DataProxy(self.env.data_source))
        self.env.calendar_dt = datetime.datetime(2016, 9, 21)

        with ExecutionContext(EXECUTION_PHASE.ON_BAR):
            data = self.indicator.get_indicator(order_book_id, 'buy_hys')
            # 此处是验证使用的是是否和本次运行结果一致的判断方法
            assert (data == 8.805)
