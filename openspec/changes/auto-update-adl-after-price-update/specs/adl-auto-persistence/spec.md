## ADDED Requirements

### Requirement: Stock update completion SHALL refresh persisted ADL data
當台股股價更新流程完成且資料已成功寫入 MySQL 後，系統 SHALL 自動觸發 ADL 重算與持久化流程，無需使用者另外手動執行 ADL 更新。

#### Scenario: Auto-refresh runs after Taiwan stock update
- **WHEN** `UpdateTaiwanStocksHandle` 完成台股資料更新且背景資料庫寫入工作已結束
- **THEN** 系統會自動開始 ADL 重算流程
- **THEN** 不需要額外呼叫手動 ADL 更新入口也能得到最新 ADL 資料

#### Scenario: Skip auto-refresh when stock update stops early
- **WHEN** 台股更新流程因 `isUpdating` 被中止或因必要資料缺失而未完成
- **THEN** 系統 MUST NOT 將這次更新視為可觸發 ADL 持久化的成功完成事件

### Requirement: System SHALL persist calculated ADL history to MySQL
系統 SHALL 依據最新的 `AD_index` 歷史資料計算累積 ADL，並將可供後續查詢的完整 ADL 歷史寫入 MySQL。

#### Scenario: Persist full ADL history
- **WHEN** ADL 自動重算流程開始
- **THEN** 系統會讀取可用的 `AD_index` 歷史資料
- **THEN** 依日期排序後以 `(上漲 - 下跌)` 的累加結果計算完整 ADL
- **THEN** 將結果寫入 MySQL 的 `adl` 資料表

#### Scenario: Replace stale ADL history with recalculated result
- **WHEN** MySQL 已存在較舊的 `adl` 資料表
- **THEN** 系統會以本次重算結果覆蓋舊資料
- **THEN** 後續讀取到的 ADL 內容必須反映最新 `AD_index` 歷史

### Requirement: ADL persistence failures SHALL NOT invalidate stock updates
若 ADL 計算或 MySQL 寫入失敗，系統 MUST 保留已完成的股價更新結果，並以可診斷的方式記錄錯誤。

#### Scenario: ADL write failure after successful stock update
- **WHEN** 台股股價資料已成功寫入 MySQL，但 ADL 計算或 `adl` 資料表寫入失敗
- **THEN** 已完成的股價更新資料仍須保留
- **THEN** 系統必須輸出錯誤訊息以便後續診斷
