"""
TGetExternalData - External Data Service (Facade Pattern)

此模組已重構：
- 已改為資料轉送器，委託給 datafetcher_core.external_data_facade
- 保留 GetExternalDataTest 繼承相容性
- 實際邏輯在 datafetcher_core 的 provider 模組中
"""
import os
import logging
from datetime import datetime
from typing import Optional

import pandas as pd

from src.Common import InfomationType as info
from datafetcher_core.interfaces import IGetExternalData
from datafetcher_core.external_data_facade import TGetExternalData as _TGetExternalData
from pydb_core.mongo_service import MongoService
from pydb_core.read_load_system import ReadLoadSystem
from pydb_core.sql_service import SqlService
from pydb_core.cache_service import HybridCacheService


class TGetExternalData(IGetExternalData):
    """讀取外部資料 - 轉送器實作

    委託給 datafetcher_core.external_data_facade.TGetExternalData。
    保留此類別供 GetExternalDataTest 繼承。
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
        self._file_path = os.getcwd()
        self._logger = logging.getLogger(__name__)

        # Internal delegate instance
        self._delegate = _TGetExternalData(
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
        return self._delegate.get_allstock_financial_statement(start, type)

    def get_allstock_monthly_statement(self, start: datetime) -> pd.DataFrame:
        """取得所有股票月營收資料"""
        return self._delegate.get_allstock_monthly_statement(start)

    def get_allstock_daily_data(self, start: datetime, end: datetime) -> pd.DataFrame:
        """取得所有股票每日股價資料"""
        return self._delegate.get_allstock_daily_data(start, end)

    def get_stock_history(self, symbol: str, start_date=None, end_date=None) -> pd.DataFrame:
        """取得股票歷史資料"""
        cache_key = f"stock_history:{symbol}:{start_date}:{end_date}"

        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            self._logger.debug(f"Cache HIT for {cache_key}")
            return cached_data

        self._logger.debug(f"Cache MISS for {cache_key}")

        data = self._delegate.get_stock_history(symbol, start_date, end_date)

        self._cache_service.set(cache_key, data, ttl=600)

        return data

    def get_stock_info(self) -> pd.DataFrame:
        """取得股票基本資訊"""
        return self._delegate.get_stock_info()

    def get_index_data(self, start: datetime, end: datetime) -> pd.DataFrame:
        """取得大盤指數資料"""
        return self._delegate.get_index_data(start, end)

    def get_allstock_monthly_report(self, start: datetime):
        """取得所有股票月營收報告 (相容舊介面)"""
        return self._delegate.get_allstock_monthly_report(start)

    def get_allstock_yield(self, symbol: str, start: datetime, end: datetime):
        """爬某天所有股票殖利率"""
        return self._delegate.get_allstock_yield(symbol, start, end)

    def get_allstock_dividend_yield(self):
        """從數據庫獲取所有股票股息殖利率數據"""
        return self._delegate.get_allstock_dividend_yield()

    def get_stock_AD_index(self, date: datetime, getNew=False):
        """取得上漲和下跌家數"""
        return self._delegate.get_stock_AD_index(date, getNew)

    def get_full_ad_index(self) -> pd.DataFrame:
        """取得完整的上漲和下跌家數歷史資料"""
        return self._delegate.get_full_ad_index()

    def get_full_adl(self) -> pd.DataFrame:
        """取得完整的騰落指標歷史資料"""
        return self._delegate.get_full_adl()
