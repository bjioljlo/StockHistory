# StockHistory 專案概述

## 專案簡介
StockHistory 是一個使用 Python 和 PyQt5 開發的綜合性股票數據管理與分析系統。本系統提供即時股票數據更新、技術分析、回測功能和視覺化工具。

## 系統架構
- **使用者介面框架**：基於 PyQt5 的桌面應用程式
- **資料庫**：支援多種資料庫 (MySQL, PostgreSQL, SQLite, MongoDB)
- **架構模式**：使用中介者控制器模式與依賴注入
- **數據源**：Yahoo Finance (yfinance)、台灣股市數據 (twstock)
- **分析工具**：TA-Lib 技術分析、matplotlib/mplfinance 圖表繪製

## 核心元件

### 主要應用程式
- `main_stock.py`：應用程式進入點，負責服務初始化
- `Controller/MediatorController.py`：中央控制器，管理所有服務
- `UI/` 目錄：使用者介面元件

### 數據服務
- `SqlService.py`：SQL 資料庫操作 (MySQL/PostgreSQL/SQLite)
- `MongoService.py`：MongoDB 操作
- `UpdateStockService.py`：股票數據獲取與更新
- `ReadLoadSystem.py`：數據加載與緩存系統

### 分析與視覺化
- `DrawFigur.py`：圖表生成與視覺化
- `BackTestService/`：回測引擎
- `FilterService/`：股票篩選與分析工具

### 外部整合
- `ExternalService/`：外部數據源整合
- `telegram_bot.py`：Telegram 機器人整合
- `ScheduleService.py`：任務排程系統

### 配置檔案
- `config.yml`：默認資料庫與應用程式配置
- `config.dev.yml`：開發環境配置（使用環境變數）
- `config.prod.yml`：生產環境配置
- `.env`：環境變數
- `requirements.txt`：Python 依賴套件

## 主要功能
1. **即時數據更新**：從多個來源自動獲取股票數據
2. **技術分析**：整合 TA-Lib 提供技術指標與訊號
3. **回測功能**：策略測試與績效分析
4. **視覺化**：互動式圖表與技術指標展示
5. **多資料庫支援**：靈活的資料庫配置
6. **Telegram 整合**：即時通知與機器人介面
7. **排程任務**：自動化數據更新與分析

## 開發注意事項
- 使用 ThreadPool 進行並行操作
- 對外部數據源實作工廠模式
- 採用依賴注入進行服務管理
- 包含完整的單元測試於 `UnitTest/` 目錄
- 支援 Docker 容器化部署 (`docker-compose.yml`)

## 依賴套件
主要依賴套件包括：pandas, numpy, matplotlib, TA-Lib, PyQt5, SQLAlchemy, pymongo 等金融數據相關 API。
