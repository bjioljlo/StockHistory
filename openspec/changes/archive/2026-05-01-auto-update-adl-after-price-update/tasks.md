## 1. Update Flow Integration

- [x] 1.1 定義台股股價更新流程的成功完成條件，確保背景 MySQL 寫入完成後才進入後處理。
- [x] 1.2 在 `src/UpdateStockService.py` 中串接自動 ADL 重算與持久化入口，並處理提早停止時不觸發的邏輯。

## 2. ADL Persistence

- [x] 2.1 實作從 `AD_index` 歷史資料重算完整 ADL 的 service/data-access 邏輯。
- [x] 2.2 將重算結果寫入 MySQL `adl` 資料表，並處理既有資料覆蓋與日期欄位格式。
- [x] 2.3 視需要調整既有 ADL 讀取路徑，讓後續分析能使用持久化後的資料而不破壞現有行為。

## 3. Validation

- [x] 3.1 在 `UnitTest/` 新增或更新測試，覆蓋自動觸發、ADL 計算結果、以及 ADL 寫入失敗不影響股價更新的情境。
- [x] 3.2 執行與更新流程相關的目標測試；若無法自動化覆蓋，補充最小必要的手動驗證步驟。
