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

## 服務介面與依賴注入

### 核心介面
系統使用標準介面進行服務抽象：

- `IService` - 基礎服務介面
- `IUpdateService` - 數據更新服務介面
- `IBackTestService` - 回測服務介面
- `IFilterService` - 篩選服務介面
- `IModel` - 模型介面

### 依賴注入容器
使用 `ServiceContainer` 管理服務生命週期：

```python
from src.Common.ServiceContainer import ServiceContainer

# 註冊服務
container = ServiceContainer()
container.register(IUpdateService, UpdateStockService, lifecycle="singleton")
container.register(IBackTestService, BackTestService, lifecycle="transient")
container.register(IFilterService, FilterService, lifecycle="factory")

# 解析服務
update_service = container.resolve(IUpdateService)
backtest_service = container.resolve(IBackTestService)
```

### 服務生命週期
- **singleton**: 整個應用程式生命週期內單例
- **transient**: 每次解析都創建新實例
- **factory**: 使用工廠模式創建實例

## 模型介面

### IModel 介面
所有模型類別必須實作標準介面：

```python
from src.Model.Interfaces.IModel import IModel

class MyModel(IModel):
    def __init__(self, dependency1, dependency2):
        """初始化模型"""
        self.dependency1 = dependency1
        self.dependency2 = dependency2

    def get_name(self) -> str:
        """取得模型名稱"""
        return "MyModel"

    def validate_parameters(self, parameters: Any) -> bool:
        """驗證參數"""
        # 參數驗證邏輯
        return True

    def execute(self, parameters: Any) -> Any:
        """執行模型操作"""
        # 模型執行邏輯
        return result

    def get_status(self) -> Dict[str, Any]:
        """取得模型狀態"""
        return {"status": "running", "metrics": {}}

    def reset(self) -> None:
        """重置模型狀態"""
        pass
```

### 模型實作範例
```python
from src.Model.Interfaces.IModel import IModel
from src.Common import ModelValidationError

class StockAnalysisModel(IModel):
    def __init__(self, data_service, config_service):
        self.data_service = data_service
        self.config_service = config_service

    def get_name(self) -> str:
        return "StockAnalysisModel"

    def validate_parameters(self, parameters: Any) -> bool:
        if not isinstance(parameters, dict):
            raise ModelValidationError("Parameters must be a dictionary")
        if "stock_code" not in parameters:
            raise ModelValidationError("Missing stock_code parameter")
        return True

    def execute(self, parameters: Any) -> Any:
        stock_code = parameters["stock_code"]
        data = self.data_service.get_stock_data(stock_code)
        # 分析邏輯
        return analysis_result

    def get_status(self) -> Dict[str, Any]:
        return {
            "status": "active",
            "processed_count": self.data_service.get_processed_count(),
            "last_update": self.data_service.get_last_update_time()
        }

    def reset(self) -> None:
        self.data_service.clear_cache()
```

## 常見問題排解

### 服務解析問題
1. **服務未註冊**：確保服務已在 ServiceContainer 中註冊
2. **生命週期錯誤**：檢查服務生命週期配置
3. **依賴遺失**：確認所有依賴已正確注入

### 介面實作問題
1. **缺少方法**：確保實作所有介面方法
2. **類型不匹配**：檢查方法簽名是否符合介面定義
3. **向後相容**：新介面方法應提供預設實作以保持相容性

