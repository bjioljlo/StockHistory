"""
Market Breadth Provider
Handles AD index, ADL and market breadth indicators

Part of TGetExternalData refactoring
"""
from datetime import datetime
import pandas as pd
import logging

from pydb_core.sql_service import SqlService
from pydb_core.mongo_service import MongoService
from pydb_core.read_load_system import ReadLoadSystem
from pydb_core.cache_service import HybridCacheService


class MarketBreadthProvider:
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

    def get_stock_AD_index(self, date: datetime, getNew: bool = False) -> pd.DataFrame:
        """
        Get advance-decline index for specific date
        
        Args:
            date: Target date
            getNew: Force refresh from external source
            
        Returns:
            DataFrame with up/down count
        """
        self._logger.info(f"Getting AD index for {date}, getNew={getNew}")
        
        cache_key = f"ad_index_{date.date()}"
        
        if not getNew:
            cached = self._cache_service.get(cache_key)
            if cached is not None:
                return cached
        
        date_str = date.strftime('%Y-%m-%d')
        
        # 從資料庫查詢指定日期
        df = self._sql_service.read_ad_index(start_date=date_str, end_date=date_str, limit=1)
        
        if not df.empty:
            # 找到記錄，補上不變動數量欄位
            df['unchanged_count'] = 0
            self._cache_service.set(cache_key, df, ttl=1800)
            return df
            
        # 當getNew=True或快取/資料庫沒有資料時，從外部來源計算
        if getNew or df.empty:
            self._logger.debug(f"Calculating new AD index for {date_str}")
            # 調用ReadLoadSystem計算當天漲跌數量
            result = self._read_load_system.calculate_ad_index_for_date(date)
            if not result.empty:
                # 寫入資料庫時需要重設索引，讓date成為一般欄位
                df_to_insert = result.reset_index()
                self._sql_service.insert_data('ad_index', df_to_insert)
                self._cache_service.set(cache_key, result, ttl=1800)
                return result
                
        # 返回結構正確的空DataFrame
        return pd.DataFrame(columns=['up_count', 'down_count', 'unchanged_count'])

    def get_full_ad_index(self) -> pd.DataFrame:
        """
        Get complete advance-decline index history
        
        Returns:
            DataFrame with full AD index history
        """
        self._logger.info("Getting full AD index history")
        
        cache_key = "ad_index_full_history"
        
        cached = self._cache_service.get(cache_key)
        if cached is not None:
            return cached
        
        # 從資料庫讀取完整AD index歷史
        result = self._sql_service.read_ad_index(limit=100000)
        
        if not result.empty:
            self._cache_service.set(cache_key, result, ttl=3600)
            
        return result

    def get_full_adl(self) -> pd.DataFrame:
        """
        Get complete Advance-Decline Line (ADL) history
        
        Returns:
            DataFrame with ADL values
        """
        self._logger.info("Getting full ADL history")
        
        cache_key = "adl_full_history"
        
        cached = self._cache_service.get(cache_key)
        if cached is not None:
            return cached
        
        # 先取得完整AD index歷史
        ad_index_history = self.get_full_ad_index()
        
        if ad_index_history.empty:
            return pd.DataFrame(columns=['ADL'])
        
        # 依日期排序
        ad_index_history = ad_index_history.sort_index()
        
        # 計算每日淨漲跌
        daily_diff = ad_index_history["up_count"] - ad_index_history["down_count"]
        
        # 累計計算ADL線
        adl_series = daily_diff.cumsum()
        
        result = pd.DataFrame({"ADL": adl_series})
        
        if not result.empty:
            self._cache_service.set(cache_key, result, ttl=3600)
            
        return result
