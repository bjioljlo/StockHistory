"""
StockHistory 快取服務

提供 Redis 快取功能，提升資料庫查詢效能。
支援查詢結果快取、資料預熱和快取失效策略。
"""

import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
import redis
import yaml
from sqlalchemy import text
import pandas as pd


class CacheService:
    """快取服務類別"""

    def __init__(self, config_path='config.yml'):
        self.config = self._load_config(config_path)

        # Redis 配置
        redis_config = self.config.get('redis', {})
        self.redis_client = redis.Redis(
            host=redis_config.get('host', 'localhost'),
            port=redis_config.get('port', 6379),
            db=redis_config.get('db', 0),
            decode_responses=True,
            socket_timeout=redis_config.get('socket_timeout', 5),
            socket_connect_timeout=redis_config.get('socket_connect_timeout', 5)
        )

        # 快取配置
        self.cache_config = {
            'default_ttl': redis_config.get('default_ttl', 3600),  # 預設1小時
            'max_memory': redis_config.get('max_memory', '512mb'),
            'query_cache_ttl': redis_config.get('query_cache_ttl', 1800),  # 查詢快取30分鐘
            'data_cache_ttl': redis_config.get('data_cache_ttl', 7200),  # 資料快取2小時
            'compression_threshold': redis_config.get('compression_threshold', 1024),  # 壓縮閾值1KB
        }

        # 設定日誌
        logging.basicConfig(
            filename='logs/cache.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # 測試連線
        try:
            self.redis_client.ping()
            self.logger.info("Redis 連線成功")
        except redis.ConnectionError:
            self.logger.error("Redis 連線失敗")
            self.redis_client = None

    def _load_config(self, config_path):
        """載入配置檔案"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"載入配置檔案失敗: {e}")
            return {}

    def _generate_cache_key(self, query: str, params: Optional[Dict] = None) -> str:
        """生成快取鍵"""
        key_data = {
            'query': query.strip(),
            'params': params or {}
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return f"query:{hashlib.md5(key_string.encode()).hexdigest()}"

    def _serialize_dataframe(self, df: pd.DataFrame) -> str:
        """序列化 DataFrame"""
        if df.empty:
            return json.dumps({'empty': True, 'columns': []})

        # 將 DataFrame 轉換為字典格式
        data = {
            'columns': df.columns.tolist(),
            'index': df.index.tolist() if not df.index.equals(range(len(df))) else None,
            'data': df.values.tolist()
        }
        return json.dumps(data, default=str)

    def _deserialize_dataframe(self, data: str) -> pd.DataFrame:
        """反序列化 DataFrame"""
        try:
            parsed = json.loads(data)
            if parsed.get('empty'):
                return pd.DataFrame(columns=parsed.get('columns', []))

            df = pd.DataFrame(
                parsed['data'],
                columns=parsed['columns']
            )

            if parsed.get('index'):
                df.index = parsed['index']

            return df
        except Exception as e:
            self.logger.error(f"反序列化 DataFrame 失敗: {e}")
            return pd.DataFrame()

    def get_cached_query(self, query: str, params: Optional[Dict] = None) -> Optional[pd.DataFrame]:
        """獲取快取的查詢結果"""
        if not self.redis_client:
            return None

        try:
            cache_key = self._generate_cache_key(query, params)
            cached_data = self.redis_client.get(cache_key)

            if cached_data:
                self.logger.info(f"快取命中: {cache_key}")
                return self._deserialize_dataframe(cached_data)

        except Exception as e:
            self.logger.error(f"獲取快取失敗: {e}")

        return None

    def set_cached_query(self, query: str, df: pd.DataFrame, params: Optional[Dict] = None,
                        ttl: Optional[int] = None) -> bool:
        """設定查詢結果快取"""
        if not self.redis_client or df.empty:
            return False

        try:
            cache_key = self._generate_cache_key(query, params)
            serialized_data = self._serialize_dataframe(df)

            # 檢查資料大小是否需要壓縮
            if len(serialized_data.encode()) > self.cache_config['compression_threshold']:
                # 使用 Redis 的壓縮功能（如果可用）
                self.redis_client.set(cache_key, serialized_data,
                                    ex=ttl or self.cache_config['query_cache_ttl'])
            else:
                self.redis_client.set(cache_key, serialized_data,
                                    ex=ttl or self.cache_config['query_cache_ttl'])

            self.logger.info(f"設定快取: {cache_key}")
            return True

        except Exception as e:
            self.logger.error(f"設定快取失敗: {e}")
            return False

    def invalidate_query_cache(self, query_pattern: str = "*") -> int:
        """失效查詢快取"""
        if not self.redis_client:
            return 0

        try:
            pattern = f"query:{query_pattern}"
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted_count = self.redis_client.delete(*keys)
                self.logger.info(f"失效快取: {deleted_count} 個鍵")
                return deleted_count
        except Exception as e:
            self.logger.error(f"失效快取失敗: {e}")

        return 0

    def get_cache_stats(self) -> Dict[str, Any]:
        """獲取快取統計資訊"""
        if not self.redis_client:
            return {'status': 'disconnected'}

        try:
            info = self.redis_client.info()
            keys = self.redis_client.keys('query:*')

            return {
                'status': 'connected',
                'total_keys': len(keys),
                'memory_used': info.get('used_memory_human', '0B'),
                'memory_peak': info.get('used_memory_peak_human', '0B'),
                'hit_rate': info.get('keyspace_hits', 0) / max(info.get('keyspace_misses', 0) + info.get('keyspace_hits', 0), 1),
                'evictions': info.get('evicted_keys', 0),
                'connections': info.get('connected_clients', 0)
            }

        except Exception as e:
            self.logger.error(f"獲取快取統計失敗: {e}")
            return {'status': 'error', 'message': str(e)}

    def warmup_cache(self, queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """預熱快取"""
        results = {
            'total_queries': len(queries),
            'successful': 0,
            'failed': 0,
            'details': []
        }

        # 這裡需要資料庫連線來執行查詢
        # 實際實作時需要傳入資料庫連線
        self.logger.info("快取預熱功能需要資料庫連線來實作")

        return results

    def set_data_cache(self, key: str, data: Any, ttl: Optional[int] = None) -> bool:
        """設定資料快取"""
        if not self.redis_client:
            return False

        try:
            if isinstance(data, (dict, list)):
                serialized_data = json.dumps(data, default=str)
            else:
                serialized_data = str(data)

            self.redis_client.set(key, serialized_data,
                                ex=ttl or self.cache_config['data_cache_ttl'])
            return True

        except Exception as e:
            self.logger.error(f"設定資料快取失敗: {e}")
            return False

    def get_data_cache(self, key: str) -> Optional[Any]:
        """獲取資料快取"""
        if not self.redis_client:
            return None

        try:
            data = self.redis_client.get(key)
            if data:
                try:
                    return json.loads(data)
                except json.JSONDecodeError:
                    return data
        except Exception as e:
            self.logger.error(f"獲取資料快取失敗: {e}")

        return None

    def delete_data_cache(self, key: str) -> bool:
        """刪除資料快取"""
        if not self.redis_client:
            return False

        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            self.logger.error(f"刪除資料快取失敗: {e}")
            return False

    def clear_all_cache(self) -> bool:
        """清除所有快取"""
        if not self.redis_client:
            return False

        try:
            self.redis_client.flushdb()
            self.logger.info("清除所有快取")
            return True
        except Exception as e:
            self.logger.error(f"清除快取失敗: {e}")
            return False

    def health_check(self) -> Dict[str, Any]:
        """快取服務健康檢查"""
        if not self.redis_client:
            return {
                'status': 'disconnected',
                'message': 'Redis 連線未初始化'
            }

        try:
            # 測試連線
            self.redis_client.ping()

            # 獲取基本資訊
            info = self.redis_client.info()

            return {
                'status': 'healthy',
                'version': info.get('redis_version', 'unknown'),
                'uptime_seconds': info.get('uptime_in_seconds', 0),
                'memory_used': info.get('used_memory_human', '0B'),
                'connected_clients': info.get('connected_clients', 0)
            }

        except redis.ConnectionError:
            return {
                'status': 'unhealthy',
                'message': 'Redis 連線失敗'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }


class CachedSqlService:
    """帶快取功能的 SQL 服務"""

    def __init__(self, sql_service, cache_service: CacheService):
        self.sql_service = sql_service
        self.cache = cache_service

    def read_stock_day_cached(self, name: str) -> pd.DataFrame:
        """快取版本的 readStockDay"""
        # 建立快取鍵
        cache_key = f"stock_day:{name.lower()}"

        # 嘗試從快取獲取
        cached_data = self.cache.get_data_cache(cache_key)
        if cached_data:
            self.cache.logger.info(f"快取命中: {cache_key}")
            return pd.DataFrame(cached_data)

        # 從資料庫獲取
        df = self.sql_service.readStockDay(name)
        if not df.empty:
            # 設定快取
            data_dict = df.to_dict('records')
            self.cache.set_data_cache(cache_key, data_dict)

        return df

    def read_dividend_yield_cached(self, name: str) -> pd.DataFrame:
        """快取版本的 readDividendYield"""
        cache_key = f"dividend_yield:{name.lower()}"

        cached_data = self.cache.get_data_cache(cache_key)
        if cached_data:
            self.cache.logger.info(f"快取命中: {cache_key}")
            return pd.DataFrame(cached_data)

        df = self.sql_service.readDividendYield(name)
        if not df.empty:
            data_dict = df.to_dict('records')
            self.cache.set_data_cache(cache_key, data_dict)

        return df

    def invalidate_stock_cache(self, stock_name: str):
        """失效特定股票的快取"""
        patterns = [
            f"stock_day:{stock_name.lower()}",
            f"dividend_yield:{stock_name.lower()}",
            f"query:*{stock_name.lower()}*"
        ]

        for pattern in patterns:
            keys = self.cache.redis_client.keys(pattern)
            if keys:
                self.cache.redis_client.delete(*keys)
                self.cache.logger.info(f"失效快取: {pattern}")


# 全域快取服務實例
_cache_service = None


def get_cache_service(config_path='config.yml') -> CacheService:
    """獲取快取服務實例"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService(config_path)
    return _cache_service


def create_cached_sql_service(sql_service) -> CachedSqlService:
    """創建帶快取功能的 SQL 服務"""
    cache_service = get_cache_service()
    return CachedSqlService(sql_service, cache_service)
