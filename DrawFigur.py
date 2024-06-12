import talib
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf
import Tools
from StockInfoData import StockInfoData
from pandas import DataFrame

class DrawFigur():
    def __init__(self) -> None:
        self.show_volume = False
        self.PICS = []
        self.panelCount = 0
    def draw_stock(self,table:DataFrame,stockInfo: StockInfoData):#table = 表 stockInfo = 股票資訊結構
        mc = mpf.make_marketcolors(up = 'r',down = 'g',edge = '',wick = 'inherit',volume = 'inherit')
        s = mpf.make_mpf_style(base_mpf_style = 'charles',marketcolors = mc)
        mpf.plot(table,type = "candle",volume=self.show_volume,style = s,addplot = self.PICS,figsize=(13,7),title = str(stockInfo.number))
    def draw_SMA(self,table:DataFrame,day:int,stockInfo: StockInfoData):#table = 表 day = 幾日均線 stockInfo = 股票資訊結構
        mclose = talib.SMA(np.array(table['Close']), day)#用np.array才可以將均線和蠟燭圖放一起
        self.PICS.append(mpf.make_addplot(mclose,panel = 0))
    def draw_BollingerBands(self,table:DataFrame,day:int,stockInfo: StockInfoData):#table = 表 day = 幾日均線 stockInfo = 股票資訊結構
        upper, middle, lower = talib.BBANDS(np.array(table['Close']))
        self.PICS.append(mpf.make_addplot(upper,panel = 0))
        self.PICS.append(mpf.make_addplot(middle,panel = 0))
        self.PICS.append(mpf.make_addplot(lower,panel = 0))
    def draw_KD(self,table:DataFrame,stockInfo: StockInfoData):#table = 表 stockInfo = 股票資訊結構
        table['k'],table['d'] = talib.STOCH(table['High'],table['Low'],table['Close'])
        table['k'].fillna(value=0,inplace = True)
        table['d'].fillna(value=0,inplace = True)
        self.panelCount = self.panelCount + 1
        self.PICS.append(mpf.make_addplot(table['k'],panel = self.panelCount,ylabel = "KD",color='red'))
        self.PICS.append(mpf.make_addplot(table['d'],panel = self.panelCount,color='blue'))
    def draw_Volume(self,table:DataFrame,stockInfo: StockInfoData):#table = 表 stockInfo = 股票資訊結構
        self.show_volume = True
        self.panelCount = self.panelCount + 1
    def draw_RSI(self,table:DataFrame,stockInfo: StockInfoData):#table = 表 stockInfo = 股票資訊結構
        mRSI = talib.RSI(np.array(table['Close']))
        self.panelCount = self.panelCount + 1
        self.PICS.append(mpf.make_addplot(mRSI,panel = self.panelCount,ylabel = "RSI"))
    def draw_ADL(self,table:DataFrame):
        self.panelCount = self.panelCount + 1
        self.PICS.append(mpf.make_addplot(table,panel = self.panelCount,color='blue',ylabel = "ADL"))
    def draw_ADLs(self,table:DataFrame):
        self.panelCount = self.panelCount + 1
        table_fast = Tools.smooth_Data(table,10)
        table_slow = Tools.smooth_Data(table,30)
        self.PICS.append(mpf.make_addplot(table_fast,panel = self.panelCount,color='red'))
        self.PICS.append(mpf.make_addplot(table_slow,panel = self.panelCount,color='blue',ylabel = "ADLs"))
    def draw_MACD(self,table:DataFrame):
        self.panelCount = self.panelCount + 1
        macd, macdsignal, macdhist = talib.MACD(table['Close'])
        self.PICS.append(mpf.make_addplot(macd,panel = self.panelCount,ylabel = 'MACD',color='blue'))
        self.PICS.append(mpf.make_addplot(macdsignal,panel = self.panelCount,color='red'))
        self.PICS.append(mpf.make_addplot(macdhist,type = 'bar',panel = self.panelCount))
    def draw_RP(self, table:DataFrame,stockNum:int,columnName:str,title:str,ylabel:str):
        axx = plt.axes()
        axx.plot(table[columnName],label = title)
        plt.xlabel("date")
        plt.ylabel(ylabel)
        plt.title(stockNum)
        plt.show()
    def draw_backtest(self,data:DataFrame):
        ax4 = plt.axes()
        ax4.plot(data,label = '回測結果',color ='b')
        plt.xlabel("date")
        plt.ylabel("%")
        plt.show()
    def draw_backtest2(self,data:DataFrame):
        ax5 = plt.axes()
        ax5.plot(data,label = '回測結果',color ='r')
        plt.xlabel("date")
        plt.ylabel("number")
        plt.show()
    def draw_Show(self):
        plt.show()
    def Clear_PICS(self):
        self.PICS = []
        self.panelCount = 0
        self.show_volume = False