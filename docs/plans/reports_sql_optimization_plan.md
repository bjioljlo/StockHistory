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
   - 儲存路徑：`yieldInfo/dividend_yield_YYYY_MM_DD.csv`
   - 資料結構：證券代號, 證券名稱, 本益比, 殖利率(%), 股價淨值比
   - 檔案數量：數千個日檔案
   - 檔案大小：每個約數MB

2. **月報數據 (monthRP/)**
   - 儲存路徑：`monthRP/monthly_report_YYYY_M.csv`
   - 資料結構：公司代號, 公司名稱, 當月營收, 上月營收, 去年當月營收, 當月累計營收, 去年累計營收, 備註等
   - 檔案數量：數百個月檔案
   - 檔案大小：每個約數MB

3. **季報數據 (seasonInfo/)**
   - 儲存路徑：`seasonInfo/YYYY-seasonX-*.csv`
   - 資料結構：公司名稱, 公司代號, 營業收入, 毛利率(%), 營業利益率(%), 稅前純益率(%), 稅後純益率(%)
   - 檔案數量：數百個季檔案
   - 檔案大小：每個約數MB

### 當前讀取方式
- 使用pandas直接從CSV檔案讀取
- 無索引優化
- 查詢效能低
- 記憶體使用量大

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
CREATE TABLE dividend_yield (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL COMMENT '股票代號',
    date DATE NOT NULL COMMENT '資料日期',
    pe_ratio DECIMAL(10,2) COMMENT '本益比',
    dividend_yield DECIMAL(5,2) COMMENT '殖利率(%)',
    pb_ratio DECIMAL(10,2) COMMENT '股價淨值比',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY unique_symbol_date (symbol, date),
    INDEX idx_symbol (symbol),
    INDEX idx_date (date),
    INDEX idx_symbol_date (symbol, date)
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
CREATE TABLE monthly_reports (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL COMMENT '股票代號',
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
    INDEX idx_symbol_period (symbol, report_year, report_month)
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
CREATE TABLE quarterly_reports (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL COMMENT '股票代號',
    report_year INT NOT NULL COMMENT '報表年份',
    report_season INT NOT NULL COMMENT '報表季別(1-4)',
    revenue BIGINT COMMENT '營業收入',
    gross_margin DECIMAL(5,2) COMMENT '毛利率(%)',
    operating_margin DECIMAL(5,2) COMMENT '營業利益率(%)',
    pre_tax_margin DECIMAL(5,2) COMMENT '稅前純益率(%)',
    net_margin DECIMAL(5,2) COMMENT '稅後純益率(%)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY unique_symbol_period (symbol, report_year, report_season),
    INDEX idx_symbol (symbol),
    INDEX idx_period (report_year, report_season),
    INDEX idx_symbol_period (symbol, report_year, report_season)
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

### 快取策略
1. **Redis快取**：針對熱門查詢結果進行快取
2. **應用層快取**：在應用層實現LRU快取
3. **資料庫快取**：利用MySQL Query Cache

## 實施計劃

### 階段一：規劃與準備 (1-2週)
1. **需求分析**
   - 分析現有查詢模式
   - 確定性能指標
   - 評估儲存需求

2. **系統設計**
   - 設計資料庫模式
   - 設計API介面
   - 設計測試案例

3. **環境準備**
   - 建立測試環境
   - 準備遷移工具
   - 準備監控工具

### 階段二：開發與測試 (3-4週)
1. **表格建立**
   - 建立新資料表格
   - 建立索引和分區
   - 設定資料庫權限

2. **資料遷移工具開發**
   - 開發CSV到資料庫遷移工具
   - 開發資料驗證工具
   - 開發效能測試工具

3. **API更新**
   - 更新SqlService類別
   - 更新資料讀取介面
   - 保持向後相容性

4. **單元測試**
   - 測試資料遷移功能
   - 測試查詢效能
   - 測試異常處理

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
```python
class ReportDataMigrator:
    def __init__(self, config):
        self.config = config
        self.db_connection = None

    def migrate_dividend_yield(self):
        """遷移股息殖利率資料"""
        # 讀取所有CSV檔案
        # 轉換資料格式
        # 批次插入資料庫
        # 驗證資料完整性

    def migrate_monthly_reports(self):
        """遷移月報資料"""
        # 類似處理邏輯

    def migrate_quarterly_reports(self):
        """遷移季報資料"""
        # 類似處理邏輯
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
