## 1. 核心實作

- [x] 1.1 修改 ExternalDataFactory 繼承 IGetExternalData 介面
- [x] 1.2 加入內部實例快取機制
- [x] 1.3 實作方法自動轉送機制 `__getattr__`
- [x] 1.4 覆寫常用的介面方法明確轉送

## 2. 驗證

- [x] 2.1 確保 `Get_instance()` 維持原來的行為
- [x] 2.2 執行單元測試確保沒有破壞現有功能
- [x] 2.3 驗證 ReportFactory 可以正常取得 get_stock_history 方法
- [x] 2.4 驗證所有其他依賴 ExternalDataFactory 的模組都可以正常運作

## 3. 整合測試

- [x] 3.1 啟動主程式確保沒有執行階段錯誤
- [x] 3.2 測試股票查詢與報表功能
- [x] 3.3 驗證所有介面方法都可以正常被呼叫
