"""
快取服務單元測試

測試 CacheService 類別的各項功能
"""

import unittest
import time
import json
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime

from src.Common.CacheService import CacheService, get_cache_service, create_cached_sql_service


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

        cache = CacheService('config.yml')

        self.assertIsNotNone(cache.redis_client)
        mock_redis_instance.ping.assert_called_once()
        self.assertEqual(cache.cache_config['default_ttl'], 3600)

    @patch('src.Common.CacheService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.CacheService.redis.Redis')
    def test_initialization_redis_failure(self, mock_redis, mock_open, mock_yaml):
        """測試 Redis 連線失敗的初始化"""
        mock_yaml.return_value = self.config
        mock_redis_instance = Mock()
        mock_redis_instance.ping.side_effect = Exception("Connection failed")
        mock_redis.return_value = mock_redis_instance

        cache = CacheService('config.yml')

        self.assertIsNone(cache.redis_client)

    @patch('src.Common.CacheService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.CacheService.redis.Redis')
    def test_generate_cache_key(self, mock_redis, mock_open, mock_yaml):
        """測試快取鍵生成"""
        mock_yaml.return_value = self.config
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance

        cache = CacheService('config.yml')
        key = cache._generate_cache_key("SELECT * FROM users", {"id": 1})

        self.assertTrue(key.startswith("query:"))
        # 確保相同參數生成相同鍵
        key2 = cache._generate_cache_key("SELECT * FROM users", {"id": 1})
        self.assertEqual(key, key2)

        # 確保不同參數生成不同鍵
        key3 = cache._generate_cache_key("SELECT * FROM users", {"id": 2})
        self.assertNotEqual(key, key3)

    @patch('src.Common.CacheService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.CacheService.redis.Redis')
    def test_dataframe_serialization(self, mock_redis, mock_open, mock_yaml):
        """測試 DataFrame 序列化"""
        mock_yaml.return_value = self.config
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance

        cache = CacheService('config.yml')

        # 測試空 DataFrame
        empty_df = pd.DataFrame()
        serialized = cache._serialize_dataframe(empty_df)
        data = json.loads(serialized)
        self.assertTrue(data['empty'])

        # 測試有資料的 DataFrame
        df = pd.DataFrame({'A': [1, 2], 'B': ['x', 'y']})
        serialized = cache._serialize_dataframe(df)
        data = json.loads(serialized)
        self.assertFalse(data['empty'])
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

        cache = CacheService('config.yml')

        # 測試反序列化
        original_df = pd.DataFrame({'A': [1, 2], 'B': ['x', 'y']})
        serialized = cache._serialize_dataframe(original_df)
        deserialized_df = cache._deserialize_dataframe(serialized)

        pd.testing.assert_frame_equal(original_df, deserialized_df)

    @patch('src.Common.CacheService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.CacheService.redis.Redis')
    def test_get_cached_query(self, mock_redis, mock_open, mock_yaml):
        """測試查詢快取獲取"""
        mock_yaml.return_value = self.config
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance

        cache = CacheService('config.yml')

        # 測試快取命中
        df = pd.DataFrame({'A': [1, 2]})
        serialized = cache._serialize_dataframe(df)
        mock_redis_instance.get.return_value = serialized

        result = cache.get_cached_query("SELECT * FROM test")
        self.assertIsNotNone(result)
        pd.testing.assert_frame_equal(result, df)

        # 測試快取未命中
        mock_redis_instance.get.return_value = None
        result = cache.get_cached_query("SELECT * FROM test")
        self.assertIsNone(result)

    @patch('src.Common.CacheService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.CacheService.redis.Redis')
    def test_set_cached_query(self, mock_redis, mock_open, mock_yaml):
        """測試查詢快取設定"""
        mock_yaml.return_value = self.config
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance

        cache = CacheService('config.yml')

        df = pd.DataFrame({'A': [1, 2]})
        result = cache.set_cached_query("SELECT * FROM test", df)

        self.assertTrue(result)
        mock_redis_instance.set.assert_called_once()

    @patch('src.Common.CacheService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.CacheService.redis.Redis')
    def test_invalidate_query_cache(self, mock_redis, mock_open, mock_yaml):
        """測試查詢快取失效"""
        mock_yaml.return_value = self.config
        mock_redis_instance = Mock()
        mock_redis_instance.keys.return_value = ['query:key1', 'query:key2']
        mock_redis_instance.delete.return_value = 2
        mock_redis.return_value = mock_redis_instance

        cache = CacheService('config.yml')
        deleted_count = cache.invalidate_query_cache()

        self.assertEqual(deleted_count, 2)
        mock_redis_instance.keys.assert_called_with('query:*')
        mock_redis_instance.delete.assert_called_once_with('query:key1', 'query:key2')

    @patch('src.Common.CacheService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.CacheService.redis.Redis')
    def test_get_cache_stats(self, mock_redis, mock_open, mock_yaml):
        """測試快取統計獲取"""
        mock_yaml.return_value = self.config
        mock_redis_instance = Mock()
        mock_redis_instance.keys.return_value = ['query:key1', 'query:key2']
        mock_redis_instance.info.return_value = {
            'used_memory_human': '10M',
            'used_memory_peak_human': '15M',
            'keyspace_hits': 100,
            'keyspace_misses': 20,
            'evicted_keys': 5,
            'connected_clients': 3
        }
        mock_redis.return_value = mock_redis_instance

        cache = CacheService('config.yml')
        stats = cache.get_cache_stats()

        self.assertEqual(stats['status'], 'connected')
        self.assertEqual(stats['total_keys'], 2)
        self.assertEqual(stats['memory_used'], '10M')
        self.assertEqual(stats['hit_rate'], 100/120)  # 100/(100+20)
        self.assertEqual(stats['evictions'], 5)
        self.assertEqual(stats['connections'], 3)

    @patch('src.Common.CacheService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.CacheService.redis.Redis')
    def test_data_cache_operations(self, mock_redis, mock_open, mock_yaml):
        """測試資料快取操作"""
        mock_yaml.return_value = self.config
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance

        cache = CacheService('config.yml')

        # 測試設定資料快取
        data = {'key': 'value', 'number': 42}
        result = cache.set_data_cache('test_key', data)
        self.assertTrue(result)

        # 測試獲取資料快取
        mock_redis_instance.get.return_value = json.dumps(data)
        cached_data = cache.get_data_cache('test_key')
        self.assertEqual(cached_data, data)

        # 測試刪除資料快取
        mock_redis_instance.delete.return_value = 1
        result = cache.delete_data_cache('test_key')
        self.assertTrue(result)

    @patch('src.Common.CacheService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.CacheService.redis.Redis')
    def test_clear_all_cache(self, mock_redis, mock_open, mock_yaml):
        """測試清除所有快取"""
        mock_yaml.return_value = self.config
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance

        cache = CacheService('config.yml')
        result = cache.clear_all_cache()

        self.assertTrue(result)
        mock_redis_instance.flushdb.assert_called_once()

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

        cache = CacheService('config.yml')
        health = cache.health_check()

        self.assertEqual(health['status'], 'healthy')
        self.assertEqual(health['version'], '7.0.0')
        self.assertEqual(health['uptime_seconds'], 3600)
        self.assertEqual(health['connected_clients'], 5)

    @patch('src.Common.CacheService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.CacheService.redis.Redis')
    def test_health_check_failure(self, mock_redis, mock_open, mock_yaml):
        """測試健康檢查失敗"""
        mock_yaml.return_value = self.config
        mock_redis_instance = Mock()
        mock_redis_instance.ping.side_effect = Exception("Connection failed")
        mock_redis.return_value = mock_redis_instance

        cache = CacheService('config.yml')
        health = cache.health_check()

        self.assertEqual(health['status'], 'error')
        self.assertIn('Connection failed', health['message'])

    @patch('src.Common.CacheService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.CacheService.redis.Redis')
    def test_get_cache_service_singleton(self, mock_redis, mock_open, mock_yaml):
        """測試單例模式"""
        mock_yaml.return_value = self.config
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance

        cache1 = get_cache_service('config.yml')
        cache2 = get_cache_service('config.yml')

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

        cache = CacheService('config.yml')
        mock_sql_service = Mock()

        cached_service = create_cached_sql_service(mock_sql_service)

        self.assertIsNotNone(cached_service.sql_service)
        self.assertIs(cached_service.cache, cache)

    @patch('src.Common.CacheService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.CacheService.redis.Redis')
    def test_read_stock_day_cached_hit(self, mock_redis, mock_open, mock_yaml):
        """測試快取命中的股票資料讀取"""
        mock_yaml.return_value = self.config
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance

        cache = CacheService('config.yml')
        mock_sql_service = Mock()

        # 模擬快取命中
        cached_data = [{'date': '2024-01-01', 'price': 100}]
        cache.redis_client.get.return_value = json.dumps(cached_data)

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

        cache = CacheService('config.yml')
        mock_sql_service = Mock()

        # 模擬快取未命中
        cache.redis_client.get.return_value = None

        # 模擬 SQL 服務返回資料
        df = pd.DataFrame({'date': ['2024-01-01'], 'price': [100]})
        mock_sql_service.readStockDay.return_value = df

        cached_service = create_cached_sql_service(mock_sql_service)
        result = cached_service.read_stock_day_cached("AAPL")

        # 應該調用 SQL 服務並設定快取
        mock_sql_service.readStockDay.assert_called_once_with("AAPL")
        cache.redis_client.set.assert_called_once()
        pd.testing.assert_frame_equal(result, df)

    @patch('src.Common.CacheService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.CacheService.redis.Redis')
    def test_invalidate_stock_cache(self, mock_redis, mock_open, mock_yaml):
        """測試股票快取失效"""
        mock_yaml.return_value = self.config
        mock_redis_instance = Mock()
        mock_redis_instance.keys.side_effect = [
            ['stock_day:aapl'],  # 第一個模式
            ['dividend_yield:aapl'],  # 第二個模式
            []  # 第三個模式
        ]
        mock_redis.return_value = mock_redis_instance

        cache = CacheService('config.yml')
        mock_sql_service = Mock()

        cached_service = create_cached_sql_service(mock_sql_service)
        cached_service.invalidate_stock_cache("AAPL")

        # 應該調用 keys 3 次（每個模式一次）
        self.assertEqual(mock_redis_instance.keys.call_count, 3)
        # 應該調用 delete 2 次（前兩個模式有結果）
        self.assertEqual(mock_redis_instance.delete.call_count, 2)


if __name__ == '__main__':
    unittest.main()
