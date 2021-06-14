"""
投资程序：
霍华．罗斯曼强调其投资风格在于为投资大众建立均衡、且以成长为导向的投资组合。选股方式偏好大型股，
管理良好且为领导产业趋势，以及产生实际报酬率的公司；不仅重视公司产生现金的能力，也强调有稳定成长能力的重要。
总市值大于等于50亿美元。
良好的财务结构。
较高的股东权益报酬。
拥有良好且持续的自由现金流量。
稳定持续的营收成长率。
优于比较指数的盈余报酬率。

===========================
选股标准：
总市值≧市场平均值*1.0。
最近一季流动比率≧市场平均值。
近四季股东权益报酬率≧市场平均值。
近五年自由现金流量均为正值。
近四季营收成长率介于6%至30%。
近四季盈余成长率介于8%至50%。
===
策略周期：
进入股池的个股平均分配资金。最大不超过5只。
逐月进行持仓价值再平衡。
5月，9月、11月月初为选股月，更新持仓股池。
===========================
"""

import pandas as pd
import numpy as np



# 初始化函数，设定基准等等
def initialize(context):
    # 设定沪深300
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    
    # 输出内容到日志 log.info()
    log.info('初始函数开始运行且全局只运行一次')
    # 过滤掉order系列API产生的比error级别低的log
    # log.set_level('order', 'error')
    #策略参数设置
    #操作的股票列表
    g.buy_list = []
    # 设置滑点
    set_slippage(FixedSlippage(0.0026))
    ### 股票相关设定 ###
    # 股票类每笔交易时的手续费是：买入时佣金万分之三，卖出时佣金万分之三加千分之一印花税, 每笔交易佣金最低扣5块钱
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    # 个股最大持仓比重
    g.security_max_proportion = 0.2
    # 最大建仓数量
    g.max_hold_stocknum = 10
    # 单只最大买入股数或金额
    g.max_buy_value = None
    g.max_buy_amount = None
    # 委托类型
    g.order_style_str = 'by_cap_mean'
    g.order_style_value = 100
    # 每月第5个交易日进行操作
    # 开盘前运行
    run_monthly(before_market_open,10,time='before_open', reference_security='000300.XSHG') 
    # 开盘时运行
    run_monthly(market_open,10,time='open', reference_security='000300.XSHG')
    
## 开盘前运行函数     
def before_market_open(context):
    # 获取要操作的股票列表,过滤st股和停牌股
    temp_list = get_stock_list(context)
    # 去除周期行业
    g.industry_list = ["801010","801040","801050","801080","801110","801120","801130","801150","801160","801200","801230","801710","801720","801730","801740","801750","801760","801770","801780","801790"]
    temp_list = industry_filter(context, temp_list, g.industry_list)

    log.info('满足条件的股票有%s只'%len(temp_list))
    #按市值进行排序
    g.buy_list = get_check_stocks_sort(context,temp_list)
    print(("the list consist of ",g.buy_list));
    

## 开盘时运行函数
def market_open(context):
    #卖出不在买入列表中的股票
    sell(context,g.buy_list)
    #买入不在持仓中的股票，按要操作的股票平均资金
    buy(context,g.buy_list)
#交易函数 - 买入
def buy(context, buy_lists):
    # 获取最终的 buy_lists 列表
    Num = g.max_hold_stocknum - len(context.portfolio.positions)
    buy_lists = buy_lists[:Num]
    # 买入股票
    if len(buy_lists)>0:
        # model1:
        # cash=Allocation_of_funds(context,buy_lists,g.max_hold_stocknum,g.max_buy_value)
        # for stock in buy_lists:
        #     order_target_value(stock,cash)
        
        # 持仓再平衡策略
        # model2
        cash=Risk_rebalancing(context,buy_lists)
        stock1=set(buy_lists)
        stock2=set(context.portfolio.positions.keys())
        buy_lists=stock1|stock2
        for stock in buy_lists:
            order_target_value(stock,cash)
    return

       
# 交易函数 - 出场
def sell(context, buy_lists):
    # 获取 sell_lists 列表
    hold_stock = list(context.portfolio.positions.keys())
    for s in hold_stock:
        #卖出不在买入列表中的股票
        if s not in buy_lists:
            order_target_value(s,0)   

#按流通市值进行排序   
#从大到小
def get_check_stocks_sort(context,check_out_lists):
    df = get_fundamentals(query(
        valuation.circulating_market_cap,
        valuation.pe_ratio,
        valuation.code
        ).filter(
            valuation.code.in_(check_out_lists)
            ).order_by(
                # 按市值降序排列
                valuation.circulating_market_cap.desc()
                ),date=context.previous_date)
    out_lists = list(df['code'].values)
    return out_lists

'''
1.总市值≧市场平均值*1.0。
2.最近一季流动比率≧市场平均值（流动资产合计/流动负债合计）。
3.近四季股东权益报酬率（roe）≧市场平均值。
4.近五年自由现金流量均为正值。（cash_flow.net_operate_cash_flow - cash_flow.net_invest_cash_flow）
5.近四季营收成长率介于6%至30%（）。    'IRYOY':indicator.inc_revenue_year_on_year, # 营业收入同比增长率(%)
6.近四季盈余成长率介于8%至50%。(eps比值)
'''
def get_stock_list(context):
    # 根据当前时间，获取四个报告期的报告时间
    t1,t2,t3,t4=statDate_value(context)
    # 获取当前市场非ST，未停牌个股，作为初始股池
    temp_list = filter_st_paused(context)   
   
    # #获取多期财务数据
    # panel = get_data(temp_list,4)
    #1.总市值≧市场平均值*1.0。
    df1=get_fundamentals(query(
        valuation.code,
        valuation.circulating_market_cap,
        ).filter(
            valuation.code.in_(temp_list)
            ),date=context.previous_date)
    dfx1=df1[df1['circulating_market_cap']>df1['circulating_market_cap'].mean()]
    l1=set(dfx1.code.values)
    
    
    #2.最近一季流动比率≧市场平均值（流动资产合计/流动负债合计）。
    df2=get_fundamentals(query(
        balance.total_current_assets,
        balance.total_current_liability,
        balance.code).filter(
            valuation.code.in_(temp_list)
                ),statDate=t1)
    # 剔除数据缺失行，以及流动性负债为0
    df2.dropna(axis=0,inplace=True)
    dfx2=df2[df2['total_current_liability'] != 0]
    dfx2['cr'] = dfx2['total_current_assets']/dfx2['total_current_liability']
    dfx2=dfx2[dfx2['cr']>dfx2['cr'].mean()]
    l2=set(dfx2.code.values)

    #3.近四季股东权益报酬率（roe）≧市场平均值。
    def roe_value(i,date,l2):
        df=get_fundamentals(query(
            indicator.code,
            indicator.roe
            ).filter(
                indicator.code.in_(l2)
                ),statDate=date)
        df.rename(columns={'roe':'roe'+str(i)},inplace=True)
        return df
    df31=roe_value(1,t1,temp_list)
    df32=roe_value(2,t2,temp_list)
    df33=roe_value(3,t3,temp_list)
    df34=roe_value(4,t4,temp_list)
    df3=df31.merge(df32,on='code')
    df3=df3.merge(df33,on='code')
    df3=df3.merge(df34,on='code')
    # 连续四个季度ROE处于市场平均之上
    dfx3=df3[(df3.roe1 >=df3.roe1.mean()) & (df3.roe2>=df3.roe2.mean()) & (df3.roe3>=df3.roe3.mean())&(df3.roe4>=df3.roe4.mean())]   
    l3=set(dfx3.code.values)

    #4.近三年自由现金流量均为正值。（cash_flow.net_operate_cash_flow - cash_flow.net_invest_cash_flow）
    # 实际年报数据需要在4月底才能公布完上一年的年报。
    y =int(context.current_dt.year)
    if context.current_dt.month>=5:
        dt1,dt2,dt3=str(y-1),str(y-2),str(y-3)
    else:
        dt1,dt2,dt3=str(y-2),str(y-3),str(y-4)
    def FCF(i,date,stocks):
        df=get_fundamentals(query(
                cash_flow.code,
                cash_flow.net_operate_cash_flow,
                cash_flow.net_invest_cash_flow
            ).filter(
                valuation.code.in_(stocks)
            ),statDate=date)
        df['FCF'+str(i)]=df['net_operate_cash_flow']+df['net_invest_cash_flow']
        df.drop(['net_operate_cash_flow','net_invest_cash_flow'],axis=1,inplace=True)
        return df
    df41= FCF(1,dt1,temp_list)
    df42= FCF(2,dt2,temp_list)
    df43= FCF(3,dt3,temp_list)
    df4=df41.merge(df42,on='code')
    df4=df4.merge(df43,on='code')
    dfx4=df4[pd.eval('(df4.FCF1 >0) & (df4.FCF2 >0) & (df4.FCF3 >0)')]   
    l4=set(dfx4.code.values)

    #5.近四季营收成长率介于0%至50%（）。    'IRYOY':indicator.inc_revenue_year_on_year, # 营业收入同比增长率(%)
    def REVENUE_value(i,date,l2):
        df=get_fundamentals(query(
            indicator.code,
            indicator.inc_revenue_year_on_year
        ).filter(
            indicator.code.in_(l2),
            indicator.inc_revenue_year_on_year>6,
            indicator.inc_revenue_year_on_year<50
        ),statDate=date)
        df.rename(columns={'inc_revenue_year_on_year':'inc_revenue_year_on_year'+str(i)},inplace=True)
        return df
    df51=REVENUE_value(1,t1,temp_list)
    df52=REVENUE_value(2,t2,temp_list)
    df53=REVENUE_value(3,t3,temp_list)
    df54=REVENUE_value(4,t4,temp_list)
    df5=df51.merge(df52,on='code')
    df5=df5.merge(df53,on='code')
    df5=df5.merge(df54,on='code')
    l5=set(df5.code.values)
    
    #6、扣非净利润近四季盈余成长率介于8%至50%
    def profit_value(i,date,l2):
        df=get_fundamentals(query(
                indicator.code,
                indicator.inc_net_profit_to_shareholders_year_on_year
            ).filter(
                indicator.code.in_(l2),
                indicator.inc_net_profit_to_shareholders_year_on_year>6,
                indicator.inc_revenue_year_on_year<50
            ),statDate=date)
        df.rename(columns={'inc_net_profit_to_shareholders_year_on_year':'inc_net_profit_to_shareholders_year_on_year'+str(i)},inplace=True)
        return df
    df61=profit_value(1,t1,temp_list)
    df62=profit_value(2,t2,temp_list)
    df63=profit_value(3,t3,temp_list)
    df64=profit_value(4,t4,temp_list)
    df6=df61.merge(df62,on='code')
    df6=df5.merge(df63,on='code')
    df6=df5.merge(df64,on='code')
    l6=set(df6.code.values)  
    
    
    #6.近四季EPS在0.04至1
    # def eps_value(i,date,l2):
    #     df=get_fundamentals(query(
    #      indicator.code,
    #      indicator.eps
    #      ).filter(
    #         indicator.code.in_(l2),
    #         indicator.eps>0.04,
    #         indicator.eps<1
    #             ),statDate=date)
    #     df.rename(columns={'eps':'epsr'+str(i)},inplace=True)
    #     return df
    # df61=eps_value(1,t1,temp_list)
    # df62=eps_value(2,t2,temp_list)
    # df63=eps_value(3,t3,temp_list)
    # df64=eps_value(4,t4,temp_list)
    # df6=df61.merge(df62,on='code')
    # df6=df6.merge(df63,on='code')
    # df6=df6.merge(df64,on='code')
    # l6=set(df6.code.values)
    return list(l1 & l2 &l3 & l4 & l5 & l6)
    
#去极值（分位数法）  
def winsorize(se):
    q = se.quantile([0.025, 0.975])
    if isinstance(q, pd.Series) and len(q) == 2:
        se[se < q.iloc[0]] = q.iloc[0]
        se[se > q.iloc[1]] = q.iloc[1]
    return se
    
#获取报告季报时间,由于实际财报公布时间和当前日期不一致，为了防止未来函数，我们对取报告的时间进行规定。
def statDate_value(context):
    dt=context.current_dt
    if 9>dt.month>=5:
        statDate1=str(dt.year)+'q1'
        statDate2=str(dt.year-1)+'q4'
        statDate3=str(dt.year-1)+'q3'
        statDate4=str(dt.year-1)+'q2'
    elif 11>dt.month>=9:
        statDate1=str(dt.year)+'q2'
        statDate2=str(dt.year)+'q1'
        statDate3=str(dt.year-1)+'q4'
        statDate4=str(dt.year-1)+'q3'
    elif dt.month>=11:
        statDate1=str(dt.year)+'q3'
        statDate2=str(dt.year)+'q2'
        statDate3=str(dt.year)+'q1'
        statDate4=str(dt.year-1)+'q4'
    else:
        statDate1=str(dt.year-1)+'q4'
        statDate2=str(dt.year-1)+'q3'
        statDate3=str(dt.year-1)+'q2'
        statDate4=str(dt.year-1)+'q1'
    return statDate1,statDate2,statDate3,statDate4
    
# 行业过滤
def industry_filter(context, security_list, industry_list):
    if len(industry_list) == 0:
        # 返回股票列表
        return security_list
    else:
        securities = []
        for s in industry_list:
            temp_securities = get_industry_stocks(s)
            securities += temp_securities
        security_list = [stock for stock in security_list if stock in securities]
        # 返回股票列表
        return security_list

# 剔除停牌、st股
def filter_st_paused(context):
    temp_list = list(get_all_securities(types=['stock']).index)    
    #剔除停牌股
    all_data = get_current_data()
    temp_list = [stock for stock in temp_list if not all_data[stock].paused]
    #剔除st股
    temp_list = [stock for stock in temp_list if not all_data[stock].is_st]
    return temp_list

# 资金分配
def Allocation_of_funds(context,buy_lists,max_hold_stocknum,max_buy_value):
    current_position=len(context.portfolio.positions.keys())
    if max_hold_stocknum-current_position>0:
        num=min(max_hold_stocknum-current_position,len(buy_lists))
        value=context.portfolio.available_cash/num
        if not max_buy_value:
            max_buy_value=context.portfolio.available_cash
        cash=min(value,max_buy_value)
    return cash
    
# 风险再平衡
def Risk_rebalancing(context,buy_lists):
    tolal_value=context.portfolio.total_value
    num1=len(context.portfolio.positions.keys())
    num2=len(buy_lists)
    if num1+num2>0:
        cash=tolal_value/(num1+num2)
    else:
        cash=tolal_value
    return cash
    