# StockHistory 股票數據分析系統

一個使用 Python 和 PyQt5 開發的綜合性股票數據管理與分析系統。

## 功能特點
- 從多個來源即時更新股票數據
- 整合 TA-Lib 進行技術分析
- 策略回測引擎
- 互動式圖表與視覺化
- 多種資料庫支援 (MySQL, PostgreSQL, SQLite, MongoDB)
- Telegram 機器人整合
- 排程自動更新數據

## 快速開始
```bash
# 1. 建議使用 pip-tools 管理依賴（可選，但推薦）
pip install pip-tools

# 產生/更新鎖定版本的 requirements.txt
pip-compile requirements.in dev-requirements.in --output-file=requirements.txt

# 2. 安裝依賴套件
pip install -r requirements.txt

# 3. 啟動應用程式（在專案根目錄下執行）
py -3 -m src.main_stock
```

## 使用 Docker 啟動（選用）

```bash
# 建議先準備好 .env 檔案（可參考 docker-compose.yml 內的環境變數說明）

# 建立並啟動所有服務（MySQL/Mongo/Redis/Flask/Golang/StockHistory）
docker-compose up --build

# 僅啟動 StockHistory 應用（其他服務已在背景跑）
docker-compose up --build stockhistory-app
```

## 資料備份與恢復

系統提供完整的資料備份與災難恢復功能，支援 MySQL、MongoDB 和 Redis 資料庫的自動備份。

### 自動備份
```bash
# 使用備份排程器（推薦）
./backup_scheduler.bat

# 或直接執行Python腳本
python -m src.Common.BackupService --type full
```

### 手動備份特定服務
```bash
# 備份MySQL資料庫
python -m src.Common.BackupService --type mysql

# 備份MongoDB資料庫
python -m src.Common.BackupService --type mongodb

# 備份Redis資料
python -m src.Common.BackupService --type redis
```

### 資料恢復
```bash
# 從最新備份恢復所有服務
python -m src.Common.RestoreService --type full

# 從特定備份檔案恢復
python -m src.Common.RestoreService --type mysql --file ./backups/mysql_backup_20231228_143000.sql.gz

# 列出所有可用備份
python -m src.Common.RestoreService --list
```

### 資料歸檔
```bash
# 執行自動歸檔（歸檔3年前資料）
python -m src.Common.ArchivalService --auto

# 壓縮舊日誌檔案
python -m src.Common.ArchivalService --compress-logs

# 查看歸檔統計
python -m src.Common.ArchivalService --stats
```

### Windows 任務排程器設定
1. 開啟任務排程器 (taskschd.msc)
2. 建立新任務
3. 設定觸發器為每日凌晨2:00
4. 設定動作為啟動程式：`backup_scheduler.bat`
5. 設定工作目錄為專案根目錄

### 雲端備份設定
在 `config.yml` 中設定雲端備份：

```yaml
cloud_backup:
  enabled: true
  provider: aws_s3  # 或 azure_blob
  bucket_name: your-backup-bucket
  key_prefix: backups/
  aws_access_key_id: your_access_key
  aws_secret_access_key: your_secret_key
  aws_region: us-east-1
```

## 文件
- [專案概述](PROJECT_CONTEXT_TW.md) - 系統架構與元件說明
- [開發指南](DEVELOPMENT_GUIDE_TW.md) - 環境設置與開發指引
- [單元測試指南](DEVELOPMENT_GUIDE_TW.md#單元測試指南) - 測試規範與最佳實踐

## 系統需求
- Python 3.8 或更新版本
- 任選一種資料庫：MySQL/PostgreSQL/SQLite/MongoDB
- TA-Lib 技術分析函式庫

## 配置設定
請參考 `config.yml` 設定資料庫與應用程式參數。

## 授權
[授權條款](LICENSE)

## 問題回報
如發現任何問題，請提交 [Issue](https://github.com/yourusername/StockHistory/issues)

## 貢獻指南
我們歡迎任何形式的貢獻！請先閱讀 [開發指南](DEVELOPMENT_GUIDE_TW.md) 和 [貢獻指南](CONTRIBUTING_TW.md) 後發送 Pull Request。
