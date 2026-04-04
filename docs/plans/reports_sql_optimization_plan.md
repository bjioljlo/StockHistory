# 股票報告SQL儲存優化計劃

## 目錄
1. [簡介](#簡介)
2. [現狀分析](#現狀分析)
3. [問題識別](#問題識別)
4. [優化策略](#優化策略)
5. [實施計劃](#實施計劃)
6. [資料遷移](#資料遷移)
7. [效能評估](#效能評估)
8. [風險評估](#風險評估)
9. [測試計劃](#測試計劃)
10. [回滾計劃](#回滾計劃)
11. [相關文件](#相關文件)

## 簡介

本計劃旨在為股價以外的其他報告數據（股息殖利率、月報、季報等）實施類似於股價數據的SQL儲存優化。通過統一的數據庫模式設計，提升查詢效能、降低維護成本，並改善系統整體效能。

參考股價數據優化的成功經驗，本計劃將分散的CSV文件儲存模式轉換為統一的關聯式數據庫表格，並實施適當的索引和分區策略。

## 現狀分析

### 當前儲存模式
1. **股息殖利率數據 (yieldInfo/)**
   - ✅ **狀態**：需要優化
   - 儲存路徑：`yieldInfo/dividend_yield_YYYY_MM_DD.csv`
   - 資料結構：證券代號, 證券名稱, 本益比, 殖利率(%), 股價淨值比
   - 檔案數量：數千個日檔案（約2000+檔案）
   - 檔案大小：每個約數MB
   - 查詢方式：`TGetExternalData.get_allstock_yield()`

2. **月報數據 (monthRP/)**
   - ✅ **狀態**：需要優化
   - 儲存路徑：`monthRP/monthly_report_YYYY_M.csv`
   - 資料結構：公司代號, 公司名稱, 當月營收, 上月營收, 去年當月營收, 當月累計營收, 去年累計營收, 備註等（11欄位）
   - 檔案數量：數百個月檔案（約200+檔案）
   - 檔案大小：每個約數MB
   - 查詢方式：`TGetExternalData.get_allstock_monthly_report()`

3. **季報數據 (seasonInfo/)**
   - ✅ **狀態**：需要優化
   - 儲存路徑：`seasonInfo/YYYY-seasonX-*.csv`
   - 資料結構：公司名稱, 公司代號, 營業收入, 毛利率(%), 營業利益率(%), 稅前純益率(%), 稅後純益率(%)
   - 檔案數量：數百個季檔案（約300+檔案）
   - 檔案大小：每個約數MB
   - 查詢方式：`TGetExternalData.get_allstock_financial_statement()`

4. **股價數據**
   - ✅ **狀態**：已優化完成
   - 儲存方式：統一的 `stock_daily_prices` 表格
   - 包含完整的OHLCV數據和索引優化

### 當前讀取方式分析
- **數據獲取流程**：
  1. 檢查SQL資料庫是否存在資料
  2. 如果不存在，從CSV檔案讀取
  3. 如果CSV不存在，從網路爬取並儲存
  4. 將資料存入SQL資料庫以供下次使用

- **效能問題**：
  - 每次查詢都讀取整個CSV檔案（無索引）
  - 記憶體使用量大（載入整個檔案）
  - I/O瓶頸（頻繁的檔案系統操作）
  - 無法有效利用資料庫的查詢優化

- **維護問題**：
  - 分散儲存，難以確保資料完整性
  - 檔案損壞風險高
  - 備份和恢復複雜
  - 擴展性差

## 問題識別

### 效能問題
1. **查詢效能低**
   - 每次查詢需要讀取整個CSV檔案
   - 無索引支持，無法快速定位數據
   - 多檔案分散存儲，難以進行跨檔案查詢

2. **記憶體使用過高**
   - 大量CSV檔案同時載入記憶體
   - 重複載入相同數據
   - 無法有效利用快取機制

3. **I/O瓶頸**
   - 頻繁的檔案系統操作
   - 磁碟碎片化
   - 無法利用數據庫連接池

### 維護問題
1. **資料一致性**
   - 分散儲存，難以確保資料完整性
   - 檔案損壞風險高
   - 備份和恢復複雜

2. **擴展性限制**
   - 新增欄位需要修改所有檔案
   - 難以進行歷史資料分析
   - 無法有效支援新功能

3. **開發效率**
   - 每次開發都需要處理檔案I/O
   - 錯誤處理複雜
   - 測試困難

## 優化策略

### 統一數據庫模式設計

#### 1. 股息殖利率表格 (`dividend_yield`)
```sql
-- 股息殖利率日數據表
CREATE TABLE dividend_yield (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL COMMENT '股票代號',
    date DATE NOT NULL COMMENT '資料日期',
    company_name VARCHAR(100) COMMENT '公司名稱',
    pe_ratio DECIMAL(10,2) COMMENT '本益比',
    dividend_yield DECIMAL(5,2) COMMENT '殖利率(%)',
    pb_ratio DECIMAL(10,2) COMMENT '股價淨值比',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY unique_symbol_date (symbol, date),
    INDEX idx_symbol (symbol),
    INDEX idx_date (date),
    INDEX idx_symbol_date (symbol, date),
    INDEX idx_dividend_yield (dividend_yield),
    INDEX idx_pe_ratio (pe_ratio)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
PARTITION BY RANGE (YEAR(date)) (
    PARTITION p2020 VALUES LESS THAN (2021),
    PARTITION p2021 VALUES LESS THAN (2022),
    PARTITION p2022 VALUES LESS THAN (2023),
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);
```

#### 2. 月報表格 (`monthly_reports`)
```sql
-- 月營收報告表
CREATE TABLE monthly_reports (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL COMMENT '股票代號',
    company_name VARCHAR(100) COMMENT '公司名稱',
    report_year INT NOT NULL COMMENT '報表年份',
    report_month INT NOT NULL COMMENT '報表月份',
    revenue_current_month BIGINT COMMENT '當月營收',
    revenue_last_month BIGINT COMMENT '上月營收',
    revenue_last_year_same_month BIGINT COMMENT '去年當月營收',
    revenue_ytd BIGINT COMMENT '當月累計營收',
    revenue_last_year_ytd BIGINT COMMENT '去年累計營收',
    notes TEXT COMMENT '備註',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY unique_symbol_period (symbol, report_year, report_month),
    INDEX idx_symbol (symbol),
    INDEX idx_period (report_year, report_month),
    INDEX idx_symbol_period (symbol, report_year, report_month),
    INDEX idx_revenue_current_month (revenue_current_month),
    INDEX idx_revenue_ytd (revenue_ytd)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
PARTITION BY RANGE (report_year) (
    PARTITION p2020 VALUES LESS THAN (2021),
    PARTITION p2021 VALUES LESS THAN (2022),
    PARTITION p2022 VALUES LESS THAN (2023),
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);
```

#### 3. 季報表格 (`quarterly_reports`)
```sql
-- 季財務報告表 (整合 PLA, BS, CPL, SCF 四種類型)
CREATE TABLE quarterly_reports (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL COMMENT '股票代號',
    company_name VARCHAR(100) COMMENT '公司名稱',
    report_year INT NOT NULL COMMENT '報表年份',
    report_season INT NOT NULL COMMENT '報表季別(1-4)',
    report_type ENUM('PLA', 'BS', 'CPL', 'SCF') NOT NULL COMMENT '報表類型',
    -- PLA 損益表欄位
    revenue BIGINT COMMENT '營業收入',
    gross_margin DECIMAL(5,2) COMMENT '毛利率(%)',
    operating_margin DECIMAL(5,2) COMMENT '營業利益率(%)',
    pre_tax_margin DECIMAL(5,2) COMMENT '稅前純益率(%)',
    net_margin DECIMAL(5,2) COMMENT '稅後純益率(%)',
    -- BS 資產負債表欄位
    total_assets BIGINT COMMENT '總資產',
    total_liabilities BIGINT COMMENT '總負債',
    equity BIGINT COMMENT '股東權益',
    -- CPL 現金流量表欄位
    operating_cash_flow BIGINT COMMENT '營業現金流量',
    investing_cash_flow BIGINT COMMENT '投資現金流量',
    financing_cash_flow BIGINT COMMENT '融資現金流量',
    -- SCF 財務比率欄位 (如果需要)
    -- 其他共同欄位
    raw_data JSON COMMENT '原始數據存儲',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY unique_symbol_period_type (symbol, report_year, report_season, report_type),
    INDEX idx_symbol (symbol),
    INDEX idx_period (report_year, report_season),
    INDEX idx_type (report_type),
    INDEX idx_symbol_period (symbol, report_year, report_season),
    INDEX idx_revenue (revenue),
    INDEX idx_net_margin (net_margin)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
PARTITION BY RANGE (report_year) (
    PARTITION p2020 VALUES LESS THAN (2021),
    PARTITION p2021 VALUES LESS THAN (2022),
    PARTITION p2022 VALUES LESS THAN (2023),
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);
```

### 索引策略
1. **主鍵索引**：使用自增ID作為主鍵
2. **唯一索引**：確保資料不重複 (symbol + date/period)
3. **查詢索引**：針對常用查詢模式建立索引
4. **複合索引**：支援範圍查詢和排序

### 分區策略
1. **時間分區**：按年份進行分區
2. **優勢**：
   - 提升查詢效能
   - 便於資料維護
   - 支援分區刪除舊資料

### API介面設計

#### 1. SqlService 新增方法
```python
class SqlService:
    # 現有方法保持不變，新增以下方法

    def read_dividend_yield(self, symbol: str = None, start_date: str = None,
                           end_date: str = None, limit: int = 1000) -> pd.DataFrame:
        """
        從統一的dividend_yield表格讀取股息殖利率數據

        Args:
            symbol: 股票代號，為None時返回所有股票
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            limit: 返回記錄數量限制

        Returns:
            pd.DataFrame: 股息殖利率數據
        """
        pass

    def read_monthly_reports(self, symbol: str = None, start_year: int = None,
                           end_year: int = None, limit: int = 1000) -> pd.DataFrame:
        """
        從統一的monthly_reports表格讀取月報數據

        Args:
            symbol: 股票代號，為None時返回所有股票
            start_year: 開始年份
            end_year: 結束年份
            limit: 返回記錄數量限制

        Returns:
            pd.DataFrame: 月報數據
        """
        pass

    def read_quarterly_reports(self, symbol: str = None, report_type: str = None,
                             start_year: int = None, end_year: int = None,
                             limit: int = 1000) -> pd.DataFrame:
        """
        從統一的quarterly_reports表格讀取季報數據

        Args:
            symbol: 股票代號，為None時返回所有股票
            report_type: 報表類型 ('PLA', 'BS', 'CPL', 'SCF')
            start_year: 開始年份
            end_year: 結束年份
            limit: 返回記錄數量限制

        Returns:
            pd.DataFrame: 季報數據
        """
        pass

    def get_dividend_yield_stats(self, symbol: str = None, date: str = None) -> Dict[str, Any]:
        """
        獲取股息殖利率統計信息

        Args:
            symbol: 股票代號，為None時返回整體統計
            date: 指定日期，為None時返回最新數據

        Returns:
            Dict: 統計信息 (平均殖利率、最高、最低等)
        """
        pass

    def get_monthly_revenue_trend(self, symbol: str, years: int = 3) -> pd.DataFrame:
        """
        獲取月營收趨勢數據

        Args:
            symbol: 股票代號
            years: 分析年數

        Returns:
            pd.DataFrame: 營收趨勢數據 (年份, 月份, 營收, 增長率)
        """
        pass

    def get_quarterly_financial_summary(self, symbol: str, year: int = None) -> Dict[str, Any]:
        """
        獲取季財務報表摘要

        Args:
            symbol: 股票代號
            year: 指定年份，為None時返回最新年份

        Returns:
            Dict: 財務摘要 (收入、利潤、資產負債等)
        """
        pass
```

#### 2. TGetExternalData 更新方法
```python
class TGetExternalData:
    # 更新現有方法以使用新的統一表格

    def get_allstock_yield(self, start: datetime) -> pd.DataFrame:
        """
        獲取股息殖利率數據 - 優化版本
        優先從SQL表格讀取，沒有時從CSV讀取並遷移
        """
        # 1. 嘗試從SQL表格讀取
        df_sql = self._sql_service.read_dividend_yield(
            start_date=start.strftime('%Y-%m-%d'),
            end_date=start.strftime('%Y-%m-%d')
        )

        if not df_sql.empty:
            return df_sql

        # 2. SQL中沒有，嘗試從CSV讀取並遷移
        # 原有邏輯保持，用於向後相容
        # ...

        # 3. 讀取成功後遷移到SQL
        if not df_csv.empty:
            self._migrate_yield_data_to_sql(df_csv, start)

        return df_csv

    def get_allstock_monthly_report(self, start: datetime) -> pd.DataFrame:
        """
        獲取月報數據 - 優化版本
        優先從SQL表格讀取，沒有時從CSV讀取並遷移
        """
        # 類似於get_allstock_yield的邏輯
        pass

    def get_allstock_financial_statement(self, start: datetime, type: info.FS_type) -> pd.DataFrame:
        """
        獲取季報數據 - 優化版本
        優先從SQL表格讀取，沒有時從CSV讀取並遷移
        """
        # 類似邏輯
        pass

    def _migrate_yield_data_to_sql(self, df: pd.DataFrame, date: datetime):
        """將股息殖利率數據遷移到SQL"""
        migrator = ReportDataMigrator(self._config)
        # 單筆遷移邏輯
        pass

    def _migrate_monthly_data_to_sql(self, df: pd.DataFrame, year: int, month: int):
        """將月報數據遷移到SQL"""
        pass

    def _migrate_quarterly_data_to_sql(self, df: pd.DataFrame, year: int, season: int, report_type: str):
        """將季報數據遷移到SQL"""
        pass
```

### 測試案例設計

#### 1. 單元測試案例
```python
class TestSqlServiceReports:
    def test_read_dividend_yield_single_symbol(self):
        """測試單個股票的股息殖利率查詢"""
        service = SqlService()
        result = service.read_dividend_yield(symbol='2330', limit=10)

        assert not result.empty
        assert 'symbol' in result.columns
        assert 'dividend_yield' in result.columns
        assert all(result['symbol'] == '2330')

    def test_read_dividend_yield_date_range(self):
        """測試日期範圍查詢"""
        service = SqlService()
        result = service.read_dividend_yield(
            start_date='2024-01-01',
            end_date='2024-01-31'
        )

        assert not result.empty
        assert all(result['date'] >= pd.to_datetime('2024-01-01').date())
        assert all(result['date'] <= pd.to_datetime('2024-01-31').date())

    def test_read_monthly_reports_year_range(self):
        """測試月報年份範圍查詢"""
        service = SqlService()
        result = service.read_monthly_reports(
            symbol='2330',
            start_year=2023,
            end_year=2024
        )

        assert not result.empty
        assert all(result['report_year'] >= 2023)
        assert all(result['report_year'] <= 2024)

    def test_read_quarterly_reports_by_type(self):
        """測試按類型查詢季報"""
        service = SqlService()
        result = service.read_quarterly_reports(
            symbol='2330',
            report_type='PLA'
        )

        assert not result.empty
        assert all(result['report_type'] == 'PLA')

    def test_dividend_yield_stats(self):
        """測試股息殖利率統計"""
        service = SqlService()
        stats = service.get_dividend_yield_stats(symbol='2330')

        assert 'avg_yield' in stats
        assert 'max_yield' in stats
        assert 'min_yield' in stats
        assert stats['avg_yield'] >= 0

class TestReportDataMigrator:
    def test_migrate_dividend_yield_batch(self):
        """測試股息殖利率批量遷移"""
        migrator = ReportDataMigrator(config)
        result = migrator.migrate_dividend_yield(
            start_date='2024-01-01',
            end_date='2024-01-31'
        )

        assert result['files_processed'] > 0
        assert result['records_inserted'] > 0

    def test_validate_migration_no_duplicates(self):
        """測試遷移驗證 - 無重複資料"""
        migrator = ReportDataMigrator(config)
        validation = migrator.validate_migration('dividend_yield')

        assert validation['status'] == 'valid'
        assert validation['duplicates'] == 0

    def test_clean_dividend_yield_data(self):
        """測試股息殖利率數據清理"""
        migrator = ReportDataMigrator(config)

        # 模擬原始數據
        raw_data = pd.DataFrame({
            '證券代號': ['2330', '2454'],
            '證券名稱': ['台積電', '聯發科'],
            '本益比': ['15.5', '20.3'],
            '殖利率(%)': ['2.5', '3.1'],
            '股價淨值比': ['3.2', '4.1']
        })

        cleaned = migrator._clean_dividend_yield_data(raw_data, 'test_file.csv')

        assert 'symbol' in cleaned.columns
        assert 'company_name' in cleaned.columns
        assert 'pe_ratio' in cleaned.columns
        assert 'dividend_yield' in cleaned.columns
        assert 'pb_ratio' in cleaned.columns
        assert cleaned['symbol'].dtype == object
        assert pd.api.types.is_numeric_dtype(cleaned['pe_ratio'])
```

#### 2. 效能測試案例
```python
class TestReportPerformance:
    def test_query_performance_baseline(self):
        """效能基準測試"""
        service = SqlService()

        start_time = time.time()
        result = service.read_dividend_yield(limit=1000)
        query_time = time.time() - start_time

        assert query_time < 1.0  # 應小於1秒
        assert len(result) <= 1000

    def test_concurrent_queries(self):
        """並發查詢測試"""
        service = SqlService()
        symbols = ['2330', '2454', '2317', '2412', '2382']

        def query_symbol(symbol):
            return service.read_dividend_yield(symbol=symbol, limit=100)

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(query_symbol, symbol) for symbol in symbols]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        assert len(results) == 5
        assert all(not df.empty for df in results)

    def test_memory_usage_during_migration(self):
        """遷移期間記憶體使用測試"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        migrator = ReportDataMigrator(config)
        migrator.migrate_dividend_yield(start_date='2024-01-01', end_date='2024-01-31')

        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_after - memory_before

        assert memory_used < 500  # 記憶體使用應小於500MB
```

### 快取策略
1. **Redis快取**：針對熱門查詢結果進行快取
2. **應用層快取**：在應用層實現LRU快取
3. **資料庫快取**：利用MySQL Query Cache

## 實施計劃

### 階段一：規劃與準備 ✅ 已完成 (1-2週)
1. **需求分析** ✅
   - 分析現有查詢模式：發現股價數據已優化，股息殖利率、月報、季報仍使用CSV
   - 確定性能指標：查詢響應時間<100ms，記憶體使用<85%
   - 評估儲存需求：股息殖利率2000+檔案，月報200+檔案，季報300+檔案

2. **系統設計** ✅
   - 設計資料庫模式：統一的MySQL表格結構，包含索引和分區
   - 設計API介面：新增的SqlService方法和更新的TGetExternalData
   - 設計測試案例：單元測試、效能測試、整合測試案例

3. **環境準備** ✅
   - 建立測試環境：`test_migration_environment.py` 測試腳本
   - 準備遷移工具：`migrate_reports_data.py` 完整遷移工具
   - 準備監控工具：`migration_monitor.py` 效能監控腳本

### 階段二：開發與修復 ✅ 已完成 (2026/01/09)
1. **核心修復** ✅
   - 修復季報數據欄位映射邏輯
   - 修復PLA報表symbol/company_name欄位處理
   - 添加數據去重邏輯防止重複鍵錯誤
   - 擴大DECIMAL欄位範圍支持更大數值
   - 修復CPL欄位映射問題

2. **API更新** ✅
   - 更新SqlService查詢方法包含所有欄位
   - 修復read_quarterly_reports方法欄位選擇
   - 確保所有CPL欄位都能被正確查詢

3. **測試腳本整理** ✅
   - 移動測試文件到正確目錄結構
   - `test_sql_service_unit.py` → `tests/unit/`
   - `test_new_sql_methods.py` → `tests/integration/`

### 階段三：整合測試 (1-2週)
1. **功能測試**
   - 測試所有查詢場景
   - 測試資料完整性
   - 測試系統穩定性

2. **效能測試**
   - 對比新舊系統效能
   - 測試並發處理能力
   - 測試記憶體使用量

3. **相容性測試**
   - 確保與現有系統相容
   - 測試邊界條件
   - 測試錯誤處理

### 階段四：生產部署 (1週)
1. **生產環境部署**
   - 建立生產環境表格
   - 執行資料遷移
   - 驗證資料完整性

2. **系統切換**
   - 更新應用程式設定
   - 啟用新功能
   - 監控系統狀態

3. **驗證與優化**
   - 驗證生產環境功能
   - 監控效能指標
   - 優化配置參數

## 資料遷移

### 遷移策略
1. **增量遷移**：分批次遷移，避免系統負擔過重
2. **驗證機制**：每批遷移後進行資料驗證
3. **錯誤處理**：完善的錯誤處理和恢復機制

### 遷移工具設計

#### 資料遷移服務 (`ReportDataMigrator`)
```python
import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy import create_engine, text
import logging

class ReportDataMigrator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_engine = create_engine(config['database']['uri'])
        self.batch_size = config.get('migration', {}).get('batch_size', 1000)
        self.logger = logging.getLogger(__name__)

    def migrate_dividend_yield(self, start_date: str = None, end_date: str = None) -> Dict[str, int]:
        """遷移股息殖利率資料"""
        csv_dir = self.config['data']['yield_dir']
        total_processed = 0
        total_inserted = 0

        # 獲取所有CSV檔案
        csv_files = self._get_csv_files(csv_dir, 'dividend_yield', start_date, end_date)

        for csv_file in csv_files:
            try:
                # 讀取CSV檔案
                df = pd.read_csv(csv_file, encoding='utf-8')

                # 數據清理和轉換
                df_cleaned = self._clean_dividend_yield_data(df, csv_file)

                if not df_cleaned.empty:
                    # 批次插入資料庫
                    inserted = self._batch_insert('dividend_yield', df_cleaned)
                    total_inserted += inserted

                total_processed += 1
                self.logger.info(f"Processed {csv_file}: {len(df_cleaned)} records")

            except Exception as e:
                self.logger.error(f"Error processing {csv_file}: {e}")

        return {
            'files_processed': total_processed,
            'records_inserted': total_inserted
        }

    def migrate_monthly_reports(self, start_year: int = None, end_year: int = None) -> Dict[str, int]:
        """遷移月報資料"""
        csv_dir = self.config['data']['month_dir']
        total_processed = 0
        total_inserted = 0

        csv_files = self._get_csv_files(csv_dir, 'monthly_report', start_year, end_year)

        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file, encoding='utf-8')
                df_cleaned = self._clean_monthly_report_data(df, csv_file)

                if not df_cleaned.empty:
                    inserted = self._batch_insert('monthly_reports', df_cleaned)
                    total_inserted += inserted

                total_processed += 1
                self.logger.info(f"Processed {csv_file}: {len(df_cleaned)} records")

            except Exception as e:
                self.logger.error(f"Error processing {csv_file}: {e}")

        return {
            'files_processed': total_processed,
            'records_inserted': total_inserted
        }

    def migrate_quarterly_reports(self, start_year: int = None, end_year: int = None) -> Dict[str, int]:
        """遷移季報資料"""
        csv_dir = self.config['data']['season_dir']
        total_processed = 0
        total_inserted = 0

        # 處理不同類型的季報 (PLA, BS, CPL, SCF)
        report_types = ['PLA', 'BS', 'CPL', 'SCF']

        for report_type in report_types:
            csv_files = self._get_csv_files(csv_dir, f'season.*{report_type}', start_year, end_year)

            for csv_file in csv_files:
                try:
                    df = pd.read_csv(csv_file, encoding='utf-8')
                    df_cleaned = self._clean_quarterly_report_data(df, csv_file, report_type)

                    if not df_cleaned.empty:
                        inserted = self._batch_insert('quarterly_reports', df_cleaned)
                        total_inserted += inserted

                    total_processed += 1

                except Exception as e:
                    self.logger.error(f"Error processing {csv_file}: {e}")

        return {
            'files_processed': total_processed,
            'records_inserted': total_inserted
        }

    def _batch_insert(self, table_name: str, df: pd.DataFrame) -> int:
        """批次插入資料"""
        if df.empty:
            return 0

        try:
            # 使用pandas to_sql進行批量插入
            df.to_sql(
                name=table_name,
                con=self.db_engine,
                if_exists='append',
                index=False,
                method='multi',
                chunksize=self.batch_size
            )
            return len(df)
        except Exception as e:
            self.logger.error(f"Batch insert failed: {e}")
            return 0

    def validate_migration(self, table_name: str) -> Dict[str, Any]:
        """驗證遷移結果"""
        try:
            with self.db_engine.connect() as conn:
                # 檢查資料完整性
                result = conn.execute(text(f"SELECT COUNT(*) as total FROM {table_name}"))
                total_count = result.fetchone()[0]

                # 檢查重複資料
                result = conn.execute(text(f"""
                    SELECT symbol, date_or_period, COUNT(*) as count
                    FROM (
                        SELECT symbol,
                               CASE
                                   WHEN date IS NOT NULL THEN DATE_FORMAT(date, '%Y-%m-%d')
                                   ELSE CONCAT(report_year, '-', LPAD(report_month, 2, '0'))
                               END as date_or_period
                        FROM {table_name}
                    ) t
                    GROUP BY symbol, date_or_period
                    HAVING COUNT(*) > 1
                """))

                duplicates = result.fetchall()

                return {
                    'total_records': total_count,
                    'duplicates': len(duplicates),
                    'status': 'valid' if len(duplicates) == 0 else 'has_duplicates'
                }

        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            return {'error': str(e)}

    def _get_csv_files(self, directory: str, pattern: str, start_filter=None, end_filter=None) -> List[str]:
        """獲取符合條件的CSV檔案列表"""
        import glob

        if not os.path.exists(directory):
            return []

        # 使用glob模式匹配檔案
        if 'dividend_yield' in pattern:
            files = glob.glob(os.path.join(directory, 'dividend_yield_*.csv'))
        elif 'monthly_report' in pattern:
            files = glob.glob(os.path.join(directory, 'monthly_report_*.csv'))
        else:
            files = glob.glob(os.path.join(directory, f'*-{pattern}.csv'))

        # 應用日期/年份過濾
        if start_filter and end_filter:
            filtered_files = []
            for file in files:
                # 從檔案名提取日期資訊並過濾
                if self._file_matches_filter(file, start_filter, end_filter):
                    filtered_files.append(file)
            return sorted(filtered_files)

        return sorted(files)

    def _file_matches_filter(self, filepath: str, start_filter, end_filter) -> bool:
        """檢查檔案是否符合日期/年份過濾條件"""
        filename = os.path.basename(filepath)

        try:
            if 'dividend_yield' in filename:
                # dividend_yield_2023_01_01.csv
                parts = filename.replace('dividend_yield_', '').replace('.csv', '').split('_')
                file_date = f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
                return start_filter <= file_date <= end_filter
            elif 'monthly_report' in filename:
                # monthly_report_2023_01.csv
                parts = filename.replace('monthly_report_', '').replace('.csv', '').split('_')
                file_year = int(parts[0])
                return start_filter <= file_year <= end_filter
            else:
                # season files: 2023-season1-PLA.csv
                year_part = filename.split('-')[0]
                file_year = int(year_part)
                return start_filter <= file_year <= end_filter
        except:
            return False

    # 數據清理方法們
    def _clean_dividend_yield_data(self, df: pd.DataFrame, source_file: str) -> pd.DataFrame:
        """清理股息殖利率數據"""
        if df.empty:
            return df

        # 從檔案名提取日期
        filename = os.path.basename(source_file)
        date_str = filename.replace('dividend_yield_', '').replace('.csv', '')
        date_parts = date_str.split('_')
        file_date = f"{date_parts[0]}-{date_parts[1].zfill(2)}-{date_parts[2].zfill(2)}"

        # 清理和標準化欄位
        df_cleaned = df.copy()
        df_cleaned['date'] = pd.to_datetime(file_date).date()

        # 重新命名欄位以匹配資料庫
        column_mapping = {
            '證券代號': 'symbol',
            '證券名稱': 'company_name',
            '本益比': 'pe_ratio',
            '殖利率(%)': 'dividend_yield',
            '股價淨值比': 'pb_ratio'
        }

        df_cleaned = df_cleaned.rename(columns=column_mapping)

        # 數據類型轉換
        numeric_columns = ['pe_ratio', 'dividend_yield', 'pb_ratio']
        for col in numeric_columns:
            if col in df_cleaned.columns:
                df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors='coerce')

        # 移除無效數據
        df_cleaned = df_cleaned.dropna(subset=['symbol'])
        df_cleaned['symbol'] = df_cleaned['symbol'].astype(str).str.strip()

        return df_cleaned[['symbol', 'date', 'company_name', 'pe_ratio', 'dividend_yield', 'pb_ratio']]

    def _clean_monthly_report_data(self, df: pd.DataFrame, source_file: str) -> pd.DataFrame:
        """清理月報數據"""
        if df.empty:
            return df

        # 從檔案名提取年月
        filename = os.path.basename(source_file)
        date_str = filename.replace('monthly_report_', '').replace('.csv', '')
        year, month = map(int, date_str.split('_'))

        df_cleaned = df.copy()
        df_cleaned['report_year'] = year
        df_cleaned['report_month'] = month

        # 重新命名欄位
        column_mapping = {
            '公司代號': 'symbol',
            '公司名稱': 'company_name',
            '當月營收': 'revenue_current_month',
            '上月營收': 'revenue_last_month',
            '去年當月營收': 'revenue_last_year_same_month',
            '當月累計營收': 'revenue_ytd',
            '去年累計營收': 'revenue_last_year_ytd',
            '備註': 'notes'
        }

        df_cleaned = df_cleaned.rename(columns=column_mapping)

        # 數據類型轉換
        numeric_columns = ['revenue_current_month', 'revenue_last_month',
                          'revenue_last_year_same_month', 'revenue_ytd', 'revenue_last_year_ytd']
        for col in numeric_columns:
            if col in df_cleaned.columns:
                df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors='coerce')

        df_cleaned = df_cleaned.dropna(subset=['symbol'])
        df_cleaned['symbol'] = df_cleaned['symbol'].astype(str).str.strip()

        return df_cleaned[['symbol', 'company_name', 'report_year', 'report_month',
                          'revenue_current_month', 'revenue_last_month',
                          'revenue_last_year_same_month', 'revenue_ytd',
                          'revenue_last_year_ytd', 'notes']]

    def _clean_quarterly_report_data(self, df: pd.DataFrame, source_file: str, report_type: str) -> pd.DataFrame:
        """清理季報數據"""
        if df.empty:
            return df

        # 從檔案名提取年季
        filename = os.path.basename(source_file)
        # 格式: 2023-season1-PLA.csv
        parts = filename.replace('.csv', '').split('-')
        year = int(parts[0])
        season = int(parts[1].replace('season', ''))

        df_cleaned = df.copy()
        df_cleaned['report_year'] = year
        df_cleaned['report_season'] = season
        df_cleaned['report_type'] = report_type

        # 重新命名欄位 (根據不同報表類型)
        base_mapping = {
            '公司代號': 'symbol',
            '公司名稱': 'company_name'
        }

        if report_type == 'PLA':
            # 損益表欄位
            pla_mapping = {
                '營業收入': 'revenue',
                '毛利率(%)': 'gross_margin',
                '營業利益率(%)': 'operating_margin',
                '稅前純益率(%)': 'pre_tax_margin',
                '稅後純益率(%)': 'net_margin'
            }
            base_mapping.update(pla_mapping)
        elif report_type == 'BS':
            # 資產負債表欄位
            bs_mapping = {
                '總資產': 'total_assets',
                '總負債': 'total_liabilities',
                '股東權益': 'equity'
            }
            base_mapping.update(bs_mapping)
        elif report_type == 'CPL':
            # 現金流量表欄位
            cpl_mapping = {
                '營業活動之淨現金流入（流出）': 'operating_cash_flow',
                '投資活動之淨現金流入（流出）': 'investing_cash_flow',
                '籌資活動之淨現金流入（流出）': 'financing_cash_flow'
            }
            base_mapping.update(cpl_mapping)

        df_cleaned = df_cleaned.rename(columns=base_mapping)

        # 數據類型轉換
        numeric_columns = [col for col in df_cleaned.columns if col not in ['symbol', 'company_name', 'report_type']]
        for col in numeric_columns:
            if col in df_cleaned.columns:
                df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors='coerce')

        df_cleaned = df_cleaned.dropna(subset=['symbol'])
        df_cleaned['symbol'] = df_cleaned['symbol'].astype(str).str.strip()

        # 存儲原始數據作為JSON
        df_cleaned['raw_data'] = df.to_json(orient='records', force_ascii=False)

        return df_cleaned
```

### 資料驗證
1. **數量驗證**：確保遷移後資料筆數一致
2. **內容驗證**：抽樣檢查資料內容正確性
3. **關聯驗證**：確保資料間關聯正確

## 效能評估

### 效能指標
1. **查詢效能**
   - 單筆查詢響應時間 < 100ms
   - 批量查詢響應時間 < 1s
   - 複雜查詢響應時間 < 5s

2. **系統資源**
   - CPU使用率 < 70%
   - 記憶體使用率 < 80%
   - 磁碟I/O < 80%

3. **並發處理**
   - 支持100個並發查詢
   - 支持10個批量操作

### 效能測試場景
1. **單筆查詢測試**
2. **範圍查詢測試**
3. **聚合查詢測試**
4. **並發壓力測試**

## 風險評估

### 技術風險
1. **資料遷移風險**
   - 資料損壞或丟失
   - 遷移過程異常中斷
   - 資料格式不一致

2. **效能風險**
   - 新系統效能不如預期
   - 資料庫負載過高
   - 記憶體使用過量

3. **相容性風險**
   - 與現有系統不相容
   - API介面變更影響其他模組
   - 第三方依賴問題

### 業務風險
1. **業務中斷**
   - 系統不可用時間過長
   - 資料查詢異常
   - 功能無法正常使用

2. **資料風險**
   - 歷史資料無法查詢
   - 資料精確性問題
   - 資料安全問題

### 風險緩解措施
1. **技術措施**
   - 完善的備份策略
   - 詳細的測試計劃
   - 漸進式部署方案

2. **業務措施**
   - 業務高峰期以外部署
   - 完善的溝通計劃
   - 緊急回滾方案

## 測試計劃

### 單元測試
1. **資料遷移測試**
   - 測試單個檔案遷移
   - 測試批量檔案遷移
   - 測試異常處理

2. **API測試**
   - 測試所有查詢介面
   - 測試錯誤處理
   - 測試效能指標

### 整合測試
1. **功能測試**
   - 測試完整業務流程
   - 測試系統間互動
   - 測試邊界條件

2. **效能測試**
   - 負載測試
   - 壓力測試
   - 耐久性測試

### 使用者接受測試
1. **業務驗收**
   - 驗證業務需求滿足度
   - 測試使用者體驗
   - 收集使用者回饋

## 回滾計劃

### 回滾策略
1. **資料回滾**
   - 保留原CSV檔案備份
   - 準備資料回滾腳本
   - 確保資料一致性

2. **程式回滾**
   - 保留舊版程式碼
   - 準備快速回滾腳本
   - 測試回滾功能

### 回滾步驟
1. **停止新系統**
2. **恢復舊程式碼**
3. **恢復舊資料檔案**
4. **驗證系統功能**
5. **通知相關人員**

### 回滾時間評估
- **程式回滾**：30分鐘
- **資料回滾**：2-4小時
- **完整回滾**：4-6小時

## 相關文件

1. [資料庫優化計劃](database_optimization_plan.py) - 股價優化參考
2. [專案開發指南](DEVELOPMENT_GUIDE.md) - 開發規範
3. [專案脈絡說明](PROJECT_CONTEXT.md) - 系統架構
4. [效能優化指南](PERFORMANCE_OPTIMIZATION_GUIDE.md) - 效能調優

## 結論

本計劃通過統一的資料庫儲存模式，將分散的CSV檔案整合到關聯式資料庫中，預期能夠：

1. **提升查詢效能**：索引和分區優化
2. **降低維護成本**：統一管理，易於維護
3. **改善系統穩定性**：減少檔案操作，降低錯誤率
4. **增強擴展性**：支援新功能開發和資料分析

實施過程將遵循漸進式部署原則，確保系統穩定性和業務連續性。所有變更都將經過充分測試，並準備完整的回滾方案。

---

**文件版本**：1.0
**撰寫日期**：2026/01/04
**審核狀態**：待審核
**撰寫日期**：2026/01/04
