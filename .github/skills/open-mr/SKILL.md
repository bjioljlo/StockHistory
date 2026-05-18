---
name: open-mr
description: 使用 GitLab CLI (glab) 建立 Merge Request。會自動偵測並安裝 glab（如果尚未安裝），處理 commit、push、開 MR 的完整流程。使用時機：當使用者說「開 MR」、「建立 MR」、「open MR」、「create merge request」時請使用此 skill。
argument-hint: "[target-branch]"
disable-model-invocation: true
---

# Open Merge Request

使用 GitLab CLI 自動建立 Merge Request。執行前請依序完成以下步驟：

## Step 1：確認 glab 已安裝

執行安裝確認腳本：

```bash
bash ${CLAUDE_SKILL_DIR}/scripts/ensure-glab.sh
```

如果腳本回傳錯誤，請告知使用者並停止後續步驟。

## Step 2：確認 glab 已登入 GitLab

```bash
glab auth status
```

如果未登入，請告知使用者執行以下互動式指令（需在終端機直接輸入，Claude 無法代為執行）：

```
! glab auth login --hostname cggitlab.chinesegamer.net
```

> 本專案使用自架 GitLab：https://cggitlab.chinesegamer.net/
> 登入時需提供在該站台產生的 Personal Access Token（需勾選 `api` scope）。

等待使用者完成互動式登入後再繼續。

## Step 3：確認 git 狀態

```bash
git status
git branch --show-current
```

- 確認目前在正確的 feature branch（不是 main / master / develop）
- 如果有未 commit 的變更，詢問使用者是否要一起 commit

## Step 4：處理未 commit 的變更（如果有）

如果有未 commit 的變更：

1. 顯示 `git diff --stat` 給使用者看
2. 詢問 commit message（建議使用 conventional commits 格式，例如 `feat: ...`、`fix: ...`）
3. 執行：
   ```bash
   git add .
   git commit -m "<使用者提供的 commit message>"
   ```

## Step 5：Push 到遠端

```bash
git push origin $(git branch --show-current)
```

如果是第一次 push 此 branch，加上 `--set-upstream`：

```bash
git push --set-upstream origin $(git branch --show-current)
```

## Step 6：決定 target branch

- 如果使用者有帶參數 `$ARGUMENTS`，使用該參數作為 target branch
- 否則，依序嘗試偵測預設 target branch：
  ```bash
  git remote show origin | grep 'HEAD branch' | awk '{print $NF}'
  ```
- 如果無法偵測，詢問使用者，預設建議 `main`

## Step 7：產生 MR 標題與描述

根據以下資訊自動產生：

```bash
git log origin/$(git remote show origin | grep 'HEAD branch' | awk '{print $NF}')..HEAD --oneline
git diff origin/$(git remote show origin | grep 'HEAD branch' | awk '{print $NF}')..HEAD --stat
```

產生格式：
- **標題**：根據 commit messages 摘要，符合 conventional commits 風格
- **描述**：必須依照專案 MR 模板（`.gitlab/merge_request_templates/Common_Merge_Request.md`）格式填寫，包含以下段落：
  - `## Reviewer` — 留空或填 `@abcd1997`
  - `## MR 描述` — 根據 commit 內容描述本次變動
  - `## 測試步驟` — 描述如何驗證變更
  - `## Redmine Issues:` — 如無對應單號，填「無」
  - `## 其他備註` — 如無則填「無」或刪除
  - `## 變動類型` — 根據變更內容勾選適當的 checkbox
  - `## 額外補充內容` — 如無則填「無」或刪除
  - 結尾保留 GitLab Quick Actions：`/draft`、`/assign @abcd1997`、`/reviewer @abcd1997`、`/label ~"feature"`

## Step 8：開立 MR

```bash
glab mr create \
  --title "<產生的標題>" \
  --description "<產生的描述>" \
  --target-branch <target-branch> \
  --yes
```

## Step 9：回傳結果

顯示 MR 連結給使用者，例如：
```
✅ MR 已建立：https://gitlab.com/your-group/your-repo/-/merge_requests/42
```

## 注意事項

- 如果任何步驟失敗，清楚說明錯誤原因並提供修正建議
- 不要在使用者未確認的情況下強制 push（`--force`）
- 如果已有同名的 MR 存在，提示使用者

## 參考資源

- 安裝腳本：[scripts/ensure-glab.sh](scripts/ensure-glab.sh)
- glab 官方文件：https://gitlab.com/gitlab-org/cli
