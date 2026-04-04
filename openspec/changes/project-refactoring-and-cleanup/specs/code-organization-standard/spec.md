## ADDED Requirements

### Requirement: 模組相依性原則

重構後的程式碼 **MUST** 符合以下組織原則：

#### Scenario: 模組相依性檢查
- Given 任何 Python 模組
- When 檢查其 import 宣告
- Then 只能 import 同層級或更低層級的模組
- And 不允許出現循環 import
- And 禁止直接 import 其他模組的內部實作類別

#### Scenario: 檔案大小限制
- Given 任何原始碼檔案
- When 計算有效程式碼行數
- Then 單一檔案不得超過 500 行
- And 單一方法/函式不得超過 50 行
- And 單一類別不得超過 15 個公開方法

#### Scenario: 命名規範
- Given 所有識別元名稱
- When 進行語法檢查
- Then 類別名稱使用 PascalCase
- And 函式/方法/變數使用 snake_case
- And 常數使用 UPPER_SNAKE_CASE
- And 私有成員使用前置底線 _ 標記