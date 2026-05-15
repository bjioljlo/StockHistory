# Repository Guidelines（StockHistory — uv / Python）

本檔給 **AI 代理與人類貢獻者** 共用：變更程式前請先讀 [快速上手](#快速上手) 與 [依賴雙軌說明](#依賴雙軌說明)；版本與指令以 `pyproject.toml`、`.python-version`、[uv 官方文件](https://docs.astral.sh/uv/) 為準。

## 目錄

- [快速上手](#快速上手)
- [依賴雙軌說明](#依賴雙軌說明)
- [專案概觀](#專案概觀-project-overview)
- [專案結構](#專案結構與模組配置)
- [建置、測試與開發指令](#建置測試與開發指令uv)
- [程式風格](#程式風格與命名慣例)
- [測試指南](#測試指南)
- [開發流程](#開發流程規範)
- [Commit 與 PR](#commit-與-pull-request-指南)
- [OpenSpec](#openspec-工作流說明)
- [Docker](#docker-本機建置windows選用)
- [相關文件](#相關文件)

## 快速上手

在專案**根目錄**：

1. 安裝 [uv](https://docs.astral.sh/uv/getting-started/installation/)（若尚未安裝）。
2. 建立環境並安裝 **開發／測試** 依賴（來自 `pyproject.toml` 的 `dev` 可選群組）：

   ```bash
   uv sync --extra dev
   ```

3. 安裝 **應用程式執行期** 依賴（目前仍以 `requirements.txt` 為主；與 Docker、既有部署一致）：

   ```bash
   uv pip install -r requirements.txt
   ```

4. 啟動桌面程式：

   ```bash
   uv run python -m src.main_stock
   ```

Windows 若習慣啟動器，亦可使用 `py -3.12 -m src.main_stock`（需已對該直譯器執行過步驟 2–3 或等效安裝）。

**TA-Lib：** 本機若 `pip` 安裝 `TA-Lib` 失敗，通常需先安裝對應平台的 **TA-Lib C 函式庫**（Windows 常見為預編譯 wheel 或第三方建置指引）；Docker 映像則應在映像內編譯／安裝 C 函式庫（見下方 Docker 一節）。

### 依賴雙軌說明

| 來源 | 內容 | 何時更新 |
|------|------|----------|
| `pyproject.toml` + `uv.lock` | 專案中繼資料、`dev` 可選依賴（測試、Lint、pre-commit 等） | 變更開發工具鏈時執行 `uv lock` 並提交鎖檔 |
| `requirements.txt` | 應用程式執行期套件 | 與 Docker／既有部署一致；多由 `requirements.in`（若使用 pip-tools）編譯而來 |

兩者並存期間：**開發者**建議 `uv sync --extra dev` 後再 `uv pip install -r requirements.txt`；**變更執行期套件**時更新 `requirements.txt`（及來源 `.in` 檔若有），並在 PR 說明與 Docker 變更。

## 專案概觀 (Project Overview)

**StockHistory（股票歷史分析系統）** 為 Python + PyQt5 桌面應用：股票資料管理、技術分析（含 TA-Lib）、回測與圖表；可搭配 MySQL、MongoDB、Redis、排程與 Telegram 等。目標使用者為本機分析與資料管線需求的研究／輔助交易場景。

### 核心技術 (Core Technologies)

| 項目 | 說明 |
|------|------|
| 語言 | Python `>=3.12`（見 `requires-python`、`.python-version`，目前 **3.12**） |
| 環境 | [uv](https://docs.astral.sh/uv/)，`pyproject.toml` + **`uv.lock`** |
| 執行期套件 | **`requirements.txt`**（與 Docker／既有流程共用）；`[project] dependencies` 尚為空，長期可收斂至 `pyproject.toml` |
| 開發套件 | `[project.optional-dependencies] dev`：pytest、pytest-cov、pytest-mock、black、isort、flake8、mypy、pre-commit 等 |
| 靜態工具 | **black**、**isort**、**flake8**（含 docstrings、bugbear）、**mypy**；未使用 ruff |

### 系統架構 (Architecture)

- **`src/`**：應用程式（入口 `python -m src.main_stock`）；非單一 `src/stockhistory/` 套件目錄。
  - **`src/Controller/`**：流程與中介（如 `MediatorController`）
  - **`src/Model/`**：模型與 `Pick` 等子模組
  - **`src/View/`**：PyQt5 UI
  - **`src/ExternalService/`** 與 **`providers/`**：外部資料
  - **`src/FilterService/`**、**`src/BackTestService/`**、**`src/UpdateStockService/`**
  - **`src/Common/`**：設定、快取、備份還原、共用工具
- **`tests/`**：`tests/unit/`、`tests/integration/`；檔名 `test_*.py`
- **`openspec/`**：規格與變更（`config.yaml`、`changes/`、歸檔）
- **`README.md`**、**`docs/`**：使用說明與設計文件

## 專案結構與模組配置

採 **`src/` 版面**；請在**根目錄**執行測試與模組，避免匯入到錯誤的工作目錄模組。

- `docker-compose.yml`、`Dockerfile`：容器部署（選用）
- `config.yml`、`.env`：本機設定與機密（**勿**將含密碼的 `.env` 提交至公開分支）

## 建置、測試與開發指令（uv）

### 環境與相依性

| 指令 | 用途 |
|------|------|
| `uv sync` | 依 `uv.lock` 同步虛擬環境與目前鎖定的專案依賴 |
| `uv sync --extra dev` | 額外安裝 **`dev`** 可選依賴（pytest、lint、pre-commit 等） |
| `uv lock` | 變更 `pyproject.toml` 內依賴後更新鎖檔；**請一併提交 `uv.lock`** |
| `uv add <套件>` | 新增並寫入 `pyproject.toml` + 更新鎖檔 |
| `uv pip install -r requirements.txt` | 在 uv 管理的環境中安裝執行期套件（與步驟 2 併用） |

### 開發工具設定（本倉已有）

- **`.flake8`**：`flake8` 行寬、忽略規則、`per-file-ignores`（根目錄執行即生效）。
- **`mypy.ini`**：型別檢查選項（目前設定排除 `tests/`、`scripts/` 等目錄）；建議對 `src` 檢查：`uv run mypy src`。
- **`.pre-commit-config.yaml`**：black、isort、flake8、mypy 等 hook；與 `pyproject.toml` 的 dev 依賴搭配使用。

### 常用指令

```bash
uv run pytest tests/unit/ -q
uv run pytest tests/ -q
uv run pytest tests/ --cov=src --cov-report=term-missing
uv run black .
uv run isort .
uv run flake8
uv run mypy src
uv run pre-commit install
uv run pre-commit run --all-files
```

首次在本機使用 pre-commit 時執行一次 **`pre-commit install`**，之後會在 `git commit` 前自動跑 hook。

### 本機無 uv 時

```bash
pip install -r requirements.txt
python -m pytest tests/
```

若仍要使用 **pre-commit** 且未透過 `pyproject.toml` 的 dev 依賴安裝，請先執行 `pip install pre-commit`，再 `pre-commit install` 與 `pre-commit run --all-files`。

### 模組設計原則

- 對外介面穩定、邊界清楚；內部可用子模組或 `_` 慣例隔離。
- 避免循環依賴與「萬用」大模組；服務協作可參考既有 **MediatorController**、工廠（如 `ExternalDataFactory`）模式。

## 程式風格與命名慣例

- 縮排 4 空格；模組／函式／變數 `snake_case`；類別 `PascalCase`；常數可用 `UPPER_SNAKE_CASE`。
- 公開 API 與非顯而易見邏輯建議型別提示；優先可讀與可維護，避免過度抽象。

## 測試指南

- **路徑：** `tests/unit/`、`tests/integration/`（舊文件若仍寫 `UnitTest/`，以本倉實際目錄為準）。
- **命名：** `test_*.py`；測試名應描述行為與預期。
- **隔離：** 外部 API、DB 等以 **Mock**／fixture 隔離；善用 `pytest-mock`。
- **回歸：** 修 bug 優先補失敗測試再修實作（TDD）；`pytest-cov` 報告可作為覆蓋率參考，具體門檻以團隊／CI 為準。
- **整合測試：** `tests/integration/` 內部分案例會載入設定與服務類別；若失敗請確認 `config.yml`／環境與路徑是否在專案根目錄執行；需真實連線 DB／Redis 的測試應在文件中標示或以 mark 隔離。

## 開發流程規範

與 **SDD（規格驅動）**、**TDD（測試驅動）** 對齊之建議順序：

1. **規格：** 更新設計／介面合約與邊界案例；較大變更可走 **OpenSpec**。
2. **測試：** 依規格寫失敗測試（紅燈）。
3. **實作：** 最小變更通過測試（綠燈）；不任意破壞已審核的介面。
4. **重構與提交：** 在測試保護下整理；`uv run` 跑測試與 pre-commit 後再開 PR。

## Commit 與 Pull Request 指南

- **Commit：** [Conventional Commits](https://www.conventionalcommits.org/)（`feat:`、`fix:`、`docs:`、`chore:` 等），訊息具體可讀。
- **分支：** `feat/...`、`fix/...` 等可辨識前綴。
- **PR：** 摘要、動機、如何驗證（含測試指令結果）；若影響安裝、環境變數或行為，同步更新 `README.md` 或 `docs/`。

## OpenSpec 工作流說明

`openspec/` 存放規格與變更（含 `config.yaml`、`changes/`、歸檔）。建議階段：**Explore → Propose → Apply → Archive**。CLI 與產物細節見 `.github/skills`、`.cline` 內與 OpenSpec 相關說明。

## Docker 本機建置（Windows，選用）

1. **TA-Lib：** Linux 映像不得依賴本機 Windows `.whl` 路徑；`Dockerfile` 須先裝 C 函式庫 `ta-lib`，`requirements.txt` 使用套件名稱。
2. **`.env`：** 依 `docker-compose.yml` 設定資料庫等（勿提交機密）。
3. **網路：** 若使用外部網路（例如 `mybridge`），需先 `docker network create mybridge`（已存在可忽略錯誤）。
4. **啟動：** 於根目錄 `docker compose up --build stockhistory-app`（首次編譯可能較久）。

## 相關文件

- [開發指南](docs/guides/DEVELOPMENT_GUIDE.md)（內容若與本檔衝突，**以本檔與 repo 實際目錄為準**）
- [專案概述](docs/guides/PROJECT_CONTEXT.md)
- [文件索引](docs/README.md)
- [快取實作指南](docs/guides/CACHE_IMPLEMENTATION_GUIDE.md)
- [README](README.md)

---

**維護：** `uv` 子命令以官方文件與團隊鎖定的 uv 版本為準。`pyproject.toml` 與 `requirements.txt` 並存期間，變更依賴須同步 Docker、CI 與上述文件。
