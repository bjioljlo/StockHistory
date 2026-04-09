"""
BackTestService Package

Refactored into modular components:
- BackTestStock: Main service facade (backwards compatible)
- BackTestFilter: Filter implementations for strategy conditions
- BackTestFilterData: Filter data factory and types
- BackTestInfoData: User information and state management
- BackTestInOutStrategy: Entry/Exit strategy implementations
- BackTestRecord: Transaction recording
- BackTestSignal: Trading signal generation
- StockInfoDataInHand: In-memory stock data management

Refactored at 2026-04-06 as part of project-refactoring-and-cleanup
"""

from .BackTestFilter import (
    BacktestFilterFactory,
    BacktestFilterType,
    Regular_quotatestFilter,
)
from .BackTestFilterData import (
    BacktestFilterDataFactory,
    BacktestFilterDataType,
)
from .BackTestInfoData import (
    BackTestInfoDataPriceByToday,
)
from .BackTestInOutStrategy import (
    KD_BackTestInOutStrategy,
    MonthRpUp_backtestInOutStrategy,
    PEG_BackTestInOutStrategy,
    PERandPBR_BackTestInOutStrategy,
    RecordHigh_backtestInOutStrategy,
    Regular_backTestInOutStrategy,
)
from .BackTestRecord import (
    IBackTestRecord,
    TBackTestRecord,
    BackTestRecord_indexWithDate,
)
from .BackTestSignal import (
    BacktestSignalFactory,
    BacktestSignalType,
    TBacktestSignal,
)
from .BackTestStock import BackTestStock
from .StockInfoDataInHand import (
    IStockInfoDataInHand,
    TStockInfoDataInHand,
    StockInfoDataInHandWithWeightedAverage,
    StockInfoDataInHandFactory,
)

__all__ = [
    'BacktestFilterFactory',
    'BacktestFilterType',
    'Regular_quotatestFilter',
    'BacktestFilterDataFactory',
    'BacktestFilterDataType',
    'BackTestInfoDataPriceByToday',
    'KD_BackTestInOutStrategy',
    'MonthRpUp_backtestInOutStrategy',
    'PEG_BackTestInOutStrategy',
    'PERandPBR_BackTestInOutStrategy',
    'RecordHigh_backtestInOutStrategy',
    'Regular_backTestInOutStrategy',
    'IBackTestRecord',
    'TBackTestRecord',
    'BackTestRecord_indexWithDate',
    'BacktestSignalFactory',
    'BacktestSignalType',
    'TBacktestSignal',
    'BackTestStock',
    'IStockInfoDataInHand',
    'TStockInfoDataInHand',
    'StockInfoDataInHandWithWeightedAverage',
    'StockInfoDataInHandFactory',
]