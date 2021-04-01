# 克隆自聚宽文章：https://www.joinquant.com/post/16755
# 标题：小盘价值股策略2.0，年化66%，回撤6.7%
# 作者：Gyro

def initialize(context):
    set_benchmark('399300.XSHE')
    log.set_level('order', 'error')
    set_option('use_real_price', True)
    
def after_code_changed(context):
    g.last_update_month = 0
    g.choicenum = 100
    g.weight = {}
    g.treasury = '000013.XSHG' # 存测试用，实盘请切换为债券基金
    g.stock_weight = 0.2 #股票比例

def before_trading_start(context):
    def sum_func(X):
        return X[0] + (X[1] + X[2] + X[3])/3
    # monthly update
    if g.last_update_month == context.current_dt.month:
        return
    g.last_update_month = context.current_dt.month
    # all stocks
    stk_sh = get_index_stocks('000001.XSHG')
    stk_sz = get_index_stocks('399106.XSHE')
    allstocks = stk_sh + stk_sz
    # stock pool
    df = get_fundamentals(query(
            valuation.code,
            valuation.market_cap,
            valuation.pb_ratio,
            valuation.pe_ratio,
            valuation.pcf_ratio,
        ).filter(
            valuation.code.in_(allstocks),
            valuation.pb_ratio>0,
            valuation.pe_ratio>0,
            valuation.pcf_ratio>0,
        )).dropna()
    # small - valuable
    df['point'] = df[['market_cap', 'pb_ratio', 'pe_ratio', 'pcf_ratio']] \
        .rank().T.apply(sum_func)
    df = df.sort_values(by='point').head(g.choicenum)
    stocks = list(df['code'])
    # weight
    g.weight = dict(zip(stocks, g.stock_weight*ones(g.choicenum)/g.choicenum))
    g.weight[g.treasury] = 0.99 - g.stock_weight

def handle_data(context, data):
    # sell
    for stock in context.portfolio.positions.keys():
        if stock not in g.weight:
            log.info('sell out ', stock)
            order_target(stock, 0);
    # buy
    for stock in g.weight.keys():
        position = g.weight[stock] * context.portfolio.total_value
        if stock not in context.portfolio.positions:
            log.info('buy ', stock)
            order_value(stock, position)
    delta = g.weight[g.treasury]*context.portfolio.total_value - context.portfolio.positions[g.treasury].value
    if abs(delta) > 110 * data[g.treasury].close and context.portfolio.available_cash > delta:
        order_value(g.treasury, delta)


def timer_show_account_info(context):
    vbalance = context.portfolio.total_value
    g.max_balance = max(g.max_balance, vbalance)
    symbols = [position.security for position in list(context.portfolio.positions.values())]

    drawdown = int((g.max_balance - vbalance) / g.max_balance * 100)
    turnover = int((context.portfolio.total_value - context.portfolio.available_cash) / context.portfolio.total_value * 100)
    record(动态回撤=drawdown, 仓位比例=turnover)
    log.info('%s 仓位[%5.2f%%] 回撤[%.2f%%] 持仓：%d %r' % (datetime_to_string(context.current_dt), turnover, drawdown, len(symbols), symbols))
    for position in list(context.portfolio.long_positions.values()):  
        log.info('%s %s 仓位[%.2f%%] 价值[%.2f]' % (datetime_to_string(context.current_dt), position.security, position.value / context.portfolio.total_value * 100 , position.value))


def datetime_to_string(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")
# end