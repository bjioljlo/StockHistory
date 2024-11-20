from abc import ABC, abstractmethod
from FilterService.StockHistory import OriginalStock
from FilterService.StockReportHistory import Indicator
from FilterService.GetStockData import All_fuc
from datetime import datetime
import Tools
import pandas as pd
import talib
import numpy as np

# ISignal
class IBacktestSignal(ABC):
    '''訊號觸發'''
    @abstractmethod
    def GetSignalResult(self, InputData: dict):
        pass

class TBacktestSignal(IBacktestSignal):
    '''訊號觸發實作'''
    def __init__(self) -> None:
        super(TBacktestSignal, self).__init__()

class KD_pickBacktestSignal(TBacktestSignal):
    '''KD值訊號-訊號觸發'''
    def __init__(self, _GetPrice: OriginalStock) -> None:
        super().__init__()
        self._getPrice: OriginalStock = _GetPrice
        
    def GetSignalResult(self, InputData: dict):
        All_stock_signal = dict()
        for key,_value in InputData.items():#先算出股票的買賣訊號
            if Tools.check_no_use_stock(key) == True:
                print('get_stock_price: ' + str(key) + ' in no use')
                continue
            if All_stock_signal.__contains__(key):
                continue
            self._getPrice.number = key
            table = self._getPrice.get_PriceByDate("2020-03-04")
            if table.empty:
                continue
            table_K,table_D = talib.STOCH(table['High'],table['Low'],table['Close'],fastk_period=50, slowk_period=20, slowk_matype=0, slowd_period=20, slowd_matype=0)
            table_sma10 = talib.SMA(np.array(table['Close']), 10)
            table_sma240 = talib.SMA(np.array(table['Close']), 240)
            signal_buy = (table_K > table_D)
            signal_sell = (table_K < table_D)
            signal_sma10 = table.Close < table_sma10
            signal_sma240 = table.Close > table_sma240
            signal = signal_buy.copy()
            signal = (signal_sma10 & signal_sma240 & signal_buy)
            signal[signal_sell] = -1
            All_stock_signal[key] = signal
        return All_stock_signal


# IFilter
class IBacktestFilter(ABC):
    '''篩選器'''
    @abstractmethod
    def RunFilter(self, Date: datetime):
        pass

class TBacktestFilter(IBacktestFilter):
    '''篩選器實作'''
    def __init__(self) -> None:
        super(TBacktestFilter, self).__init__()

class Regular_quotatestFilter(TBacktestFilter):
    '''定期定額-篩選器'''
    def __init__(self, _stock: str) -> None:
        super().__init__()
        self._StockNumber:str = _stock
        
    def RunFilter(self, Date: datetime):
        return self._StockNumber
        
class KD_pickBacktestFilter(TBacktestFilter):
    '''KD值選股-篩選器'''
    def __init__(self, _indicator: Indicator) -> None:
        super().__init__()
        self._Indicator:Indicator = _indicator
        
    def RunFilter(self, Date: datetime):
        Result_data = {}
        for num in range(1, 5):
            ResultKeyName = self._Indicator.name + "_data_" + str(num)
            Result_data[ResultKeyName] = pd.DataFrame(All_fuc(Tools.changeDateMonth(Date,(-3 * num)),self._Indicator).get_Filter_Auto(0,999))
            Result_data[ResultKeyName].rename(columns={self._Indicator.name :ResultKeyName},inplace=True)
        mask = Tools.MixDataFrames(Result_data)
        
        AVG_data = (mask[self._Indicator.name + "_data_1"]+mask[self._Indicator.name + "_data_2"]+
                           mask[self._Indicator.name + "_data_3"]+mask[self._Indicator.name + "_data_4"])/4

        Result_data_1 = pd.Series(mask[self._Indicator.name + "_data_1"])
        Result_data_mask = Result_data_1 > AVG_data
        Result_data = Result_data_mask[Result_data_mask]
        return Result_data
