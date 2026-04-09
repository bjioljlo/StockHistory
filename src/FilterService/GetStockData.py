"""
GetStockData - Filter 服務轉發模組

注意：此模組為過渡時期的匯入轉發層，未來將會移除。
新程式碼請直接從對應模組匯入：
- 篩選器: from src.FilterService.StockHistory import *
- 財務指標: from src.FilterService.StockReportHistory import *
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



# The following compatibility class has been removed
# All usages should be updated to use the implementation classes directly:
# - StockFilter
# - StockFilterInfo
# - SMA_Stock
# - StockRecordHigh
# - StockPriceBetterMA
# - StockAvgVolMultiple

__all__ = [
]
