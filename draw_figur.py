import talib
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf
import tools
from StockInfoData import StockInfoData
from pandas import DataFrame

show_volume = False

PICS = []
panelCount = 0

def draw_stock(table:DataFrame,stockInfo: StockInfoData):#table = 表 stockInfo = 股票資訊結構
    mc = mpf.make_marketcolors(up = 'r',down = 'g',edge = '',wick = 'inherit',volume = 'inherit')
    s = mpf.make_mpf_style(base_mpf_style = 'charles',marketcolors = mc)
    mpf.plot(table,type = "candle",volume=show_volume,style = s,addplot = PICS,figsize=(13,7),title = str(stockInfo.number))
def draw_SMA(table:DataFrame,day:int,stockInfo: StockInfoData):#table = 表 day = 幾日均線 stockInfo = 股票資訊結構
    mclose = talib.SMA(np.array(table['Close']), day)#用np.array才可以將均線和蠟燭圖放一起
    PICS.append(mpf.make_addplot(mclose,panel = 0))
def draw_BollingerBands(table:DataFrame,day:int,stockInfo: StockInfoData):#table = 表 day = 幾日均線 stockInfo = 股票資訊結構
    upper, middle, lower = talib.BBANDS(np.array(table['Close']))
    PICS.append(mpf.make_addplot(upper,panel = 0))
    PICS.append(mpf.make_addplot(middle,panel = 0))
    PICS.append(mpf.make_addplot(lower,panel = 0))
def draw_KD(table:DataFrame,stockInfo: StockInfoData):#table = 表 stockInfo = 股票資訊結構
    table['k'],table['d'] = talib.STOCH(table['High'],table['Low'],table['Close'])
    table['k'].fillna(value=0,inplace = True)
    table['d'].fillna(value=0,inplace = True)
    global panelCount
    panelCount = panelCount + 1
    PICS.append(mpf.make_addplot(table['k'],panel = panelCount,ylabel = "KD",color='red'))
    PICS.append(mpf.make_addplot(table['d'],panel = panelCount,color='blue'))
def draw_Volume(table:DataFrame,stockInfo: StockInfoData):#table = 表 stockInfo = 股票資訊結構
    global show_volume,panelCount
    show_volume = True
    panelCount = panelCount + 1
def draw_RSI(table:DataFrame,stockInfo: StockInfoData):#table = 表 stockInfo = 股票資訊結構
    mRSI = talib.RSI(np.array(table['Close']))
    global panelCount
    panelCount = panelCount + 1
    PICS.append(mpf.make_addplot(mRSI,panel = panelCount,ylabel = "RSI"))
def draw_ADL(table:DataFrame):
    PICS.append(mpf.make_addplot(table,panel = 0,color='blue',ylabel = "ADL"))
def draw_ADLs(table:DataFrame):
    global panelCount
    panelCount = panelCount + 1
    table_fast = tools.smooth_Data(table,10)
    table_slow = tools.smooth_Data(table,30)
    PICS.append(mpf.make_addplot(table_fast,panel = panelCount,color='red'))
    PICS.append(mpf.make_addplot(table_slow,panel = panelCount,color='blue',ylabel = "ADLs"))
def draw_MACD(table:DataFrame):
    global panelCount
    panelCount = panelCount + 1
    macd, macdsignal, macdhist = talib.MACD(table['Close'])
    PICS.append(mpf.make_addplot(macd,panel = panelCount,ylabel = 'MACD',color='blue'))
    PICS.append(mpf.make_addplot(macdsignal,panel = panelCount,color='red'))
    PICS.append(mpf.make_addplot(macdhist,type = 'bar',panel = panelCount))
def draw_RP(table:DataFrame,stockNum:int,columnName:str,title:str,ylabel:str):
    axx = plt.axes()
    axx.plot(table[columnName],label = title)
    plt.xlabel("date")
    plt.ylabel(ylabel)
    plt.title(stockNum)
    plt.show()
def draw_backtest(data:DataFrame):
    ax4 = plt.axes()
    ax4.plot(data,label = '回測結果',color ='b')
    plt.xlabel("date")
    plt.ylabel("%")
    plt.show()
def draw_backtest2(data:DataFrame):
    ax5 = plt.axes()
    ax5.plot(data,label = '回測結果',color ='r')
    plt.xlabel("date")
    plt.ylabel("number")
    plt.show()
def draw_Show():
    plt.show()
def Clear_PICS():
    global PICS,panelCount,show_volume
    PICS = []
    panelCount = 0
    show_volume = False
    
    

