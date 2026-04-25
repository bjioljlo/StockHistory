## Why

目前專案中 `get_stock_history` 方法存在 35 處呼叫、5 種不同實作，介面簽章不一致、參數類型不匹配，導致程式碼到處需要做類型轉換，隱藏許多 bug 風險，且重複查詢造成效能浪費。需要統一介面與實作，消除技術債。

## What Changes

- ✅ 統一所有 `get_stock_history` 實作的介面簽章
- ✅ 修正參數類型不匹配問題（str/int 不一致）
- ✅ 補齊 end_date 參數支援
- ✅ 在介面層加入快取機制
- ✅ 移除重複的轉接層與包裝
- ⚠️ **BREAKING**: 修正 `DailyDataProvider` 不符合 `IGetExternalData` 介面合約的問題

## Capabilities

### New Capabilities
- `stock-history-cache`: 股票歷史資料查詢快取機制
- `stock-history-batch`: 批次查詢多檔股票歷史資料

### Modified Capabilities
- `external-data-service`: 更新股票歷史查詢介面合約

## Impact

- 影響模組: `src/ExternalService/`, `src/FilterService/`, `src/BackTestService/`, `src/ScheduleService.py`
- 所有 35 處呼叫端不需要修改，向後相容
- 測試檔案需要對應更新 Mock 行為
- 不影響現有商業邏輯，僅重構底層實作