## 1. 準備與驗證

- [ ] 1.1 執行完整測試套件確保基準狀態正常
- [ ] 1.2 掃描整個程式碼庫建立完整的相容性程式碼清單
- [ ] 1.3 建立舊介面與新介面的對照表

## 2. Common 模組清理

- [x] 2.1 移除 Common/CacheService.py 中的 CacheService 別名 ✅
- [x] 2.2 移除 Common/ConfigService.py 中的舊相容函式 ✅
- [x] 2.3 移除 Common/PerformanceMonitor.py 中的舊相容函式 ✅
- [x] 2.4 清理 Common/Tools.py 已棄用的模組包裝 ✅
- [x] 2.5 執行 Common 模組相關測試 ✅

## 3. Service 層清理

- [x] 3.1 移除 BackTestService 中的相容別名和 Facade ✅
- [x] 3.2 移除 ExternalService/TGetExternalData.py 相容層 ✅
- [ ] 3.3 移除 UpdateStockService 相容介面
- [ ] 3.4 移除 FilterService/GetStockData.py 中的相容類別
- [ ] 3.5 執行各 Service 模組測試

## 4. Controller 與 Model 層清理

- [x] 4.1 移除 Controller.py 中的舊函式別名 ✅
- [ ] 4.2 移除 MediatorController.py 已棄用介面
- [ ] 4.3 移除 Model_pick.py 的 Facade 相容層
- [ ] 4.4 更新所有內部匯入路徑
- [ ] 4.5 執行 Controller 與 Model 測試

## 5. 全域與彙總清理

- [ ] 5.1 清理 src/__init__.py 中的相容匯入
- [ ] 5.2 移除各模組 __init__.py 中的相容別名
- [ ] 5.3 移除所有相關的警告訊息
- [ ] 5.4 移除所有標註「向後相容」的註解

## 6. 驗證與完成

- [ ] 6.1 執行完整單元測試套件
- [ ] 6.2 執行整合測試
- [ ] 6.3 驗證 UI 功能正常運作
- [ ] 6.4 建立遷移指引文件
- [ ] 6.5 提交變更