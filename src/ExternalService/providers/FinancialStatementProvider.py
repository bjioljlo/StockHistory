"""
Financial Statement Provider
Handles quarterly financial statement data operations

Part of TGetExternalData refactoring
"""
import os
from datetime import datetime
import pandas as pd
import logging

from src.Common import InfomationType as info
from src.SqlService import SqlService
from src.MongoService import MongoService
from src.ReadLoadSystem import ReadLoadSystem
from src.Common.CacheService import HybridCacheService
from src.Common import Tools


class FinancialStatementProvider:
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

    def get_allstock_financial_statement(self, start: datetime, type: info.FS_type) -> pd.DataFrame:
        """
        Get all stock financial statements for specific quarter
        
        Args:
            start: Target date (any date in target quarter)
            type: Financial statement type
            
        Returns:
            DataFrame with financial statement data
        """
        self._logger.info(f"Getting {type} financial statement data: {start}")
        
        if not Tools.Have_DayRP(start):
            return pd.DataFrame()
        
        season = int(((start.month - 1) / 3) + 1)
        
        if not Tools.CheckFS_season(start):
            self._logger.warning("Season financial statement data not available yet")
            return pd.DataFrame()

        cache_key = f"financial_statement_{start.year}_{season}_{type.value}"
        file_name = f"{start.year}-season{season}-{type.value}"
        file_path = f"{self._file_path}/season/{file_name}"

        # 1. Get from cache first
        cached_data = self._cache_service.get(cache_key)
        if cached_data is not None:
            return cached_data

        # 2. Get from SQL database
        sql_data = self._get_financial_statement_from_sql(start, season, type)
        if not sql_data.empty:
            processed_data = self._process_financial_statement_data(sql_data, start, season, type)
            self._cache_service.set(cache_key, processed_data, ttl=86400)
            return processed_data

        # 3. Get from local file
        file_data = self._get_financial_statement_from_file(file_path, start, season, type)
        if not file_data.empty:
            processed_data = self._process_financial_statement_data(file_data, start, season, type)
            self._save_financial_statement_to_db(processed_data, type)
            self._cache_service.set(cache_key, processed_data, ttl=86400)
            return processed_data

        # 4. Download from external source
        self._financial_statement(start.year, season, type)
        self._logger.info(f"Downloaded {start.month} financial statement OK")

        crawler_data = pd.read_csv(f"{file_path}.csv")
        processed_data = self._process_financial_statement_data(crawler_data, start, season, type)
        self._save_financial_statement_to_db(processed_data, type)
        self._cache_service.set(cache_key, processed_data, ttl=86400)
        
        return processed_data

    def _get_financial_statement_from_sql(self, start: datetime, season: int, type: info.FS_type) -> pd.DataFrame:
        """Get financial statement data from SQL database"""
        # TODO: Implement SQL query
        return pd.DataFrame()

    def _process_financial_statement_data(self, data: pd.DataFrame, start: datetime, season: int, type: info.FS_type) -> pd.DataFrame:
        """Process and clean financial statement data"""
        # TODO: Implement data processing
        return data

    def _get_financial_statement_from_file(self, filename: str, start: datetime, season: int, type: info.FS_type) -> pd.DataFrame:
        """Get financial statement data from local file"""
        # TODO: Implement file reading
        return pd.DataFrame()

    def _save_financial_statement_to_db(self, data: pd.DataFrame, type: info.FS_type) -> None:
        """Save financial statement data to database"""
        # TODO: Implement database save
        pass

    def _financial_statement(self, year: int, season: int, type: info.FS_type) -> None:
        """Download financial statement data from external source"""
        # TODO: Implement crawler
        pass