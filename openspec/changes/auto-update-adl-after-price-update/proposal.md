## Why

目前台股股價更新流程與 ADL 產出是分離的。`src/UpdateStockService.py` 會更新個股資料，`AD_index` 也已有獨立更新流程與 MySQL 落地，但真正的騰落指標 `ADL` 仍只在 `src/FilterService/StockReportHistory.py` 內以記憶體即時計算，導致更新完成後資料可能仍是舊的，且需要額外手動觸發相關流程。

## What Changes

- 在台股股價更新完成後，自動觸發 ADL 計算流程，不再依賴使用者額外手動執行。
- 以既有 `AD_index` 歷史資料為基礎，計算累積騰落指標 `ADL`，並寫入 MySQL 資料表。
- 明確定義更新失敗或缺少必要資料時的行為，避免股價更新流程因 ADL 寫入問題而無法完成。
- 為 `src/UpdateStockService.py`、`src/FilterService/StockReportHistory.py`、`src/SqlService.py` 與對應測試補齊可驗證的行為描述。

## Capabilities

### New Capabilities
- `adl-auto-persistence`: 在股價更新完成後自動重算並持久化 ADL 到 MySQL，讓後續讀取與分析可使用最新資料。

### Modified Capabilities

None.

## Impact

- Affected code:
  - `src/UpdateStockService.py`
  - `src/FilterService/StockReportHistory.py`
  - `src/ExternalService/TGetExternalData.py`
  - `src/SqlService.py`
  - `UnitTest/`
- Affected systems:
  - MySQL schema will gain or refresh an `adl` table for persisted indicator history.
  - 台股更新流程的完成階段將多一個 ADL 後處理步驟。
- Non-goals:
  - 不在此變更中重做 ADLs 比例指標的自動持久化。
  - 不改寫整體排程架構或重新設計所有技術指標的資料儲存模型。
