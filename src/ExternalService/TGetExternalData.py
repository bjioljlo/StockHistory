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
from src.ExternalService.providers.FinancialStatementProvider import FinancialStatementProvider
from src.ExternalService.providers.MonthlyStatementProvider import MonthlyStatementProvider
from src.ExternalService.providers.DailyDataProvider import DailyDataProvider


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
        self._financial_statement_provider = FinancialStatementProvider(
            sql_service, mongo_service, read_load_system, cache_service
        )
        self._monthly_statement_provider = MonthlyStatementProvider(
            sql_service, mongo_service, read_load_system, cache_service
        )
        self._daily_data_provider = DailyDataProvider(
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
        return self._financial_statement_provider.get_allstock_financial_statement(start, type)

    def get_allstock_monthly_statement(self, start: datetime) -> pd.DataFrame:
        """取得所有股票月營收資料"""
        return self._monthly_statement_provider.get_allstock_monthly_statement(start)

    def get_allstock_daily_data(self, start: datetime, end: datetime) -> pd.DataFrame:
        """取得所有股票每日股價資料"""
        return self._daily_data_provider.get_allstock_daily_data(start, end)

    def get_stock_history(self, symbol: str, start_date=None, end_date=None) -> pd.DataFrame:
        """取得股票歷史資料"""
        # 建立快取鍵值
        cache_key = f"stock_history:{symbol}:{start_date}:{end_date}"
        
        # 檢查快取
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            self._logger.debug(f"Cache HIT for {cache_key}")
            return cached_data
            
        self._logger.debug(f"Cache MISS for {cache_key}")
        
        # 呼叫底層實作
        data = self._daily_data_provider.get_stock_history(symbol, start_date, end_date)
        
        # 儲存到快取 (128筆限制由底層CacheService處理, TTL 600秒)
        self._cache_service.set(cache_key, data, ttl=600)
        
        return data

    def get_stock_info(self) -> pd.DataFrame:
        """取得股票基本資訊"""
        return self._daily_data_provider.get_stock_info()

    def get_index_data(self, start: datetime, end: datetime) -> pd.DataFrame:
        """取得大盤指數資料"""
        return self._daily_data_provider.get_index_data(start, end)

    def get_allstock_monthly_report(self, start: datetime):
        """取得所有股票月營收報告 (相容舊介面)"""
        return self._monthly_statement_provider.get_allstock_monthly_report(start)

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

    # All business logic implemented in separate provider modules
    # This class acts as pure Facade following single responsibility principle
