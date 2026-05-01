## Why

系統目前已完成 dailyReport 與 monthReport 模組，但缺少季度 (season) 層級的報告功能。季度報告對於中長期投資策略分析至關重要，能夠提供不同時間週期的技術指標與過濾條件，補齊日、月、季三個時間維度的完整分析能力。

## What Changes

- 新增 `seasonReport` 模組，依照現有 dailyReport / monthReport 的架構設計實作
- 支援季度等級的技術指標計算 (包含所有現有月報告指標與季度專屬指標)
- 整合現有過濾器與排名系統至季度報告
- 提供季度報告的 UI 介面與匯出功能
- 保留與現有日/月報告一致的 API 介面與輸出格式

## Capabilities

### New Capabilities
- `season-report`: 季度股票報告功能，提供季度層級的技術指標計算、過濾、排名與報表輸出

### Modified Capabilities
- `report-common`: 擴充現有報告公用模組，支援季度時間週期參數

## Impact

- 新增模組: `src/ReportService/SeasonReport.py`
- 修改現有模組: `src/Controller/ReportController.py`, `src/View/ReportView.py`
- 擴充共用函式庫: `src/Common/ReportUtils.py`
- 新增測試: `UnitTest/test_season_report.py`
- 不影響現有 dailyReport 與 monthReport 的功能與輸出
- 無破壞性變更
