#!/usr/bin/env python3
"""
資料清理腳本
清理和修正遷移後發現的資料問題
"""

import sys
import os
import mysql.connector
from datetime import datetime
from typing import List, Dict, Any
import logging
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CleanupConfig:
    """清理配置"""
    host: str = "localhost"
    user: str = "demo"
    password: str = "~Demo123"
    database: str = "demo"
    port: int = 3307
    dry_run: bool = False

class DataCleaner:
    """資料清理器"""

    def __init__(self, config: CleanupConfig):
        self.config = config
        self.connection = None
        self.stats = {
            'fixed_ohlc': 0,
            'removed_duplicates': 0,
            'fixed_nulls': 0,
            'removed_invalid_dates': 0
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

    def fix_ohlc_logic_errors(self) -> int:
        """修正 OHLC 邏輯錯誤"""
        logger.info("修正 OHLC 邏輯錯誤...")

        cursor = self.connection.cursor()

        try:
            # 找出有 OHLC 邏輯錯誤的記錄
            cursor.execute("""
                SELECT id, symbol, date, open, high, low, close
                FROM stock_daily_prices
                WHERE NOT (low <= open AND open <= high
                      AND low <= close AND close <= high
                      AND low <= high)
            """)

            invalid_records = cursor.fetchall()
            fixed_count = 0

            for record in invalid_records:
                record_id, symbol, date, open_price, high, low, close = record

                # 修正策略：重新計算合理的高低價
                # 使用開盤價和收盤價的範圍來修正
                new_low = min(open_price, close) if open_price and close else (open_price or close or 0)
                new_high = max(open_price, close) if open_price and close else (open_price or close or 0)

                # 確保新計算的值合理
                if new_low > 0 and new_high >= new_low:
                    if not self.config.dry_run:
                        cursor.execute("""
                            UPDATE stock_daily_prices
                            SET low = %s, high = %s
                            WHERE id = %s
                        """, (new_low, new_high, record_id))

                    fixed_count += 1
                    logger.debug(f"修正記錄 {record_id}: {symbol} {date} - low:{low}->{new_low}, high:{high}->{new_high}")

            if not self.config.dry_run and fixed_count > 0:
                self.connection.commit()

            logger.info(f"修正了 {fixed_count} 個 OHLC 邏輯錯誤")
            self.stats['fixed_ohlc'] = fixed_count
            return fixed_count

        finally:
            cursor.close()

    def remove_duplicate_records(self) -> int:
        """移除重複記錄，保留最新的"""
        logger.info("清理重複記錄...")

        cursor = self.connection.cursor()

        try:
            # 找出重複記錄（保留ID最大的，即最新的）
            cursor.execute("""
                SELECT GROUP_CONCAT(id ORDER BY id DESC) as ids,
                       symbol, date, COUNT(*) as count
                FROM stock_daily_prices
                GROUP BY symbol, date
                HAVING count > 1
            """)

            duplicates = cursor.fetchall()
            removed_count = 0

            for ids_str, symbol, date, count in duplicates:
                ids = ids_str.split(',')
                keep_id = ids[0]  # 保留ID最大的
                remove_ids = ids[1:]  # 刪除其他的

                if not self.config.dry_run:
                    # 使用 IN 語句刪除重複記錄
                    placeholders = ','.join(['%s'] * len(remove_ids))
                    cursor.execute(f"""
                        DELETE FROM stock_daily_prices
                        WHERE id IN ({placeholders})
                    """, remove_ids)

                removed_count += len(remove_ids)
                logger.debug(f"清理重複: {symbol} {date} - 保留ID:{keep_id}, 刪除{len(remove_ids)}個")

            if not self.config.dry_run and removed_count > 0:
                self.connection.commit()

            logger.info(f"移除了 {removed_count} 個重複記錄")
            self.stats['removed_duplicates'] = removed_count
            return removed_count

        finally:
            cursor.close()

    def remove_invalid_date_records(self) -> int:
        """移除無效日期記錄"""
        logger.info("清理無效日期記錄...")

        cursor = self.connection.cursor()

        try:
            # 找出無效日期記錄
            cursor.execute("""
                SELECT COUNT(*) as invalid_count
                FROM stock_daily_prices
                WHERE date < '2000-01-01' OR date > CURDATE()
            """)

            invalid_count = cursor.fetchone()[0]

            if invalid_count > 0:
                if not self.config.dry_run:
                    cursor.execute("""
                        DELETE FROM stock_daily_prices
                        WHERE date < '2000-01-01' OR date > CURDATE()
                    """)
                    self.connection.commit()

                logger.info(f"移除了 {invalid_count} 個無效日期記錄")
            else:
                logger.info("沒有發現無效日期記錄")

            self.stats['removed_invalid_dates'] = invalid_count
            return invalid_count

        finally:
            cursor.close()

    def fix_null_values(self) -> int:
        """修正空值（用預設值填補）"""
        logger.info("修正空值...")

        cursor = self.connection.cursor()

        try:
            # 統計各欄位的空值
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN open IS NULL THEN 1 ELSE 0 END) as null_open,
                    SUM(CASE WHEN close IS NULL THEN 1 ELSE 0 END) as null_close,
                    SUM(CASE WHEN high IS NULL THEN 1 ELSE 0 END) as null_high,
                    SUM(CASE WHEN low IS NULL THEN 1 ELSE 0 END) as null_low
                FROM stock_daily_prices
            """)

            null_counts = cursor.fetchone()
            null_open, null_close, null_high, null_low = null_counts

            fixed_count = 0

            # 修正空值策略：用收盤價填補開盤價，用開盤價填補收盤價
            if null_open > 0 or null_close > 0:
                if not self.config.dry_run:
                    cursor.execute("""
                        UPDATE stock_daily_prices
                        SET open = COALESCE(open, close),
                            close = COALESCE(close, open)
                        WHERE open IS NULL OR close IS NULL
                    """)
                fixed_count += null_open + null_close

            # 對於高低價，使用開盤收盤價的平均或其他邏輯
            if null_high > 0 or null_low > 0:
                if not self.config.dry_run:
                    # 用開盤收盤價的最大最小值來估計
                    cursor.execute("""
                        UPDATE stock_daily_prices
                        SET
                            high = COALESCE(high, GREATEST(open, close)),
                            low = COALESCE(low, LEAST(open, close))
                        WHERE high IS NULL OR low IS NULL
                    """)
                fixed_count += null_high + null_low

            if not self.config.dry_run and fixed_count > 0:
                self.connection.commit()

            logger.info(f"修正了 {fixed_count} 個空值")
            self.stats['fixed_nulls'] = fixed_count
            return fixed_count

        finally:
            cursor.close()

    def run_full_cleanup(self) -> Dict[str, Any]:
        """執行完整清理"""
        logger.info("=== 開始資料清理 ===")

        if self.config.dry_run:
            logger.info("DRY RUN 模式：只會顯示要進行的操作，不會實際修改資料")

        try:
            self.connect()

            results = {
                'ohlc_fixed': self.fix_ohlc_logic_errors(),
                'duplicates_removed': self.remove_duplicate_records(),
                'invalid_dates_removed': self.remove_invalid_date_records(),
                'nulls_fixed': self.fix_null_values()
            }

            # 清理後重新分析表格
            cursor = self.connection.cursor()
            cursor.execute("ANALYZE TABLE stock_daily_prices")
            cursor.close()

            logger.info("=== 清理完成統計 ===")
            logger.info(f"修正 OHLC 錯誤: {results['ohlc_fixed']}")
            logger.info(f"移除重複記錄: {results['duplicates_removed']}")
            logger.info(f"移除無效日期: {results['invalid_dates_removed']}")
            logger.info(f"修正空值: {results['nulls_fixed']}")

            total_changes = sum(results.values())
            logger.info(f"總計處理記錄: {total_changes}")

            return results

        except Exception as e:
            logger.error(f"清理失敗: {e}")
            raise
        finally:
            if self.connection:
                self.connection.close()

def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description='資料清理工具')
    parser.add_argument('--dry-run', action='store_true', help='僅模擬運行，不實際修改資料庫')
    parser.add_argument('--host', default='localhost', help='資料庫主機')
    parser.add_argument('--port', type=int, default=3307, help='資料庫端口')
    parser.add_argument('--user', default='demo', help='資料庫用戶名')
    parser.add_argument('--password', default='~Demo123', help='資料庫密碼')
    parser.add_argument('--database', default='demo', help='資料庫名稱')

    args = parser.parse_args()

    config = CleanupConfig(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database,
        dry_run=args.dry_run
    )

    cleaner = DataCleaner(config)

    try:
        results = cleaner.run_full_cleanup()

        if config.dry_run:
            print("\n🔍 DRY RUN 完成 - 這是預估的清理結果")
        else:
            print("\n✅ 資料清理完成")

        print(f"修正 OHLC 錯誤: {results['ohlc_fixed']}")
        print(f"移除重複記錄: {results['duplicates_removed']}")
        print(f"移除無效日期: {results['invalid_dates_removed']}")
        print(f"修正空值: {results['nulls_fixed']}")

        total = sum(results.values())
        if total > 0:
            print(f"\n📊 總計處理了 {total} 筆記錄")
            return 0
        else:
            print("\n✨ 資料已經很乾淨了")
            return 0

    except Exception as e:
        print(f"\n❌ 清理失敗: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
