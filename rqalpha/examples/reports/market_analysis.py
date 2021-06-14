# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: louis
@Time: 2021-04-20 11:34
"""

# 分析指数近期走势
import datetime

import numpy as np
import pandas as pd
import datetime as dt
import warnings
import seaborn as sns
from numba import jit, int64, int32
from decimal import Decimal, ROUND_HALF_UP

warnings.filterwarnings('ignore')

from rqalpha.data.bar_dict_price_board import BarDictPriceBoard
from rqalpha.data.base_data_source import BaseDataSource
from rqalpha.data.data_proxy import DataProxy
from rqalpha.model.instrument import Instrument

data_proxy = DataProxy(BaseDataSource('/Users/louis/.rqalpha/bundle' ,{}), BarDictPriceBoard)

def round_up(number, num_digits):
    """
    按指定位数对数值进行四舍五入。
    :param number:要四舍五入的数字。
    :param num_digits:要进行四舍五入运算的位数。
    :return:返回结果。
    """
    if num_digits > 0:
        res = round_up(number * 10, num_digits - 1) / 10
    else:
        res = Decimal(number * 10 ** num_digits).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * 10 ** -num_digits
    return res


class MarketView(object):
    
    def __init__(self, data_proxy):
        self.data_proxy = data_proxy
        pass
    
    @staticmethod
    def colors():
        colors = ['#FFFFCC', '#99FF99', '#66FFFF', '#3333FF', '#FF00FF', '#333333', '#FFFF99', '#66FF66', '#33FFFF',
                  '#0000FF', '#FF00CC', '#666666', '#FFFF66', '#33FF33', '#00FFFF', '#3300FF', '#CC0099', '#999999',
                  '#FFFF33', '#00FF00', '#00CCFF', '#3300CC', '#FF33CC', '#CCCCCC', '#FFFF00', '#00FF33', '#0099CC',
                  '#6633FF', '#990066', '#FFFFFF', '#CCFF00', '#00CC33', '#33CCFF', '#330099', '#CC3399', '#FF3300',
                  '#99CC00', '#33FF66', '#006699', '#6633CC', '#FF66CC', '#CC3300', '#CCFF33', '#009933', '#3399CC',
                  '#9966FF', '#FF0099', '#FF6633', '#669900', '#33CC66', '#66CCFF', '#6600FF', '#660033', '#993300',
                  '#99CC33', '#66FF99', '#0099FF', '#330066', '#993366', '#CC6633', '#CCFF66', '#00FF66', '#003366',
                  '#663399', '#CC6699', '#FF9966', '#99FF00', '#006633', '#336699', '#9966CC', '#CC0066', '#FF6600',
                  '#336600', '#339966', '#6699CC', '#6600CC', '#FF99CC', '#663300', '#669933', '#66CC99', '#0066CC',
                  '#CC99FF', '#FF3399', '#996633', '#99CC66', '#00CC66', '#99CCFF', '#9933FF', '#FF0066', '#CC9966',
                  '#66CC00', '#99FFCC', '#3399FF', '#9900FF', '#990033', '#CC6600', '#CCFF99', '#33FF99', '#0066FF',
                  '#660099', '#CC3366', '#FFCC99', '#99FF33', '#00FF99', '#003399', '#9933CC', '#FF6699', '#FF9933',
                  '#66FF00', '#009966', '#3366CC', '#CC66FF', '#CC0033', '#FF9900', '#339900', '#33CC99', '#6699FF',
                  '#9900CC', '#FF3366', '#996600', '#66CC33', '#66FFCC', '#0033CC', '#CC33FF', '#FF0033', '#CC9933',
                  '#99FF66', '#00CC99', '#3366FF', '#CC00FF', '#330000', '#FFCC66', '#33CC00', '#33FFCC', '#0033FF',
                  '#330033', '#663333', '#CC9900', '#66FF33', '#00FFCC', '#000033', '#663366', '#660000', '#FFCC33',
                  '#33FF00', '#003333', '#333366', '#660066', '#996666', '#FFCC00', '#003300', '#336666', '#000066',
                  '#996699', '#993333', '#333300', '#336633', '#006666', '#666699', '#993399', '#990000', '#666633',
                  '#006600', '#669999', '#333399', '#990099', '#CC9999', '#666600', '#669966', '#339999', '#000099',
                  '#CC99CC', '#CC6666', '#999966', '#339933', '#009999', '#9999CC', '#CC66CC', '#CC3333', '#999933',
                  '#009900', '#99CCCC', '#6666CC', '#CC33CC', '#CC0000', '#999900', '#99CC99', '#66CCCC', '#3333CC',
                  '#CC00CC', '#FFCCCC', '#CCCC99', '#66CC66', '#33CCCC', '#0000CC', '#FFCCFF', '#FF9999', '#CCCC66',
                  '#33CC33', '#00CCCC', '#CCCCFF', '#FF99FF', '#FF6666', '#CCCC33', '#00CC00', '#CCFFFF', '#9999FF',
                  '#FF66FF', '#FF3333', '#CCCC00', '#CCFFCC', '#99FFFF', '#6666FF', '#FF33FF', '#FF0000']
        return colors

    @staticmethod
    def panel_data(date=dt.datetime.now(), count=120, stock_min_list_days=180):
        """返回数据panel"""
        instruments = data_proxy.all_instruments(["CS"])[:10]
        instrs = [instrument for instrument in instruments if instrument.listed_date < (
                    date - dt.timedelta(days=stock_min_list_days)) and instrument.status == 'Active'
                  and instrument.board_type == 'MainBoard']
    
        datas = []
        for ins in instrs:
            print(ins.order_book_id)
            data = data_proxy.history_bars(ins.order_book_id, dt=date, bar_count=count, frequency='1d',
                                                        field=['datetime', 'open', 'high', 'low', 'close', 'limit_up', 'limit_down',
                                                               'volume', 'total_turnover'])
            datas.append(data)
        panel = np.vstack(tuple(datas))
        cols = [name.order_book_id for name in instrs]
        return cols, panel
    
    # @staticmethod
    # def industry(stock_list=[], industry_category='zjw'):
    #     """返回股票行业"""
    #     if stock_list:
    #         return [Instrument(order_book_id).industry_name for order_book_id in stock_list]
    #     else:
    #         instruments = data_proxy.all_instruments(["CS"])
    #         return [instrument.industry_name for instrument in instruments]
    
    
    @staticmethod
    def index_change(date=dt.datetime.now()):
        zhishu_list = ['000001.XSHG', '000016.XSHG', '000300.XSHG', '000905.XSHG', '399001.XSHE', '399005.XSHE',
                       '399006.XSHE']
        #panel = get_price(zhishu_list, end_date=date, count=11, fields=['close', 'volume', 'money'])
        datas = []
        for order_book_id in zhishu_list:
            data = data_proxy.history_bars(order_book_id, dt=date, bar_count=11, frequency='1d',
                                           field=['close', 'volume', 'total_turnover'])
            
            datas.append(data)
        panel = np.vstack(tuple(datas))
        
        s_close = panel['close'][:,-1]
        s_return1 = ((panel['close'][:,-1] / panel['close'][:,-2]) - 1) * 100
        s_return3 = ((panel['close'][:,-1] / panel['close'][:,-4]) - 1) * 100
        s_return5 = ((panel['close'][:,-1] / panel['close'][:,-6]) - 1) * 100
        s_volume = ((panel['volume'][:,-1] / panel['volume'][:,-2]) - 1) * 100
        s_volume3 = ((panel['volume'][:,-3:].sum(axis=1) / panel['volume'][:,-6:-3].sum(axis=1)) - 1) * 100
        s_volume5 = ((panel['volume'][:,-5:].sum(axis=1) / panel['volume'][:,-10:-5].sum(axis=1)) - 1) * 100
        s_money = ((panel['total_turnover'][:,-1] / panel['total_turnover'][:,-2]) - 1) * 100
        s_money3 = ((panel['total_turnover'][:,-3:].sum(axis=1) / panel['total_turnover'][:,-6:-3].sum(axis=1)) - 1) * 100
        s_money5 = ((panel['total_turnover'][:,-5:].sum(axis=1) / panel['total_turnover'][:,-10:-5].sum(axis=1)) - 1) * 100
        
        tt = pd.DataFrame({'指数值':s_close.tolist(), '涨跌幅%':s_return1.tolist()})
        df = pd.DataFrame(data={'指数值': s_close.tolist(), '涨跌幅%': s_return1.tolist(), '3日涨跌%': s_return3.tolist(), '5日涨跌%': s_return5.tolist(),
                           '1日量变%': s_volume.tolist(), '3日量变%': s_volume3.tolist(), '5日量变%': s_volume5.tolist(), '1日额变%': s_money.tolist(),
                           '3日额变%': s_money3.tolist(), '5日额变%': s_money5.tolist()}, index=zhishu_list)
        
        df.index = ['上证指数', '上证50', '沪深300', '中证500', '深成指', '中小板指', '创业板指']
        df = df.round(2)
        cm = sns.light_palette("green", as_cmap=True)
        return df.style.background_gradient(cmap=cm,
                                            subset=['涨跌幅%', '3日涨跌%', '5日涨跌%', '1日量变%', '3日量变%', '5日量变%', '1日额变%',
                                                    '3日额变%', '5日额变%']).set_caption(
            "{date}指数变化".format(date=date.strftime('%Y-%m-%d')))
    
    @staticmethod
    def high_limit_stat(panel, count=14):
        """
        涨停统计
        """
        df_pre_close = pd.DataFrame(panel['close']).shift(axis=1)
        
        s_zt = (panel['close'] == panel['limit_up']).sum(axis=0)
        s_zb = ((panel['high'] == panel['limit_up']) & (
            (panel['close'] < panel['limit_up']))).sum(axis=0)
        s_up7p = (panel['close'] > df_pre_close * 1.07).sum(axis=0)
        s_up57 = ((panel['close'] > df_pre_close * 1.05) & (
                panel['close'] <= df_pre_close * 1.07)).sum(axis=0)
        s_up35 = ((panel['close'] > df_pre_close * 1.03) & (
                panel['close'] <= df_pre_close * 1.05)).sum(axis=0)
        s_up03 = ((panel['close'] > df_pre_close * 1.00) & (
                panel['close'] <= df_pre_close * 1.03)).sum(axis=0)
        s_dn03 = ((panel['close'] <= df_pre_close * 1.00) & (
                panel['close'] >= df_pre_close * 0.97)).sum(axis=0)
        s_dn35 = ((panel['close'] < df_pre_close * 0.97) & (
                panel['close'] <= df_pre_close * 0.95)).sum(axis=0)
        s_dn57 = ((panel['close'] < df_pre_close * 0.95) & (
                panel['close'] <= df_pre_close * 0.93)).sum(axis=0)
        s_dn7p = ((panel['close'] < df_pre_close * 0.93) & (
                panel['close'] > df_pre_close * 0.90)).sum(axis=0)
        s_dt = (panel['low'] == panel['limit_down']).sum(axis=0)
        df = pd.DataFrame({'涨停': s_zt.tolist(),
                           '+7-10': s_up7p.tolist(), '+5-7': s_up57.tolist(), '+3-5': s_up35.tolist(), '+0-3': s_up03.tolist(),
                           '-0-3': s_dn03.tolist(), '-3-5': s_dn35.tolist(), '-5-7': s_dn57.tolist(), '-7-10': s_dn7p.tolist(), '跌停': s_dt.tolist(),
                           '炸板': s_zb.tolist()}, index=panel['datetime'][0,:].tolist())
        df = df.sort_index(ascending=False)
        df1 = df.iloc[:count]
        start_date = datetime.datetime.strptime(str(df1.index[-1]), '%Y%m%d%H%M%S')
        end_date = datetime.datetime.strptime(str(df1.index[0]), '%Y%m%d%H%M%S')
        df1.index = [datetime.datetime.strptime(str(d), '%Y%m%d%H%M%S').strftime("%Y-%m-%d") for d in df1.index]
        cm = sns.light_palette("green", as_cmap=True)
        return df1.style.background_gradient(cmap=cm, axis=1).\
            set_caption(
            "{start}到{end}市场热度变化".format(start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d")))
    
    @staticmethod
    @jit(int32[:, :](int64[:, :]))
    def lianban(arr):
        """连板数统计 arr值含义 0没有涨停/1涨停/2停牌"""
        ret = np.zeros((arr.shape[0], arr.shape[1]), np.int32)
        for row in np.arange(1, arr.shape[0]):
            for col in np.arange(0, arr.shape[1]):
                if arr[row, col] == 1 and arr[row - 1, col] == 0:  # 首板
                    ret[row, col] = 1
                elif arr[row, col] == 1 and arr[row - 1, col] == 1:  # 连板
                    ret[row, col] = ret[row - 1, col] + 1
                elif arr[row, col] == 1 and arr[row - 1, col] == -1:  # 前一日停牌,如果是涨停停牌,累加停牌前涨停数
                    i = row - 1
                    while arr[i, col] == -1:
                        i = i - 1
                    if arr[i, col] == 1:
                        ret[row, col] = ret[i, col] + 1
        return ret
    
    @staticmethod
    def high_limit_record(panel, cols, filter_st=False):
        """日期，股票代码，第几个涨停 """
        # 涨停
        # arr_up = ((panel['close'].values == panel['high_limit'].values) & (panel['paused'].values == 0)).astype(int)
        arr_up = (panel['close'] == panel['limit_up']).astype(int)
        # ST股票涨跌停5%
        st = panel['close'][:,(panel['limit_up'] < panel['limit_down'] * 1.2).any(axis=0)]
        # 构建二维数组，1代表涨停，-1代表停牌，0 代表其他
        #arr_paused = np.where(panel['paused'] > 0, -1, 0)
        #arr_cb = np.where(arr_up > 0, arr_up, arr_paused)
        # 涨停累加DataFrame
        df = pd.DataFrame(MarketView.lianban(arr_up), index=cols, columns=panel.dtype.names)
        if filter_st:
            st_columns = panel['close'].columns[
                (panel['limit_up'] < panel['limit_down'] * 1.2).any(axis=0)]
            df = df[list(set(list(df.columns)).difference(set(list(st_columns))))]
        # 过滤涨停记录->日期，股票代码，第几个涨停
        df1 = df.reset_index().melt(id_vars='index')
        df2 = df1[df1['value'] > 0]
        return df2
    
    @staticmethod
    def 板块热度(df_category, panel, return_filter=0.05):
        """支持股票和类别 多对多关系，格式:股票代码,类别 """
        # df_cat=df_category[df_category.iloc[:,0].isin(list(panel['close'].columns))]
        arr_relation = df_category.values
        code_sorted = np.sort(np.unique(arr_relation[:, 0]))
        category_sorted = np.sort(np.unique(arr_relation[:, 1]))
        
        code_idx = np.searchsorted(code_sorted, arr_relation[:, 0])
        category_idx = np.searchsorted(category_sorted, arr_relation[:, 1])
        # 多对多关系矩阵
        relation_metrix = np.zeros((code_sorted.shape[0], category_sorted.shape[0]), np.int32)
        for i in np.arange(0, arr_relation.shape[0]):
            relation_metrix[code_idx[i], category_idx[i]] = 1
        arr1 = (panel['close'][code_sorted].values > panel['pre_close'][code_sorted].values * (
                1 + return_filter)).astype(int)
        # 结果矩阵 (股票热度数组*股票类别矩阵) ->按类别加总->类别热度
        ret_cat = np.zeros((arr1.shape[0], category_sorted.shape[0]), np.int32)
        for i in np.arange(0, arr1.shape[0]):
            ret_cat[i] = (arr1[i:i + 1, :].T * relation_metrix).sum(axis=0)
        df = pd.DataFrame(ret_cat, columns=category_sorted, index=panel['close'].index)
        return df
    
    @staticmethod
    def 每日热点(df_hot, topN=5):
        """展示每日热度排行"""
        df1 = df_hot.reset_index().melt(id_vars='index').groupby('index').apply(
            lambda dx: dx.nlargest(topN, 'value')).reset_index(drop=True)
        
        def add_rank(dx):
            dx['rank'] = dx['value'].rank(ascending=False, method='first').astype(int)
            return dx
        
        df2 = df1.groupby('index').apply(add_rank)
        df2['val'] = df2['variable'] + ":" + df2['value'].astype(str)
        df3 = df2.drop_duplicates(subset=['index', 'rank']).pivot(index='index', columns='rank', values='val').iloc[
              ::-1]
        df3.index = df3.index.date
        sorted_cat = np.sort(np.unique([cat.split(":")[0] for cat in df3.values.reshape(df3.shape[0] * df3.shape[1])]))
        
        def highlight_vals(val, color='green'):
            return 'background-color: %s' % MarketView.colors()[np.searchsorted(sorted_cat, val.split(":")[0])] + "70"
        
        return df3.style.applymap(highlight_vals).set_caption('每日热度排行')
    
    @staticmethod
    def 连板数统计(df_up_limit, count=50):
        """涨停数统计矩阵"""
        # 日期，股票代码，涨停数 -> 日期(行)，涨停数(列)，股票数量(值)
        df3 = df_up_limit.groupby(['index', 'value']).count().reset_index()
        df4 = df3.pivot(index='index', columns='value', values='variable')
        
        df5 = df4.sort_index(ascending=False).iloc[:count]
        cm = sns.light_palette("green", as_cmap=True)
        df5.index = df5.index.date
        return df5.fillna(0).style.background_gradient(cmap=cm, axis=0).set_caption("连板数统计")

cols, data = MarketView.panel_data()

MarketView.index_change()

MarketView.high_limit_stat(data, cols)



