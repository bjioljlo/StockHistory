#!/usr/bin/env python3
"""
StockHistory 生產環境資料遷移腳本
專為生產環境優化的分批遷移工具，包含進度追蹤和錯誤恢復
"""

import sys
import os
import pandas as pd
import mysql.connector
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
import json
import time
from dataclasses import dataclass

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('production_migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ProductionMigrationConfig:
    """生產環境遷移配置"""
    host: str = "localhost"
    user: str = "demo"
    password: str = "~Demo123"
    database: str = "demo"
    port: int = 3307
    batch_size: int = 5000  # 生產環境使用較大的批次
    max_workers: int = 4  # 並發處理數量
    checkpoint_interval: int = 10000  # 檢查點間隔
    retry_attempts: int = 3
    retry_delay: int = 5  # 重試延遲（秒）
    dry_run: bool = False
    resume_from_checkpoint: bool = False
    checkpoint_file: str = "migration_checkpoint.json"

class ProductionMigrator:
    """生產環境遷移器"""

    def __init__(self, config: ProductionMigrationConfig):
        self.config = config
        self.connection = None
        self.checkpoint_data = {}
        self.stats = {
            'tables_processed': 0,
            'rows_migrated': 0,
            'batches_processed': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }

    def connect(self):
        """建立資料庫連接"""
        try:
            self.connection = mysql.connector.connect(
                host=self.config.host,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                port=self.config.port,
                autocommit=False  # 手動控制交易
            )
            logger.info("資料庫連接成功")
        except Exception as e:
            logger.error(f"資料庫連接失敗: {e}")
            raise

    def load_checkpoint(self) -> bool:
        """載入檢查點"""
        if not self.config.resume_from_checkpoint or not os.path.exists(self.config.checkpoint_file):
            return False

        try:
            with open(self.config.checkpoint_file, 'r', encoding='utf-8') as f:
                self.checkpoint_data = json.load(f)
            logger.info(f"載入檢查點: {self.checkpoint_data}")
            return True
        except Exception as e:
            logger.warning(f"無法載入檢查點: {e}")
            return False

    def save_checkpoint(self, table_name: str, last_id: int, progress: Dict[str, Any]):
        """保存檢查點"""
        checkpoint = {
            'table_name': table_name,
            'last_id': last_id,
            'progress': progress,
            'timestamp': datetime.now().isoformat(),
            'stats': self.stats
        }

        try:
            with open(self.config.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存檢查點失敗: {e}")

    def get_migration_queue(self) -> List[str]:
        """獲取遷移隊列"""
        cursor = self.connection.cursor()

        try:
            # 獲取所有股票表格，排除已遷移完成的
            cursor.execute("SHOW TABLES")
            all_tables = [table[0] for table in cursor.fetchall()]

            # 過濾股票表格
            stock_tables = []
            exclude_patterns = ['stock_daily_prices', 'migrations', 'schema', 'checkpoint']

            for table in all_tables:
                if any(pattern in table.lower() for pattern in exclude_patterns):
                    continue

                if self._is_stock_table(table):
                    stock_tables.append(table)

            # 如果有檢查點，從檢查點恢復
            if self.checkpoint_data:
                current_table = self.checkpoint_data.get('table_name')
                if current_table in stock_tables:
                    start_idx = stock_tables.index(current_table)
                    stock_tables = stock_tables[start_idx:]

            logger.info(f"遷移隊列: {len(stock_tables)} 個表格")
            return stock_tables

        finally:
            cursor.close()

    def ensure_ad_index_table_exists(self):
        """Initialize AD index table with English column names."""
        if self.config.dry_run:
            logger.info("DRY RUN: skip creating ad_index table")
            return

        create_table_sql = """
        CREATE TABLE IF NOT EXISTS ad_index (
            date DATE NOT NULL COMMENT 'Trading date',
            up_count INT NOT NULL DEFAULT 0 COMMENT 'Number of advancing stocks',
            down_count INT NOT NULL DEFAULT 0 COMMENT 'Number of declining stocks',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (date),
            INDEX idx_date (date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        COMMENT='Advance/Decline index daily values';
        """

        cursor = self.connection.cursor()
        try:
            cursor.execute(create_table_sql)
            self.connection.commit()
            logger.info("ad_index table initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize ad_index table: {e}")
            raise
        finally:
            cursor.close()

    def _is_stock_table(self, table_name: str) -> bool:
        """判斷是否為股票表格"""
        table_lower = table_name.lower()

        # 台灣股票模式
        if table_lower.endswith('.tw') or (table_lower.replace('.tw', '').isdigit() and 4 <= len(table_lower.replace('.tw', '')) <= 5):
            return True

        # 美股模式
        if len(table_lower) <= 5 and table_lower.replace('.', '').isalnum():
            return True

        return False

    def ensure_unified_table_exists(self):
        """確保統一表格存在"""
        if self.config.dry_run:
            logger.info("DRY RUN: 跳過建立統一表格")
            return

        create_table_sql = """
        CREATE TABLE IF NOT EXISTS stock_daily_prices (
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
            PRIMARY KEY (symbol, date),
            INDEX idx_market (market),
            INDEX idx_date (date),
            INDEX idx_symbol_market (symbol, market)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        COMMENT='統一股票日線資料表 - 生產環境'
        PARTITION BY RANGE (YEAR(date)) (
            PARTITION p2015 VALUES LESS THAN (2016),
            PARTITION p2016 VALUES LESS THAN (2017),
            PARTITION p2017 VALUES LESS THAN (2018),
            PARTITION p2018 VALUES LESS THAN (2019),
            PARTITION p2019 VALUES LESS THAN (2020),
            PARTITION p2020 VALUES LESS THAN (2021),
            PARTITION p2021 VALUES LESS THAN (2022),
            PARTITION p2022 VALUES LESS THAN (2023),
            PARTITION p2023 VALUES LESS THAN (2024),
            PARTITION p2024 VALUES LESS THAN (2025),
            PARTITION p_future VALUES LESS THAN MAXVALUE
        );
        """

        cursor = self.connection.cursor()
        try:
            cursor.execute(create_table_sql)
            self.connection.commit()
            logger.info("統一資料表格準備完成")
        except Exception as e:
            logger.error(f"建立統一表格失敗: {e}")
            raise
        finally:
            cursor.close()

    def migrate_table_batched(self, table_name: str) -> bool:
        """分批遷移單個表格"""
        try:
            logger.info(f"=== 開始遷移表格: {table_name} ===")

            # 檢查表格是否存在以及是否有資料
            if not self._table_exists_and_has_data(table_name):
                logger.info(f"表格 {table_name} 不存在或為空，跳過")
                return True

            # 獲取總行數
            total_rows = self._get_table_row_count(table_name)
            logger.info(f"表格 {table_name} 總行數: {total_rows:,}")

            # 計算批次數量
            batch_size = self.config.batch_size
            total_batches = (total_rows + batch_size - 1) // batch_size

            # 從檢查點恢復或從頭開始
            start_batch = 0
            if self.checkpoint_data and self.checkpoint_data.get('table_name') == table_name:
                start_batch = self.checkpoint_data.get('progress', {}).get('current_batch', 0)
                logger.info(f"從批次 {start_batch} 恢復遷移")

            # 分批處理
            for batch_idx in range(start_batch, total_batches):
                if not self._migrate_batch(table_name, batch_idx, batch_size):
                    return False

                # 保存檢查點
                if batch_idx % (self.config.checkpoint_interval // batch_size) == 0:
                    progress = {
                        'current_batch': batch_idx,
                        'total_batches': total_batches,
                        'processed_rows': batch_idx * batch_size
                    }
                    self.save_checkpoint(table_name, batch_idx * batch_size, progress)

            logger.info(f"表格 {table_name} 遷移完成")
            return True

        except Exception as e:
            logger.error(f"遷移表格 {table_name} 失敗: {e}")
            self.stats['errors'] += 1
            return False

    def _table_exists_and_has_data(self, table_name: str) -> bool:
        """檢查表格是否存在且有資料"""
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}` LIMIT 1")
            count = cursor.fetchone()[0]
            return count > 0
        except Exception:
            return False
        finally:
            cursor.close()

    def _get_table_row_count(self, table_name: str) -> int:
        """獲取表格行數"""
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            return cursor.fetchone()[0]
        finally:
            cursor.close()

    def _migrate_batch(self, table_name: str, batch_idx: int, batch_size: int) -> bool:
        """遷移單個批次"""
        offset = batch_idx * batch_size

        for attempt in range(self.config.retry_attempts):
            try:
                # 讀取批次資料
                df = self._read_batch_data(table_name, offset, batch_size)
                if df.empty:
                    return True

                # 轉換資料格式
                migrated_data = self._transform_batch_data(df, table_name)

                # 插入資料
                if not self.config.dry_run:
                    self._insert_batch_data(migrated_data)

                self.stats['rows_migrated'] += len(migrated_data)
                self.stats['batches_processed'] += 1

                logger.info(f"批次 {batch_idx + 1}: 處理 {len(migrated_data)} 行資料")

                return True

            except Exception as e:
                logger.warning(f"批次 {batch_idx + 1} 嘗試 {attempt + 1} 失敗: {e}")
                if attempt < self.config.retry_attempts - 1:
                    time.sleep(self.config.retry_delay)
                else:
                    logger.error(f"批次 {batch_idx + 1} 最終失敗")
                    return False

    def _read_batch_data(self, table_name: str, offset: int, batch_size: int) -> pd.DataFrame:
        """讀取批次資料"""
        query = f"SELECT * FROM `{table_name}` LIMIT {batch_size} OFFSET {offset}"
        return pd.read_sql(query, self.connection)

    def _transform_batch_data(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """轉換批次資料格式"""
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

        existing_columns = {k: v for k, v in column_mapping.items() if k in transformed.columns}
        transformed = transformed.rename(columns=existing_columns)

        # 確保日期格式正確
        if 'date' in transformed.columns:
            transformed['date'] = pd.to_datetime(transformed['date']).dt.date

        return transformed

    def _insert_batch_data(self, df: pd.DataFrame):
        """批次插入資料"""
        if df.empty:
            return

        columns = ['symbol', 'market', 'date', 'open', 'high', 'low', 'close', 'adj_close', 'volume']
        existing_cols = [col for col in columns if col in df.columns]

        placeholders = ', '.join(['%s'] * len(existing_cols))
        columns_str = ', '.join([f'`{col}`' for col in existing_cols])

        insert_sql = f"""
        INSERT INTO stock_daily_prices ({columns_str})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE
        {', '.join([f'`{col}` = VALUES(`{col}`)' for col in existing_cols[3:]])},
        updated_at = CURRENT_TIMESTAMP
        """

        cursor = self.connection.cursor()

        try:
            # 批次處理
            data = [tuple(row) for row in df[existing_cols].values]
            cursor.executemany(insert_sql, data)
            self.connection.commit()

        except Exception as e:
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def _extract_symbol(self, table_name: str) -> str:
        """從表格名稱提取股票代碼"""
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

    def run_production_migration(self) -> bool:
        """執行生產環境遷移"""
        try:
            logger.info("=== 開始生產環境資料遷移 ===")
            self.stats['start_time'] = datetime.now()

            self.connect()
            self.load_checkpoint()
            self.ensure_unified_table_exists()
            self.ensure_ad_index_table_exists()

            migration_queue = self.get_migration_queue()

            if not migration_queue:
                logger.info("沒有需要遷移的表格")
                return True

            success_count = 0
            for table in migration_queue:
                if self.migrate_table_batched(table):
                    success_count += 1
                    self.stats['tables_processed'] += 1
                else:
                    logger.error(f"表格 {table} 遷移失敗，停止遷移")
                    break

            self.stats['end_time'] = datetime.now()

            # 清理檢查點檔案
            if os.path.exists(self.config.checkpoint_file):
                os.remove(self.config.checkpoint_file)

            # 最終統計
            self._log_final_stats(success_count, len(migration_queue))

            return self.stats['errors'] == 0

        except Exception as e:
            logger.error(f"生產環境遷移失敗: {e}")
            return False
        finally:
            if self.connection:
                self.connection.close()

    def _log_final_stats(self, success_count: int, total_count: int):
        """記錄最終統計"""
        duration = self.stats['end_time'] - self.stats['start_time'] if self.stats['end_time'] else timedelta(0)

        logger.info("="*60)
        logger.info("生產環境遷移完成統計")
        logger.info("="*60)
        logger.info(f"總表格數: {total_count}")
        logger.info(f"成功遷移: {success_count}")
        logger.info(f"失敗數: {self.stats['errors']}")
        logger.info(f"總行數: {self.stats['rows_migrated']:,}")
        logger.info(f"總批次: {self.stats['batches_processed']:,}")
        logger.info(f"耗時: {duration}")
        logger.info(f"平均處理速度: {self.stats['rows_migrated'] / duration.total_seconds():.0f} 行/秒" if duration.total_seconds() > 0 else "N/A")
        logger.info("="*60)

def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description='StockHistory 生產環境遷移工具')
    parser.add_argument('--dry-run', action='store_true', help='僅模擬運行，不實際修改資料庫')
    parser.add_argument('--resume', action='store_true', help='從檢查點恢復遷移')
    parser.add_argument('--host', default='localhost', help='資料庫主機')
    parser.add_argument('--port', type=int, default=3307, help='資料庫端口')
    parser.add_argument('--user', default='demo', help='資料庫用戶名')
    parser.add_argument('--password', default='~Demo123', help='資料庫密碼')
    parser.add_argument('--database', default='demo', help='資料庫名稱')
    parser.add_argument('--batch-size', type=int, default=5000, help='批次處理大小')
    parser.add_argument('--max-workers', type=int, default=4, help='並發處理數量')
    parser.add_argument('--checkpoint-interval', type=int, default=10000, help='檢查點間隔')
    parser.add_argument('--retry-attempts', type=int, default=3, help='重試次數')
    parser.add_argument('--retry-delay', type=int, default=5, help='重試延遲（秒）')

    args = parser.parse_args()

    config = ProductionMigrationConfig(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database,
        batch_size=args.batch_size,
        max_workers=args.max_workers,
        checkpoint_interval=args.checkpoint_interval,
        retry_attempts=args.retry_attempts,
        retry_delay=args.retry_delay,
        dry_run=args.dry_run,
        resume_from_checkpoint=args.resume
    )

    migrator = ProductionMigrator(config)
    success = migrator.run_production_migration()

    if success:
        print("✅ 生產環境遷移成功完成")
        return 0
    else:
        print("❌ 生產環境遷移失敗")
        return 1

if __name__ == "__main__":
    sys.exit(main())
