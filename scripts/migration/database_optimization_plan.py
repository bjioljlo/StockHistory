#!/usr/bin/env python3
"""
資料庫優化計劃 - 基於程式碼分析的設計
StockHistory 資料庫優化與爬蟲資料整理計劃
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Any

class DatabaseOptimizationPlan:
    """資料庫優化計劃"""

    def __init__(self):
        self.current_structure = self._analyze_current_structure()
        self.proposed_structure = self._design_unified_schema()

    def _analyze_current_structure(self) -> Dict[str, Any]:
        """分析現有資料庫結構（基於程式碼分析）"""
        print("=== 現有資料庫結構分析 ===")

        # 基於程式碼分析的結構
        structure = {
            "database_type": "MySQL + MongoDB",
            "table_pattern": "每檔股票一個表格",
            "table_naming": "股票代碼小寫",
            "primary_key": "Date (日期)",
            "typical_columns": [
                "Date", "Open", "High", "Low", "Close",
                "Adj Close", "Volume"
            ],
            "data_sources": ["Yahoo Finance", "Taiwan Stock Exchange"],
            "estimated_tables": "~1000+ (台灣上市 + 美股)",
            "issues": [
                "表格分散，難以管理",
                "缺乏統一的索引策略",
                "查詢跨表格複雜",
                "備份和維護困難",
                "無法有效分區"
            ]
        }

        for key, value in structure.items():
            if key != "issues":
                print(f"{key}: {value}")
            else:
                print(f"{key}:")
                for issue in value:
                    print(f"  - {issue}")

        return structure

    def _design_unified_schema(self) -> Dict[str, Any]:
        """設計統一的資料庫模式"""
        print("\n=== 統一資料庫模式設計 ===")

        schema = {
            "main_table": "stock_daily_prices",
            "columns": {
                "id": "BIGINT AUTO_INCREMENT PRIMARY KEY",
                "symbol": "VARCHAR(20) NOT NULL",  # 股票代碼
                "market": "VARCHAR(10) NOT NULL", # TW/US/HK 等
                "date": "DATE NOT NULL",
                "open": "DECIMAL(10,2)",
                "high": "DECIMAL(10,2)",
                "low": "DECIMAL(10,2)",
                "close": "DECIMAL(10,2)",
                "adj_close": "DECIMAL(10,2)",
                "volume": "BIGINT",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
            },
            "indexes": [
                "PRIMARY KEY (id)",
                "UNIQUE KEY unique_symbol_date (symbol, date)",
                "INDEX idx_symbol (symbol)",
                "INDEX idx_market (market)",
                "INDEX idx_date (date)",
                "INDEX idx_symbol_date (symbol, date)"
            ],
            "partitioning": {
                "strategy": "按年份分區",
                "partition_by": "YEAR(date)",
                "retention": "保留最近10年資料"
            },
            "advantages": [
                "統一資料模型，便於管理",
                "高效能查詢和索引",
                "支援分區，提高效能",
                "便於備份和維護",
                "支援多市場整合"
            ]
        }

        print("統一資料表結構:")
        for col, definition in schema["columns"].items():
            print(f"  {col}: {definition}")

        print("\n索引策略:")
        for index in schema["indexes"]:
            print(f"  - {index}")

        print(f"\n分區策略: {schema['partitioning']['strategy']}")

        return schema

    def create_migration_plan(self) -> Dict[str, Any]:
        """建立遷移計劃"""
        print("\n=== 資料遷移計劃 ===")

        migration_plan = {
            "phase_1": {
                "name": "評估與規劃",
                "duration": "1-2週",
                "tasks": [
                    "分析現有表格結構和資料量",
                    "設計統一的股票資料表模式",
                    "評估遷移風險和影響",
                    "制定詳細遷移計劃",
                    "準備測試環境"
                ]
            },
            "phase_2": {
                "name": "開發與測試",
                "duration": "2-3週",
                "tasks": [
                    "開發資料遷移工具",
                    "建立資料驗證機制",
                    "在測試環境完整測試遷移",
                    "準備回滾計劃",
                    "效能測試"
                ]
            },
            "phase_3": {
                "name": "生產環境遷移",
                "duration": "1週",
                "tasks": [
                    "建立生產環境備份",
                    "執行分批遷移",
                    "驗證資料完整性",
                    "監控系統穩定性",
                    "最終切換"
                ]
            },
            "phase_4": {
                "name": "優化與監控",
                "duration": "持續",
                "tasks": [
                    "效能調優",
                    "監控系統運作",
                    "處理遷移後問題",
                    "記錄和總結經驗"
                ]
            }
        }

        for phase_key, phase_data in migration_plan.items():
            print(f"{phase_key.upper()}: {phase_data['name']} ({phase_data['duration']})")
            for task in phase_data['tasks']:
                print(f"  - {task}")
            print()

        return migration_plan

    def generate_migration_script_template(self) -> str:
        """生成遷移腳本模板"""
        template = '''
#!/usr/bin/env python3
"""
資料庫遷移腳本模板
將分散的股票表格遷移到統一的 stock_daily_prices 表格
"""

import sys
import os
import pandas as pd
import mysql.connector
from datetime import datetime
from typing import List, Dict
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None

    def connect(self):
        """建立資料庫連接"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            logger.info("資料庫連接成功")
        except Exception as e:
            logger.error(f"資料庫連接失敗: {e}")
            raise

    def get_all_stock_tables(self) -> List[str]:
        """獲取所有股票表格名稱"""
        cursor = self.connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]

        # 過濾出股票表格（排除系統表格）
        stock_tables = []
        for table in tables:
            # 這裡需要根據實際的表格命名規則來過濾
            if self._is_stock_table(table):
                stock_tables.append(table)

        cursor.close()
        return stock_tables

    def _is_stock_table(self, table_name: str) -> bool:
        """判斷是否為股票表格"""
        # 實現表格過濾邏輯
        # 例如：檢查是否包含股票代碼模式
        return True  # 臨時實現

    def migrate_table(self, table_name: str, batch_size: int = 1000):
        """遷移單個表格"""
        try:
            # 讀取舊表格資料
            query = f"SELECT * FROM `{table_name}`"
            df = pd.read_sql(query, self.connection)

            if df.empty:
                logger.warning(f"表格 {table_name} 為空，跳過")
                return

            # 轉換資料格式
            migrated_data = self._transform_data(df, table_name)

            # 批次插入新表格
            self._batch_insert(migrated_data, batch_size)

            logger.info(f"表格 {table_name} 遷移完成")

        except Exception as e:
            logger.error(f"遷移表格 {table_name} 失敗: {e}")
            raise

    def _transform_data(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """轉換資料格式以適應新表格"""
        # 實現資料轉換邏輯
        transformed = df.copy()

        # 添加 symbol 和 market 欄位
        transformed['symbol'] = self._extract_symbol(table_name)
        transformed['market'] = self._determine_market(table_name)

        # 重新命名欄位
        column_mapping = {
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Adj Close': 'adj_close',
            'Volume': 'volume'
        }
        transformed = transformed.rename(columns=column_mapping)

        return transformed

    def _extract_symbol(self, table_name: str) -> str:
        """從表格名稱提取股票代碼"""
        # 實現股票代碼提取邏輯
        return table_name.upper()

    def _determine_market(self, table_name: str) -> str:
        """確定市場類型"""
        if table_name.endswith('.tw'):
            return 'TW'
        elif len(table_name) <= 5:
            return 'US'
        else:
            return 'OTHER'

    def _batch_insert(self, df: pd.DataFrame, batch_size: int):
        """批次插入資料"""
        # 實現批次插入邏輯
        pass

    def create_unified_table(self):
        """建立統一的資料表格"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS stock_daily_prices (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            market VARCHAR(10) NOT NULL,
            date DATE NOT NULL,
            open DECIMAL(10,2),
            high DECIMAL(10,2),
            low DECIMAL(10,2),
            close DECIMAL(10,2),
            adj_close DECIMAL(10,2),
            volume BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY unique_symbol_date (symbol, date),
            INDEX idx_symbol (symbol),
            INDEX idx_market (market),
            INDEX idx_date (date),
            INDEX idx_symbol_date (symbol, date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """

        cursor = self.connection.cursor()
        cursor.execute(create_table_sql)
        self.connection.commit()
        cursor.close()

        logger.info("統一資料表格建立完成")

    def run_migration(self):
        """執行完整遷移"""
        try:
            self.connect()
            self.create_unified_table()

            stock_tables = self.get_all_stock_tables()
            logger.info(f"找到 {len(stock_tables)} 個股票表格")

            for table in stock_tables:
                self.migrate_table(table)

            logger.info("資料遷移完成")

        except Exception as e:
            logger.error(f"遷移失敗: {e}")
            raise
        finally:
            if self.connection:
                self.connection.close()

def main():
    # 資料庫配置
    db_config = {
        'host': 'localhost',
        'user': 'demo',
        'password': '~Demo123',
        'database': 'demo',
        'port': 3307
    }

    migrator = DatabaseMigrator(db_config)
    migrator.run_migration()

if __name__ == "__main__":
    main()
'''
        return template

def main():
    """主函數"""
    plan = DatabaseOptimizationPlan()
    migration_plan = plan.create_migration_plan()

    print("\n=== 遷移腳本模板 ===")
    template = plan.generate_migration_script_template()
    print(template)

    print("\n=== 建議的執行順序 ===")
    print("1. 在測試環境建立新資料庫結構")
    print("2. 運行遷移腳本進行資料遷移")
    print("3. 驗證資料完整性")
    print("4. 效能測試")
    print("5. 生產環境部署")

if __name__ == "__main__":
    main()
