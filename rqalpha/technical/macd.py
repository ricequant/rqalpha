import talib as tl
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.ticker as mticker
import matplotlib.dates as dates
import matplotlib.dates as mdates
import datetime

class MACD:
    # 查寻一个时间段内某标的的macd信息
    def __init__(self, stock_data, fastperiod, slowperiod, signalperiod):
        close = stock_data['close']
        date = stock_data['date']
        self.dif, self.dea, self.macd = tl.MACDEXT(close, fastperiod=fastperiod, fastmatype=1, slowperiod=slowperiod, slowmatype=1, signalperiod=signalperiod, signalmatype=1)
        self.dif = pd.Series(self.dif).sort_index(ascending=False).dropna().reset_index(drop=True)
        self.dea = pd.Series(self.dea).sort_index(ascending=False).dropna().reset_index(drop=True)
        self.macd = pd.Series(self.macd).sort_index(ascending=False).dropna().reset_index(drop=True) * 2
        self.sz = len(self.dif)
        self.close = pd.Series(close).sort_index(ascending=False).reset_index(drop=True).head(self.sz)
        self.date = pd.Series(date).sort_index(ascending=False).reset_index(drop=True).head(self.sz)

    def get_date_by_index(self, N=0):
        return self.date[N]

    # 判断往前第N个时段是否为金叉，N取值范围为(0, self.sz)，缺省N=0
    def is_gold_cross(self, N=0):
        return (self.dif[N+1] < self.dea[N+1] and self.dif[N] > self.dea[N])

    # 判断往前第N个时段是否为死叉，N取值范围为(0, self.sz)，缺省N=0
    def is_death_cross(self, N=0):
        return (self.dif[N+1] > self.dea[N+1] and self.dif[N] < self.dea[N])

    # 判断往前第N个时段是否为0轴上，N取值范围为(0, self.sz)，缺省N=0
    def is_high_value(self, N=0):
        return (self.dif[N] > 0 and self.dea[N] > 0)

    # 判断往前第N个时段是否为0轴下，N取值范围为(0, self.sz)，缺省N=0
    def is_low_value(self, N=0):
        return (self.dif[N] < 0 and self.dea[N] < 0)

    # 判断往前第N个时段是否是低位二次金叉，缺省N=0
    def is_second_low_gold_cross(self, N=0):
        # 判断当前是否发生金叉，并且位置在0轴之下
        if not self.is_gold_cross(N=N) or not self.is_low_value(N=N):
            return False
        flag = False
        for i in range(N+1, self.sz-1):
            if not self.is_low_value(N=i):
                break
            if self.is_gold_cross(N=i):
                flag = True
                break
        return flag

    # 判断往前第N个时段是否是高位二次死叉，缺省N=0
    def is_second_high_death_cross(self, N=0):
        # 判断当前是否发生死叉，并且位置在0轴之上
        if not self.is_death_cross(N=N) or not self.is_high_value(N=N):
            return False
        flag = False
        for i in range(N+1, self.sz-1):
            if not self.is_high_value(N=i):
                break
            if self.is_death_cross(N=i):
                flag = True
                break
        return flag

    # 判断往前第N个时段是否是快慢线底背离(价格与DIF的背离)，缺省N=0
    # price创新低，但dif没有创新低
    def is_bottom_divergence(self, N=0):
        ret = None
        # 如果不是金叉，直接退出
        if not self.is_gold_cross(N=N):
            return ret
        step = 1
        for i in range(N+1, self.sz-1):
            #找到上一个死叉
            if step == 1 and self.is_death_cross(N=i):
                start1, end1 = N+1, i
                step = 2
            #找到上一个金叉
            if step == 2 and self.is_gold_cross(N=i):
                start2 = i+1
                step = 3
            #再找到上一个死叉
            if step == 3 and self.is_death_cross(N=i):
                end2 = i
                step = 4
                break
        if step == 4:
            # 求两个区间的最低价
            min1 = 1e8
            min2 = 1e8
            for i in range(start1, end1+1):
                if min1 > self.close[i]:
                    min1 = self.close[i]
                    id1 = i
            for i in range(start2, end2+1):
                if min2 > self.close[i]:
                    min2 = self.close[i]
                    id2 = i
            if self.close[id1] < self.close[id2] and self.dif[id1] > self.dif[id2]:
                ret = (self.date[id2], self.date[id1])
        return ret

    # 判断往前第N个时段是否是快慢线顶背离(价格与DIF的背离)，缺省N=0
    def is_top_divergence(self, N=0):
        ret = None
        # 如果不是死叉，直接退出
        if not self.is_death_cross(N=N):
            return ret
        step = 1
        for i in range(N+1, self.sz-1):
            #找到上一个金叉
            if step == 1 and self.is_gold_cross(N=i):
                start1, end1 = N+1, i
                step = 2
            #找到上一个死叉
            if step == 2 and self.is_death_cross(N=i):
                start2 = i+1
                step = 3
            #再找到上一个金叉
            if step == 3 and self.is_gold_cross(N=i):
                end2 = i
                step = 4
                break
        if step == 4:
            # 求两个区间的最高价
            max1 = -1e8
            max2 = -1e8
            id1 = 0
            id2 = 0
            for i in range(start1, end1+1):
                if max1 < self.close[i]:
                    max1 = self.close[i]
                    id1 = i
            for i in range(start2, end2+1):
                if max2 < self.close[i]:
                    max2 = self.close[i]
                    id2 = i
            if self.close[id1] > self.close[id2] and self.dif[id1] < self.dif[id2]:
                ret = (self.date[id2], self.date[id1])
        return ret

    # 将macd信息图例化
    def show_macd(self):
        dif = self.dif.sort_index(ascending=False).reset_index(drop=True)
        dea = self.dea.sort_index(ascending=False).reset_index(drop=True)
        macd = self.macd.sort_index(ascending=False).reset_index(drop=True)
        date = self.date.sort_index(ascending=False).reset_index(drop=True)
        plt.rcParams['font.sans-serif']=['SimHei']  # 用来正常显示中文标签
        plt.rcParams['axes.unicode_minus']=False  # 用来正常显示负号
        plt.figure(figsize=(20, 5))
        plt.title('MACD 金叉死叉示例图')
        plt.plot(dea)
        plt.plot(dif)
        for i in range(0, len(macd)):
            plt.bar(i, macd[i], color='r' if macd[i] > 0 else 'g')
        plt.legend(['DEA', 'DIF'], loc=2)
        plt.show()

    # 将macd的金叉与死叉标注出来
    def show_cross(self):
        dif = self.dif.sort_index(ascending=False).reset_index(drop=True)
        dea = self.dea.sort_index(ascending=False).reset_index(drop=True)
        macd = self.macd.sort_index(ascending=False).reset_index(drop=True)
        date = self.date.sort_index(ascending=False).reset_index(drop=True)
        plt.rcParams['font.sans-serif']=['SimHei']  # 用来正常显示中文标签
        plt.rcParams['axes.unicode_minus']=False  # 用来正常显示负号
        fig = plt.figure(figsize=(18, 5))
        ax = fig.add_subplot(111)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(ticker.MultipleLocator(3))
        ax.set_xlim([0, len(date)])
        ax.yaxis.grid(color='white', linestyle='--', linewidth=0.5)
        ax.patch.set_facecolor('#303030')
        ax.set_xticklabels(date[i] for i in range(0, len(date), 3))
        plt.title('MACD 金叉死叉示例图')
        plt.xticks(rotation=50)
        plt.plot(dea, color='lightblue')
        plt.plot(dif, color='white')
        for i in range(0, len(macd)):
            plt.bar(i, macd[i], color='r' if macd[i] > 0 else 'g')
        for i in range(1, len(macd)):
            if dif[i-1] < dea[i-1] and dif[i] > dea[i]:
                # 用红圈标出金叉
                plt.scatter(i, dea[i], color='', marker='o', edgecolors='red', s=150, linewidths=1.5)
            elif dif[i-1] > dea[i-1] and dif[i] < dea[i]:
                # 用绿圈标出死叉
                plt.scatter(i, dea[i], color='', marker='o', edgecolors='green', s=150, linewidths=1.5)
        plt.legend(['DEA', 'DIF'], loc=2)
        plt.show()
