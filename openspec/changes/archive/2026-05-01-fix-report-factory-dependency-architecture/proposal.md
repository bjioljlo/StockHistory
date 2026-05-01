## Why

整個系統的依賴注入架構存在根本設計錯誤：`ExternalDataFactory` 被整個系統當成 `IGetExternalData` 介面實例在使用，但它本身只是工廠類別，沒有實作任何介面方法，導致執行階段隨機出現 `'ExternalDataFactory' object has no attribute 'xxx'` 錯誤。

這個問題已經造成數次來回除錯，現在需要一次性根本解決。

## What Changes

- ✅ 讓 `ExternalDataFactory` 直接實作 `IGetExternalData` 介面
- ✅ 內部自動管理真正實例的生命週期與快取
- ✅ 提供透明的方法轉送機制
- ✅ **完全向後相容**：所有既有程式碼不需要做任何修改
- ✅ 解決整個系統到處都把 Factory 當成實例注入的架構問題

## Capabilities

### New Capabilities

- `external-data-factory-proxy`: ExternalDataFactory 同時扮演工廠與實例代理的角色，對外提供完整的 IGetExternalData 介面

### Modified Capabilities

*(無)* - 這是純架構修復，所有功能行為維持不變

## Impact

- ✅ 受影響模組：`src/ExternalService/ExternalDataFactory.py`
- ✅ 對整個系統完全透明，不需要修改任何其他程式碼
- ✅ 解決所有「找不到方法」的執行階段錯誤
- ✅ 保留所有現有功能、API、行為完全不變