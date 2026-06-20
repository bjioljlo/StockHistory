"""
Legacy StockHistory module - Backward compatibility wrapper
============================================================

Now imports from extracted package: stockpicker-core.
Original definitions moved to stockpicker_core.stock_history.
"""

import warnings

from stockpicker_core.stock_history import (
    IStock, TStock, OriginalStock, OriginalStockByYahoo,
    OriginalStockTest, VirtualStockFuc, RangeDate_Stock,
    SMA_Stock, RecordHigh_Stock, VirtualStockFilterFuc,
    StockPriceBetterMA, StockRecordHigh, StockFilter,
    StockFilterInfo, StockAvgVolMultiple,
)

warnings.warn(
    "src.FilterService.StockHistory is deprecated. Use stockpicker_core.stock_history instead.",
    DeprecationWarning,
    stacklevel=2,
)
