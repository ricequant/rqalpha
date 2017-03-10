from rqalpha.const import ACCOUNT_TYPE
from rqalpha.model.account import BenchmarkAccount, StockAccount, FutureAccount


def init_accounts(env):
    accounts = {}
    config = env.config
    start_date = config.base.start_date
    total_cash = 0
    for account_type in config.base.account_list:
        if account_type == ACCOUNT_TYPE.STOCK:
            stock_starting_cash = config.base.stock_starting_cash
            accounts[ACCOUNT_TYPE.STOCK] = StockAccount(env, stock_starting_cash, start_date)
            total_cash += stock_starting_cash
        elif account_type == ACCOUNT_TYPE.FUTURE:
            future_starting_cash = config.base.future_starting_cash
            accounts[ACCOUNT_TYPE.FUTURE] = FutureAccount(env, future_starting_cash, start_date)
            total_cash += future_starting_cash
        else:
            raise NotImplementedError
    if config.base.benchmark is not None:
        accounts[ACCOUNT_TYPE.BENCHMARK] = BenchmarkAccount(env, total_cash, start_date)

    return accounts