"""
Legacy StockDataSynchronizer module - Backward compatibility wrapper
=====================================================================

Now delegates to datafetcher_core.synchronizer.
"""
import warnings

from datafetcher_core.synchronizer import StockDataSynchronizer

warnings.warn(
    "src.UpdateStockService.StockDataSynchronizer is deprecated. "
    "Use datafetcher_core.synchronizer directly.",
    DeprecationWarning,
    stacklevel=2,
)
