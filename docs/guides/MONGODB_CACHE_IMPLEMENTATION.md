# MongoDB 智慧快取層實現方案

## 📋 專案概述

StockHistory 系統已完成資料庫統一化遷移（從個別股票表格到統一的 `stock_daily_prices` 表格）。本方案定義 MongoDB 作為智慧快取層的具體實現方式。

## 🏗️ 整體架構

### 當前架構
```
使用者請求
    ↓
快取層：Memory → MongoDB → MySQL → Local File → Yahoo Finance
    ↓
資料回應
```

### MongoDB 定位
- **角色**：智慧快取層，專門處理熱門股票的快速存取
- **資料來源**：從 MySQL 統一表格同步熱門股票資料
- **快取策略**：基於查詢頻率動態決定快取內容

## 🎯 實現目標

1. **效能提升**：熱門股票讀取速度提升 2-5 倍
2. **智慧快取**：自動識別和快取熱門股票
3. **資源優化**：減少 MySQL 的查詢壓力
4. **向後相容**：保持現有 API 介面不變

## 📁 檔案結構

```
src/
├── MongoService.py              # MongoDB 連線和基本操作
├── SqlService.py                # MySQL 統一表格操作
├── UpdateStockService.py        # 資料更新和同步服務
├── ExternalService/
│   └── TGetExternalData.py      # 資料讀取優先順序
└── Common/
    ├── CacheService.py          # 新增：快取管理服務
    └── PerformanceMonitor.py    # 效能監控
```

## 🔧 具體實現步驟

### 步驟 1：建立快取管理服務

**新增檔案：`src/Common/CacheService.py`**

```python
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd

class CacheService:
    """MongoDB 快取管理服務"""

    def __init__(self, mongo_service, sql_service, cache_size: int = 100):
        self.mongo_service = mongo_service
        self.sql_service = sql_service
        self.cache_size = cache_size  # 快取的股票數量上限
        self.query_stats: Dict[str, int] = {}  # 股票查詢統計
        self.last_update = datetime.now()
        self.update_interval = timedelta(hours=1)  # 快取更新間隔
        self._lock = threading.Lock()

    def record_query(self, stock_symbol: str):
        """記錄股票查詢統計"""
        with self._lock:
            self.query_stats[stock_symbol] = self.query_stats.get(stock_symbol, 0) + 1

    def get_hot_stocks(self, limit: int = None) -> List[str]:
        """獲取熱門股票列表"""
        if limit is None:
            limit = self.cache_size

        with self._lock:
            # 按查詢次數排序，返回最熱門的股票
            sorted_stocks = sorted(
                self.query_stats.items(),
                key=lambda x: x[1],
                reverse=True
            )
            return [stock for stock, _ in sorted_stocks[:limit]]

    def should_update_cache(self) -> bool:
        """檢查是否需要更新快取"""
        return datetime.now() - self.last_update > self.update_interval

    def update_cache(self):
        """更新 MongoDB 快取"""
        if not self.should_update_cache():
            return

        print("Updating MongoDB cache for hot stocks...")
        hot_stocks = self.get_hot_stocks(self.cache_size)

        for stock_symbol in hot_stocks:
            try:
                # 從 MySQL 讀取資料
                df = self.sql_service.readStockDay(stock_symbol)
                if not df.empty:
                    # 同步到 MongoDB
                    self.mongo_service.saveTable(stock_symbol.lower(), df)
                    print(f"Cached {stock_symbol} to MongoDB")
            except Exception as e:
                print(f"Failed to cache {stock_symbol}: {e}")

        self.last_update = datetime.now()
        print(f"MongoDB cache updated for {len(hot_stocks)} hot stocks")

    def cleanup_cold_cache(self, days_threshold: int = 30):
        """清理冷門股票的快取"""
        print("Cleaning up cold cache entries...")

        try:
            # 獲取 MongoDB 中的所有集合
            db = self.mongo_service.mongodb
            collections = db.list_collection_names()

            # 篩選出股票集合（排除系統集合）
            stock_collections = [
                col for col in collections
                if not col.startswith('system.') and col not in ['ad_index']
            ]

            hot_stocks = set(self.get_hot_stocks(self.cache_size * 2))  # 保留更多熱門股票
            cold_stocks = []

            for collection in stock_collections:
                stock_symbol = collection.upper()
                if stock_symbol not in hot_stocks:
                    cold_stocks.append(collection)

            # 刪除冷門股票的集合
            for collection in cold_stocks:
                db.drop_collection(collection)
                print(f"Dropped cold cache collection: {collection}")

            print(f"Cleaned up {len(cold_stocks)} cold cache entries")

        except Exception as e:
            print(f"Error during cache cleanup: {e}")
```

### 步驟 2：修改主程式初始化

**修改檔案：`src/main_stock.py`**

```python
# 新增快取服務匯入
from src.Common.CacheService import CacheService

# 在服務初始化區塊中加入快取服務
cache_service = CacheService(
    mongo_service=mongo_service,
    sql_service=sql_service,
    cache_size=100  # 快取 100 支熱門股票
)

# 將快取服務注入到相關服務中
update_service = UpdateStockService(
    sql_service=sql_service,
    mongo_service=mongo_service,
    read_load_system=read_load_system,
    cache_service=cache_service  # 新增參數
)

external_data_factory = ExternalDataFactory(
    sql_service=sql_service,
    mongo_service=mongo_service,
    read_load_system=read_load_system,
    cache_service=cache_service  # 新增參數
)
```

### 步驟 3：修改資料讀取邏輯

**修改檔案：`src/ExternalService/TGetExternalData.py`**

```python
def get_stock_history(self, number: str, start=datetime.strptime("2005-1-1", "%Y-%m-%d")) -> pd.DataFrame:
    """取得股票歷史資料，加入快取統計"""

    # 記錄查詢統計
    if hasattr(self, '_cache_service') and self._cache_service:
        self._cache_service.record_query(number)

    # 保持現有的讀取邏輯
    # 1. Memory
    # 2. MongoDB
    # 3. MySQL
    # 4. Local File
    # 5. Yahoo Finance

    # ... 現有程式碼保持不變 ...

    # 在成功獲取資料後，檢查是否需要更新快取
    if not m_history.empty and hasattr(self, '_cache_service') and self._cache_service:
        # 非同步更新快取（避免阻塞主要讀取流程）
        threading.Thread(
            target=self._cache_service.update_cache,
            daemon=True
        ).start()

    return result
```

### 步驟 4：修改資料更新邏輯

**修改檔案：`src/UpdateStockService.py`**

```python
def _save_stock_data_to_db(self, data_queue: queue.Queue):
    """儲存資料到資料庫，加入快取更新"""

    while True:
        item = data_queue.get()
        if item is None:
            data_queue.task_done()
            break

        stock_name, df_result, fetch_start_date = item

        try:
            # 資料驗證
            if self._data_validator:
                is_valid, errors, cleaned_df = self._data_validator.validate_stock_data(
                    stock_name, df_result, source='yahoo'
                )
                if not is_valid:
                    print(f"Data validation failed for {stock_name}: {errors}")
                    df_result = cleaned_df
                else:
                    df_result = cleaned_df

            # 儲存到 MySQL
            is_initial_fetch = (fetch_start_date.year == 2005 and
                              fetch_start_date.month == 1 and
                              fetch_start_date.day == 1)

            with self._sql_service.server_flask.app_context():
                save_ok = False
                if is_initial_fetch:
                    save_ok = self._replace_stock_data(stock_name, df_result)
                else:
                    save_ok = self._upsert_stock_data(stock_name, df_result)

                if save_ok:
                    print("Saved " + stock_name + " to DB OK!")

                    # 更新 MongoDB 快取（如果是熱門股票）
                    if hasattr(self, '_cache_service') and self._cache_service:
                        hot_stocks = self._cache_service.get_hot_stocks()
                        if stock_name.upper().replace('.TW', '').replace('.US', '').replace('.HK', '') in hot_stocks:
                            try:
                                self._mongo_service.saveTable(stock_name.lower(), df_result)
                                print(f"Updated cache for hot stock: {stock_name}")
                            except Exception as e:
                                print(f"Failed to update cache for {stock_name}: {e}")
                else:
                    print(f"Failed to save {stock_name} to SQL DB.")

        except Exception as e:
            print(f"An unexpected error occurred while saving {stock_name}: {e}")
        finally:
            data_queue.task_done()
```

### 步驟 5：加入定期快取維護

**修改檔案：`src/ScheduleService.py`**

```python
def RunOtherSchedule(self, progress_callback=None):
    """執行其他排程任務，包括快取維護"""
    print("Update stocks other Info start!")

    # 現有的 ADL 更新邏輯
    self.__RunUpDateADL(progress_callback)

    # 新增：快取維護
    if hasattr(self, '_cache_service') and self._cache_service:
        print("Performing cache maintenance...")

        # 更新快取
        self._cache_service.update_cache()

        # 清理冷門快取（每週執行一次）
        import datetime
        if datetime.datetime.now().weekday() == 6:  # 星期日
            self._cache_service.cleanup_cold_cache()

        print("Cache maintenance completed!")

    print("Update stocks other Info end!")
```

## 🧪 測試和驗證

### 測試案例

1. **基本功能測試**
```python
# 測試快取服務初始化
cache_service = CacheService(mongo_service, sql_service, cache_size=50)

# 測試熱門股票識別
cache_service.record_query("2330")
cache_service.record_query("2454")
hot_stocks = cache_service.get_hot_stocks(10)
assert "2330" in hot_stocks
```

2. **效能測試**
```python
import time

# 測試有快取 vs 無快取的讀取速度
start_time = time.time()
data1 = get_stock_history("2330")  # 應該從 MongoDB 快取讀取
time_with_cache = time.time() - start_time

# 清除快取後測試
clear_mongo_cache("2330")
start_time = time.time()
data2 = get_stock_history("2330")  # 應該從 MySQL 讀取
time_without_cache = time.time() - start_time

print(f"With cache: {time_with_cache:.3f}s")
print(f"Without cache: {time_without_cache:.3f}s")
print(f"Speedup: {time_without_cache / time_with_cache:.1f}x")
```

### 效能指標

- **目標**：熱門股票讀取速度提升 2-5 倍
- **快取命中率**：> 80% 對於前 100 支熱門股票
- **快取更新頻率**：每小時自動更新
- **記憶體使用**：控制在合理範圍內

## 📊 監控和維護

### 監控指標

1. **快取效能**
   - 快取命中率
   - 平均讀取時間
   - 快取大小

2. **系統健康**
   - MongoDB 連線狀態
   - 快取同步狀態
   - 錯誤率

### 維護任務

1. **每日維護**
   - 更新熱門股票統計
   - 同步快取資料

2. **每週維護**
   - 清理冷門快取
   - 檢查快取一致性

3. **每月維護**
   - 效能評估和優化
   - 容量規劃

## 🚀 部署和上線

### 部署步驟

1. **程式碼部署**
   ```bash
   # 部署新版本程式碼
   git pull
   pip install -r requirements.txt
   ```

2. **資料庫準備**
   ```bash
   # 確保 MongoDB 正在運行
   sudo systemctl status mongod

   # 初始化快取服務
   python -c "from src.Common.CacheService import CacheService; print('Cache service ready')"
   ```

3. **服務重啟**
   ```bash
   # 重啟應用程式
   sudo systemctl restart stockhistory-app
   ```

### 灰度上線策略

1. **階段 1**：10% 使用者啟用新快取功能
2. **階段 2**：50% 使用者啟用，監控效能
3. **階段 3**：全量上線，持續監控

## 🎯 預期效益

### 效能提升
- **熱門股票查詢**：響應時間從 ~200ms 降至 ~50ms
- **系統吞吐量**：提升 30-50%
- **使用者體驗**：明顯感受到的更快響應

### 資源優化
- **MySQL 負載**：減少 40% 的重複查詢
- **快取效率**：智慧識別熱門股票，資源利用最大化
- **儲存成本**：MongoDB 只儲存熱門資料，節省空間

### 系統穩定性
- **容錯能力**：多層快取確保服務可用性
- **擴展性**：可以輕鬆調整快取大小和策略
- **維護性**：模組化設計，易於維護和更新

## 🔧 後續優化

### 階段 2 優化項目

1. **智慧預載**
   - 基於使用者行為預測快取需求
   - 週末預載下週熱門股票

2. **分散式快取**
   - Redis 作為 L1 快取
   - MongoDB 作為 L2 快取

3. **機器學習優化**
   - 使用 ML 預測股票熱度
   - 動態調整快取大小

---

## 📝 總結

此方案將 MongoDB 定位為智慧快取層，實現了：

- ✅ **效能大幅提升**：熱門股票讀取速度提升 2-5 倍
- ✅ **資源有效利用**：只快取真正需要的資料
- ✅ **架構清晰**：MySQL 負責權威儲存，MongoDB 負責快速存取
- ✅ **向後相容**：現有 API 介面完全不變
- ✅ **可擴展性**：可以輕鬆調整快取策略和大小

下一階段的 agent 可以根據此文檔進行具體的程式碼實現和測試。
