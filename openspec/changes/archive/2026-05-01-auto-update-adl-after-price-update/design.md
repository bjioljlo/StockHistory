## Context

目前 `src/UpdateStockService.py` 的台股更新流程會把下載結果放入背景儲存執行緒，由 `_save_stock_data_to_db` 非同步寫入 MySQL。另一方面，`AD_index` 可透過 `src/ExternalService/TGetExternalData.py` 取得並寫入 MySQL，但 `ADL` 本身只在 `src/FilterService/StockReportHistory.py` 內以 `AD_index` 即時計算並快取在記憶體，沒有獨立落地資料表。

這代表系統缺少一個「股價資料更新完成後，產出最新 ADL 並寫入 MySQL」的明確收尾步驟。因為現有更新流程在背景寫入尚未完成前就印出完成訊息，若直接在下載迴圈尾端觸發 ADL，將可能使用到未完全寫入的資料。

## Goals / Non-Goals

**Goals:**
- 在既有 `UpdateStockService` 流程內加入自動 ADL 持久化，不新增平行架構。
- 將「更新完成」定義為台股資料佇列已寫入完成後，再執行 ADL 重算。
- 以現有 `AD_index` 為唯一來源重算完整 ADL，並寫入 MySQL `adl` 資料表。
- 保持股價更新與 ADL 失敗的錯誤邊界分離，避免後處理失敗回滾主流程結果。

**Non-Goals:**
- 不在本次變更中一併持久化 `ADLs` 比例指標。
- 不重新設計所有背景任務或 thread pool 行為。
- 不修改現有圖表/UI 呈現方式，除非讀取 ADL 資料需要最小必要調整。

## Decisions

### 1. 在台股更新流程的資料庫寫入完成點觸發 ADL 後處理

決策：將自動 ADL 重算掛在 `UpdateTaiwanStocksHandle` 對應流程內，且必須等到 stock data queue 已 `join`、背景儲存執行緒已完成後再觸發。

原因：
- 這是最接近「股價更新完成」語意的位置。
- 可避免在資料尚未全部落地時就開始後續計算。
- 不需要額外新增排程器或 controller 層協調。

替代方案：
- 在 UI/controller 層更新完成後再呼叫 ADL：會讓業務規則分散到 UI。
- 直接沿用既有手動 `RunUpdateADLNow`：無法滿足自動化需求。

### 2. 以完整 `AD_index` 歷史重算整張 `adl` 表

決策：每次自動後處理時，從 MySQL 讀取完整 `AD_index`，排序後重新計算 cumulative ADL，並整張覆蓋 `adl` 表。

原因：
- `ADL` 是 `AD_index` 的純衍生資料，全量重算規則簡單、容易驗證。
- 近一年至數年等級的日資料量不大，對這個桌面應用與 MySQL 使用情境成本可接受。
- 可避免增量更新時處理缺口、重跑、回補與基準值錯誤。

替代方案：
- 只追加最新一天 ADL：需依賴既有 `adl` 最後一筆與資料完整性，錯誤恢復較複雜。

### 3. 持久化邏輯以 service 層方法封裝，讀取端保留最小改動

決策：在 service/external-data 範圍新增或擴充 ADL 持久化方法，由 `UpdateStockService` 呼叫；現有 `ADL_Indicator` 如需讀取 MySQL，可做最小必要調整，但不在本次設計中強制重構整體指標架構。

原因：
- `UpdateStockService` 已是更新流程的組裝點。
- `SqlService` 已有 `saveTable` / `readStockDay` 能力，可重用現有 MySQL 存取模式。
- 可把變更範圍集中在更新與資料存取模組。

替代方案：
- 把持久化寫進 `ADL_Indicator`：會混合查詢/計算與更新職責。

## Risks / Trade-offs

- [背景儲存執行緒完成時機與目前訊息不一致] → 透過 queue 同步點與明確完成條件避免過早觸發 ADL。
- [全量重算會增加更新尾端時間] → ADL 僅使用日級資料，先採簡單可驗證方案；若後續有明顯效能問題，再評估增量化。
- [現有 `saveTable` 可能寫入 index 欄位格式與 `readStockDay` 假設不完全一致] → 在實作時明確整理 `Date` 欄位與索引格式，並補測試驗證。
- [ADL 後處理失敗造成使用者誤以為整體更新失敗] → 分開記錄主流程成功與 ADL 後處理失敗訊息。

## Migration Plan

1. 在程式碼中新增 ADL 持久化流程並接到台股更新完成點。
2. 首次部署後，下一次成功台股更新時自動產生或覆蓋 `adl` 表。
3. 若需回滾，可移除自動觸發與持久化邏輯；既有股價更新流程不依賴 `adl` 表存在。

## Open Questions

- 是否也需要在手動 `RunUpdateADLNow` 路徑中同步寫入 `adl`，以維持所有入口一致性？本 change 預設至少涵蓋台股股價更新後的自動流程。
