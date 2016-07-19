import numpy as np
import talib
import math

def getExtremem(arrayHighPriceResult, arrayLowPriceResult):
    np_arrayHighPriceResult = np.array(arrayHighPriceResult[:-1])
    np_arrayLowPriceResult = np.array(arrayLowPriceResult[:-1])
    maxResult = np_arrayHighPriceResult.max()
    minResult = np_arrayLowPriceResult.min()
    return [maxResult, minResult]

def getAtrAndUnit(atrArrayResult, atrLengthResult, portfolioValueResult):
    atr = atrArrayResult[atrLengthResult-1]
    unit = math.floor(portfolioValueResult * .01 / atr)
    return [atr, unit]

def getStopPrice(firstOpenPriceResult, units_hold_result, atrResult):
    stopPrice =  firstOpenPriceResult - 2*atrResult + (units_hold_result-1)*0.5*atrResult
    return stopPrice


def init(context):
    context.tradedayNum = 0
    context.unit = 0
    context.atr = 0
    context.tradingSignal = 'start'
    context.preTradingSignal = ''
    context.units_hold_max = 4
    context.units_hold = 0
    context.quantity = 0
    context.max_add = 0
    context.firstOpenPrice = 0
    context.s = 'CSI300.INDX'
    context.openObserveTime = 55;
    context.closeObserveTime = 20;
    context.atrTime = 20;

def handle_bar(context, bar_dict):
    portfolioValue = context.portfolio.portfolio_value
    highPrice = history(context.openObserveTime+1, '1d', 'high')[context.s]
    lowPriceForAtr = history(context.openObserveTime+1, '1d', 'low')[context.s]
    lowPriceForExtremem = history(context.closeObserveTime+1, '1d', 'low')[context.s]
    closePrice = history(context.openObserveTime+2, '1d', 'close')[context.s]
    closePriceForAtr = closePrice[:-1]

    atrArray = talib.ATR(highPrice.values, lowPriceForAtr.values, closePriceForAtr.values, timeperiod=context.atrTime)

    maxx = getExtremem(highPrice.values, lowPriceForExtremem.values)[0]
    minn = getExtremem(highPrice.values, lowPriceForExtremem.values)[1]
    atr = atrArray[-2]


    if (context.tradingSignal != 'start'):
        if (context.units_hold != 0):
            context.max_add += 0.5 * getAtrAndUnit(atrArray, atrArray.size, portfolioValue)[0]
    else:
        context.max_add = bar_dict[context.s].last


    curPosition = context.portfolio.positions[context.s].quantity
    availableCash = context.portfolio.cash
    marketValue = context.portfolio.market_value


    if (curPosition > 0 and bar_dict[context.s].last < getStopPrice(context.firstOpenPrice, context.units_hold, atr)):
        context.tradingSignal = 'stop'
    else:
        if (curPosition > 0 and bar_dict[context.s].last < minn):
            context.tradingSignal = 'exit'
        else:
            if (bar_dict[context.s].last > context.max_add and context.units_hold != 0 and context.units_hold < context.units_hold_max and availableCash > bar_dict[context.s].last*context.unit):
                context.tradingSignal = 'entry_add'
            else:
                if (bar_dict[context.s].last > maxx and context.units_hold == 0):
                    context.max_add = bar_dict[context.s].last
                    context.tradingSignal = 'entry'


    atr = getAtrAndUnit(atrArray, atrArray.size, portfolioValue)[0]
    if context.tradedayNum % 5 == 0:
        context.unit = getAtrAndUnit(atrArray, atrArray.size, portfolioValue)[1]
    context.tradedayNum += 1
    context.quantity = context.unit



    if (context.tradingSignal != context.preTradingSignal or (context.units_hold < context.units_hold_max and context.units_hold > 1) or context.tradingSignal == 'stop'):

        if context.tradingSignal == 'entry':
            context.quantity = context.unit
            if availableCash > bar_dict[context.s].last*context.quantity:
                order_shares(context.s, context.quantity)
                context.firstOpenPrice = bar_dict[context.s].last
                context.units_hold = 1


        if context.tradingSignal == 'entry_add':
            context.quantity = context.unit
            order_shares(context.s, context.quantity)
            context.units_hold += 1


        if context.tradingSignal == 'stop':
            if (context.units_hold > 0):
                order_shares(context.s, -context.quantity)
                context.units_hold -= 1


        if context.tradingSignal == 'exit':
            if curPosition > 0:
                order_shares(context.s, -curPosition)
                context.units_hold = 0


    context.preTradingSignal = context.tradingSignal
