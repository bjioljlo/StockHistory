"""
Filter Service Interface

Part of Task 4.5: Service interfaces and dependency injection.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Tuple

import pandas as pd

from src.Common import InfomationType as info


class IFilterService(ABC):
    """Interface for stock filtering services"""
    
    @abstractmethod
    def get_Filter(self, name: str, max_value: int, min_value: int, price_type: info.Price_type) -> pd.DataFrame:
        """Apply generic stock filter"""
        pass
    
    @abstractmethod
    def get_FilterInfo(self, group_name: str) -> pd.DataFrame:
        """Get filter group information"""
        pass
    
    @abstractmethod
    def get_Filter_SMA(self, name: str, max_value: int, min_value: int, avg_days: int, price_type: info.Price_type) -> pd.DataFrame:
        """Apply SMA filter"""
        pass
    
    @abstractmethod
    def get_Filter_RecordHigh(self, flash_days: int, record_days: int, price_type: info.Price_type) -> pd.DataFrame:
        """Apply record high filter"""
        pass
    
    @abstractmethod
    def get_Filter_StockPriceBetterMA(self, day_range: int, price_type: info.Price_type, better_type: int) -> pd.DataFrame:
        """Apply price vs MA filter"""
        pass
    
    @abstractmethod
    def get_Filter_AvgVolMultiple(self, avg_days: int, multiple: float, price_type: info.Price_type) -> pd.DataFrame:
        """Apply volume multiple filter"""
        pass