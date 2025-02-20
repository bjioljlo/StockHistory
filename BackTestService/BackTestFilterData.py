from abc import ABC, abstractmethod
from enum import Enum
import sys
from StockInfoData import StockInfoSignalData, StockInfoData
from typing import Callable
from .FilterAndSignalStrategy import IBacktestFilter, IBacktestSignal
from datetime import datetime
from pandas import Series
import twstock as ts #抓取台灣股票資料套件  

BuyStockEvent = Callable[[str], bool]
class BacktestFilterDataType(Enum):
    KD = "KD"
    
class IBackTestFilterData(ABC):
    '''回測篩選+過濾訊號'''
    @property
    @abstractmethod
    def FilterStock(self) -> dict[str, StockInfoSignalData]:
        """
        A dictionary of stock numbers and their corresponding
        StockInfoSignalData objects.

        This property should be implemented by subclasses to provide
        the stock numbers and their corresponding
        StockInfoSignalData objects.

        Returns:
            A dictionary of stock numbers and their corresponding
            StockInfoSignalData objects.
        """
        raise NotImplementedError( "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name))
    @abstractmethod
    def GoToNextWorkDay(self, _dateNow: datetime):
        """
        Go to the next work day.

        This method should be implemented by subclasses to move the current date
        to the next work day.

        Parameters:
            _dateNow (datetime): The current date.

        Returns:
            None
        """
        raise NotImplementedError( "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name))
    @abstractmethod
    def ShouldBuyStocks(self) -> set[str]:
        """
        Determine which stocks should be bought.

        This method should be implemented by subclasses to decide if stocks
        should be bought based on specific criteria or signals.

        Returns:
            A set of strings of stock numbers that should be bought.
        """
        raise NotImplementedError( "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name))
    @abstractmethod
    def ShouldSellStocks(self) -> set[str]:
        """
        Determine which stocks should be sold.

        This method should be implemented by subclasses to decide if stocks
        should be sold based on specific criteria or signals.

        Returns:
            A set of stock numbers that should be sold.
        """
        raise NotImplementedError( "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name))
@staticmethod
def BacktestFilterDataFactory(_backtestFilterDataType: BacktestFilterDataType, _buyStockfun: BuyStockEvent, 
                            _filter:IBacktestFilter, _signal:IBacktestSignal, _startdate:datetime, _enddate:datetime) -> IBackTestFilterData:
    if _backtestFilterDataType == BacktestFilterDataType.KD:
        return KD_pickFilterData(_buyStockfun, _filter, _signal, _startdate, _enddate)
    raise NotImplementedError( "{} is wrong type.".format(sys._getframe().f_code.co_name))
    
class TBackTestFilterData(IBackTestFilterData):
    '''回測篩選實作'''   
    def __init__(self, _buyStockfun: BuyStockEvent, _filter:IBacktestFilter, _signal:IBacktestSignal, _startdate:datetime, _enddate:datetime) -> None:
        super(TBackTestFilterData, self).__init__()
        self._FilterStock:dict[str, StockInfoSignalData] = {}
        self.__BuyStockfun:BuyStockEvent = _buyStockfun #買入事件
        self._Filter:IBacktestFilter = _filter #回測篩選器
        self._Signal:IBacktestSignal = _signal #回測訊號
        self._DateNow:datetime = _startdate #當前日期
        self._EndDate:datetime = _enddate #回測結束日期
    @property
    def FilterStock(self) -> dict[str, StockInfoSignalData]:
        return self._FilterStock
    def _FinishFilterData(self, _NewData: Series):
        for key, value in _NewData.items():
            if key in self._FilterStock.keys():
                continue
            m_stock = ts.codes[str(key)]
            stockinfo: StockInfoData = StockInfoData(m_stock.code,m_stock.name,m_stock.type,m_stock.start,m_stock.market,m_stock.group)
            self._FilterStock[str(key)] = StockInfoSignalData(stockinfo, value)
    def _CheckFilterData(self, _NewData: Series):
        _result = Series()
        for key, value in self._FilterStock.items():
            if (key in _NewData.keys()) or not (value.singnal[self._DateNow] == -1):
                _result[key] = value
        self._FilterStock = _result
        
class KD_pickFilterData(TBackTestFilterData):
    '''KD值-回測篩選'''   
    def _RuuFilter(self):
        FilterData: Series = self._Filter.RunFilter(self._DateNow) # 篩選
        SignalData: Series = self._Signal.GetSignalResult(FilterData, self._EndDate) # 訊號
        self._FinishFilterData(SignalData)
        self._CheckFilterData(FilterData)

    def GoToNextWorkDay(self, _dateNow: datetime):
        self._DateNow = _dateNow
        self._RuuFilter()
    def ShouldBuyStocks(self) -> set[str]:
        _shouldBuyStocks = set()
        for key, value in self._FilterStock.items():
            if value.singnal[self._DateNow] == True:
                _shouldBuyStocks.add(key)
        return _shouldBuyStocks
    def ShouldSellStocks(self) -> set[str]:
        _shouldSellStocks = set()
        for key, value in self._FilterStock.items():
            if value.singnal[self._DateNow] == -1:
                _shouldSellStocks.add(key)
        return _shouldSellStocks