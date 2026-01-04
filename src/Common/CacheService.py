"""
混合快取層實現

整合 Redis (L1快取) 和 MongoDB (L2智慧快取) 的混合快取架構：
- Redis：高性能短期快取，取代原有的 Memory 快取
- MongoDB：智慧快取層，專門處理熱門股票的完整歷史資料
"""

import json
import logging
import hashlib
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import redis
import yaml
import pandas as pd

class HybridCacheService:
    """混合快取服務：Redis + MongoDB"""

    def __init__(self, mongo_service, sql_service, config_path='config.yml', cache_size: int = 100):
        # 載入配置
        self.config = self._load_config(config_path)

        # Redis 配置 (L1 快取)
        redis_config = self.config.get('redis', {})
        self.redis_client = redis.Redis(
            host=redis_config.get('host', 'localhost'),
            port=redis_config.get('port', 6379),
            db=redis_config.get('db', 0),
            decode_responses=True,
            socket_timeout=redis_config.get('socket_timeout', 5),
            socket_connect_timeout=redis_config.get('socket_connect_timeout', 5)
        )

        # MongoDB 配置 (L2 智慧快取)
        self.mongo_service = mongo_service
        self.sql_service = sql_service
        self.cache_size = cache_size  # MongoDB 快取的股票數量上限

        # 查詢統計 (用於智慧快取)
        self.query_stats: Dict[str, int] = {}
        self.last_mongo_update = datetime.now()
        self.mongo_update_interval = timedelta(hours=1)
        self._lock = threading.Lock()

        # Redis 快取配置
        self.redis_config = {
            'default_ttl': redis_config.get('default_ttl', 3600),  # 1小時
            'query_cache_ttl': redis_config.get('query_cache_ttl', 1800),  # 30分鐘
            'data_cache_ttl': redis_config.get('data_cache_ttl', 7200),  # 2小時
            'compression_threshold': redis_config.get('compression_threshold', 1024),
        }

        # 設定日誌
        logging.basicConfig(
            filename='logs/cache.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # 測試 Redis 連線
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

    def _generate_cache_key(self, key_type: str, identifier: str) -> str:
        """生成快取鍵"""
        return f"{key_type}:{identifier.lower()}"

    def _serialize_dataframe(self, df: pd.DataFrame) -> str:
        """序列化 DataFrame 為 Redis 儲存"""
        if df.empty:
            return json.dumps({'empty': True, 'columns': []})

        # 確保索引是字符串格式，避免 datetime.date 編碼問題
        index_list = None
        if not df.index.equals(range(len(df))):
            # 將索引轉換為字符串列表
            index_list = [str(idx) for idx in df.index]

        # 將 DataFrame 轉換為字典格式
        data = {
            'columns': df.columns.tolist(),
            'index': index_list,
            'data': df.values.tolist()
        }
        return json.dumps(data, default=str)

    def _deserialize_dataframe(self, data: str) -> pd.DataFrame:
        """從 Redis 反序列化 DataFrame"""
        try:
            parsed = json.loads(data)
            if parsed.get('empty'):
                return pd.DataFrame(columns=parsed.get('columns', []))

            df = pd.DataFrame(parsed['data'], columns=parsed['columns'])

            if parsed.get('index'):
                df.index = parsed['index']

            return df
        except Exception as e:
            self.logger.error(f"反序列化 DataFrame 失敗: {e}")
            return pd.DataFrame()

    # ========== Redis L1 快取操作 ==========

    def get_redis_cache(self, key: str) -> Optional[Any]:
        """從 Redis 獲取快取"""
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
            self.logger.error(f"Redis 獲取快取失敗: {e}")

        return None

    def set_redis_cache(self, key: str, data: Any, ttl: Optional[int] = None) -> bool:
        """設定 Redis 快取"""
        if not self.redis_client:
            return False

        try:
            if isinstance(data, (dict, list, pd.DataFrame)):
                if isinstance(data, pd.DataFrame):
                    serialized_data = self._serialize_dataframe(data)
                else:
                    serialized_data = json.dumps(data, default=str)
            else:
                serialized_data = str(data)

            self.redis_client.set(key, serialized_data, ex=ttl or self.redis_config['data_cache_ttl'])
            return True

        except Exception as e:
            self.logger.error(f"Redis 設定快取失敗: {e}")
            return False

    def delete_redis_cache(self, key: str) -> bool:
        """刪除 Redis 快取"""
        if not self.redis_client:
            return False

        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            self.logger.error(f"Redis 刪除快取失敗: {e}")
            return False

    # ========== MongoDB L2 智慧快取操作 ==========

    def record_query(self, stock_symbol: str):
        """記錄股票查詢統計"""
        with self._lock:
            self.query_stats[stock_symbol] = self.query_stats.get(stock_symbol, 0) + 1

    def get_hot_stocks(self, limit: int = None) -> List[str]:
        """獲取熱門股票列表"""
        if limit is None:
            limit = self.cache_size

        with self._lock:
            sorted_stocks = sorted(
                self.query_stats.items(),
                key=lambda x: x[1],
                reverse=True
            )
            return [stock for stock, _ in sorted_stocks[:limit]]

    def should_update_mongo_cache(self) -> bool:
        """檢查是否需要更新 MongoDB 快取"""
        return datetime.now() - self.last_mongo_update > self.mongo_update_interval

    def update_mongo_cache(self):
        """更新 MongoDB 智慧快取"""
        if not self.should_update_mongo_cache():
            return

        print("Updating MongoDB smart cache for hot stocks...")
        hot_stocks = self.get_hot_stocks(self.cache_size)

        for stock_symbol in hot_stocks:
            try:
                # 從 MySQL 讀取完整資料
                df = self.sql_service.readStockDay(stock_symbol)
                if not df.empty:
                    # 同步到 MongoDB
                    self.mongo_service.saveTable(stock_symbol.lower(), df)
                    print(f"Smart cached {stock_symbol} to MongoDB")
            except Exception as e:
                print(f"Failed to smart cache {stock_symbol}: {e}")

        self.last_mongo_update = datetime.now()
        print(f"MongoDB smart cache updated for {len(hot_stocks)} hot stocks")

    def get_mongo_cache(self, stock_symbol: str) -> Optional[pd.DataFrame]:
        """從 MongoDB 獲取股票資料"""
        try:
            # 檢查 MongoDB 連線是否已初始化
            if not self.mongo_service or not self.mongo_service.mongodb:
                self.logger.warning("MongoDB connection not initialized")
                return None

            collection = self.mongo_service.mongodb[stock_symbol.lower()]
            cursor = collection.find()

            # 將游標轉換為列表，處理日期欄位
            data = []
            for doc in cursor:
                # 移除 MongoDB 的 _id 欄位
                if '_id' in doc:
                    del doc['_id']

                # 處理日期欄位，將字符串轉換回 datetime
                if 'Date' in doc and isinstance(doc['Date'], str):
                    try:
                        doc['Date'] = pd.to_datetime(doc['Date'])
                    except:
                        pass  # 如果轉換失敗，保持原樣

                data.append(doc)

            if data:
                df = pd.DataFrame(data)

                # 設定日期索引
                if 'Date' in df.columns:
                    df = df.set_index('Date')
                    # 確保索引是 DatetimeIndex
                    df.index = pd.to_datetime(df.index)

                return df
        except Exception as e:
            self.logger.error(f"MongoDB 獲取快取失敗: {e}")

        return None

    def cleanup_cold_mongo_cache(self, days_threshold: int = 30):
        """清理 MongoDB 冷門股票快取"""
        print("Cleaning up cold MongoDB cache entries...")

        try:
            db = self.mongo_service.mongodb
            collections = db.list_collection_names()

            # 篩選出股票集合
            stock_collections = [
                col for col in collections
                if not col.startswith('system.') and col not in ['ad_index']
            ]

            hot_stocks = set(self.get_hot_stocks(self.cache_size * 2))
            cold_stocks = []

            for collection in stock_collections:
                stock_symbol = collection.upper()
                if stock_symbol not in hot_stocks:
                    cold_stocks.append(collection)

            # 刪除冷門股票集合
            for collection in cold_stocks:
                db.drop_collection(collection)
                print(f"Dropped cold cache collection: {collection}")

            print(f"Cleaned up {len(cold_stocks)} cold MongoDB cache entries")

        except Exception as e:
            print(f"Error during MongoDB cache cleanup: {e}")

    # ========== 統一快取介面 ==========

    def get_stock_data(self, stock_symbol: str) -> Optional[pd.DataFrame]:
        """
        統一的股票資料獲取介面
        優先順序：Redis (L1) → MongoDB (L2)
        """
        # 1. 嘗試從 Redis L1 快取獲取
        redis_key = self._generate_cache_key("stock", stock_symbol)
        redis_data = self.get_redis_cache(redis_key)

        if redis_data and isinstance(redis_data, dict):
            try:
                df = pd.DataFrame(
                    redis_data['data'],
                    columns=redis_data['columns']
                )
                if redis_data.get('index'):
                    df.index = redis_data['index']
                self.logger.info(f"L1 Cache hit for {stock_symbol}")
                return df
            except:
                pass

        # 2. 嘗試從 MongoDB L2 智慧快取獲取
        mongo_data = self.get_mongo_cache(stock_symbol)
        if mongo_data is not None and not mongo_data.empty:
            # 同步到 Redis L1 快取（確保索引轉換為字符串）
            index_list = [str(idx) for idx in mongo_data.index] if not mongo_data.index.equals(range(len(mongo_data))) else None
            self.set_redis_cache(redis_key, {
                'data': mongo_data.values.tolist(),
                'columns': mongo_data.columns.tolist(),
                'index': index_list
            })
            self.logger.info(f"L2 Cache hit for {stock_symbol}")
            return mongo_data

        return None

    def set_stock_data(self, stock_symbol: str, df: pd.DataFrame):
        """
        設定股票資料到快取
        同時更新 Redis L1 和 MongoDB L2 (如果為熱門股票)
        """
        if df.empty:
            return

        # 1. 更新 Redis L1 快取
        redis_key = self._generate_cache_key("stock", stock_symbol)
        # 確保索引轉換為字符串以避免 datetime.date 編碼問題
        index_list = [str(idx) for idx in df.index] if not df.index.equals(range(len(df))) else None
        cache_data = {
            'data': df.values.tolist(),
            'columns': df.columns.tolist(),
            'index': index_list
        }
        self.set_redis_cache(redis_key, cache_data)

        # 2. 如果是熱門股票，也更新 MongoDB L2 快取
        hot_stocks = self.get_hot_stocks()
        if stock_symbol.upper() in hot_stocks:
            try:
                self.mongo_service.saveTable(stock_symbol.lower(), df)
                self.logger.info(f"Updated L2 cache for hot stock {stock_symbol}")
            except Exception as e:
                self.logger.error(f"Failed to update L2 cache for {stock_symbol}: {e}")

    def invalidate_stock_cache(self, stock_symbol: str):
        """失效特定股票的快取"""
        # 刪除 Redis L1 快取
        redis_key = self._generate_cache_key("stock", stock_symbol)
        self.delete_redis_cache(redis_key)

        # 也可以選擇從 MongoDB 刪除，但通常保留作為智慧快取
        self.logger.info(f"Invalidated cache for {stock_symbol}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """獲取完整快取統計"""
        stats = {
            'redis': {'status': 'disconnected'},
            'mongodb': {'status': 'disconnected'},
            'query_stats': {
                'total_queries': len(self.query_stats),
                'hot_stocks': len(self.get_hot_stocks())
            }
        }

        # Redis 統計
        if self.redis_client:
            try:
                info = self.redis_client.info()
                keys = self.redis_client.keys('stock:*')
                stats['redis'] = {
                    'status': 'connected',
                    'cached_stocks': len(keys),
                    'memory_used': info.get('used_memory_human', '0B'),
                    'hit_rate': info.get('keyspace_hits', 0) / max(info.get('keyspace_misses', 0) + info.get('keyspace_hits', 0), 1)
                }
            except Exception as e:
                stats['redis'] = {'status': 'error', 'message': str(e)}

        # MongoDB 統計
        try:
            db = self.mongo_service.mongodb
            collections = db.list_collection_names()
            stock_collections = [
                col for col in collections
                if not col.startswith('system.') and col not in ['ad_index']
            ]

            total_docs = sum(db[col].count_documents({}) for col in stock_collections)

            stats['mongodb'] = {
                'status': 'connected',
                'cached_stocks': len(stock_collections),
                'total_documents': total_docs,
                'last_update': self.last_mongo_update.isoformat()
            }
        except Exception as e:
            stats['mongodb'] = {'status': 'error', 'message': str(e)}

        return stats

    def clear_all_cache(self) -> bool:
        """清除所有快取"""
        redis_ok = True
        mongo_ok = True

        # 清除 Redis
        if self.redis_client:
            try:
                self.redis_client.flushdb()
                self.logger.info("Cleared Redis cache")
            except Exception as e:
                self.logger.error(f"Failed to clear Redis cache: {e}")
                redis_ok = False

        # 清除 MongoDB 快取集合
        try:
            db = self.mongo_service.mongodb
            collections = db.list_collection_names()
            stock_collections = [
                col for col in collections
                if not col.startswith('system.') and col not in ['ad_index']
            ]

            for collection in stock_collections:
                db.drop_collection(collection)

            self.logger.info(f"Cleared {len(stock_collections)} MongoDB cache collections")
        except Exception as e:
            self.logger.error(f"Failed to clear MongoDB cache: {e}")
            mongo_ok = False

        return redis_ok and mongo_ok

    def health_check(self) -> Dict[str, Any]:
        """快取服務健康檢查"""
        health = {
            'overall_status': 'healthy',
            'redis': {'status': 'unknown'},
            'mongodb': {'status': 'unknown'}
        }

        # Redis 健康檢查
        if self.redis_client:
            try:
                self.redis_client.ping()
                info = self.redis_client.info()
                health['redis'] = {
                    'status': 'healthy',
                    'version': info.get('redis_version', 'unknown'),
                    'memory_used': info.get('used_memory_human', '0B')
                }
            except Exception as e:
                health['redis'] = {'status': 'unhealthy', 'message': str(e)}
                health['overall_status'] = 'degraded'
        else:
            health['redis'] = {'status': 'disabled'}
            health['overall_status'] = 'degraded'

        # MongoDB 健康檢查
        try:
            db = self.mongo_service.mongodb
            db.command('ping')
            health['mongodb'] = {'status': 'healthy'}
        except Exception as e:
            health['mongodb'] = {'status': 'unhealthy', 'message': str(e)}
            health['overall_status'] = 'degraded'

        return health


# 保持向後相容的別名
CacheService = HybridCacheService

# 全域快取服務實例
_cache_service = None

def get_cache_service(mongo_service=None, sql_service=None, config_path='config.yml') -> HybridCacheService:
    """獲取混合快取服務實例"""
    global _cache_service
    if _cache_service is None and mongo_service and sql_service:
        _cache_service = HybridCacheService(mongo_service, sql_service, config_path)
    return _cache_service
