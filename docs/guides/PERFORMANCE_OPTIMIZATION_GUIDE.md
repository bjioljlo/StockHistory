# StockHistory 效能監控與優化使用指南

本文檔說明如何使用剛剛實現的效能監控與優化功能。

## 目錄

- [StockHistory 效能監控與優化使用指南](#stockhistory-效能監控與優化使用指南)
  - [目錄](#目錄)
  - [效能監控服務 (PerformanceMonitor)](#效能監控服務-performancemonitor)
    - [基本使用](#基本使用)
    - [進階使用](#進階使用)
  - [查詢優化服務 (QueryOptimizer)](#查詢優化服務-queryoptimizer)
    - [分析慢查詢](#分析慢查詢)
    - [分析資料表索引](#分析資料表索引)
    - [優化單個查詢](#優化單個查詢)
  - [資料壓縮服務 (DataCompressionService)](#資料壓縮服務-datacompressionservice)
    - [分析壓縮潛力](#分析壓縮潛力)
    - [壓縮舊資料](#壓縮舊資料)
    - [優化資料表儲存](#優化資料表儲存)
    - [壓縮維護任務](#壓縮維護任務)
  - [快取服務 (CacheService)](#快取服務-cacheservice)
    - [基本快取操作](#基本快取操作)
    - [查詢結果快取](#查詢結果快取)
    - [快取統計](#快取統計)
    - [使用 CachedSqlService](#使用-cachedsqlservice)
  - [讀寫分離服務 (ReadWriteSplitService)](#讀寫分離服務-readwritesplitservice)
    - [基本讀寫分離操作](#基本讀寫分離操作)
    - [叢集狀態監控](#叢集狀態監控)
    - [讀寫分離效益分析](#讀寫分離效益分析)
    - [模擬讀寫分離效果](#模擬讀寫分離效果)
    - [生成配置範本](#生成配置範本)
    - [遷移計劃](#遷移計劃)
  - [整合使用範例](#整合使用範例)
    - [完整的最佳化工作流程](#完整的最佳化工作流程)
  - [配置說明](#配置說明)
    - [config.yml 配置範例](#configyml-配置範例)
    - [環境變數](#環境變數)
  - [注意事項](#注意事項)
  - [故障排除](#故障排除)
    - [常見問題](#常見問題)

## 效能監控服務 (PerformanceMonitor)

### 基本使用

```python
from src.Common.PerformanceMonitor import get_performance_monitor

# 獲取效能監控實例
monitor = get_performance_monitor()

# 監控查詢效能
with monitor.monitor_query("mysql", "SELECT * FROM stocks WHERE date >= '2024-01-01'"):
    # 執行您的查詢邏輯
    df = sql_service.readStockDay("AAPL")

# 獲取效能報告
report = monitor.get_performance_report()
print(f"總查詢數: {report['query_performance']['total_queries']}")
print(f"慢查詢數: {report['query_performance']['slow_queries_count']}")
```

### 進階使用

```python
# 自定義監控裝飾器
@monitor.monitor_query("mongodb", "複雜的股票分析查詢")
def complex_stock_analysis():
    # 您的複雜查詢邏輯
    pass

# 手動觸發系統指標收集
monitor.collect_system_metrics()

# 匯出效能指標
monitor.export_metrics("performance_report.json")
```

## 查詢優化服務 (QueryOptimizer)

### 分析慢查詢

```python
from src.Common.QueryOptimizer import QueryOptimizer

optimizer = QueryOptimizer()

# 分析最近7天的慢查詢
slow_queries = optimizer.analyze_slow_queries(days=7)
for query in slow_queries:
    print(f"慢查詢: {query['sql_text']}")
    print(f"平均執行時間: {query['avg_time_sec']:.2f}秒")
    print(f"執行次數: {query['exec_count']}")
    print(f"優化建議: {query['optimization_suggestions']}")
```

### 分析資料表索引

```python
# 分析特定資料表的索引使用情況
index_analysis = optimizer.analyze_table_indexes("stocks")
print(f"資料表: {index_analysis['table_name']}")
print("索引資訊:")
for index_name, index_info in index_analysis['indexes'].items():
    print(f"  - {index_name}: {len(index_info['columns'])} 欄位")

print("優化建議:")
for suggestion in index_analysis['recommendations']:
    print(f"  - {suggestion}")
```

### 優化單個查詢

```python
# 優化特定查詢
sql_query = "SELECT * FROM stocks WHERE date >= '2024-01-01' ORDER BY volume DESC"
optimization_result = optimizer.optimize_query(sql_query)

print(f"原始查詢: {optimization_result['original_query']}")
print(f"效能評分: {optimization_result['analysis']['performance_score']}/100")
print("優化建議:")
for suggestion in optimization_result['recommendations']:
    print(f"  - {suggestion}")

if 'optimized_query' in optimization_result:
    print(f"優化後查詢: {optimization_result['optimized_query']}")
```

## 資料壓縮服務 (DataCompressionService)

### 分析壓縮潛力

```python
from src.Common.DataCompressionService import DataCompressionService

compressor = DataCompressionService()

# 分析資料表壓縮潛力
analysis = compressor.analyze_table_compression_potential("stocks")
print(f"資料表: {analysis['table_name']}")
print(f"總記錄數: {analysis['total_rows']}")
print(f"舊記錄數: {analysis['old_records']}")
print(f"資料大小: {analysis['data_size_mb']:.2f} MB")
print(f"預估壓縮後大小: {analysis['estimated_compressed_size_mb']:.2f} MB")
print(f"壓縮潛力: {analysis['compression_potential_mb']:.2f} MB")

print("壓縮建議:")
for suggestion in analysis['recommendations']:
    print(f"  - {suggestion}")
```

### 壓縮舊資料

```python
# 壓縮超過1年的舊資料
result = compressor.compress_old_data("stocks")
if result['status'] == 'success':
    print(f"成功壓縮 {result['compressed_records']} 條記錄")
    print(f"壓縮檔案: {result['archive_file']}")
else:
    print(f"壓縮失敗: {result['message']}")
```

### 優化資料表儲存

```python
# 優化資料表儲存空間
optimization_result = compressor.optimize_table_storage("stocks")
if optimization_result['status'] == 'success':
    print(f"{optimization_result['message']}")
    print(f"壓縮已應用: {optimization_result['compression_applied']}")
```

### 壓縮維護任務

```python
# 執行完整的壓縮維護任務
maintenance_result = compressor.run_compression_maintenance()
for task in maintenance_result['tasks']:
    print(f"任務: {task['task']}")
    print(f"狀態: {task['result']['status']}")
    if task['result']['status'] == 'success':
        print(f"結果: {task['result'].get('message', '完成')}")
```

## 快取服務 (CacheService)

### 基本快取操作

```python
from src.Common.CacheService import get_cache_service

cache = get_cache_service()

# 設定資料快取
stock_data = {"symbol": "AAPL", "price": 150.00, "volume": 1000000}
cache.set_data_cache("stock:AAPL", stock_data)

# 獲取資料快取
cached_data = cache.get_data_cache("stock:AAPL")
if cached_data:
    print(f"快取命中: {cached_data}")
else:
    print("快取未命中")

# 刪除快取
cache.delete_data_cache("stock:AAPL")
```

### 查詢結果快取

```python
# 快取查詢結果
query = "SELECT * FROM stocks WHERE symbol = ?"
params = ["AAPL"]
df = sql_service.readStockDay("AAPL")

# 設定查詢快取
cache.set_cached_query(query, df, params)

# 獲取快取的查詢結果
cached_df = cache.get_cached_query(query, params)
if cached_df is not None:
    print("使用快取的查詢結果")
else:
    print("重新執行查詢")
```

### 快取統計

```python
# 獲取快取統計資訊
stats = cache.get_cache_stats()
print(f"快取狀態: {stats['status']}")
print(f"總鍵數: {stats['total_keys']}")
print(f"記憶體使用: {stats['memory_used']}")
print(f"命中率: {stats['hit_rate']:.2%}")
```

### 使用 CachedSqlService

```python
from src.Common.CacheService import create_cached_sql_service

# 創建帶快取功能的 SQL 服務
original_sql_service = SqlService()
cached_sql_service = create_cached_sql_service(original_sql_service)

# 使用快取版本的方法
df = cached_sql_service.read_stock_day_cached("AAPL")  # 自動快取
df = cached_sql_service.read_dividend_yield_cached("AAPL")  # 自動快取

# 失效特定股票的快取
cached_sql_service.invalidate_stock_cache("AAPL")
```

## 讀寫分離服務 (ReadWriteSplitService)

### 基本讀寫分離操作

```python
from src.Common.ReadWriteSplitService import ReadWriteSplitService

# 注意：需要先在 config.yml 中配置 read_write_split 設定
rw_service = ReadWriteSplitService()

# 執行寫入操作（自動路由到主庫）
result = rw_service.execute_write(
    "INSERT INTO stocks (symbol, price, volume) VALUES (?, ?, ?)",
    ["AAPL", 150.00, 1000000]
)

# 執行讀取操作（自動路由到從庫）
results = rw_service.execute_read(
    "SELECT * FROM stocks WHERE symbol = ?",
    ["AAPL"]
)
```

### 叢集狀態監控

```python
# 獲取叢集狀態
cluster_status = rw_service.get_cluster_status()
print("寫入主節點狀態:")
print(f"  健康: {cluster_status['write_master']['healthy']}")

print("讀取副本狀態:")
for replica in cluster_status['read_replicas']:
    print(f"  副本 {replica['id']}: 健康={replica['healthy']}")
```

### 讀寫分離效益分析

```python
# 分析讀寫分離的效益
benefits = rw_service.analyze_read_write_split_benefits()
print(f"當前設定: {benefits['current_setup']}")
print("效能效益:")
print(f"  讀取操作提升: {benefits['performance_benefits']['estimated_improvement']['read_operations']}")
print(f"  寫入操作提升: {benefits['performance_benefits']['estimated_improvement']['write_operations']}")

print("建議:")
for recommendation in benefits['recommendations']:
    print(f"  - {recommendation}")
```

### 模擬讀寫分離效果

```python
# 模擬讀寫分離效果（假設80%為讀取操作）
simulation = rw_service.simulate_read_write_split(read_percentage=0.8)
print("模擬結果:")
print(f"  總操作數: {simulation['assumptions']['total_operations']}")
print(f"  讀取操作: {simulation['current_single_db']['read_operations']}")
print(f"  寫入操作: {simulation['current_single_db']['write_operations']}")
print(f"  預計讀取延遲減少: {simulation['estimated_improvements']['read_latency_reduction']}")
```

### 生成配置範本

```python
# 生成讀寫分離配置範本
config_template = rw_service.generate_read_write_split_config()
print("讀寫分離配置範本:")
print(yaml.dump(config_template, default_flow_style=False, allow_unicode=True))
```

### 遷移計劃

```python
# 獲取遷移計劃
migration_plan = rw_service.create_migration_plan()
print("遷移階段:")
for phase_name, phase_info in migration_plan.items():
    if phase_name.startswith('phase_'):
        print(f"  {phase_name}: {phase_info['duration']}")
        print(f"    任務: {', '.join(phase_info['tasks'])}")
```

## 整合使用範例

### 完整的最佳化工作流程

```python
from src.Common.PerformanceMonitor import get_performance_monitor
from src.Common.QueryOptimizer import QueryOptimizer
from src.Common.DataCompressionService import DataCompressionService
from src.Common.CacheService import get_cache_service, create_cached_sql_service
from src.Common.ReadWriteSplitService import ReadWriteSplitService

def optimize_stock_system():
    """完整的系統優化工作流程"""

    # 1. 初始化所有服務
    monitor = get_performance_monitor()
    optimizer = QueryOptimizer()
    compressor = DataCompressionService()
    cache = get_cache_service()

    # 2. 效能監控：監控關鍵查詢
    with monitor.monitor_query("mysql", "股票資料查詢"):
        # 您的查詢邏輯
        pass

    # 3. 查詢優化：分析和優化慢查詢
    slow_queries = optimizer.analyze_slow_queries()
    for query_info in slow_queries:
        optimization = optimizer.optimize_query(query_info['sql_text'])
        print(f"優化建議: {optimization['recommendations']}")

    # 4. 資料壓縮：壓縮舊資料
    compression_result = compressor.compress_old_data("stocks")
    print(f"壓縮結果: {compression_result['message']}")

    # 5. 快取整合：為 SQL 服務加入快取
    cached_sql_service = create_cached_sql_service(original_sql_service)

    # 6. 讀寫分離：分析可行性
    if ReadWriteSplitService:  # 檢查是否已配置
        rw_service = ReadWriteSplitService()
        analysis = rw_service.analyze_read_write_split_benefits()
        print(f"讀寫分離效益: {analysis['performance_benefits']}")

    # 7. 生成完整報告
    performance_report = monitor.get_performance_report()
    cache_stats = cache.get_cache_stats()
    compression_stats = compressor.get_compression_statistics()

    return {
        'performance': performance_report,
        'cache': cache_stats,
        'compression': compression_stats
    }

# 執行優化
results = optimize_stock_system()
print("優化完成!")
```

## 配置說明

### config.yml 配置範例

```yaml
# 效能監控配置
monitoring:
  enable_performance_monitoring: true
  slow_query_threshold: 2.0  # 秒

# Redis 配置（用於快取）
redis:
  host: localhost
  port: 6379
  db: 0
  default_ttl: 3600
  query_cache_ttl: 1800
  data_cache_ttl: 7200

# 讀寫分離配置（可選）
read_write_split:
  enabled: true
  write_master:
    type: mysql
    host: mysql-master
    port: 3306
    database: stock_data
    username: "${MYSQL_USER}"
    password: "${MYSQL_PASSWORD}"
  read_replicas:
    - type: mysql
      host: mysql-replica-1
      port: 3306
      database: stock_data
      username: "${MYSQL_USER}"
      password: "${MYSQL_PASSWORD}"
    - type: mysql
      host: mysql-replica-2
      port: 3306
      database: stock_data
      username: "${MYSQL_USER}"
      password: "${MYSQL_PASSWORD}"
```

### 環境變數

```bash
# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# 資料庫配置
MYSQL_USER=your_user
MYSQL_PASSWORD=your_password
MYSQL_HOST=mysql-master
MYSQL_DATABASE=stock_data

# 效能監控
ENABLE_PERFORMANCE_MONITORING=true
SLOW_QUERY_THRESHOLD=2.0
```

## 注意事項

1. **效能監控**: 預設不會自動啟動，需要在程式碼中手動監控關鍵操作
2. **Redis 依賴**: 快取服務需要 Redis 服務運行
3. **讀寫分離**: 需要額外的資料庫副本配置
4. **壓縮操作**: 壓縮是不可逆的，請先備份資料
5. **資源消耗**: 監控服務會消耗一些系統資源，生產環境請謹慎配置

## 故障排除

### 常見問題

1. **Redis 連線失敗**
   ```python
   # 檢查 Redis 服務狀態
   cache.health_check()
   ```

2. **讀寫分離連線失敗**
   ```python
   # 檢查叢集狀態
   rw_service.get_cluster_status()
   ```

3. **效能監控無資料**
   ```python
   # 手動收集指標
   monitor.collect_system_metrics()
   monitor.collect_database_metrics()
   ```

4. **壓縮失敗**
   ```python
   # 檢查檔案系統權限和空間
   compressor.get_compression_statistics()
   ```

通過這些功能的使用，您可以顯著提升 StockHistory 系統的效能、可靠性和可維護性。
