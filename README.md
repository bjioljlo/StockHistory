# StockHistory 股票數據分析系統

一個使用 Python 和 PyQt5 開發的綜合性股票數據管理與分析系統。

## 功能特點
- 從多個來源即時更新股票數據
- 整合 TA-Lib 進行技術分析
- 策略回測引擎
- 互動式圖表與視覺化
- 多種資料庫支援 (MySQL, PostgreSQL, SQLite, MongoDB)
- Telegram 機器人整合
- 排程自動更新數據

## 快速開始
```bash
# 安裝依賴套件
pip install -r requirements.txt

# 啟動應用程式
python main_stock.py
```

## 文件
- [專案概述](PROJECT_CONTEXT_TW.md) - 系統架構與元件說明
- [開發指南](DEVELOPMENT_GUIDE_TW.md) - 環境設置與開發指引
- [單元測試指南](DEVELOPMENT_GUIDE_TW.md#單元測試指南) - 測試規範與最佳實踐

## 系統需求
- Python 3.8 或更新版本
- 任選一種資料庫：MySQL/PostgreSQL/SQLite/MongoDB
- TA-Lib 技術分析函式庫

## 配置設定
請參考 `config.yml` 設定資料庫與應用程式參數。

## 授權
[授權條款](LICENSE)

## 問題回報
如發現任何問題，請提交 [Issue](https://github.com/yourusername/StockHistory/issues)

## 貢獻指南
我們歡迎任何形式的貢獻！請先閱讀 [開發指南](DEVELOPMENT_GUIDE_TW.md) 和 [貢獻指南](CONTRIBUTING_TW.md) 後發送 Pull Request。
