"""
Date Validator Service for Stock Pick Model

Extracted from Model_pick.py - single responsibility: valid trading date detection
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from src.Common import InfomationType as info
from src.ExternalService.ExternalDataFactory import ExternalDataFactory
from src.FilterService.StockHistory import OriginalStockByYahoo


logger = logging.getLogger(__name__)


class DateValidatorService:
    """Finds valid trading dates"""

    def __init__(self, external_data_factory: ExternalDataFactory):
        self._external_data_factory = external_data_factory

    def get_valid_trading_date(self, end_date: datetime, max_attempts: int = 30) -> datetime:
        """
        Find the most recent valid trading date starting from end_date and going backwards

        Args:
            end_date: Date to start searching from
            max_attempts: Maximum number of days to search backwards

        Returns:
            Valid trading date

        Raises:
            ValueError: If no valid date found within max_attempts
        """
        date = end_date
        attempts = 0

        while attempts < max_attempts:
            try:
                stock_data = OriginalStockByYahoo(self._external_data_factory, 2330)
                price = stock_data.get_PriceByDateAndType(date, info.Price_type.Close)
                if price is not None:
                    logger.info(f"找到有效交易日期: {date.strftime('%Y-%m-%d')}")
                    return date
            except Exception as e:
                logger.warning(f"檢查日期 {date.strftime('%Y-%m-%d')} 時發生錯誤: {e}")

            date = date + timedelta(days=-1)
            attempts += 1

        raise ValueError(f"在 {max_attempts} 天內找不到有效的交易日期")