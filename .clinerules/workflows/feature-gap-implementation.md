# Feature Gap Implementation

從 `docs/feature-gaps.md` 中挑選最高優先項目，透過 OpenSpec 完成完整流程：propose → apply → 整合測試 → commit。

**Input**: 可選，可指定要處理的 gap 編號（例如 gap 2），否則從最高優先未完成項目開始。

## Steps

### 1. 確認當前分支與狀態 + 檢查 feature-gaps 來源

```bash
git branch --show-current
git status --short
```

確保在 `develop` 分支且工作目錄乾淨。

同時檢查 feature-gaps 來源是否存在：
```bash
test -f docs/feature-gaps.md && echo "exists" || echo "not-exists"
```

### 2. 獲取 Feature Gap 資訊

根據 Step 1 的檢查結果，分為兩種情境：

**情境 A：`docs/feature-gaps.md` 存在**
讀取 `docs/feature-gaps.md`，從 🔴 高優先開始，找第一個尚未實作的項目（或依 Input 指定的 gap 編號）。

記錄該項目的：
- 編號與標題（如 `1. 🫀 自動心跳與斷線偵測`）
- 核心需求摘要
- 轉換為 kebab-case change name（如 `auto-heartbeat-detection`）

**情境 B：`docs/feature-gaps.md` 不存在**
- 若使用者已在 Input 中提供 gap 描述（如「實作心跳」或「實作 gap 編號 1」），則直接解析使用
- 否則，詢問使用者描述想要實作的功能缺口（名稱、需求、行為），例如：
  - 「我想要自動心跳與斷線偵測」
  - 「新增房間/頻道管理功能」
- 基於描述萃取功能名稱，轉換為 kebab-case change name
- gap 編號設為 `custom`，標題取自分類名稱

### 3. OpenSpec Propose

使用 openspec-propose skill 建立 change artifacts。執行順序：

```bash
openspec new change "<change-name>"
openspec instructions proposal --change "<change-name>" --json   # 產出 proposal.md
openspec instructions specs --change "<change-name>" --json      # 產出 specs
openspec instructions design --change "<change-name>" --json     # 產出 design.md
openspec instructions tasks --change "<change-name>" --json      # 產出 tasks.md
```

產出 artifacts 時需仔細閱讀現有程式碼以確保設計準確。

### 4. 建立功能分支

```bash
git checkout develop
git pull origin develop
git checkout -b feature/<change-name>
```

### 5. 實作（OpenSpec Apply）

使用 openspec-apply skill 逐一實作 tasks.md 中的任務：

- 修改核心原始碼（`src/socket_package/`）
- 根據 specs 中的 scenarios 撰寫單元測試（`tests/`）
- 撰寫整合測試（`tests/integration/`）

### 6. 測試驗證

```bash
uv run pytest -q                    # 全部測試（含整合）
uv run pytest -q -m "not integration"  # 僅單元測試
```

確認所有測試通過、無 regression。

### 7. Commit

```bash
git add -A
git commit -m "feat: <簡短描述>

<詳細變更說明>

Closes feature-gap #<number>: <change-name>"
```

使用 Conventional Commits 格式（feat/fix/refactor/chore/docs）。

> commit 訊息中的 `#<number>`：
> - 若 gap 來自 `docs/feature-gaps.md`：填寫對應的 gap 編號
> - 若為自定義 gap（情境 B）：省略編號，改為 `Closes feature-gap: <change-name>`

## 注意事項

- 每個 gap 從 develop 開新分支，不要累積在同一個分支
- 整合測試應使用 `@pytest.mark.integration` 標記
- 避免修改不相關的檔案
- 若實作中發現設計問題，先更新 OpenSpec artifacts 再繼續