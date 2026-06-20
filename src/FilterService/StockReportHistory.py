"""
Legacy StockReportHistory module - Backward compatibility wrapper
==================================================================

Now imports from extracted package: stockpicker-core.
Original definitions moved to stockpicker_core.stock_report_history.
"""

import warnings

from stockpicker_core.stock_report_history import (
    IReport, TReport, AllStockReport,
    Season_Report, Month_Report, Day_Report, ADL_Report, DividendYield_Report,
    SeasonReportFactory, MonthReportFactory, DayReportFactory,
    DividendYieldReportFactory, ADLReportFactory,
    Indicator, ROE_Indicator, FreeCF_Indicator, Debt_Indicator,
    MR_Growth_Indicator, SR_Growth_Indicator, OM_Growth_Indicator,
    PEG_Indicator, OCFPerShare_Indicator, PCF_Indicator,
    Original_Indicator,
    ADL_Indicator, ADLs_Indicator,
)

warnings.warn(
    "src.FilterService.StockReportHistory is deprecated. Use stockpicker_core.stock_report_history instead.",
    DeprecationWarning,
    stacklevel=2,
)