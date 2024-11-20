from abc import ABC, abstractmethod
import sys
from StockInfoData import StockInfoSignalData
from typing import Callable
from BackTestService.BackTestStrategy import IBacktestFilter, IBacktestSignal
from datetime import datetime, timedelta

BuyStockEvent = Callable[[str], bool]

class IBackTestFilterData(ABC):
    '''回測篩選'''
    @property
    @abstractmethod
    def FilterStock(self) -> dict[str, StockInfoSignalData]:
        pass
    
    @abstractmethod
    def GoToNextWorkDay(self):
        pass
    
    @abstractmethod
    def ShouldBuyStocks(self) -> {str}:
        pass
class TBackTestFilterData(IBackTestFilterData):
    '''回測篩選實作'''   
    def __init__(self, _buyStockfun: BuyStockEvent, _filter:IBacktestFilter, _signal:IBacktestSignal, _startdate:datetime) -> None:
        super(TBackTestFilterData, self).__init__()
        self._FilterStock:dict[str, StockInfoSignalData] = {}
        self.__BuyStockfun:BuyStockEvent = _buyStockfun #買入事件
        self._Filter:IBacktestFilter = _filter #回測篩選器
        self._Signal:IBacktestSignal = _signal #回測訊號
        self._DateNow:datetime = _startdate #當前日期
    @property
    def FilterStock(self) -> dict[str, StockInfoSignalData]:
        return self._FilterStock
    @abstractmethod
    def ShouldBuyStocks(self) -> {str}:
        raise NotImplementedError( "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name))
    @abstractmethod
    def GoToNextWorkDay(self):
        raise NotImplementedError( "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name))
class Regular_quotaFilterData(TBackTestFilterData):
    '''定期定額'''
    def GoToNextWorkDay(self):
        # TODO 固定買入的訊號，買入時機由IBacktestSignal來決定，買入股票給IBacktestFilter決定
        pass
class KD_pickFilterData(TBackTestFilterData):
    '''KD值-回測篩選'''   
    # 這方法只有測試
    def _RuuFilter(self):
        self.FilterData = self._Filter.RunFilter(self._DateNow)
        self.SignalData = self._Signal.GetSignalResult(self.FilterData)
    def GoToNextWorkDay(self):
        # TODO 主要何時跑篩選還是由外部使用者決定 或者 紀錄下次篩選的日期然後由這邊跑
        self._RuuFilter() 