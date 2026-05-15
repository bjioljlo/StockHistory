# 自由現金流圖表功能修正

## 問題描述

主畫面「自由現金流紀錄」按鈕（`button_getFreeCF`）點擊後，無法正確繪製自由現金流圖表。

## 根因分析

1. `Model_main._create_and_draw_chart` 的 FreeCF_index 分支（第 105-108 行）僅將 `_FS_type` 設為 `SCF`，然後直接抓取原始現金流量表資料
2. 自由現金流 = 營業活動現金流量（OCF）+ 投資活動現金流量（ICF），並非 SCF 報表中的單一欄位
3. 缺少 `showClumn` 設定，導致繪圖時選錯欄位

## 影響範圍

- **`src/Model/Model_main.py`**：唯一需修改的檔案

## 實作方案

在 `_create_and_draw_chart` 的 FreeCF_index 分支中，實例化 `FreeCF_Indicator`（已存在於 `StockReportHistory.py`），傳入 SCF 類型的 `Season_Report`，使用其 `get_ReportByNumber` 方法計算 `FreeCF = OCF + ICF`。

## 不修改的檔案

- `src/Controller/Controller_main.py`：按鈕連接已存在
- `src/View/View_main.py`：無需變更
- `UI/UI_main.ui`：按鈕已存在
- `src/FilterService/StockReportHistory.py`：`FreeCF_Indicator` 邏輯正確
