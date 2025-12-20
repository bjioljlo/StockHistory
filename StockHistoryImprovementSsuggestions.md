# StockHistory 專案分析與改進建議

這份文件分析了您目前的專案結構和實踐，並提供了一些可以讓專案更穩健、更易於維護和擴展的建議。

## 總體評價

此專案結構完整，涵蓋了從資料獲取、分析、回測到使用者介面的各個層面。看得出來您採用了 MVC (Model-View-Controller) 的設計模式來組織程式碼，並且利用 Docker 進行容器化，這都是非常好的實踐。單元測試目錄的存在也表示您對程式碼品質有所要求。

以下是一些可以進一步提升專案品質的具體建議：

---

### 1. 專案結構與模組化

**問題:**
根目錄下的文件較為零散 (`main_stock.py`, `MongoService.py`, `ScheduleService.py` 等)。當專案規模擴大時，這會讓結構顯得混亂，且不利於打包與發布。

**建議:**
- **建立 `src` (或應用名稱) 目錄**: 將所有核心的 Python 原始碼，例如 `Controller`, `Model`, `View`, `BackTestService` 以及根目錄下的 `.py` 檔案，全部移動到一個 `src` 目錄下。
- **優點**:
    - **結構清晰**: 原始碼、設定檔 (`config.yml`)、容器設定 (`docker-compose.yml`) 和文件 (`README.md`) 在根目錄各司其職。
    - **避免命名衝突**: 可以有效避免與 Python 內建或第三方套件的命名衝突。
    - **易於打包**: 未來若要將專案打包成可安裝的套件，`src` 結構會非常方便。

**執行任務 (Tasks):**
- [x] 建立 `src` 目錄
- [x] 將 `BackTestService` 目錄移至 `src/`
- [x] 將 `Common` 目錄移至 `src/`
- [x] 將 `Controller` 目錄移至 `src/`
- [x] 將 `ExternalService` 目錄移至 `src/`
- [x] 將 `FilterService` 目錄移至 `src/`
- [x] 將 `Model` 目錄移至 `src/`
- [x] 將 `ThreadPool` 目錄移至 `src/`
- [x] 將 `View` 目錄移至 `src/`
- [x] 將 `DrawFigur.py` 移至 `src/`
- [x] 將 `main_stock.py` 移至 `src/`
- [x] 將 `MongoService.py` 移至 `src/`
- [x] 將 `ReadLoadSystem.py` 移至 `src/`
- [x] 將 `ScheduleService.py` 移至 `src/`
- [x] 將 `SqlService.py` 移至 `src/`
- [x] 將 `StockInfos.py` 移至 `src/`
- [x] 將 `telegram_bot.py` 移至 `src/`
- [x] 將 `UpdateStockService.py` 移至 `src/`
- [x] 修正所有因檔案移動而失效的 `import` 敘述（含 `src` 與 `UnitTest`，`py -3 -m compileall src`、`py -3 -m pytest UnitTest` 皆通過）
- [x] 更新相關設定檔 (如 `docker-compose.yml`, `.vscode/launch.json`) 中的路徑（目前僅有 `docker-compose.yml`，路徑已與現有結構相容，無需修改；暫無 `.vscode/launch.json`）

---

### 2. 依賴管理

**問題:**
`requirements.txt` 雖然記錄了專案依賴，但它無法區分開發環境依賴 (如 `pytest`) 和生產環境依賴。手動維護 `requirements.txt` 也容易出錯。

**建議:**
- **採用現代化的依賴管理工具**:
    - **Poetry** 或 **PDM**: 這些工具使用 `pyproject.toml` 檔案來管理依賴，可以清晰地分離正式依賴和開發依賴，並能鎖定依賴版本 (`poetry.lock` / `pdm.lock`)，確保在任何環境下都能建立出完全相同的執行環境。
    - **pip-tools**: 如果不想更換工具鏈，可以使用 `pip-tools`。您可以建立 `requirements.in` (正式依賴) 和 `dev-requirements.in` (開發依賴)，然後用指令自動生成對應的 `requirements.txt` 檔案。

**執行任務 (Tasks):**
- [x] 盤點現有 `requirements.txt`，區分正式依賴與開發/測試依賴
- [x] 建立 `requirements.in` 並只保留正式執行環境依賴
- [x] 建立 `dev-requirements.in` 並只保留開發/測試工具（pytest、flake8 等）
- [x] 在 `requirements.txt` 中標註使用 `pip-tools` 的推薦更新流程
- [x] 在 `README.md` 更新安裝與啟動流程（含 `pip-compile` 與 `py -3 -m src.main_stock`）
- [x] 在 `DEVELOPMENT_GUIDE.md` 更新依賴安裝、啟動與測試流程，統一使用新的指令

---

### 3. 容器化 (Docker)

**問題:**
從 `docker-compose.yml` 來看，您已經在使用 Docker 來管理服務，這是非常好的做法。但可以更進一步，確保開發與生產環境的一致性。

**建議:**
- **檢查 `Dockerfile`**: 確保應用程式的 `Dockerfile` 遵循最佳實踐，例如：
    - 使用多階段構建 (multi-stage builds) 來減小最終映像檔的大小。
    - 不要以 `root` 使用者身份執行應用。
    - 有效利用 Docker 的快取機制來加速映像檔建置。
- **環境變數管理**: 敏感資訊 (如資料庫密碼、API 金鑰) 不應寫死在 `config.yml` 或 `docker-compose.yml` 中。應改為透過環境變數傳入容器。可以在 `docker-compose.yml` 中使用 `.env` 檔案來載入這些變數。

**執行任務 (Tasks):**
- [x] 新增 Python 應用的 `Dockerfile`，設定合適的 `WORKDIR` 與啟動指令（`python -m src.main_stock`），並改用非 root 使用者
- [x] 在 `docker-compose.yml` 中新增 `stockhistory-app` 服務，與 MySQL/MongoDB/Redis 同一個網路
- [x] 在 `README.md` 新增「使用 Docker 啟動」章節，說明如何 `docker-compose up --build` 啟動整套服務或僅啟動 `stockhistory-app`
- [x] 在 `DEVELOPMENT_GUIDE.md` 補充 Docker 啟動方式，與本機啟動並存
- [ ] 調整 `Dockerfile` 為 multi-stage build 以縮小映像大小（目前為單階段，效能已可接受，未來若正式部署再優化）
- [ ] 將敏感設定全面改由 `.env` 與環境變數管理（目前 `docker-compose.yml` 已支援 `.env`，但 `config.yml` 尚待整理）

```yaml
# docker-compose.yml
services:
  app:
    build: .
    env_file:
      - .env
```

```# .env
MONGO_USERNAME=your_user
MONGO_PASSWORD=your_secret_password
```

---

### 4. 併發處理

**問題:**
專案中包含了自定義的 `ThreadPool` 目錄。雖然在特定場景下自定義執行緒池是必要的，但 Python 的標準庫已經提供了強大且穩定的實作。

**建議:**
- **使用 `concurrent.futures`**: 優先考慮使用 Python 內建的 `concurrent.futures.ThreadPoolExecutor` 或 `ProcessPoolExecutor`。
- **優點**:
    - **更穩定**: 經過了大量測試和驗證。
    - **易於使用**: API 簡單直觀。
    - **減少維護成本**: 不再需要維護自定義的程式碼。

只有在 `concurrent.futures` 無法滿足極端效能或特殊功能需求時，才考慮自定義實作。

**執行任務 (Tasks):**
- [x] 分析所有 ThreadPool 的使用情況，確定哪些功能是必要的
- [x] 建立一個簡單的 ConcurrentUtils 模組，使用 concurrent.futures 提供基本功能
- [x] 重構 ScheduleService.py，將 enable_queue_mode 和 submit_task 替換為直接使用 ThreadPoolExecutor 和手動順序管理
- [x] 重構 Model_backtest.py，將 submit_task 替換為 executor.submit 和 add_done_callback
- [x] 重構 main_stock.py 和 MediatorController.py 的初始化和使用
- [x] 更新 UnitTest/test_threadpool.py 以測試新的實現
- [x] 移除 src/ThreadPool 目錄
- [x] 修正所有 import 語句，移除對 ThreadPool 的引用
- [x] 運行測試確保功能正常（`py -3 -m pytest UnitTest`）
- [x] 運行編譯檢查確保無語法錯誤（`py -3 -m compileall src`）

---

### 5. 使用者介面 (UI)

**問題:**
`UI` 目錄中同時包含 `.ui` (Qt Designer 檔案) 和 `.py` (轉換後的 Python 程式碼)。`ui2py.py` 的存在暗示您是手動或透過腳本進行轉換。

**建議:**
- **自動化轉換流程**:
    - 可以將 `ui2py.py` 的邏輯整合到建置流程或 Makefile/`justfile` 中，確保每次修改 `.ui` 檔案後都能自動產生最新的 `.py` 檔案。
    - **動態載入 `.ui` 檔案**: 另一種更靈活的方式是在執行階段動態載入 `.ui` 檔案，而不是轉換成 `.py`。`PyQt` 和 `PySide` 都支援這種方式。這樣可以讓 UI 設計師和開發者更好地協作，修改 UI 不再需要重新產生 Python 程式碼。

**執行任務 (Tasks):**
- [x] 修改所有 MyWindow 類別（MyWindow, MyBacktestWindow, MyPickWindow）以動態載入 .ui 檔案，使用 uic.loadUi 替換 setupUi
- [x] 移除 View 檔案中對 Ui_ 類別的 import
- [x] 移除 UI/ 目錄中的生成 .py 檔案（UI_main.py, UI_backtest.py, UI_pick.py）
- [x] 刪除或更新 ui2py.py 腳本，使其成為可選的工具
- [x] 測試 UI 功能正常運作
- [x] 更新相關文檔

---

### 6. 測試

**問題:**
`UnitTest` 目錄的存在是個好習慣。但可以透過一些工具讓測試更全面。

**建議:**
- **測試覆蓋率**: 引入 `pytest-cov` 套件來計算測試覆蓋率。這能幫助您了解哪些程式碼路徑尚未被測試覆蓋。
- **Mocking**: 測試與外部服務 (如資料庫、外部 API) 互動的程式碼時，應使用 `unittest.mock` 或 `pytest-mock` 來模擬這些外部依賴，使單元測試更快速、更獨立。
