from rqalpha.environment import Environment
from rqalpha.const import DAYS_CNT


def init(context):
    context.s1 = '600519.XSHG'
    context.fired = False

def before_trading(context):
    assert context.config.base.custom_trading_days_a_year == 242
    assert Environment.get_instance().trading_days_a_year == 242

def handle_bar(context, bar_dict):
    if not context.fired:
        # order_percent并且传入1代表买入该股票并且使其占有投资组合的100%
        order_percent(context.s1, 1)
        context.fired = True

def after_trading(context):
    logger.info(context.portfolio)
    env = Environment.get_instance()
    
    # 计算按252天的年化收益率
    date_count = float(env.data_proxy.count_trading_dates(context.config.base.start_date, env.trading_dt.date()))
    unit_net_value = context.portfolio.unit_net_value
    annualized_returns252 = unit_net_value ** (DAYS_CNT.TRADING_DAYS_A_YEAR / date_count) - 1
    # 实际按242天的年化收益率
    annualized_returns242 = context.portfolio.annualized_returns
    annualized_returns = context.portfolio.annualized_returns
    assert annualized_returns252 != annualized_returns242
    assert annualized_returns242 == annualized_returns


__config__ = {
    "base": {
        "start_date": "2025-01-01",
        "end_date": "2025-06-01",
        "frequency": "1d",
        "matching_type": "current_bar",
        "accounts": {
            "stock": 1000000
        },
        # 严格意义上说A股一年的交易日是242天左右
        "custom_trading_days_a_year": 242
    },
    "extra": {
        "log_level": "error",
    },
    "mod": {
        "sys_analyser": {
            "benchmark": "000300.XSHG",
            "enabled": True,
            "plot": True
        }
    }
}
