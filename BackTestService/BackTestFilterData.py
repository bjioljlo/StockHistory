import sys
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Callable

import twstock as ts  # 抓取台灣股票資料套件
from pandas import Series

from StockInfoData import StockInfoData, StockInfoSignalData

from .FilterAndSignalStrategy import IBacktestFilter, IBacktestSignal

BuyStockEvent = Callable[[str], bool]


class BacktestFilterDataType(Enum):
    KD = "KD"
    PEG = "PEG"
    RegularQuota = "RegularQuota"
    RecordHigh = "RecordHigh"
    PERandPBR = "PERandPBR"
    MonthRP_Up = "MonthRP_Up"


class IBackTestFilterData(ABC):
    """回測篩選+過濾訊號"""

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
        raise NotImplementedError(
            "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name)
        )

    @abstractmethod
    def RuuFilter(self):
        raise NotImplementedError(
            "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name)
        )

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
        raise NotImplementedError(
            "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name)
        )

    @abstractmethod
    def ShouldBuyStocks(self) -> set[str]:
        """
        Determine which stocks should be bought.

        This method should be implemented by subclasses to decide if stocks
        should be bought based on specific criteria or signals.

        Returns:
            A set of strings of stock numbers that should be bought.
        """
        raise NotImplementedError(
            "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name)
        )

    @abstractmethod
    def ShouldSellStocks(self, _dataInHand: dict) -> set[str]:
        """
        Determine which stocks should be sold.

        This method should be implemented by subclasses to decide if stocks
        should be sold based on specific criteria or signals.

        Returns:
            A set of stock numbers that should be sold.
        """
        raise NotImplementedError(
            "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name)
        )


@staticmethod
def BacktestFilterDataFactory(
    _backtestFilterDataType: BacktestFilterDataType,
    _buyStockfun: BuyStockEvent,
    _filter: IBacktestFilter,
    _signal: IBacktestSignal,
    _startdate: datetime,
    _enddate: datetime,
) -> IBackTestFilterData:
    if _backtestFilterDataType == BacktestFilterDataType.KD:
        return KD_pickFilterData(_buyStockfun, _filter, _signal, _startdate, _enddate)
    elif _backtestFilterDataType == BacktestFilterDataType.PEG:
        return PEG_pickFilterData(_buyStockfun, _filter, _signal, _startdate, _enddate)
    elif _backtestFilterDataType == BacktestFilterDataType.RegularQuota:
        return RegularQuota_pickFilterData(
            _buyStockfun, _filter, _signal, _startdate, _enddate
        )
    elif _backtestFilterDataType == BacktestFilterDataType.RecordHigh:
        return RecordHigh_pickFilterData(
            _buyStockfun, _filter, _signal, _startdate, _enddate
        )
    elif _backtestFilterDataType == BacktestFilterDataType.PERandPBR:
        return PERandPBR_pickFilterData(
            _buyStockfun, _filter, _signal, _startdate, _enddate
        )
    elif _backtestFilterDataType == BacktestFilterDataType.MonthRP_Up:
        return MonthRpUp_pickFilterData(_buyStockfun, _filter, _signal, _startdate, _enddate)
    raise NotImplementedError(
        "{} is wrong type.".format(sys._getframe().f_code.co_name)
    )


class TBackTestFilterData(IBackTestFilterData):
    """回測篩選實作"""

    def __init__(
        self,
        _buyStockfun: BuyStockEvent,
        _filter: IBacktestFilter,
        _signal: IBacktestSignal,
        _startdate: datetime,
        _enddate: datetime,
    ) -> None:
        super(TBackTestFilterData, self).__init__()
        self._FilterStockNow: Series = Series()  # 當天篩選
        self._FilterStock: dict[str, StockInfoSignalData] = {}  # 信號暫存
        self.__BuyStockfun: BuyStockEvent = _buyStockfun  # 買入事件
        self._Filter: IBacktestFilter = _filter  # 回測篩選器
        self._Signal: IBacktestSignal = _signal  # 回測訊號
        self._DateNow: datetime = _startdate  # 當前日期
        self._EndDate: datetime = _enddate  # 回測結束日期

    @property
    def FilterStock(self) -> dict[str, StockInfoSignalData]:
        return self._FilterStockNow

    def _FinishFilterData(self, _NewData: Series):
        """
        Processes new stock data and stores the corresponding signals.
        將信號放入暫存
        This method iterates over the provided series of new stock data,
        checks if each stock is already present in the _FilterStock dictionary,
        and if not, retrieves the stock information and creates a StockInfoSignalData
        object with the signal value. The new stock information and signal are then
        stored in the _FilterStock dictionary.

        Args:
            _NewData (Series): A pandas Series where keys are stock identifiers
                            and values are the corresponding signal data.

        Returns:
            None
        """
        for key, value in _NewData.items():
            if key in self._FilterStock.keys():
                continue
            m_stock = ts.codes[str(key)]
            stockinfo: StockInfoData = StockInfoData(
                m_stock.code,
                m_stock.name,
                m_stock.type,
                m_stock.start,
                m_stock.market,
                m_stock.group,
            )
            self._FilterStock[str(key)] = StockInfoSignalData(stockinfo, value)

    def _CheckFilterData(self, _NewData: Series):
        """
        Filters out stocks with a sell signal from the current filter stock list.
        將信號暫存中為賣出的股票挑掉
        This method iterates through the current filter stock dictionary and
        checks if each stock key is present in the new data keys or if the
        stock's signal is not a sell signal (value.singnal[self._DateNow] != -1).
        Only stocks that meet these conditions are retained in the result.

        Args:
            _NewData (Series): A pandas Series containing new stock data with
                            stock identifiers as keys and their associated
                            signal data as values.

        Returns:
            None
        """
        _result = Series()
        for key, value in self._FilterStock.items():
            if (key in _NewData.keys()) or not (value.singnal[self._DateNow] == -1):
                _result[key] = value
        self._FilterStock = _result

    def GoToNextWorkDay(self, _dateNow: datetime):
        self._DateNow = _dateNow


class PEG_pickFilterData(TBackTestFilterData):
    """PEG值-回測篩選"""

    def RuuFilter(self):
        self._FilterStockNow: Series = self._Filter.RunFilter(self._DateNow)  # 篩選
        SignalData: Series = self._Signal.GetSignalResult(
            self._FilterStockNow, self._EndDate
        )  # 訊號
        self._FinishFilterData(SignalData)

    def ShouldBuyStocks(self):
        _shouldBuyStocks = set()
        if not self._FilterStockNow.empty:
            self._FilterStockNow.sort_values
            Temp_buy = self._FilterStockNow.head(10)
            for key, value in Temp_buy.items():
                try:
                    _shouldBuyStocks.add(str(key))
                except KeyError:
                    print(f"Error: {key} not in data/msg:{KeyError}")
        return _shouldBuyStocks

    def ShouldSellStocks(self, _dataInHand: dict):
        _shouldSellStocks = set()
        for key, value in self._FilterStock.items():
            try:
                if (key in _dataInHand.keys()) and not value.singnal[self._DateNow]:
                    _shouldSellStocks.add(key)
            except KeyError:
                print(f"Error: {key} not in data/msg:{KeyError}")
        return _shouldSellStocks


class KD_pickFilterData(TBackTestFilterData):
    """KD值-回測篩選"""

    def RuuFilter(self):
        self._FilterStockNow: Series = self._Filter.RunFilter(self._DateNow)  # 篩選
        SignalData: Series = self._Signal.GetSignalResult(
            self._FilterStockNow, self._EndDate
        )  # 訊號
        self._FinishFilterData(SignalData)

    def ShouldBuyStocks(self) -> set[str]:
        _shouldBuyStocks = set()
        for key, value in self._FilterStockNow.items():
            try:
                if (
                    not self._FilterStock[str(key)].singnal[self._DateNow] == -1
                    and self._FilterStock[str(key)].singnal[self._DateNow]
                ):
                    _shouldBuyStocks.add(str(key))
            except KeyError:
                print(f"Error: {key} not in data/msg:{KeyError}")
        return _shouldBuyStocks

    def ShouldSellStocks(self, _dataInHand: dict) -> set[str]:
        _shouldSellStocks = set()
        for key, value in _dataInHand.items():
            try:
                if self._FilterStock[key].singnal[self._DateNow] == -1:
                    _shouldSellStocks.add(key)
            except KeyError:
                print(f"Error: {key} not in data/msg:{KeyError}")
        return _shouldSellStocks


class RegularQuota_pickFilterData(TBackTestFilterData):
    """定期定額-回測篩選"""

    def RuuFilter(self):
        self._FilterStockNow: Series = self._Filter.RunFilter(self._DateNow)  # 篩選

    def ShouldBuyStocks(self):
        _shouldBuyStocks = set()
        _shouldBuyStocks.add(self._Filter.RunFilter(self._DateNow)[0])
        return _shouldBuyStocks

    def ShouldSellStocks(self, _dataInHand):
        _shouldSellStocks = set()
        return _shouldSellStocks


class RecordHigh_pickFilterData(TBackTestFilterData):
    """創新高-回測篩選"""

    def RuuFilter(self):
        self._FilterStockNow: Series = self._Filter.RunFilter(self._DateNow)  # 篩選
        SignalData: Series = self._Signal.GetSignalResult(
            self._FilterStockNow, self._EndDate
        )  # 訊號
        self._FinishFilterData(SignalData)

    def ShouldBuyStocks(self):
        _shouldBuyStocks = set()
        if not self._FilterStockNow.empty:
            self._FilterStockNow.sort_values
            Temp_buy = self._FilterStockNow.head(3)
            for key, value in Temp_buy.items():
                try:
                    _shouldBuyStocks.add(str(key))
                except KeyError:
                    print(f"Error: {key} not in data/msg:{KeyError}")
        return _shouldBuyStocks

    def ShouldSellStocks(self, _dataInHand: dict):
        _shouldSellStocks = set()
        for key, value in self._FilterStock.items():
            try:
                if (key in _dataInHand.keys()) and not value.singnal[self._DateNow]:
                    _shouldSellStocks.add(key)
            except KeyError:
                print(f"Error: {key} not in data/msg:{KeyError}")
        return _shouldSellStocks


class PERandPBR_pickFilterData(TBackTestFilterData):
    """PER和PBR-回測篩選"""

    def RuuFilter(self):
        self._FilterStockNow: Series = self._Filter.RunFilter(self._DateNow)  # 篩選

    def ShouldBuyStocks(self):
        _shouldBuyStocks = set()
        if not self._FilterStockNow.empty:
            self._FilterStockNow.sort_values
            Temp_buy = self._FilterStockNow.head(3)
            for key, value in Temp_buy.items():
                try:
                    _shouldBuyStocks.add(str(key))
                except KeyError:
                    print(f"Error: {key} not in data/msg:{KeyError}")
        return _shouldBuyStocks

    def ShouldSellStocks(self, _dataInHand):
        _shouldSellStocks = set()
        for key, value in self._FilterStockNow.items():
            try:
                if key in _dataInHand.keys():
                    _shouldSellStocks.add(key)
            except KeyError:
                print(f"Error: {key} not in data/msg:{KeyError}")
        return _shouldSellStocks
    
class MonthRpUp_pickFilterData(TBackTestFilterData):
    """月營收增高-回測篩選"""

    def RuuFilter(self):
        self._FilterStockNow: Series = self._Filter.RunFilter(self._DateNow)  # 篩選
        SignalData: Series = self._Signal.GetSignalResult(
            self._FilterStockNow, self._EndDate
        )  # 訊號
        self._FinishFilterData(SignalData)
    def ShouldBuyStocks(self):
        _shouldBuyStocks = set()
        if not self._FilterStockNow.empty:
            self._FilterStockNow.sort_values
            Temp_buy = self._FilterStockNow.head(3)
            for key, value in Temp_buy.items():
                try:
                    _shouldBuyStocks.add(str(key))
                except KeyError:
                    print(f"Error: {key} not in data/msg:{KeyError}")
        return _shouldBuyStocks

    def ShouldSellStocks(self, _dataInHand: dict):
        _shouldSellStocks = set()
        for key, value in self._FilterStock.items():
            try:
                if (key in _dataInHand.keys()) and not value.singnal[self._DateNow]:
                    _shouldSellStocks.add(key)
            except KeyError:
                print(f"Error: {key} not in data/msg:{KeyError}")
        return _shouldSellStocks
