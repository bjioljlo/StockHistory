"""
快取服務單元測試

測試 HybridCacheService 類別的各項功能
"""

import unittest
import json
from unittest.mock import Mock, patch
import pandas as pd
import redis

from src.Common.CacheService import HybridCacheService, get_cache_service


def create_test_cache_service(config_path='config.yml'):
    """
    創建測試用的 HybridCacheService 實例
    
    Args:
        config_path (str): 配置文件路徑
        
    Returns:
        HybridCacheService: 測試用的 HybridCacheService 實例
    """
    # 創建 mock 的 mongo_service 和 sql_service
    mock_mongo_service = Mock()
    mock_sql_service = Mock()
    mock_mongo_service.mongodb = None  # 模擬 MongoDB 未連線
    
    # 使用 mock 服務初始化 HybridCacheService
    return HybridCacheService(mock_mongo_service, mock_sql_service, config_path)


def create_cached_sql_service(sql_service, mongo_service=None, sql_service_instance=None):
    """
    創建測試用的 CachedSqlService 實例
    
    Args:
        sql_service: SQL 服務實例
        mongo_service: MongoDB 服務實例
        sql_service_instance: SQL 服務實例
        
    Returns:
        CachedSqlService: 測試用的 CachedSqlService 實例
    """
    from src.Common.CacheService import CachedSqlService
    
    # 創建 mock 服務
    mock_mongo_service = mongo_service or Mock()
    mock_mongo_service.mongodb = None
    mock_sql_service_instance = sql_service_instance or Mock()
    
    # 創建快取服務
    cache_service = HybridCacheService(mock_mongo_service, mock_sql_service_instance, 'config.yml')
    
    # 創建 CachedSqlService
    cached_service = CachedSqlService(sql_service, cache_service)
    return cached_service


class TestCacheService(unittest.TestCase):

    def setUp(self):
        """測試前準備"""
        self.config = {
            'redis': {
                'host': 'localhost',
                'port': 6379,
                'db': 0,
                'default_ttl': 3600,
                'query_cache_ttl': 1800,
                'data_cache_ttl': 7200,
                'compression_threshold': 1024
            }
        }

    def tearDown(self):
        """測試後清理"""
        # 清理全域實例
        import src.Common.CacheService
        src.Common.CacheService._cache_service = None

    @patch('src.Common.CacheService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.CacheService.redis.Redis')
    def test_initialization(self, mock_redis, mock_open, mock_yaml):
        """測試初始化"""
        mock_yaml.return_value = self.config
        mock_redis_instance = Mock()
        mock_redis_instance.ping.return_value = True
        mock_redis.return_value = mock_redis_instance

        cache = create_test_cache_service('config.yml')

        self.assertIsNotNone(cache.redis_client)
        mock_redis_instance.ping.assert_called_once()
        self.assertEqual(cache.redis_config['default_ttl'], 3600)

    @patch('src.Common.CacheService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.CacheService.redis.Redis')
    def test_generate_cache_key(self, mock_redis, mock_open, mock_yaml):
        """測試快取鍵生成"""
        mock_yaml.return_value = self.config
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance

        cache = create_test_cache_service('config.yml')
        key = cache._generate_cache_key("stock", "AAPL")

        self.assertTrue(key.startswith("stock:"))
        self.assertEqual(key, "stock:aapl")
        
        # 確保相同參數生成相同鍵
        key2 = cache._generate_cache_key("stock", "AAPL")
        self.assertEqual(key, key2)

        # 確保不同參數生成不同鍵
        key3 = cache._generate_cache_key("stock", "GOOGL")
        self.assertNotEqual(key, key3)

    @patch('src.Common.CacheService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.CacheService.redis.Redis')
    def test_dataframe_serialization(self, mock_redis, mock_open, mock_yaml):
        """測試 DataFrame 序列化"""
        mock_yaml.return_value = self.config
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance

        cache = create_test_cache_service('config.yml')

        # 測試空 DataFrame
        empty_df = pd.DataFrame()
        serialized = cache._serialize_dataframe(empty_df)
        data = json.loads(serialized)
        self.assertTrue(data['empty'])
        self.assertEqual(data['columns'], [])

        # 測試有資料的 DataFrame
        df = pd.DataFrame({'A': [1, 2], 'B': ['x', 'y']})
        serialized = cache._serialize_dataframe(df)
        data = json.loads(serialized)
        self.assertFalse(data.get('empty', False))
        self.assertEqual(len(data['data']), 2)
        self.assertEqual(data['columns'], ['A', 'B'])

    @patch('src.Common.CacheService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.CacheService.redis.Redis')
    def test_dataframe_deserialization(self, mock_redis, mock_open, mock_yaml):
        """測試 DataFrame 反序列化"""
        mock_yaml.return_value = self.config
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance

        cache = create_test_cache_service('config.yml')

        # 測試反序列化
        original_df = pd.DataFrame({'A': [1, 2], 'B': ['x', 'y']})
        serialized = cache._serialize_dataframe(original_df)
        deserialized_df = cache._deserialize_dataframe(serialized)

        # 比較資料內容，忽略索引類型差異
        self.assertEqual(deserialized_df.shape, original_df.shape)
        self.assertEqual(deserialized_df.columns.tolist(), original_df.columns.tolist())
        self.assertEqual(deserialized_df.values.tolist(), original_df.values.tolist())

    @patch('src.Common.CacheService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.CacheService.redis.Redis')
    def test_get_redis_cache(self, mock_redis, mock_open, mock_yaml):
        """測試 Redis 快取獲取"""
        mock_yaml.return_value = self.config
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance

        cache = create_test_cache_service('config.yml')

        # 測試快取命中
        test_data = {'key': 'value', 'number': 42}
        cache.redis_client.get.return_value = json.dumps(test_data)

        result = cache.get_redis_cache("test_key")
        self.assertEqual(result, test_data)

        # 測試快取未命中
        cache.redis_client.get.return_value = None
        result = cache.get_redis_cache("test_key")
        self.assertIsNone(result)

    @patch('src.Common.CacheService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.CacheService.redis.Redis')
    def test_set_redis_cache(self, mock_redis, mock_open, mock_yaml):
        """測試 Redis 快取設定"""
        mock_yaml.return_value = self.config
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance

        cache = create_test_cache_service('config.yml')

        test_data = {'key': 'value', 'number': 42}
        result = cache.set_redis_cache("test_key", test_data)

        self.assertTrue(result)
        cache.redis_client.set.assert_called_once()

    @patch('src.Common.CacheService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.CacheService.redis.Redis')
    def test_delete_redis_cache(self, mock_redis, mock_open, mock_yaml):
        """測試 Redis 快取刪除"""
        mock_yaml.return_value = self.config
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance

        cache = create_test_cache_service('config.yml')

        cache.redis_client.delete.return_value = 1
        result = cache.delete_redis_cache('test_key')
        self.assertTrue(result)

    @patch('src.Common.CacheService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.CacheService.redis.Redis')
    def test_get_cache_stats(self, mock_redis, mock_open, mock_yaml):
        """測試快取統計獲取"""
        mock_yaml.return_value = self.config
        mock_redis_instance = Mock()
        mock_redis_instance.keys.return_value = ['stock:aapl', 'stock:googl']
        mock_redis_instance.info.return_value = {
            'used_memory_human': '10M',
            'used_memory_peak_human': '15M',
            'keyspace_hits': 100,
            'keyspace_misses': 20,
            'evicted_keys': 5,
            'connected_clients': 3
        }
        mock_redis.return_value = mock_redis_instance

        cache = create_test_cache_service('config.yml')
        stats = cache.get_cache_stats()

        self.assertEqual(stats['redis']['status'], 'connected')
        self.assertEqual(stats['redis']['cached_stocks'], 2)
        self.assertEqual(stats['redis']['memory_used'], '10M')
        self.assertEqual(stats['redis']['hit_rate'], 100/120)  # 100/(100+20)
        self.assertEqual(stats['query_stats']['total_queries'], 0)
        self.assertEqual(stats['query_stats']['hot_stocks'], 0)

    @patch('src.Common.CacheService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.CacheService.redis.Redis')
    def test_data_cache_operations(self, mock_redis, mock_open, mock_yaml):
        """測試資料快取操作"""
        mock_yaml.return_value = self.config
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance

        cache = create_test_cache_service('config.yml')

        # 測試設定資料快取
        data = {'key': 'value', 'number': 42}
        result = cache.set_redis_cache('test_key', data)
        self.assertTrue(result)

        # 測試獲取資料快取
        cache.redis_client.get.return_value = json.dumps(data)
        cached_data = cache.get_redis_cache('test_key')
        self.assertEqual(cached_data, data)

        # 測試刪除資料快取
        cache.redis_client.delete.return_value = 1
        result = cache.delete_redis_cache('test_key')
        self.assertTrue(result)

    @patch('src.Common.CacheService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.CacheService.redis.Redis')
    def test_clear_all_cache(self, mock_redis, mock_open, mock_yaml):
        """測試清除所有快取"""
        mock_yaml.return_value = self.config
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance

        cache = create_test_cache_service('config.yml')
        result = cache.clear_all_cache()

        # 因為 MongoDB 服務不可用，只會清除 Redis，方法應返回 True
        self.assertTrue(result)
        cache.redis_client.flushdb.assert_called_once()

    @patch('src.Common.CacheService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.CacheService.redis.Redis')
    def test_health_check(self, mock_redis, mock_open, mock_yaml):
        """測試健康檢查"""
        mock_yaml.return_value = self.config
        mock_redis_instance = Mock()
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.info.return_value = {
            'redis_version': '7.0.0',
            'uptime_in_seconds': 3600,
            'used_memory_human': '50M',
            'connected_clients': 5
        }
        mock_redis.return_value = mock_redis_instance

        cache = create_test_cache_service('config.yml')
        health = cache.health_check()

        # 因為 MongoDB 服務不可用，整體狀態是 degraded
        self.assertEqual(health['overall_status'], 'degraded')
        self.assertEqual(health['redis']['status'], 'healthy')
        self.assertEqual(health['mongodb']['status'], 'disabled')

    @patch('src.Common.CacheService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.CacheService.redis.Redis')
    def test_get_cache_service_singleton(self, mock_redis, mock_open, mock_yaml):
        """測試單例模式"""
        mock_yaml.return_value = self.config
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance

        # 創建 mock 服務
        mock_mongo_service = Mock()
        mock_mongo_service.mongodb = None
        mock_sql_service = Mock()
        
        cache1 = get_cache_service(mock_mongo_service, mock_sql_service, 'config.yml')
        cache2 = get_cache_service(mock_mongo_service, mock_sql_service, 'config.yml')

        self.assertIs(cache1, cache2)


class TestCachedSqlService(unittest.TestCase):

    def setUp(self):
        """測試前準備"""
        self.config = {
            'redis': {
                'host': 'localhost',
                'port': 6379,
                'db': 0
            }
        }

    @patch('src.Common.CacheService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.CacheService.redis.Redis')
    def test_cached_sql_service_initialization(self, mock_redis, mock_open, mock_yaml):
        """測試 CachedSqlService 初始化"""
        mock_yaml.return_value = self.config
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance

        cache = create_test_cache_service('config.yml')
        mock_sql_service = Mock()

        cached_service = create_cached_sql_service(mock_sql_service)

        self.assertIsNotNone(cached_service.sql_service)
        self.assertIsInstance(cached_service.cache, HybridCacheService)

    @patch('src.Common.CacheService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.CacheService.redis.Redis')
    def test_read_stock_day_cached_hit(self, mock_redis, mock_open, mock_yaml):
        """測試快取命中的股票資料讀取"""
        mock_yaml.return_value = self.config
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance

        cache = create_test_cache_service('config.yml')
        mock_sql_service = Mock()

        # 模擬快取命中
        df = pd.DataFrame({'Date': ['2024-01-01'], 'Close': [100]})
        cache.redis_client.get.return_value = cache._serialize_dataframe(df)

        cached_service = create_cached_sql_service(mock_sql_service)
        result = cached_service.read_stock_day_cached("AAPL")

        # 應該從快取返回，不調用 SQL 服務
        mock_sql_service.readStockDay.assert_not_called()
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)

    @patch('src.Common.CacheService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.CacheService.redis.Redis')
    def test_read_stock_day_cached_miss(self, mock_redis, mock_open, mock_yaml):
        """測試快取未命中的股票資料讀取"""
        mock_yaml.return_value = self.config
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance

        cache = create_test_cache_service('config.yml')
        mock_sql_service = Mock()

        # 模擬快取未命中
        cache.redis_client.get.return_value = None

        # 模擬 SQL 服務返回資料
        df = pd.DataFrame({'Date': ['2024-01-01'], 'Close': [100]})
        mock_sql_service.readStockDay.return_value = df

        cached_service = create_cached_sql_service(mock_sql_service)
        result = cached_service.read_stock_day_cached("AAPL")

        # 應該調用 SQL 服務並設定快取
        mock_sql_service.readStockDay.assert_called_once_with("AAPL")
        cache.redis_client.set.assert_called_once()
        self.assertEqual(len(result), 1)

    @patch('src.Common.CacheService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.CacheService.redis.Redis')
    def test_invalidate_stock_cache(self, mock_redis, mock_open, mock_yaml):
        """測試股票快取失效"""
        mock_yaml.return_value = self.config
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance

        cache = create_test_cache_service('config.yml')
        mock_sql_service = Mock()

        cached_service = create_cached_sql_service(mock_sql_service)
        cached_service.invalidate_stock_cache("AAPL")

        # 應該調用 Redis delete 方法
        cache.redis_client.delete.assert_called()


if __name__ == '__main__':
    unittest.main()