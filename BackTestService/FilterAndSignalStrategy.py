import sys
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import List

import numpy as np
import pandas as pd
import talib

from FilterService.GetStockData import All_Stock_Filters_fuc
from FilterService.StockHistory import SMA_Stock
import Tools
from FilterService import All_fuc, Indicator, OriginalStock
import InfomationType as info


# ISignal
class BacktestSignalType(Enum):
    KD = 1
    Date = 2
    PEG = 3
    RegularQuota = 4
    RecordHigh = 5


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
    else:
        return None


class TBacktestSignal(IBacktestSignal):
    """訊號觸發實作"""

    def __init__(self) -> None:
        super(TBacktestSignal, self).__init__()

    def GetSignalResult(self, InputData: pd.Series, _Date) -> pd.Series:
        return pd.Series()


class PEG_pickBacktestSignal(TBacktestSignal):
    """PEG值訊號-訊號觸發"""

    def __init__(self, _GetPrice: OriginalStock) -> None:
        super().__init__()
        self._getPrice: OriginalStock = _GetPrice
        self._tempSignals: pd.Series = pd.Series()
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
        self._tempSignals: pd.Series = pd.Series()

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
        self._tempSignals: pd.Series = pd.Series()
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


# IFilter
class BacktestFilterType(Enum):
    KD = 1
    Date = 2
    PEG = 3
    RegularQuota = 4
    RecordHigh = 5


class IBacktestFilter(ABC):
    """篩選器"""

    @abstractmethod
    def RunFilter(self, Date: datetime) -> pd.Series:
        raise NotImplementedError(
            "{} is virtual! Must be overwritten.".format(sys._getframe().f_code.co_name)
        )


def BacktestFilterFactory(
    _backtestFilterType: BacktestFilterType, _indicators: List[Indicator]
) -> IBacktestFilter:
    if _backtestFilterType == BacktestFilterType.KD:
        return KD_pickBacktestFilter(_indicators[0])
    elif _backtestFilterType == BacktestFilterType.PEG:
        return PEG_pickBacktestFilter(_indicators)
    elif _backtestFilterType == BacktestFilterType.RecordHigh:
        return RecordHigh_pickBacktestFilter(_indicators)
    else:
        return None


class TBacktestFilter(IBacktestFilter):
    """篩選器實作"""

    def __init__(self, _indicators: List[Indicator]) -> None:
        super(TBacktestFilter, self).__init__()


class PEG_pickBacktestFilter(TBacktestFilter):
    """PEG值選股-篩選器"""

    def __init__(self, _indicators: List[Indicator]) -> None:
        self.PEG_Indicator: Indicator = _indicators[0]
        self.MonthReportUp_indicator: Indicator = _indicators[1]

    def RunFilter(self, Date: datetime) -> pd.Series:
        Result_data = {}
        Result_data[self.PEG_Indicator.name] = All_fuc(
            Date, self.PEG_Indicator
        ).get_Filter_Auto(1, 0.66)

        Result_data[self.MonthReportUp_indicator.name] = All_fuc(
            Date, self.MonthReportUp_indicator
        ).get_Smooth_Up_Auto(4, 4)
        Result_data = Tools.MixDataFrames(Result_data)
        return Result_data[self.PEG_Indicator.name]


class Regular_quotatestFilter(TBacktestFilter):
    """定期定額-篩選器"""

    def __init__(self, _stock: str) -> None:
        self._StockNumber: str = _stock

    def RunFilter(self, Date: datetime) -> pd.Series:
        Result_data = {}
        Result_data[0] = self._StockNumber
        return Result_data


class KD_pickBacktestFilter(TBacktestFilter):
    """KD值選股-篩選器"""

    def __init__(self, _indicator: Indicator) -> None:
        self._Indicator: Indicator = _indicator

    def RunFilter(self, Date: datetime) -> pd.Series:
        Result_data = pd.DataFrame()
        for num in range(1, 5):
            ResultKeyName = self._Indicator.name + "_data_" + str(num)
            Result_data[ResultKeyName] = All_fuc(
                Tools.changeDateMonth(Date, (-3 * num)), self._Indicator
            ).get_Filter_Auto(0, 999)
        mask = Tools.MixDataFrames(Result_data)

        AVG_data = (
            mask[self._Indicator.name + "_data_1"]
            + mask[self._Indicator.name + "_data_2"]
            + mask[self._Indicator.name + "_data_3"]
            + mask[self._Indicator.name + "_data_4"]
        ) / 4

        Result_data_1 = pd.Series(mask[self._Indicator.name + "_data_1"])
        Result_data_mask = Result_data_1 > AVG_data
        Result_data = Result_data_mask[Result_data_mask]
        return Result_data


class RecordHigh_pickBacktestFilter(TBacktestFilter):
    """#創新高-篩選器"""

    def __init__(self, _indicators: List[Indicator]) -> None:
        self.ROE_Indicator: Indicator = _indicators[0]
        self.PBR_indicator: Indicator = _indicators[1]

    def RunFilter(self, Date: datetime):
        Result_data = {}
        Result_data[self.ROE_Indicator.name] = All_fuc(
            Date, self.ROE_Indicator
        ).get_Filter_Auto(10000, 3)
        Result_data[self.ROE_Indicator.name + "_last_seson"] = All_fuc(
            Date - timedelta(weeks=12), self.ROE_Indicator
        ).get_Filter_Auto(10000, 1)
        Result = Tools.MixDataFrames(Result_data)
        Result_data["RecordHigh"] = All_Stock_Filters_fuc(
            Date, Result
        ).get_Filter_RecordHigh(
            60,
            1,
            info.Price_type.High,
        )

        Result_data[self.ROE_Indicator.name + "_last_seson"] = All_fuc(
            Date - timedelta(weeks=12), self.ROE_Indicator
        ).get_Filter_Auto(10000, 1)
        Result_data[self.PBR_indicator.name] = All_fuc(
            Date, self.PBR_indicator
        ).get_Filter_Auto(10000, 1)
        Result = Tools.MixDataFrames(Result_data)
        Result_data["price"] = All_Stock_Filters_fuc(Date, Result).get_Filter(
            "price", 2000, 7, info.Price_type.Close
        )
        Result = Tools.MixDataFrames(Result_data)
        Result_data["volume"] = All_Stock_Filters_fuc(Date, Result).get_Filter_SMA(
            "volume", 99999999999, 500000, 5, info.Price_type.Volume
        )
        Result = Tools.MixDataFrames(Result_data)
        TempPointResult = Result_data["ROE"] / Result_data["ROE_last_seson"]
        Result_data["point"] = (
            pd.DataFrame(TempPointResult["ROE"] / Result_data["PBR"]["PBR"])
            .dropna()
            .rename(columns={0: "point"})
        )
        Result = Tools.MixDataFrames(Result_data)
        Result = Result.sort_values(by="point", ascending=False)
        return Result["point"]
