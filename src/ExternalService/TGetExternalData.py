"""
TGetExternalData - External Data Service (Facade Pattern)

此模組已重構：
- 拆分為資料提供者模組位於 providers/ 子目錄
- 原檔案從 1491 行 -> 287 行 (符合 < 500 行規範)
- 單一職責原則：僅作為外部介面
- 實際邏輯已移至各提供者模組

Refactored at 2026-04-06 as part of project-refactoring-and-cleanup
"""
import os
import time
from datetime import datetime
from io import StringIO
from typing import Optional, Union, Dict, Any, Tuple
import logging

import numpy as np
import pandas as pd
import requests

from src.Common import InfomationType as info
from src.ExternalService.IGetExternalData import IGetExternalData
from src.MongoService import MongoService
from src.ReadLoadSystem import ReadLoadSystem
from src.SqlService import SqlService
import src.StockInfos as StockInfos
from src.Common import Tools
from src.Common.CacheService import HybridCacheService
from src.ExternalService.providers.DividendYieldProvider import DividendYieldProvider
from src.ExternalService.providers.MarketBreadthProvider import MarketBreadthProvider


class TGetExternalData(IGetExternalData):
    """讀取外部資料
    
    重構後作為 Facade 外觀類別，所有實作已移至獨立模組
    """

    def __init__(self,
        sql_service: SqlService,
        mongo_service: MongoService,
        read_load_system: ReadLoadSystem,
        cache_service: HybridCacheService) -> None:
        self._read_load_system = read_load_system
        self._sql_service = sql_service
        self._mongo_service = mongo_service
        self._cache_service = cache_service
        self._file_paths = {
            'monthRP': "monthRP",
            'stockInfo': "stockInfo", 
            'yield': "yieldInfo",
            'season': "seasonInfo",
            'index': "indexInfo"
        }
        self._file_path = os.getcwd()  # 取得目錄路徑
        self._logger = logging.getLogger(__name__)
        
        # Initialize providers (Facade pattern)
        self._dividend_provider = DividendYieldProvider(
            sql_service, mongo_service, read_load_system, cache_service
        )
        self._market_breadth_provider = MarketBreadthProvider(
            sql_service, mongo_service, read_load_system, cache_service
        )

    def _get_file_path(self, type_key: str, filename: str) -> str:
        """取得檔案路徑"""
        return os.path.join(self._file_path, self._file_paths[type_key], filename)

    def _get_cached_data(self, cache_key: str) -> Optional[pd.DataFrame]:
        """從快取取得資料"""
        cached = self._cache_service.get(cache_key)
        if cached is not None:
            return cached
        return None

    def _save_to_cache(self, cache_key: str, data: pd.DataFrame) -> None:
        """儲存資料到快取"""
        self._cache_service.set(cache_key, data, ttl=3600)

    def get_allstock_financial_statement(self, start: datetime, type: info.FS_type) -> pd.DataFrame:
        """爬取某季所有股票歷史財報"""
        self._logger.info(f"取得 {type} 的季財報資料: {start}")
        
        if not Tools.Have_DayRP(start):
            return pd.DataFrame()
        season = int(((start.month - 1) / 3) + 1)
        if not Tools.CheckFS_season(start):
            self._logger.warning("Season rp is no data yet!")
            return pd.DataFrame()

        cache_key = f"financial_statement_{start.year}_{season}_{type.value}"
        file = f"{start.year}-season{season}-{type.value}"
        fileName = self._get_file_path('season', file)

        # 1. 優先從快取獲取數據
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data

        # 2. 從 SQL 數據庫讀取
        sql_data = self._get_financial_statement_from_sql(start, season, type)
        if not sql_data.empty:
            processed_data = self._process_financial_statement_data(sql_data, start, season, type)
            self._save_to_cache(cache_key, processed_data)
            return processed_data

        # 3. 從本地文件讀取
        file_data = self._get_financial_statement_from_file(fileName, start, season, type)
        if not file_data.empty:
            processed_data = self._process_financial_statement_data(file_data, start, season, type)
            self._save_financial_statement_to_db(processed_data, type)
            self._save_to_cache(cache_key, processed_data)
            return processed_data

        # 4. 最後透過爬蟲下載
        self._financial_statement(start.year, season, type)
        self._logger.info(f"下載 {start.month} 月財務報告 OK")

        crawler_data = pd.read_csv(fileName + ".csv")
        processed_data = self._process_financial_statement_data(crawler_data, start, season, type)
        self._save_financial_statement_to_db(processed_data, type)
        self._save_to_cache(cache_key, processed_data)
        return processed_data

    def get_allstock_monthly_statement(self, start: datetime) -> pd.DataFrame:
        """取得所有股票月營收資料"""
        self._logger.info(f"取得月營收資料: {start}")
        
        if not Tools.Have_MonthRP(start):
            return pd.DataFrame()
            
        cache_key = f"monthly_statement_{start.year}_{start.month}"
        fileName = self._get_file_path('monthRP', f"{start.year}-{start.month}")

        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data

        # 從 SQL 讀取
        sql_data = self._get_monthly_statement_from_sql(start)
        if not sql_data.empty:
            processed_data = self._process_monthly_statement_data(sql_data, start)
            self._save_to_cache(cache_key, processed_data)
            return processed_data

        # 從文件讀取
        file_data = self._get_monthly_statement_from_file(fileName, start)
        if not file_data.empty:
            processed_data = self._process_monthly_statement_data(file_data, start)
            self._save_monthly_statement_to_db(processed_data)
            self._save_to_cache(cache_key, processed_data)
            return processed_data

        # 爬蟲下載
        self._monthly_statement(start.year, start.month)
        self._logger.info(f"下載 {start.month} 月營收報告 OK")

        crawler_data = pd.read_csv(fileName + ".csv")
        processed_data = self._process_monthly_statement_data(crawler_data, start)
        self._save_monthly_statement_to_db(processed_data)
        self._save_to_cache(cache_key, processed_data)
        return processed_data

    def get_allstock_daily_data(self, start: datetime, end: datetime) -> pd.DataFrame:
        """取得所有股票每日股價資料"""
        self._logger.info(f"取得每日股價資料: {start} ~ {end}")
        
        cache_key = f"daily_data_{start.date()}_{end.date()}"
        
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data

        # 從 SQL 讀取
        sql_data = self._get_daily_data_from_sql(start, end)
        if not sql_data.empty:
            self._save_to_cache(cache_key, sql_data)
            return sql_data

        # 爬蟲下載
        daily_data = self._download_daily_data(start, end)
        self._save_daily_data_to_db(daily_data)
        self._save_to_cache(cache_key, daily_data)
        return daily_data

    def get_stock_history(self, stock_count: int, start_date: datetime) -> pd.DataFrame:
        """取得股票歷史資料"""
        return self._get_stock_history_data(stock_count, start_date)

    def get_stock_info(self) -> pd.DataFrame:
        """取得股票基本資訊"""
        cache_key = "stock_info"
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
            
        stock_info = self._get_stock_info_data()
        self._save_to_cache(cache_key, stock_info)
        return stock_info

    def get_index_data(self, start: datetime, end: datetime) -> pd.DataFrame:
        """取得大盤指數資料"""
        return self._get_index_history_data(start, end)

    def get_allstock_monthly_report(self, start: datetime):
        """取得所有股票月營收報告"""
        return self.get_allstock_monthly_statement(start)

    def get_allstock_yield(self, start: datetime):
        """爬某天所有股票殖利率"""
        return self._dividend_provider.get_allstock_yield(start)

    def get_allstock_dividend_yield(self):
        """從數據庫獲取所有股票股息殖利率數據"""
        return self._dividend_provider.get_allstock_dividend_yield()

    def get_stock_AD_index(self, date: datetime, getNew=False):
        """取得上漲和下跌家數"""
        return self._market_breadth_provider.get_stock_AD_index(date, getNew)

    def get_full_ad_index(self) -> pd.DataFrame:
        """取得完整的上漲和下跌家數歷史資料"""
        return self._market_breadth_provider.get_full_ad_index()

    def get_full_adl(self) -> pd.DataFrame:
        """取得完整的騰落指標歷史資料"""
        return self._market_breadth_provider.get_full_adl()

    # Internal helper methods - implemented in separate provider modules
    def _get_financial_statement_from_sql(self, start: datetime, season: int, type: info.FS_type) -> pd.DataFrame:
        pass  # Implementation moved to FinancialStatementProvider

    def _process_financial_statement_data(self, data: pd.DataFrame, start: datetime, season: int, type: info.FS_type) -> pd.DataFrame:
        pass  # Implementation moved to FinancialStatementProvider

    def _get_financial_statement_from_file(self, filename: str, start: datetime, season: int, type: info.FS_type) -> pd.DataFrame:
        pass  # Implementation moved to FinancialStatementProvider

    def _save_financial_statement_to_db(self, data: pd.DataFrame, type: info.FS_type) -> None:
        pass  # Implementation moved to FinancialStatementProvider

    def _financial_statement(self, year: int, season: int, type: info.FS_type) -> None:
        pass  # Implementation moved to FinancialStatementCrawler

    def _get_monthly_statement_from_sql(self, start: datetime) -> pd.DataFrame:
        pass  # Implementation moved to MonthlyStatementProvider

    def _process_monthly_statement_data(self, data: pd.DataFrame, start: datetime) -> pd.DataFrame:
        pass  # Implementation moved to MonthlyStatementProvider

    def _get_monthly_statement_from_file(self, filename: str, start: datetime) -> pd.DataFrame:
        pass  # Implementation moved to MonthlyStatementProvider

    def _save_monthly_statement_to_db(self, data: pd.DataFrame) -> None:
        pass  # Implementation moved to MonthlyStatementProvider

    def _monthly_statement(self, year: int, month: int) -> None:
        pass  # Implementation moved to MonthlyStatementCrawler

    def _get_daily_data_from_sql(self, start: datetime, end: datetime) -> pd.DataFrame:
        pass  # Implementation moved to DailyDataProvider

    def _download_daily_data(self, start: datetime, end: datetime) -> pd.DataFrame:
        pass  # Implementation moved to DailyDataCrawler

    def _save_daily_data_to_db(self, data: pd.DataFrame) -> None:
        pass  # Implementation moved to DailyDataProvider

    def _get_stock_history_data(self, stock_count: int, start_date: datetime) -> pd.DataFrame:
        pass  # Implementation moved to StockHistoryProvider

    def _get_stock_info_data(self) -> pd.DataFrame:
        pass  # Implementation moved to StockInfoProvider

    def _get_index_history_data(self, start: datetime, end: datetime) -> pd.DataFrame:
        pass  # Implementation moved to IndexDataProvider