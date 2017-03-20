from rqalpha.const import ACCOUNT_TYPE
from rqalpha.model.account import BenchmarkAccount, StockAccount, FutureAccount
from rqalpha.model.position import Positions, StockPosition, FuturePosition
from rqalpha.model.portfolio import Portfolio


def init_portfolio(env):
    accounts = {}
    config = env.config
    start_date = config.base.start_date
    total_cash = 0
    for account_type in config.base.account_list:
        if account_type == ACCOUNT_TYPE.STOCK:
            stock_starting_cash = config.base.stock_starting_cash
            accounts[ACCOUNT_TYPE.STOCK] = StockAccount(stock_starting_cash, Positions(StockPosition))
        elif account_type == ACCOUNT_TYPE.FUTURE:
            future_starting_cash = config.base.future_starting_cash
            accounts[ACCOUNT_TYPE.FUTURE] = FutureAccount(future_starting_cash, Positions(FuturePosition))
        else:
            raise NotImplementedError
    if config.base.benchmark is not None:
        benchmark_account = BenchmarkAccount(total_cash, Positions(StockPosition))
    else:
        benchmark_account = None

    return Portfolio(start_date, 1, total_cash, accounts, benchmark_account)
