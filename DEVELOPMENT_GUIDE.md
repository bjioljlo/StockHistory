# StockHistory 開發指南

## 環境設置

### 必要條件
- Python 3.8 或更新版本
- 任選一種資料庫：MySQL/PostgreSQL/SQLite
- MongoDB (選用)
- TA-Lib 技術分析函式庫 (需單獨安裝)

### 安裝步驟（建議使用 pip-tools 管理依賴）
```bash
# 1. 安裝 pip-tools（建議全域或虛擬環境內）
pip install pip-tools

# 2. 由來源檔產生鎖定版本的 requirements.txt
pip-compile requirements.in dev-requirements.in --output-file=requirements.txt

# 3. 安裝專案依賴
pip install -r requirements.txt
```

### 配置設定
1. 複製並修改 `config.yml` 中的資料庫設定
2. 在 `.env` 檔案中設置環境變數
3. 確保資料庫服務正在運行

### 啟動應用程式（本機）
```bash
py -3 -m src.main_stock
```

### 使用 Docker 啟動（選用）
```bash
# 在專案根目錄
docker-compose up --build stockhistory-app
```

## 開發流程

### 程式碼結構
- `Controller/`: 使用者介面控制器和業務邏輯
- `Model/`: 資料模型和實體
- `View/`: 使用者介面元件和視圖
- `Service/`: 業務邏輯服務
- `Common/`: 共享工具和配置

### 資料庫結構
系統使用多種資料庫：
- **SQL 資料庫**：存儲股價、技術指標、用戶資料
- **MongoDB**：緩存數據、日誌、臨時存儲

### 新增功能步驟
1. 在適當的目錄中創建服務類別
2. 在 `Controller/` 目錄中添加控制器
3. 在 `MediatorController` 中註冊服務
4. 如需要，添加使用者介面元件
5. 在 `UnitTest/` 中編寫單元測試

### 測試
```bash
# 僅安裝開發/測試依賴（若尚未安裝）
pip install -r requirements.txt

# 執行單元測試
py -3 -m pytest UnitTest/

# 執行測試覆蓋率分析
py -3 -m pytest UnitTest/ --cov=src --cov-report=html

# 生成覆蓋率報告（在 htmlcov/ 目錄中查看）
# 使用 pytest-mock 進行更完善的 mocking 測試
```

## 重要設計模式

### 依賴注入
所有服務都通過 MediatorController 注入：
```python
mediator_controller = Mediator_Controller(
    schedule=schedule_service,
    sql_service=sql_service,
    # ... 其他服務
)
```

### 工廠模式
外部數據源使用工廠模式：
```python
external_data_factory = ExternalDataFactory(
    sql_service=sql_service,
    mongo_service=mongo_service,
    read_load_system=read_load_system
)
```

### 服務通訊
服務之間通過中介者控制器進行通訊，保持鬆散耦合。

## 常見問題排解

### 常見問題
1. **資料庫連接問題**：檢查 config.yml 設定
2. **TA-Lib 安裝問題**：需先單獨安裝 TA-Lib
3. **記憶體問題**：監控大型數據集操作
4. **線程池**：根據系統調整線程數量

### 除錯技巧
- 在 `config.yml` 中啟用日誌記錄
- 使用 pytest 進行單元測試
- 檢查日誌目錄中的應用程式日誌

## API 整合

### 支援的數據源
- Yahoo Finance (yfinance)
- 台灣證券交易所 (twstock)
- 通過工廠模式整合的自定義外部 API

### 添加新數據源
1. 在 `ExternalService/` 中實現
2. 添加到 `ExternalDataFactory`
3. 根據需要更新配置
