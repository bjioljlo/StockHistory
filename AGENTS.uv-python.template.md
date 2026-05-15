# Repository Guidelines（uv 管理之 Python 專案 — AGENTS 範本）

> **使用方式：** 複製本檔為專案根目錄的 `AGENTS.md`（或併入既有 `AGENTS.md`），將「佔位說明」與範例路徑替換為實際套件名稱、目錄與 Python 版本。

## 專案概觀 (Project Overview)

（在此簡述專案目的、主要使用者或整合場景，以及是否為函式庫、CLI、服務或應用程式。）

### 核心技術 (Core Technologies)

- **語言：** Python（版本以 `pyproject.toml` 的 `requires-python` 與 `.python-version` 為準，例如 `>= 3.12`）
- **套件與環境管理：** [`uv`](https://docs.astral.sh/uv/)（`pyproject.toml`、`uv.lock`）
- **測試：** `pytest`（可依團隊慣例搭配 `unittest` 風格或純 pytest）
- **（選填）** 靜態檢查／格式化：例如 `ruff`、`mypy`，以 `pyproject.toml` 或 `[tool.uv]` 腳本為準

### 系統架構 (Architecture)

（依實際專案列出主要模組與職責，範例格式如下，請刪除不適用項並補齊真實路徑。）

- **`src/<package_name>/`**：核心實作；公開 API 建議由 `src/<package_name>/__init__.py` 集中匯出
- **`tests/`**：測試；檔名建議 `test_*.py`
- **`README.md`**：安裝、使用方式、開發指令與 API 摘要
- **`pyproject.toml`**：專案中繼資料、相依性、建置後端（如 `hatchling`）、工具設定
- **`uv.lock`**：鎖定之解析後相依性（應納入版本控制，除非團隊另有約定）

## 專案結構與模組配置

建議採 **`src/` 版面**，避免匯入時誤用到工作目錄下的同名模組。

### 目錄結構（範例）

- `src/<package_name>/`：應用程式或套件原始碼
- `tests/`：單元／整合測試
- `.python-version`：供 `uv`、`pyenv` 等辨識預設直譯器版本（與 `requires-python` 對齊）
- `.gitignore`：忽略 `__pycache__/`、`.venv/`、建置產物、本機設定等
- `pyproject.toml`、`uv.lock`：專案與鎖檔

（若專案採 **OpenSpec** 或其他規格目錄，可在此列出，例如 `openspec/`。）

## 建置、測試與開發指令（uv）

在**專案根目錄**執行；代理或鏡像設定依團隊環境調整。

### 環境與相依性

- `uv sync`：依 `uv.lock` 建立／更新虛擬環境並安裝執行期相依性
- `uv sync --dev`：一併安裝開發／測試用群組（依 `pyproject.toml` 中 `[dependency-groups]` 或 `[tool.uv]` 定義為準）
- `uv lock`：更新鎖檔（新增或變更依賴後應執行並提交 `uv.lock`）
- `uv add <套件>`：新增執行期依賴並更新鎖檔
- `uv add --dev <套件>`：新增開發依賴（實際旗標以所用 `uv` 版本文件為準）

### 在專案環境中執行指令

- `uv run pytest`：於 uv 管理的環境中執行測試（可加 `-q` 精簡輸出）
- `uv run ruff check .` / `uv run ruff format .`：若專案已設定 ruff
- `uv run python -m <module>`：執行模組（例如入口或範例）

### 本機無 uv 時的後備方式

若環境僅有已啟用的 venv 與已安裝的依賴：

- `python -m pytest`
- `pip install -e .`：以 editable 安裝目前套件，便於開發時匯入

### 模組設計原則（請依專案調整）

- 公開 API 盡量穩定、邊界清楚；內部實作可使用 `_` 前綴或子模組隔離
- 避免循環依賴與過大的「萬用」模組；職責單一、可測試為優先

## 程式風格與命名慣例

- **縮排：** 4 個空格
- **命名：** 模組／函式／變數 `snake_case`；類別 `PascalCase`；常數可依團隊慣例使用 `UPPER_SNAKE_CASE`
- **型別提示：** 公開介面與非顯而易見的邏輯建議標註型別
- **簡潔：** 優先可讀與可維護，避免過早或過度的抽象

## 測試指南

- **位置：** `tests/`（或 `pyproject.toml` 設定的測試路徑）
- **命名：** `test_*.py`；測試函式／方法名稱應描述行為與預期
- **涵蓋：** 優先核心邏輯、錯誤路徑與對外契約（API、CLI 選項等）
- **Bug 修復：** 應附**回歸測試**；理想上先寫失敗測試再修正實作（TDD）

## 開發流程規範

所有功能開發建議嚴格依下列順序，與 **SDD（Specification-Driven Development，規格驅動開發）** 及 **TDD（Test-Driven Development，測試驅動開發）** 對齊：

1. **規格先行：** 撰寫或更新規格文件，明確定義需求、API／行為與邊界案例
2. **測試依規格：** 依規格撰寫（或更新）測試，使測試足以驗證規格內容
3. **實作：** 撰寫程式直至測試通過，避免「先實作再補規格」造成漂移
4. **驗證與提交：** 確認實作與規格一致後，再進行 commit／PR

執行測試與靜態檢查時，優先使用 **`uv run …`**，以確保與鎖檔及 CI 一致。

## Commit 與 Pull Request 指南

- **Commit 訊息：** 建議遵循 [Conventional Commits](https://www.conventionalcommits.org/)（例如 `feat:`、`fix:`、`docs:`、`chore:`），內容具體、可從訊息理解變更意圖
- **分支：** 使用可辨識目的的名稱（例如 `feat/...`、`fix/...`）
- **Pull Request：** 應包含變更摘要、動機、測試結果（或如何驗證）；若影響對外 API 或安裝／使用方式，請同步更新 `README.md` 或官方文件

## OpenSpec 工作流說明（選用）

若專案採 **OpenSpec** 管理規格與變更，可採用下列階段：

1. **Explore** — 探索需求、釐清問題與規格
2. **Propose** — 提出變更提案（設計、API、任務拆解）
3. **Apply** — 依規格與任務實作
4. **Archive** — 完成後封存變更紀錄

相關目錄通常為 `openspec/`（含 `config.yaml`、`changes/` 等）；未使用 OpenSpec 的專案可刪除此節。

## 貢獻補充說明

- 範例與測試中的 `import` 路徑應與**實際發佈的套件名稱**一致（例如 `import <package_name>`），避免依賴未安裝的相對路徑技巧
- 新增依賴後請執行 **`uv lock`**（或等效流程）並將 **`uv.lock`** 一併提交，除非儲存庫政策另有規定

---

**範本維護：** 可依團隊需求增刪「選用」章節；與 `uv` 相關的子命令請以 [官方文件](https://docs.astral.sh/uv/) 與專案鎖定的 `uv` 版本為準。
