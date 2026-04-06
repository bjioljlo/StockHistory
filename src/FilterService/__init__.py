"""
FilterService Package

Refactored into modular components:
- All_Stock_Filters_fuc: Main service facade (backwards compatible)
- StockHistory: Stock data filters and calculators
- StockReportHistory: Financial report indicators
- GetStockData: Stock data retrieval and filtering

Refactored at 2026-04-06 as part of project-refactoring-and-cleanup
"""

from .GetStockData import All_Stock_Filters_fuc
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

__all__ = [
    'All_Stock_Filters_fuc',
    'OriginalStock',
    'OriginalStockByYahoo',
    'RangeDate_Stock',
    'RecordHigh_Stock',
    'SMA_Stock',
    'StockFilter',
    'StockFilterInfo',
    'StockPriceBetterMA',
    'StockRecordHigh',
    'StockAvgVolMultiple',
    'ADL_Indicator',
    'ADL_Report',
    'ADLs_Indicator',
    'Day_Report',
    'Debt_Indicator',
    'FreeCF_Indicator',
    'Indicator',
    'Month_Report',
    'MR_Growth_Indicator',
    'OCFPerShare_Indicator',
    'OM_Growth_Indicator',
    'Original_Indicator',
    'PCF_Indicator',
    'PEG_Indicator',
    'ROE_Indicator',
    'Season_Report',
    'SR_Growth_Indicator',
    'TReport',
]