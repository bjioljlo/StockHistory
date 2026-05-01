## Why

在先前的 `project-refactoring-and-cleanup` 重構完成後，系統中保留了超過 40 處向後相容性程式碼，包含 Facade 外觀類別、匯入別名、已棄用函式等。這些相容性層現在已成為技術債，增加了程式碼複雜度、維護成本和潛在錯誤點。重構已完成超過 24 小時，所有功能都已驗證正常，現在是清理這些過渡性程式碼的適當時機。

## What Changes

- ✅ 移除所有標示為「向後相容」的別名和 Facade 類別
- ✅ 移除所有已棄用的模組包裝層
- ✅ 更新所有仍在使用舊介面的內部程式碼
- ✅ 移除相關的警告訊息和過時文件
- ⚠️ **BREAKING**: 舊的匯入路徑和類別名稱將不再有效
- ⚠️ **BREAKING**: 外部依賴舊介面的程式碼需要更新

## Capabilities

### New Capabilities
- (無) 此變更不新增任何功能，僅清理現有程式碼

### Modified Capabilities
- (無) 所有功能行為完全不變，僅移除相容性介面層

## Impact

**受影響模組**:
- `src/BackTestService/` - 5 處
- `src/Controller/` - 4 處
- `src/Model/` - 3 處
- `src/UpdateStockService/` - 2 處
- `src/ExternalService/` - 3 處
- `src/FilterService/` - 12 處
- `src/Common/` - 13 處

**風險評估**:
- 低風險: 所有相容性程式碼都是單純轉發，沒有業務邏輯
- 所有功能已經在新實作上經過完整測試
- 移除後程式碼庫將減少大約 1200 行過渡性程式碼