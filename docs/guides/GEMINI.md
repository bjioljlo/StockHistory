# Gemini 使用說明

本文件旨在說明如何在 `StockHistory` 專案中使用 Gemini 來輔助開發、分析或執行其他任務。

## 目錄

- [Gemini 使用說明](#gemini-使用說明)
  - [目錄](#目錄)
  - [專案概觀](#專案概觀)
  - [開始使用](#開始使用)
    - [環境需求](#環境需求)
    - [安裝](#安裝)
  - [如何使用 Gemini](#如何使用-gemini)
    - [設定 API 金鑰](#設定-api-金鑰)
    - [互動方式](#互動方式)
    - [範例指令](#範例指令)
  - [主要功能](#主要功能)
  - [注意事項](#注意事項)

---

## 專案概觀

`StockHistory` 是一個用於分析台灣股市歷史數據、回測交易策略並管理股票資訊的 Python 專案。從專案結構分析，它包含以下幾個部分：
- **數據服務**: 支援多種資料庫 (MySQL, PostgreSQL, MongoDB)。
- **回測引擎**: 提供了回測交易策略的功能 (`BackTestService`)。
- **數據過濾與分析**: 能夠篩選和處理股票數據 (`FilterService`, `twstock`, `yfinance`, `TA-Lib`)。
- **使用者介面**: 同時包含桌面應用程式 (PyQt5) 和 Web 服務 (Flask) 的可能性。
- **排程服務**: 可以設定定時任務 (`ScheduleService`)。

Gemini 在此專案中扮演的角色是 [請填寫 Gemini 的用途，例如：協助進行程式碼生成與重構、自動化數據分析、將自然語言查詢轉換為數據篩選條件等]。

## 開始使用

### 環境需求

- Python 3.x
- pip, virtualenv
- Docker (專案中包含 `docker-compose.yml`)

### 安裝

1.  **複製專案庫：**
    ```bash
    git clone https://github.com/bjioljlo/StockHistory
    cd StockHistory
    ```

2.  **建立並啟動虛擬環境 (建議)：**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **安裝相依套件：**
    ```bash
    pip install -r requirements.txt
    ```

## 如何使用 Gemini

這部分說明如何與 Gemini CLI 互動來協助您完成任務。

### 設定 API 金鑰

根據分析，專案設定檔 (`config.yml`) 中未包含 Gemini API 金鑰，因此最可能的方式是透過環境變數來設定。

在您開始使用之前，請確認已設定您的 API 金鑰。
```bash
# 建議的環境變數名稱 (請依實際程式碼確認)
export GEMINI_API_KEY="YOUR_API_KEY"
```

### 互動方式

您可以透過 Gemini CLI 直接下達指令。Gemini 可以讀取您的程式碼、修改檔案、執行指令，並根據您的要求提供協助。

### 範例指令

以下是一些您可能會用到的範例指令：

- **詢問關於程式碼的問題：**
  > "請解釋 `MongoService.py` 這個檔案的作用。"

- **要求產生新的程式碼：**
  > "請在 `FilterService` 目錄下新增一個 `NewFilter.py` 檔案，並實作一個基礎的篩選器類別。"

- **修改現有程式碼：**
  > "請幫我在 `telegram_bot.py` 中新增一個發送每日摘要的功能。"

- **執行測試：**
  > "請執行 `UnitTest` 目錄下的所有測試，並告訴我結果。"

## 主要功能

[請根據您打算使用 Gemini 的方式，條列出此專案結合 Gemini 後可達成的核心功能]

- **功能一：** [例如：自動生成每日股市分析報告]
- **功能二：** [例如：根據自然語言指令執行股票回測]
- **功能三：** [例如：優化現有的交易策略算法]

## 注意事項

- 在執行任何修改檔案系統或執行腳本的指令前，請仔細檢查 Gemini 提供的說明。
- 敏感資訊 (如 API 金鑰、密碼) 不應直接寫在程式碼中或提交至版本控制系統。
