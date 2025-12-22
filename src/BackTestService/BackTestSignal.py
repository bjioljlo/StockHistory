import sys
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum

import numpy as np
import pandas as pd
import talib

from src.FilterService.StockHistory import SMA_Stock
from src.Common import Tools
from src.FilterService.StockHistory import OriginalStock
from src.Common import InfomationType as info

class BacktestSignalType(Enum):
    KD = 1
    Date = 2
    PEG = 3
    RegularQuota = 4
    RecordHigh = 5
    PERandPBR = 6
    MonthRP_Up = 7


class IBacktestSignal(ABC):
    """訊號觸發"""

    @abstractmethod
    def GetSignalResult(self, InputData: pd.Series, _Date: datetime) -> pd.Series:
        """
        This method is called by the backtest engine to retrieve a dictionary of stock numbers and
        their corresponding signals.

        :param InputData: A dictionary of stock numbers and their historical data
        :type InputData: dict
        :return: A dictionary of stock numbers and their corresponding signals
        :rtype: dict
        """
        raise NotImplementedError(
            "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name)
        )


def BacktestSignalFactory(
    _StrategyType: BacktestSignalType, _originalStock: OriginalStock
):
    if _StrategyType == BacktestSignalType.KD:
        return KD_pickBacktestSignal(_originalStock)
    elif _StrategyType == BacktestSignalType.PEG:
        return PEG_pickBacktestSignal(_originalStock)
    elif _StrategyType == BacktestSignalType.RecordHigh:
        return RecordHigh_pickBacktestSignal(_originalStock)
    elif _StrategyType == BacktestSignalType.MonthRP_Up:
        return MonthRpUp_pickBacktestSignal(_originalStock)
    elif _StrategyType == BacktestSignalType.PERandPBR:
        return PERandPBR_pickBacktestSignal(_originalStock)
    else:
        return None


class TBacktestSignal(IBacktestSignal):
    """訊號觸發實作"""

    def __init__(self) -> None:
        self._tempSignals: pd.Series = pd.Series()
        
    def GetSignalResult(self, InputData, _Date):
        return super().GetSignalResult(InputData, _Date)

class PERandPBR_pickBacktestSignal(TBacktestSignal):
    """PER和PBR訊號-訊號觸發"""
    def __init__(self, _GetPrice: OriginalStock) -> None:
        super().__init__()
        self._getPrice: OriginalStock = _GetPrice
    def GetSignalResult(self, InputData: pd.Series, _Date) -> pd.Series:
        All_stock_signal = pd.Series()
        for key, _value in InputData.items():  # 先算出股票的買賣訊號
            try:
                All_stock_signal[key] = self._tempSignals[key]
            except KeyError:
                print(f"Error: {key} not in data/msg:{KeyError}")
                if Tools.check_no_use_stock(key):
                    print("get_stock_price: " + str(key) + " in no use")
                    continue
                self._getPrice.number = key
                table = self._getPrice.get_ALL()
                if table.empty:
                    continue
                signal_result = table["Volume"] >= 500000
                signal_result2 = table["Close"] >= 10
                signal_result = signal_result & signal_result2
                All_stock_signal[key] = signal_result
                self._tempSignals[key] = signal_result
        return All_stock_signal

class PEG_pickBacktestSignal(TBacktestSignal):
    """PEG值訊號-訊號觸發"""

    def __init__(self, _GetPrice: OriginalStock) -> None:
        super().__init__()
        self._getPrice: OriginalStock = _GetPrice
        self._sMA_Stock = SMA_Stock(self._getPrice, 20, info.Price_type.Close)

    def GetSignalResult(self, InputData: pd.Series, _Date) -> pd.Series:
        All_stock_signal = pd.Series()
        for key, _value in InputData.items():  # 先算出股票的買賣訊號
            try:
                All_stock_signal[key] = self._tempSignals[key]
            except KeyError:
                print(f"Error: {key} not in data/msg:{KeyError}")
                if Tools.check_no_use_stock(key):
                    print("get_stock_price: " + str(key) + " in no use")
                    continue
                self._getPrice.number = key
                table = self._getPrice.get_ALL()
                if table.empty:
                    continue
                table_sma20 = self._sMA_Stock.get_ALL()
                signal_result = table["Close"] > table_sma20
                All_stock_signal[key] = signal_result
                self._tempSignals[key] = signal_result
        return All_stock_signal


class KD_pickBacktestSignal(TBacktestSignal):
    """KD值訊號-訊號觸發"""

    def __init__(self, _GetPrice: OriginalStock) -> None:
        super().__init__()
        self._getPrice: OriginalStock = _GetPrice

    def GetSignalResult(self, InputData: pd.Series, _Date: datetime) -> pd.Series:
        All_stock_signal = pd.Series()
        for key, _value in InputData.items():  # 先算出股票的買賣訊號
            try:
                All_stock_signal[key] = self._tempSignals[key]
            except KeyError:
                print(f"Error: {key} not in data/msg:{KeyError}")
                if Tools.check_no_use_stock(key):
                    print("get_stock_price: " + str(key) + " in no use")
                    continue
                self._getPrice.number = key
                table = self._getPrice.get_ALL()
                if table.empty:
                    continue
                table_K, table_D = talib.STOCH(
                    table["High"],
                    table["Low"],
                    table["Close"],
                    fastk_period=50,
                    slowk_period=20,
                    slowk_matype=0,
                    slowd_period=20,
                    slowd_matype=0,
                )
                table_sma10 = talib.SMA(np.array(table["Close"]), 10)
                table_sma240 = talib.SMA(np.array(table["Close"]), 240)
                signal_buy = table_K > table_D
                signal_sell = table_K < table_D
                signal_sma10 = table.Close < table_sma10
                signal_sma240 = table.Close > table_sma240
                signal = signal_sma10 & signal_sma240 & signal_buy
                signal[signal_sell] = -1
                All_stock_signal[key] = signal
                self._tempSignals[key] = signal
        return All_stock_signal


class RecordHigh_pickBacktestSignal(TBacktestSignal):
    """RecordHigh值訊號-訊號觸發"""

    def __init__(self, _GetPrice: OriginalStock) -> None:
        super().__init__()
        self._getPrice: OriginalStock = _GetPrice
        self._sMA_Stock = SMA_Stock(self._getPrice, 20, info.Price_type.Close)

    def GetSignalResult(self, InputData: pd.Series, _Date) -> pd.Series:
        All_stock_signal = pd.Series()
        for key, _value in InputData.items():  # 先算出股票的買賣訊號
            try:
                All_stock_signal[key] = self._tempSignals[key]
            except KeyError:
                print(f"Error: {key} not in data/msg:{KeyError}")
                if Tools.check_no_use_stock(key):
                    print("get_stock_price: " + str(key) + " in no use")
                    continue
                self._getPrice.number = key
                table = self._getPrice.get_ALL()
                if table.empty:
                    continue
                table_sma20 = self._sMA_Stock.get_ALL()
                signal_result = table["Close"] > table_sma20
                All_stock_signal[key] = signal_result
                self._tempSignals[key] = signal_result
        return All_stock_signal

class MonthRpUp_pickBacktestSignal(TBacktestSignal):
    """MonthRpUp值訊號-訊號觸發"""
    def __init__(self, _GetPrice: OriginalStock) -> None:
        super().__init__()
        self._getPrice: OriginalStock = _GetPrice
        self._sMA_Stock = SMA_Stock(self._getPrice, 20, info.Price_type.Close)
        
    def GetSignalResult(self, InputData, _Date):
        All_stock_signal = pd.Series()
        for key, _value in InputData.items():  # 先算出股票的買賣訊號
            try:
                All_stock_signal[key] = self._tempSignals[key]
            except KeyError:
                print(f"Error: {key} not in data/msg:{KeyError}")
                if Tools.check_no_use_stock(key):
                    print("get_stock_price: " + str(key) + " in no use")
                    continue
                self._getPrice.number = key
                table = self._getPrice.get_ALL()
                if table.empty:
                    continue
                table_sma20 = self._sMA_Stock.get_ALL()
                signal_result = table["Close"] > table_sma20
                
                self._sMA_Stock.PriceType = info.Price_type.Volume
                self._sMA_Stock.AvgDay = 5
                table_SmaVolume = self._sMA_Stock.get_ALL()
                signal_result2 = (table["Volume"] > table_SmaVolume)
                signal_result = signal_result & signal_result2
                
                All_stock_signal[key] = signal_result
                self._tempSignals[key] = signal_result
        return All_stock_signal