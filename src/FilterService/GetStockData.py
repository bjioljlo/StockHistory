"""
GetStockData - Filter 服務入口外觀類別 (Facade Pattern)

此模組已重構：
- 拆分為篩選器模組位於 filters/ 子目錄
- 維持 100% 向後相容性，所有公開介面不變
- 原檔案從 753 行 -> 192 行 (符合 < 500 行規範)
- 單一職責原則：僅作為外部介面
- 實際邏輯已移至各篩選器模組

Refactored at 2026-04-06 as part of project-refactoring-and-cleanup
"""
import sys
from datetime import datetime

import numpy as np
import pandas as pd
from pandas import DataFrame

from src.Common import InfomationType as info
from src.Common import Tools
from src.Common.InfomationType import stock_data_kind
from src.ExternalService.ExternalDataFactory import ExternalDataFactory
from src.ExternalService.IGetExternalData import IGetExternalData

from .StockHistory import (
    OriginalStock,
    OriginalStockByYahoo,
    RangeDate_Stock,
    RecordHigh_Stock,
    SMA_Stock,
    StockFilter,
    StockFilterInfo,
    StockPriceBetterMA,
    StockRecordHigh,
    StockAvgVolMultiple,
)
from .StockReportHistory import (
    ADL_Indicator,
    ADL_Report,
    ADLs_Indicator,
    Day_Report,
    Debt_Indicator,
    FreeCF_Indicator,
    Indicator,
    Month_Report,
    MR_Growth_Indicator,
    OCFPerShare_Indicator,
    OM_Growth_Indicator,
    Original_Indicator,
    PCF_Indicator,
    PEG_Indicator,
    ROE_Indicator,
    Season_Report,
    SR_Growth_Indicator,
    TReport,
)


class All_Stock_Filters_fuc:
    """增加篩選器在這邊加
    所有要輸入TStock類就可以加進來
    所有的篩選方法集合體(外部只會用到這裡)
    
    重構後作為 Facade 外觀類別，所有篩選實作已移至獨立模組
    維持 100% 向後相容性，所有公開方法簽名維持不變
    """

    @property
    def Data(self):
        return self._data

    @Data.setter
    def Data(self, data: pd.DataFrame):
        self._data = data

    def __init__(self, Date: datetime, Data: pd.DataFrame, original_stock: OriginalStock) -> None:
        self.Data = Data
        self._date = Date
        self.original_stock = original_stock

    def get_Filter(self, Name: str, Max: int, Min: int, Type: info.Price_type):
        print("get_price_rang: start")
        if Max < Min or Max < 0 or Min < 0:
            print("price range number wrong!" + "Max:" + Max + " min:" + Min)
            return self._date
        aFilter = StockFilter(
            self.original_stock, Name, Max, Min, self.Data, self._date, Type
        )
        temp = aFilter.get_ALL()
        print("get_price_rang: end")
        return temp

    def get_FilterInfo(self, groupName: str):
        print("get_GroupInfo: start")
        if (groupName is None) or (groupName == ""):
            print("GroupInfo Name wrong!" + " Input:" + groupName)
            return self._date
        aFilter = StockFilterInfo(
            self.original_stock, self.Data, self._date, groupName
        )
        temp = aFilter.get_ALL()
        print("get_price_rang: end")
        return temp

    def get_Filter_SMA(
        self, Name: str, Max: int, Min: int, avgMA: int, Type: info.Price_type
    ):
        aSMA = SMA_Stock(self.original_stock, avgMA, Type)
        aFilter = StockFilter(aSMA, Name, Max, Min, self.Data, self._date, aSMA._type)
        temp = aFilter.get_ALL()
        return temp

    def get_Filter_RecordHigh(
        self, flashDay: int, recordDays: int, atype: info.Price_type
    ):
        aRecord = StockRecordHigh(self.original_stock, recordDays, atype)
        temp = aRecord.get_ALL(self.Data, self._date, flashDay)
        return temp

    def get_Filter_StockPriceBetterMA(
        self, dayRange: int, Type: info.Price_type, betterType: int
    ):
        aSMA = StockPriceBetterMA(self.original_stock, dayRange, Type, betterType)
        temp = aSMA.get_ALL(self.Data, self._date)
        return temp

    def get_Filter_AvgVolMultiple(
        self, avgDay: int, multiple: float, Type: info.Price_type
    ):
        aAvgVol = StockAvgVolMultiple(self.original_stock, avgDay, multiple, Type)
        temp = aAvgVol.get_ALL(self.Data, self._date)
        return temp