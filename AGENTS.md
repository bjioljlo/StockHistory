# 股票歷史分析系統 - 代理模組說明

## 目錄
1. [簡介](#簡介)
2. [專案概述](#專案概述)
3. [核心代理](#核心代理)
4. [模組說明](#模組說明)
5. [代理通訊](#代理通訊)
6. [開發指南](#開發指南)
7. [Docker 本機建置指南 (Windows)](#docker-本機建置指南-windows)
8. [相關文件](#相關文件)

## 簡介
本文檔描述股票歷史分析系統中的代理(Agent)架構和設計。本系統採用多代理架構來處理不同的功能模組。

## 專案概述
StockHistory 是一個基於 Python 和 PyQt5 的綜合性股票數據管理與分析系統，提供即時股票數據更新、技術分析、回測功能及可視化工具。

### 主要特點
- 即時數據更新：從多個來源自動獲取股票數據
- 技術分析：整合 TA-Lib 提供技術指標和信號
- 回測功能：策略測試與績效分析
- 可視化：互動式圖表和技術指標

## 核心代理

### 1. 主控代理 (Controller Agent)
- **職責**：協調其他代理的工作流程
- **主要功能**：
  - 初始化系統
  - 管理代理生命週期
  - 處理代理間通訊

### 2. 資料獲取代理 (Data Fetcher Agent)
- **職責**：從外部API獲取股票數據
- **主要功能**：
  - 連接外部數據源
  - 數據預處理
  - 快取管理

### 3. 分析代理 (Analysis Agent)
- **職責**：執行技術和基本面分析
- **主要功能**：
  - 技術指標計算
  - 趨勢分析
  - 生成交易信號

## 模組說明

### 回測模組
- 回測策略執行
- 績效指標計算
- 風險評估

### 過濾器模組
- 股票篩選
- 條件過濾
- 排名系統

## 代理通訊
- 使用事件驅動架構
- 訊息佇列
- 同步/非同步處理

## 開發指南
1. 新增代理：
   - 繼承基礎代理類別
   - 實作必要接口
   - 註冊到主控代理
   - 為新代理建立對應的測試檔案和測試案例

2. 除錯：
   - 日誌記錄
   - 單元測試
   - 效能監控

3. 最佳實踐：
   - 保持單一職責
   - 使用依賴注入
   - 錯誤處理
   - 先撰寫測試案例，再實現功能
   - 確保新功能的測試覆蓋率達到 80% 以上

4. 測試規範：
   - 所有代理必須有對應的單元測試
   - 測試檔案命名格式：`test_{agent_name}.py`
   - 測試案例應包含正常流程和異常情況
   - 使用 Mock 測試外部依賴
   - 定期執行測試套件確保功能正常

## Docker 本機建置指南 (Windows)

本指南將協助您在 Windows 環境下，透過 `docker-compose` 成功建置並執行 `stockhistory-app` 服務。

### 問題說明

在原始設定中，`docker-compose build` 會失敗，主要原因如下：
1.  **不相容的套件依賴**：`requirements.txt` 中指定的 `TA-Lib` 套件是一個指向您本機 Windows 檔案 (`.whl`) 的路徑。
2.  **環境差異**：Docker 在 Linux 容器環境中建置映像，它無法存取您本機的 Windows 檔案系統，且 Windows 專用的 `.whl` 套件也無法在 Linux 上安裝。
3.  **缺少核心函式庫**：`TA-Lib` Python 套件需要一個名為 `ta-lib` 的底層 C 語言函式庫才能編譯。原始的 `Dockerfile` 中缺少了安裝此函式庫的步驟。

### 解決方案

為了解決以上問題，我們進行了以下修改：

1.  **修正 `requirements.txt`**：將 `TA-Lib` 的依賴從本地檔案路徑改為通用的套件名稱 `TA-Lib`。
2.  **修改 `Dockerfile`**：在 `Dockerfile` 中加入了從源碼編譯和安裝 `ta-lib` C 函式庫的指令，確保 Python 套件在安裝時能找到它。

### 執行步驟

請依照以下步驟操作：

#### 步驟 1：建立環境變數檔案

`docker-compose.yml` 需要一個 `.env` 檔案來設定資料庫的密碼。我們已經為您建立了一個範本檔案 `.env`。請根據您的需求修改其中的預設值。

```dotenv
# .env
# 請將預設密碼替換為您想設定的實際密碼

MYSQL_ROOT_PASSWORD=your_mysql_root_password
MYSQL_DATABASE=stock_data
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
```

#### 步驟 2：確保 Docker 環境就緒

- 請確保您的 Docker Desktop 正在執行，並且設定為使用 Linux 容器。
- `docker-compose.yml` 中的服務使用了一個名為 `mybridge` 的外部網路。請執行以下指令來建立它（如果已存在，指令會提示錯誤，可以忽略）：

```bash
docker network create mybridge
```

#### 步驟 3：建置並執行 Docker 容器

開啟您的終端機 (例如 PowerShell 或 CMD)，並確定您位於專案的根目錄下（與 `docker-compose.yml` 檔案同層）。然後執行以下指令：

```bash
docker compose up --build stockhistory-app
```

- `--build` 參數會強制 Docker 重新建置 `stockhistory-app` 的映像，這會應用我們修改後的 `Dockerfile` 和 `requirements.txt`。
- 首次執行時，Docker 會下載 `ta-lib` 的源碼並進行編譯，這可能會需要幾分鐘的時間。
- 指令會同時啟動 `stockhistory-app` 以及其依賴的資料庫服務 (`mysqlserver`, `mongoserver`, `redisserver` 等)。

執行成功後，您應該能看到所有服務的日誌輸出，表示系統正在運作。

## 相關文件
1. [開發指南](DEVELOPMENT_GUIDE.md) - 詳細的開發指引和規範
2. [專案概述](PROJECT_CONTEXT.md) - 專案架構和核心組件說明
3. [README](README.md) - 專案簡介和快速開始指南