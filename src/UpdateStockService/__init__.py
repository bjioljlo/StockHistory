"""
UpdateStockService Package

Modular components:
- StockDataDownloader: Data downloading with retry logic
- StockDataSynchronizer: SQL <-> MongoDB synchronization
- ADLUpdater: Advance-Decline Line calculation and updates
"""

from datafetcher_core.downloader import StockDataDownloader
from .StockDataSynchronizer import StockDataSynchronizer
from .ADLUpdater import ADLUpdater
from src.Common.DataValidationService import DataValidationService

# Legacy compatibility alias
UpdateStockService = StockDataSynchronizer

__all__ = [
    'StockDataDownloader',
    'StockDataSynchronizer',
    'ADLUpdater',
    'UpdateStockService',
    'DataValidationService',
]
