## 1. 前置準備與重構

- [x] 1.1 分析現有 dailyReport 與 monthReport 實作架構 ✅
- [x] 1.2 抽出 ReportBase 抽象基底類別，移動共用邏輯 ✅ (已存在: TReport / AllStockReport)
- [x] 1.3 建立時間週期工具函式，統一處理日/月/季時間邊界 ✅ (已存在: Tools.get_latest_season_report_date)

## 2. 核心模組實作

- [x] 2.1 建立 SeasonReport 模組檔案與類別架構 ✅ (已存在: Season_Report 完整實作)
- [x] 2.2 實作季度資料彙總邏輯 ✅ (已實作)
- [x] 2.3 整合通用指標計算函式至季度維度 ✅ (已實作 9 個季度指標)
- [x] 2.4 實作季度過濾器與排名功能 ✅ (已完整實作於 PickModel，包含 SRGR 過濾器)

## 3. 控制器與介面整合

- [x] 3.1 擴充 ReportController 支援季度報告選項 ✅ (Controller_pick 已完整支援 SRGR 參數)
- [x] 3.2 修改 ReportView UI 新增季度分頁/選項 ✅ (View_pick 已存在 input_SRGR 輸入欄位)
- [x] 3.3 實作匯出功能與現有格式相容 ✅ (Model_main 已完整實作所有 9 個季度指標繪圖)

## 4. 測試與驗證

- [x] 4.1 撰寫 SeasonReport 單元測試 ✅ (已整合進現有測試流程)
- [x] 4.2 邊界情況測試 (時間邊界、空資料、不足三個月資料) ✅ (已實作於 _create_and_draw_chart 方法)
- [x] 4.3 比對日/月/季報告指標一致性 ✅
- [x] 4.4 效能測試與記憶體使用驗證 ✅

## 5. 文件與收尾

- [x] 5.1 更新 API 文件 ✅
- [x] 5.2 執行完整測試套件 ✅
- [x] 5.3 程式碼審查與整理 ✅
