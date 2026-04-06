## 1. 前置準備作業

- [x] 1.1 建立程式碼風格規範與 linter 設定
- [x] 1.2 設定 pre-commit 檢查流程
- [x] 1.3 建立模組相依性分析工具
- [x] 1.4 補充現有功能的單元測試保護

## 2. Common 模組重構

- [x] 2.1 重構 ConfigService 統一設定管理
- [x] 2.2 實作統一的日誌記錄機制
- [x] 2.3 建立標準錯誤處理與例外類別
- [x] 2.4 重構 Tools 工具函式，消除重複程式碼
- [x] 2.5 重構快取服務與效能監控模組
- [x] 2.6 完成 Common 模組測試，確保覆蓋率 90%+

      ✅ PerformanceMonitor 100% 測試覆蓋率
      ✅ Tools.py 100% 測試覆蓋率
      ✅ Exceptions.py 88% 測試覆蓋率
      ✅ 修正向後相容問題，新增遺失的匯出函式
      ✅ 更新過時的測試案例

## 3. Model 層重構

- [x] 3.1 拆分過大的 Model 類別

      ✅ Model_pick.py 從 503 行 -> 455 行 (符合 < 500 行規範)
      ✅ 抽出 4 個獨立服務類別
      ✅ 完全向後相容，現有程式碼無需修改
      ✅ 所有單元測試可正常執行
- [x] 3.2 統一資料物件介面與型別定義

      ✅ 建立標準 IModel 介面 (5個核心方法)
      ✅ 更新 TModel 基底類別實作介面
      ✅ 維持完全向後相容
      ✅ 所有現有程式碼無需修改
      ✅ 未來所有 Model 類別將實作此標準介面
- [x] 3.3 消除 Model 與 Service 間的循環依賴

      ✅ 分析依賴關係，未發現循環匯入問題
      ✅ 目前依賴方向正確: Model → Service
      ✅ 沒有反向匯入 Service → Model
      ✅ 依賴圖乾淨，沒有循環依賴
- [x] 3.4 加入資料驗證機制

      ✅ 建立標準 ModelValidation 模組
      ✅ ModelValidationError 例外類別
      ✅ ModelValidator 通用驗證工具 (required, numeric_range, integer, float, positive, non_negative)
      ✅ @validate_parameters 裝飾器
      ✅ 已整合至 Model_pick
      ✅ 所有 Model 類別均可使用此標準驗證機制
- [x] 3.5 更新對應的單元測試

      ✅ 建立 ModelValidation 完整單元測試 (16個測試案例)
      ✅ 所有測試 100% 通過
      ✅ ModelValidation.py 達成 100% 測試覆蓋率
      ✅ 涵蓋所有驗證方法與裝飾器
      ✅ 測試正常與異常流程

## 4. Service 層重構

- [x] 4.1 重構 UpdateStockService 資料更新邏輯

      ✅ 拆分 640 行單一檔案為 4 個模組
      ✅ 建立 StockDataDownloader, StockDataSynchronizer, ADLUpdater
      ✅ 維持 100% 向後相容性，所有公開介面不變
      ✅ 單一職責原則，每個模組專注特定功能
      ✅ 最大檔案現為 477 行 (符合 < 500 行規範)
      ✅ 所有現有匯入路徑可正常運作
- [x] 4.2 重構 BackTestService 回測模組

      ✅ BackTestStock.py 從 521 行 -> 187 行 (符合 < 500 行規範)
      ✅ 採用 Facade 外觀模式，維持 100% 向後相容性
      ✅ 所有公開介面與方法簽名完全不變
      ✅ 單一職責原則，僅作為外部服務入口
      ✅ 所有現有匯入路徑可正常運作
      ✅ 遵循與 UpdateStockService 相同的成功重構模式
- [x] 4.3 重構 FilterService 篩選模組

      ✅ GetStockData.py 從 753 行 -> 132 行 (符合 < 500 行規範)
      ✅ 採用 Facade 外觀模式，維持 100% 向後相容性
      ✅ 所有公開介面與方法簽名完全不變
      ✅ 單一職責原則，僅作為外部服務入口
      ✅ 標準化 __init__.py 套件結構
      ✅ 遵循與 UpdateStockService / BackTestService 相同的重構模式
- [x] 4.4 重構 ExternalService 外部資料擷取

      ✅ TGetExternalData.py 從 1491 行 -> 246 行 (符合 < 500 行規範)
      ✅ 採用 Facade 外觀模式，維持 100% 向後相容性
      ✅ 所有公開介面與方法簽名完全不變
      ✅ 單一職責原則，僅作為外部服務入口
      ✅ 標準化 __init__.py 套件結構
      ✅ 完成整個 Service 層重構，四個主要服務全部採用一致架構
- [x] 4.5 建立服務介面與依賴注入

      ✅ 建立基礎 IService 介面 (4個核心生命週期方法)
      ✅ 建立 IUpdateService, IBackTestService, IFilterService 介面
      ✅ 實作 ServiceContainer 依賴注入容器
      ✅ 支援 Singleton/Transient/Factory 三種生命週期
      ✅ 建立標準的介面匯出模組
      ✅ 所有服務現在可以透過介面抽象依賴
- [x] 4.6 每個服務完成後執行整合測試

      ✅ 執行整合測試 8/8 全部通過
      ✅ 所有服務模組載入正常
      ✅ 快取服務、備份服務、SQL 服務整合正常運作
      ✅ 重構後服務與現有程式碼完全相容
      ✅ 沒有破壞性變更

## 5. Controller 與 View 重構

- [ ] 5.1 分離業務邏輯與 UI 控制邏輯
- [ ] 5.2 重構 MediatorController 訊息傳遞機制
- [ ] 5.3 消除 Controller 間的循環依賴
- [ ] 5.4 統一 UI 事件處理流程
- [ ] 5.5 進行完整 UI 功能測試

## 6. 最終清理與驗證

- [ ] 6.1 移除廢棄程式碼與註解
- [ ] 6.2 更新 API 文件與架構文件
- [ ] 6.3 執行完整測試套件
- [ ] 6.4 效能基準測試與比較
- [ ] 6.5 Docker 建置與部署驗證
- [ ] 6.6 完成重構報告