"""
BackTest Service Interface

Part of Task 4.5: Service interfaces and dependency injection.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Callable, Optional

import pandas as pd

from src.Common.Parameter import RecordBackTestParameter


class IBackTestService(ABC):
    """Interface for backtesting services"""
    
    @abstractmethod
    def backtest_KD_pick(self, parameters: RecordBackTestParameter, output_folder: str, callback: Optional[Callable] = None) -> pd.DataFrame:
        """Run KD indicator backtest strategy"""
        pass
    
    @abstractmethod
    def backtest_PEG_pick(self, parameters: RecordBackTestParameter, output_folder: str, callback: Optional[Callable] = None) -> pd.DataFrame:
        """Run PEG strategy backtest"""
        pass
    
    @abstractmethod
    def backtest_PERandPBR(self, parameters: RecordBackTestParameter, output_folder: str, callback: Optional[Callable] = None) -> pd.DataFrame:
        """Run PER/PBR strategy backtest"""
        pass
    
    @abstractmethod
    def backtest_Regular_quota(self, parameters: RecordBackTestParameter, output_folder: str, callback: Optional[Callable] = None) -> pd.DataFrame:
        """Run regular quota strategy backtest"""
        pass
    
    @abstractmethod
    def backtest_Record_high(self, parameters: RecordBackTestParameter, output_folder: str, callback: Optional[Callable] = None) -> pd.DataFrame:
        """Run record high strategy backtest"""
        pass
    
    @abstractmethod
    def backtest_monthRP_Up(self, parameters: RecordBackTestParameter, output_folder: str, callback: Optional[Callable] = None) -> pd.DataFrame:
        """Run monthly revenue growth strategy backtest"""
        pass