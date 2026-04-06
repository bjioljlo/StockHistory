"""
Update Stock Service Interface

Part of Task 4.5: Service interfaces and dependency injection.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

import pandas as pd


class IUpdateService(ABC):
    """Interface for stock data update services"""
    
    @abstractmethod
    def update_stock_prices(self, date: Optional[datetime] = None) -> bool:
        """Update stock price data"""
        pass
    
    @abstractmethod
    def update_financial_reports(self, year: int, quarter: int) -> bool:
        """Update financial report data"""
        pass
    
    @abstractmethod
    def update_monthly_revenue(self, year: int, month: int) -> bool:
        """Update monthly revenue data"""
        pass
    
    @abstractmethod
    def get_update_status(self) -> dict:
        """Get current update status"""
        pass
    
    @abstractmethod
    def schedule_automatic_updates(self, interval_hours: int) -> None:
        """Schedule automatic updates"""
        pass