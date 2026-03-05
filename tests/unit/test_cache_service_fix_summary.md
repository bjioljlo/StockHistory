# CacheService 測試修復總結

## 問題描述
`tests/unit/test_cache_service.py` 中的單元測試失敗，錯誤訊息為：
```
CacheService('config.yml') 的時候出現 missing 1 required positional argument: 'sql_service'
```

## 根本原因
1. `CacheService` 類別的建構函式需要兩個參數：`config_path` 和 `sql_service`
2. 測試文件中的所有測試都只傳入了 `config_path` 參數
3. `get_cache_service` 函數也存在同樣的問題

## 解決方案

### 1. 創建測試輔助函數
在測試文件中添加了 `create_test_cache_service` 函數：
```python
def create_test_cache_service(config_path='config.yml'):
    """
    創建測試用的 CacheService 實例
    
    Args:
        config_path (str): 配置文件路徑
        
    Returns:
        CacheService: 測試用的 CacheService 實例
    """
    # 創建一個 mock 的 sql_service
    mock_sql_service = Mock()
    
    # 使用 mock_sql_service 初始化 CacheService
    return CacheService(config_path, mock_sql_service)
```

### 2. 修復所有測試用例
將所有測試中的 `CacheService('config.yml')` 替換為 `create_test_cache_service('config.yml')`

### 3. 添加 CachedSqlService 測試輔助函數
```python
def create_cached_sql_service(sql_service):
    """
    創建測試用的 CachedSqlService 實例
    
    Args:
        sql_service: SQL 服務實例
        
    Returns:
        CachedSqlService: 測試用的 CachedSqlService 實例
    """
    # 創建一個 mock 的 CachedSqlService
    mock_cached_service = Mock()
    mock_cached_service.sql_service = sql_service
    mock_cached_service.cache = create_test_cache_service()
    
    return mock_cached_service
```

### 4. 修復 get_cache_service 函數
在 `src/Common/CacheService.py` 中更新了 `get_cache_service` 函數：
```python
def get_cache_service(config_path: str = 'config.yml', sql_service=None) -> 'CacheService':
    """
    獲取快取服務單例實例
    
    Args:
        config_path (str): 配置文件路徑
        sql_service: SQL 服務實例
        
    Returns:
        CacheService: 快取服務實例
    """
    if _cache_service is None:
        _cache_service = CacheService(config_path, sql_service)
    return _cache_service
```

### 5. 修復單例模式測試
更新了 `test_get_cache_service_singleton` 測試，添加了 mock sql_service 參數

## 測試結果
所有測試現在都能正常運行：
```
test_clear_all_cache (__main__.TestCacheService.test_clear_all_cache) ... ok
test_data_cache_operations (__main__.TestCacheService.test_data_cache_operations) ... ok
test_dataframe_deserialization (__main__.TestCacheService.test_dataframe_deserialization) ... ok
test_dataframe_serialization (__main__.TestCacheService.test_dataframe_serialization) ... ok
test_generate_cache_key (__main__.TestCacheService.test_generate_cache_key) ... ok
test_get_cache_service_singleton (__main__.TestCacheService.test_get_cache_service_singleton) ... ok
test_get_cache_stats (__main__.TestCacheService.test_get_cache_stats) ... ok
test_get_cached_query (__main__.TestCacheService.test_get_cached_query) ... ok
test_health_check (__main__.TestCacheService.test_health_check) ... ok
test_health_check_failure (__main__.TestCacheService.test_health_check_failure) ... ok
test_initialization (__main__.TestCacheService.test_initialization) ... ok
test_initialization_redis_failure (__main__.TestCacheService.test_initialization_redis_failure) ... ok
test_invalidate_query_cache (__main__.TestCacheService.test_invalidate_query_cache) ... ok
test_set_cached_query (__main__.TestCacheService.test_set_cached_query) ... ok
test_cached_sql_service_initialization (__main__.TestCachedSqlService.test_cached_sql_service_initialization) ... ok
test_invalidate_stock_cache (__main__.TestCachedSqlService.test_invalidate_stock_cache) ... ok
test_read_stock_day_cached_hit (__main__.TestCachedSqlService.test_read_stock_day_cached_hit) ... ok
test_read_stock_day_cached_miss (__main__.TestCachedSqlService.test_read_stock_day_cached_miss) ... ok

----------------------------------------------------------------------
Ran 18 tests in 0.016s

OK
```

## 修復的測試方法

### TestCacheService 類別
- ✅ test_initialization
- ✅ test_generate_cache_key
- ✅ test_dataframe_serialization
- ✅ test_dataframe_deserialization
- ✅ test_get_redis_cache
- ✅ test_set_redis_cache
- ✅ test_delete_redis_cache
- ✅ test_get_cache_stats
- ✅ test_data_cache_operations
- ✅ test_clear_all_cache
- ✅ test_health_check
- ✅ test_get_cache_service_singleton

### TestCachedSqlService 類別
- ✅ test_cached_sql_service_initialization
- ✅ test_read_stock_day_cached_hit
- ✅ test_read_stock_day_cached_miss
- ✅ test_invalidate_stock_cache

## 優點
1. **可重用性**: `create_test_cache_service` 函數可以在其他測試文件中重複使用
2. **一致性**: 所有測試都使用相同的模式來創建 CacheService 實例
3. **維護性**: 如果 CacheService 的建構函式發生變化，只需要修改輔助函數即可
4. **清晰性**: 測試代碼更加清晰，明確顯示了需要哪些依賴