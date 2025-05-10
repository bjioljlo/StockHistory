import sys
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import List

import pandas as pd

from FilterService.GetStockData import All_Stock_Filters_fuc
import Tools
from FilterService import All_fuc, Indicator
import InfomationType as info


class BacktestFilterType(Enum):
    KD = 1
    Date = 2
    PEG = 3
    RegularQuota = 4
    RecordHigh = 5
    PERandPBR = 6
    MonthRP_Up = 7


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
    elif _backtestFilterType == BacktestFilterType.PERandPBR:
        return PERandPBR_pickBacktestFilter(_indicators)
    elif _backtestFilterType == BacktestFilterType.MonthRP_Up:
        return MonthRpUp_pickbacktestFilter(_indicators)
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
        ).get_Smooth_Up_Auto(4, 5)
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
        Result_data[self.PBR_indicator.name] = All_fuc(
            Date, self.PBR_indicator
        ).get_Filter_Auto(10000, 1)
        Result = Tools.MixDataFrames(Result_data)
        Result_data["RecordHigh"] = All_Stock_Filters_fuc(
            Date, Result
        ).get_Filter_RecordHigh(
            60,
            1,
            info.Price_type.High,
        )
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


class PERandPBR_pickBacktestFilter(TBacktestFilter):
    """PER PBR-篩選器"""

    def __init__(self, _indicators: List[Indicator]) -> None:
        self.PER_Indicator: Indicator = _indicators[0]
        self.PBR_indicator: Indicator = _indicators[1]

    def RunFilter(self, Date: datetime):
        Result_data = {}
        Result_data[self.PER_Indicator.name] = All_fuc(
            Date, self.PER_Indicator
        ).get_Filter_Auto(10000, 13)
        Result_data[self.PBR_indicator.name] = All_fuc(
            Date, self.PBR_indicator
        ).get_Filter_Auto(10000, 0.7)
        Result = Tools.MixDataFrames(Result_data)
        return Result[self.PER_Indicator.name]
    
class MonthRpUp_pickbacktestFilter(TBacktestFilter):
    """月營收成長-篩選器"""

    def __init__(self, _indicators: List[Indicator]) -> None:
        self.MonthReportUp_indicator: Indicator = _indicators[0]
        self.ROE_indicator: Indicator = _indicators[1]
        self.PER_indicator: Indicator = _indicators[2]
        self.PBR_indicator: Indicator = _indicators[3]

    def RunFilter(self, Date: datetime) -> pd.Series:
        Result_data = {}
        Result_data[self.MonthReportUp_indicator.name] = All_fuc(
            Date, self.MonthReportUp_indicator
        ).get_Smooth_Up_Auto(4, 5)
        Result_data[self.ROE_indicator.name] = All_fuc(
            Date, self.ROE_indicator
        ).get_Filter_Auto(10000, 3)
        Result_data[self.PER_indicator.name] = All_fuc(
            Date, self.PER_indicator
        ).get_Filter_Auto(10000, 13)
        Result_data[self.PBR_indicator.name] = All_fuc(
            Date, self.PBR_indicator
        ).get_Filter_Auto(10000, 0.7)
        Result_data = Tools.MixDataFrames(Result_data)
        return Result_data[self.PBR_indicator.name]
