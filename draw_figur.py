import talib
import numpy as np
import matplotlib.pyplot as plt
import mpl_finance as mpf

fig = plt.figure(figsize=(24,20))
ax = fig.add_axes([0,0.3,1,0.4])
ax2 = fig.add_axes([0,0.2,1,0.1])
ax3 = fig.add_axes([0,0,1,0.2])

def draw_stock(table,stockInfo):#table = 表 stockInfo = 股票資訊結構
    ax.set_xticks(range(0,len(table.index),30))
    ax.set_xticklabels(table.index[::30])
    mpf.candlestick2_ochl(ax,table['Open'],table['Close'],
                            table['High'],table['Low'],
                            width=0.6,colorup='r',colordown='g',alpha=0.75)
def draw_SMA(table,day,stockInfo):#table = 表 day = 幾日均線 stockInfo = 股票資訊結構
    mclose = talib.SMA(np.array(table['Close']), day)#用np.array才可以將均線和蠟燭圖放一起
    ax.plot(mclose,label = stockInfo.number+' '+str(day)+ ' days-'+'SMA')
def draw_KD(table,stockInfo):#table = 表 stockInfo = 股票資訊結構
    table['k'],table['d'] = talib.STOCH(table['High'],table['Low'],table['Close'])
    table['k'].fillna(value=0,inplace = True)
    table['d'].fillna(value=0,inplace = True)
    ax2.set_xticks(range(0,len(table.index),30))
    ax2.set_xticklabels(table.index[::30])
    ax2.plot(table['k'],label= 'K')
    ax2.plot(table['d'],label = 'D')
def draw_Volume(table,stockInfo):#table = 表 stockInfo = 股票資訊結構
    ax3.set_xticks(range(0,len(table.index),30))
    ax3.set_xticklabels(table.index[::30])
    mpf.volume_overlay(ax3,table['Open'],table['Close'],
                            table['Volume'],colorup='r',colordown='g',
                           width=0.5,alpha=0.8)
def draw_Show():
    ax.legend()
    ax2.legend()
    plt.show()
    