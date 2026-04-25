## Context

目前 `get_stock_history` 在專案中有 35 處呼叫、分散在 12 個檔案，存在 5 種不同的介面簽章實作。
介面合約 `IGetExternalData` 定義與底層實作 `DailyDataProvider` 完全不匹配，造成 LSP 原則違反。

## Goals / Non-Goals

**Goals:**
- 100% 向後相容所有現有呼叫端
- 統一所有實作的介面簽章
- 消除參數類型轉換的重複程式碼
- 加入記憶體快取減少重複資料庫查詢
- 保留所有現有商業邏輯不變

**Non-Goals:**
- 不會修改商業邏輯或資料來源
- 不會變更回傳的 DataFrame 格式
- 不會重構整個 ExternalService 架構
- 不會改變任何外部 API 呼叫行為

## Decisions

1. **統一介面簽章**: 所有實作統一使用 `get_stock_history(self, symbol: str, start_date: datetime | None = None, end_date: datetime | None = None) -> pd.DataFrame`
2. **類型處理**: 在底層實作內部處理 str 轉 int，不再要求呼叫端轉型
3. **快取層**: 在 `TGetExternalData` 轉接層加入 LRU 快取，快取大小 128 筆，TTL 10 分鐘
4. **漸進式重構**: 先修正介面問題，再最佳化效能，最後移除過時程式碼

## Risks / Trade-offs

- [風險] 測試檔案中的 Mock 行為可能失敗 → 補充整合測試確保行為一致
- [風險] 快取造成記憶體使用量增加 → 設定合理的快取大小與過期時間
- [取捨] 向後相容會暫時保留一些過時方法 → 標註 deprecated 標籤預留移除時間

## Migration Plan

1. 先修正 `DailyDataProvider` 介面簽章
2. 加入快取層
3. 驗證所有現有測試通過
4. 逐步移除呼叫端的類型轉換程式碼
5. 最後刪除重複的實作