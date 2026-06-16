"""
StockDataDownloader - backward compatibility wrapper

Now delegates to datafetcher_core.downloader.
"""
import warnings

from datafetcher_core.downloader import StockDataDownloader

warnings.warn(
    "src.UpdateStockService.StockDataDownloader is deprecated. "
    "Use datafetcher_core.downloader directly.",
    DeprecationWarning,
    stacklevel=2,
)
