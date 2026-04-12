"""
Monthly Statement Provider
Handles monthly revenue report operations

Part of TGetExternalData refactoring
"""
import os
from datetime import datetime
import pandas as pd
import logging

from src.SqlService import SqlService
from src.MongoService import MongoService
from src.ReadLoadSystem import ReadLoadSystem
from src.Common.CacheService import HybridCacheService
from src.Common import Tools


class MonthlyStatementProvider:
    def __init__(self,
                 sql_service: SqlService,
                 mongo_service: MongoService,
                 read_load_system: ReadLoadSystem,
                 cache_service: HybridCacheService):
        self._sql_service = sql_service
        self._mongo_service = mongo_service
        self._read_load_system = read_load_system
        self._cache_service = cache_service
        self._logger = logging.getLogger(__name__)
        self._file_path = read_load_system.get_data_path() if read_load_system else os.getcwd()

    def get_allstock_monthly_statement(self, start: datetime) -> pd.DataFrame:
        """
        Get all stock monthly revenue statement
        
        Args:
            start: Target month date
            
        Returns:
            DataFrame with monthly revenue data
        """
        self._logger.info(f"Getting monthly statement data: {start}")
        
        if not Tools.Have_MonthRP(start):
            return pd.DataFrame()

        cache_key = f"monthly_statement_{start.year}_{start.month}"
        file_name = f"{start.year}-{start.month}"
        file_path = f"{self._file_path}/monthRP/{file_name}"

        # 1. Get from cache first
        cached_data = self._cache_service.get(cache_key)
        if cached_data is not None:
            return cached_data

        # 2. Get from SQL database
        sql_data = self._get_monthly_statement_from_sql(start)
        if not sql_data.empty:
            processed_data = self._process_monthly_statement_data(sql_data, start)
            self._cache_service.set(cache_key, processed_data, ttl=86400)
            return processed_data

        # 3. Get from local file
        file_data = self._get_monthly_statement_from_file(file_path, start)
        if not file_data.empty:
            processed_data = self._process_monthly_statement_data(file_data, start)
            self._save_monthly_statement_to_db(processed_data)
            self._cache_service.set(cache_key, processed_data, ttl=86400)
            return processed_data

        # 4. Download from external source
        self._monthly_statement(start.year, start.month)
        self._logger.info(f"Downloaded {start.month} monthly statement OK")

        crawler_data = pd.read_csv(f"{file_path}.csv")
        processed_data = self._process_monthly_statement_data(crawler_data, start)
        self._save_monthly_statement_to_db(processed_data)
        self._cache_service.set(cache_key, processed_data, ttl=86400)
        
        return processed_data

    def get_allstock_monthly_report(self, start: datetime) -> pd.DataFrame:
        """Legacy method for backward compatibility"""
        return self.get_allstock_monthly_statement(start)

    def _get_monthly_statement_from_sql(self, start: datetime) -> pd.DataFrame:
        """Get monthly statement data from SQL database"""
        # TODO: Implement SQL query
        return pd.DataFrame()

    def _process_monthly_statement_data(self, data: pd.DataFrame, start: datetime) -> pd.DataFrame:
        """Process and clean monthly statement data"""
        # TODO: Implement data processing
        return data

    def _get_monthly_statement_from_file(self, filename: str, start: datetime) -> pd.DataFrame:
        """Get monthly statement data from local file"""
        # TODO: Implement file reading
        return pd.DataFrame()

    def _save_monthly_statement_to_db(self, data: pd.DataFrame) -> None:
        """Save monthly statement data to database"""
        # TODO: Implement database save
        pass

    def _monthly_statement(self, year: int, month: int) -> None:
        """Download monthly statement data from external source"""
        # TODO: Implement crawler
        pass