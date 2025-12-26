#!/usr/bin/env python3
"""
StockHistory 資料庫遷移腳本
將分散的股票表格遷移到統一的 stock_daily_prices 表格
"""

import sys
import os
import pandas as pd
import mysql.connector
from datetime import datetime
from typing import List, Dict, Any
import logging
from dataclasses import dataclass

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MigrationConfig:
    """遷移配置"""
    host: str = "localhost"
    user: str = "demo"
    password: str = "~Demo123"
    database: str = "demo"
    port: int = 3307
    batch_size: int = 1000
    dry_run: bool = False

class DatabaseMigrator:
    """資料庫遷移器"""

    def __init__(self, config: MigrationConfig):
        self.config = config
        self.connection = None
        self.stats = {
            'tables_processed': 0,
            'rows_migrated': 0,
            'errors': 0
        }

    def connect(self):
        """建立資料庫連接"""
        try:
            self.connection = mysql.connector.connect(
                host=self.config.host,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                port=self.config.port
            )
            logger.info("資料庫連接成功")
        except Exception as e:
            logger.error(f"資料庫連接失敗: {e}")
            raise

    def get_all_stock_tables(self) -> List[str]:
        """獲取所有股票表格名稱"""
        cursor = self.connection.cursor()
        cursor.execute("SHOW TABLES")
        all_tables = [table[0] for table in cursor.fetchall()]
        cursor.close()

        # 過濾出股票表格
        stock_tables = []
        exclude_patterns = ['stock_daily_prices', 'migrations', 'schema']

        for table in all_tables:
            # 排除系統表格
            if any(pattern in table.lower() for pattern in exclude_patterns):
                continue

            # 包含股票相關表格
            if self._is_stock_table(table):
                stock_tables.append(table)

        logger.info(f"找到 {len(stock_tables)} 個股票表格")
        return stock_tables

    def _is_stock_table(self, table_name: str) -> bool:
        """判斷是否為股票表格"""
        # 台灣股票：通常以.tw結尾或為4-5位數字
        # 美股：通常為1-5位字母
        table_lower = table_name.lower()

        # 台灣股票模式
        if table_lower.endswith('.tw') or (table_lower.replace('.tw', '').isdigit() and 4 <= len(table_lower.replace('.tw', '')) <= 5):
            return True

        # 美股模式（簡單檢查）
        if len(table_lower) <= 5 and table_lower.replace('.', '').isalnum():
            return True

        return False

    def create_unified_table(self):
        """建立統一的資料表格"""
        if self.config.dry_run:
            logger.info("DRY RUN: 跳過建立統一表格")
            return

        create_table_sql = """
        CREATE TABLE IF NOT EXISTS stock_daily_prices (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL COMMENT '股票代碼',
            market VARCHAR(10) NOT NULL COMMENT '市場類型: TW/US/HK',
            date DATE NOT NULL COMMENT '交易日期',
            open DECIMAL(10,2) COMMENT '開盤價',
            high DECIMAL(10,2) COMMENT '最高價',
            low DECIMAL(10,2) COMMENT '最低價',
            close DECIMAL(10,2) COMMENT '收盤價',
            adj_close DECIMAL(10,2) COMMENT '調整後收盤價',
            volume BIGINT COMMENT '成交量',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY unique_symbol_date (symbol, date),
            INDEX idx_symbol (symbol),
            INDEX idx_market (market),
            INDEX idx_date (date),
            INDEX idx_symbol_date (symbol, date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='統一股票日線資料表';
        """

        cursor = self.connection.cursor()
        try:
            cursor.execute(create_table_sql)
            self.connection.commit()
            logger.info("統一資料表格建立完成")
        except Exception as e:
            logger.error(f"建立統一表格失敗: {e}")
            raise
        finally:
            cursor.close()

    def migrate_table(self, table_name: str) -> bool:
        """遷移單個表格"""
        try:
            logger.info(f"開始遷移表格: {table_name}")

            # 讀取舊表格資料
            df = self._read_table_data(table_name)
            if df.empty:
                logger.warning(f"表格 {table_name} 為空，跳過")
                return True

            # 轉換資料格式
            migrated_data = self._transform_data(df, table_name)

            # 插入新表格
            if not self.config.dry_run:
                self._insert_to_unified_table(migrated_data)

            self.stats['tables_processed'] += 1
            self.stats['rows_migrated'] += len(migrated_data)

            logger.info(f"表格 {table_name} 遷移完成，處理 {len(migrated_data)} 行資料")
            return True

        except Exception as e:
            logger.error(f"遷移表格 {table_name} 失敗: {e}")
            self.stats['errors'] += 1
            return False

    def _read_table_data(self, table_name: str) -> pd.DataFrame:
        """讀取表格資料"""
        query = f"SELECT * FROM `{table_name}`"
        return pd.read_sql(query, self.connection)

    def _transform_data(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """轉換資料格式"""
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

        # 只重新命名存在的欄位
        existing_columns = {k: v for k, v in column_mapping.items() if k in transformed.columns}
        transformed = transformed.rename(columns=existing_columns)

        # 確保日期欄位格式正確
        if 'date' in transformed.columns:
            transformed['date'] = pd.to_datetime(transformed['date']).dt.date

        return transformed

    def _extract_symbol(self, table_name: str) -> str:
        """從表格名稱提取股票代碼"""
        # 移除可能的副檔名並轉大寫
        symbol = table_name.upper().replace('.TW', '').replace('.TW', '')
        return symbol

    def _determine_market(self, table_name: str) -> str:
        """確定市場類型"""
        table_lower = table_name.lower()
        if table_lower.endswith('.tw') or (table_lower.replace('.tw', '').isdigit() and len(table_lower.replace('.tw', '')) >= 4):
            return 'TW'
        elif len(table_lower) <= 5 and not table_lower.replace('.', '').isdigit():
            return 'US'
        else:
            return 'OTHER'

    def _insert_to_unified_table(self, df: pd.DataFrame):
        """插入資料到統一表格"""
        if df.empty:
            return

        # 準備插入語句
        columns = ['symbol', 'market', 'date', 'open', 'high', 'low', 'close', 'adj_close', 'volume']
        existing_cols = [col for col in columns if col in df.columns]

        placeholders = ', '.join(['%s'] * len(existing_cols))
        columns_str = ', '.join([f'`{col}`' for col in existing_cols])

        insert_sql = f"""
        INSERT INTO stock_daily_prices ({columns_str})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE
        {', '.join([f'`{col}` = VALUES(`{col}`)' for col in existing_cols[3:]])}
        """

        cursor = self.connection.cursor()

        try:
            # 批次處理
            batch_size = self.config.batch_size
            for i in range(0, len(df), batch_size):
                batch_df = df.iloc[i:i+batch_size]
                data = [tuple(row) for row in batch_df[existing_cols].values]
                cursor.executemany(insert_sql, data)
                self.connection.commit()

                logger.debug(f"插入批次 {i//batch_size + 1}: {len(data)} 行")

        except Exception as e:
            logger.error(f"批次插入失敗: {e}")
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def validate_migration(self) -> Dict[str, Any]:
        """驗證遷移結果"""
        logger.info("開始驗證遷移結果")

        validation_results = {
            'total_rows_old': 0,
            'total_rows_new': 0,
            'tables_validated': 0,
            'issues': []
        }

        try:
            cursor = self.connection.cursor()

            # 檢查新表格總行數
            cursor.execute("SELECT COUNT(*) FROM stock_daily_prices")
            validation_results['total_rows_new'] = cursor.fetchone()[0]

            # 檢查樣本資料
            cursor.execute("""
                SELECT symbol, market, COUNT(*) as count
                FROM stock_daily_prices
                GROUP BY symbol, market
                LIMIT 10
            """)

            sample_data = cursor.fetchall()
            logger.info("樣本驗證資料:")
            for row in sample_data:
                logger.info(f"  {row[0]} ({row[1]}): {row[2]} 行")

            validation_results['sample_data'] = sample_data

        except Exception as e:
            validation_results['issues'].append(f"驗證失敗: {e}")
        finally:
            cursor.close()

        return validation_results

    def run_migration(self) -> bool:
        """執行完整遷移"""
        try:
            logger.info("=== 開始資料庫遷移 ===")
            logger.info(f"配置: {self.config}")

            self.connect()
            self.create_unified_table()

            stock_tables = self.get_all_stock_tables()

            if not stock_tables:
                logger.warning("沒有找到股票表格")
                return True

            success_count = 0
            for table in stock_tables:
                if self.migrate_table(table):
                    success_count += 1

            logger.info(f"=== 遷移完成統計 ===")
            logger.info(f"總表格數: {len(stock_tables)}")
            logger.info(f"成功遷移: {success_count}")
            logger.info(f"失敗數: {self.stats['errors']}")
            logger.info(f"總行數: {self.stats['rows_migrated']}")

            # 驗證結果
            if success_count > 0:
                validation = self.validate_migration()
                logger.info(f"新表格總行數: {validation['total_rows_new']}")

            return self.stats['errors'] == 0

        except Exception as e:
            logger.error(f"遷移失敗: {e}")
            return False
        finally:
            if self.connection:
                self.connection.close()

def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description='StockHistory 資料庫遷移工具')
    parser.add_argument('--dry-run', action='store_true', help='僅模擬運行，不實際修改資料庫')
    parser.add_argument('--host', default='localhost', help='資料庫主機')
    parser.add_argument('--port', type=int, default=3307, help='資料庫端口')
    parser.add_argument('--user', default='demo', help='資料庫用戶名')
    parser.add_argument('--password', default='~Demo123', help='資料庫密碼')
    parser.add_argument('--database', default='demo', help='資料庫名稱')
    parser.add_argument('--batch-size', type=int, default=1000, help='批次處理大小')

    args = parser.parse_args()

    config = MigrationConfig(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database,
        batch_size=args.batch_size,
        dry_run=args.dry_run
    )

    migrator = DatabaseMigrator(config)
    success = migrator.run_migration()

    if success:
        print("✅ 遷移成功完成")
        return 0
    else:
        print("❌ 遷移失敗")
        return 1

if __name__ == "__main__":
    sys.exit(main())
