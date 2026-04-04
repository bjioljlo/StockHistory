#!/usr/bin/env python3
"""
直接刪除有問題的記錄腳本
針對無法修正的資料問題，直接刪除這些記錄
"""

import sys
import mysql.connector
from typing import Dict, Any
import logging
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """資料庫配置"""
    host: str = "localhost"
    user: str = "demo"
    password: str = "~Demo123"
    database: str = "demo"
    port: int = 3307

class RecordDeleter:
    """記錄刪除器"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connection = None

    def connect(self):
        """建立資料庫連接"""
        try:
            self.connection = mysql.connector.connect(
                host=self.config.host,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                port=self.config.port,
                autocommit=True  # 自動提交
            )
            logger.info("資料庫連接成功")
        except Exception as e:
            logger.error(f"資料庫連接失敗: {e}")
            raise

    def get_problem_counts(self) -> Dict[str, int]:
        """獲取各類問題記錄的數量"""
        cursor = self.connection.cursor()

        try:
            counts = {}

            # 負數價格記錄
            cursor.execute("""
                SELECT COUNT(*) FROM stock_daily_prices
                WHERE open < 0 OR high < 0 OR low < 0 OR close < 0
            """)
            counts['negative_prices'] = cursor.fetchone()[0]

            # OHLC 邏輯錯誤記錄
            cursor.execute("""
                SELECT COUNT(*) FROM stock_daily_prices
                WHERE NOT (low <= open AND open <= high
                      AND low <= close AND close <= high
                      AND low <= high)
            """)
            counts['ohlc_errors'] = cursor.fetchone()[0]

            # 零成交量記錄
            cursor.execute("""
                SELECT COUNT(*) FROM stock_daily_prices
                WHERE volume = 0
            """)
            counts['zero_volume'] = cursor.fetchone()[0]

            # 總記錄數
            cursor.execute("SELECT COUNT(*) FROM stock_daily_prices")
            counts['total_records'] = cursor.fetchone()[0]

            return counts

        finally:
            cursor.close()

    def delete_negative_price_records(self) -> int:
        """刪除負數價格記錄"""
        cursor = self.connection.cursor()

        try:
            logger.info("刪除負數價格記錄...")

            cursor.execute("""
                DELETE FROM stock_daily_prices
                WHERE open < 0 OR high < 0 OR low < 0 OR close < 0
            """)

            deleted_count = cursor.rowcount
            logger.info(f"已刪除 {deleted_count} 個負數價格記錄")

            return deleted_count

        finally:
            cursor.close()

    def delete_ohlc_error_records(self) -> int:
        """刪除 OHLC 邏輯錯誤記錄"""
        cursor = self.connection.cursor()

        try:
            logger.info("刪除 OHLC 邏輯錯誤記錄...")

            cursor.execute("""
                DELETE FROM stock_daily_prices
                WHERE NOT (low <= open AND open <= high
                      AND low <= close AND close <= high
                      AND low <= high)
            """)

            deleted_count = cursor.rowcount
            logger.info(f"已刪除 {deleted_count} 個 OHLC 邏輯錯誤記錄")

            return deleted_count

        finally:
            cursor.close()

    def delete_excessive_zero_volume_records(self, keep_threshold: int = 1000) -> int:
        """刪除過多的零成交量記錄，保留指定數量的合理記錄"""
        cursor = self.connection.cursor()

        try:
            logger.info(f"清理零成交量記錄，保留 {keep_threshold} 個合理的記錄...")

            # 檢查零成交量記錄總數
            cursor.execute("SELECT COUNT(*) FROM stock_daily_prices WHERE volume = 0")
            total_zero_volume = cursor.fetchone()[0]

            if total_zero_volume <= keep_threshold:
                logger.info(f"零成交量記錄數量 ({total_zero_volume}) 在合理範圍內，無需刪除")
                return 0

            # 刪除超過閾值的零成交量記錄（保留最近更新的記錄）
            # 使用子查詢刪除不在保留範圍內的記錄
            cursor.execute(f"""
                DELETE FROM stock_daily_prices
                WHERE volume = 0
                AND (symbol, date) NOT IN (
                    SELECT symbol, date
                    FROM stock_daily_prices
                    WHERE volume = 0
                    ORDER BY updated_at DESC
                    LIMIT {keep_threshold}
                )
            """)

            deleted_count = cursor.rowcount
            logger.info(f"已刪除 {deleted_count} 個過多的零成交量記錄")

            return deleted_count

        finally:
            cursor.close()

    def run_deletion(self) -> Dict[str, Any]:
        """執行完整的刪除操作"""
        logger.info("=== 開始刪除有問題的記錄 ===")

        try:
            self.connect()

            # 獲取初始統計
            initial_counts = self.get_problem_counts()
            logger.info("初始問題統計:")
            for key, value in initial_counts.items():
                logger.info(f"  {key}: {value:,}")

            # 執行刪除操作
            results = {
                'negative_prices_deleted': self.delete_negative_price_records(),
                'ohlc_errors_deleted': self.delete_ohlc_error_records(),
                'zero_volume_deleted': self.delete_excessive_zero_volume_records()
            }

            # 獲取最終統計
            final_counts = self.get_problem_counts()
            logger.info("最終問題統計:")
            for key, value in final_counts.items():
                logger.info(f"  {key}: {value:,}")

            # 計算總刪除數量
            total_deleted = sum(results.values())
            logger.info(f"總計刪除了 {total_deleted:,} 個有問題的記錄")

            return {
                'initial_counts': initial_counts,
                'final_counts': final_counts,
                'results': results,
                'total_deleted': total_deleted
            }

        except Exception as e:
            logger.error(f"刪除操作失敗: {e}")
            raise
        finally:
            if self.connection:
                self.connection.close()

def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description='直接刪除有問題記錄的工具')
    parser.add_argument('--host', default='localhost', help='資料庫主機')
    parser.add_argument('--port', type=int, default=3307, help='資料庫端口')
    parser.add_argument('--user', default='demo', help='資料庫用戶名')
    parser.add_argument('--password', default='~Demo123', help='資料庫密碼')
    parser.add_argument('--database', default='demo', help='資料庫名稱')
    parser.add_argument('--keep-zero-volume', type=int, default=1000,
                       help='保留的零成交量記錄數量')

    args = parser.parse_args()

    config = DatabaseConfig(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database
    )

    deleter = RecordDeleter(config)

    try:
        results = deleter.run_deletion()

        print("\n=== 刪除操作完成 ===")
        print("刪除統計:")
        print(f"  負數價格記錄: {results['results']['negative_prices_deleted']:,}")
        print(f"  OHLC 邏輯錯誤: {results['results']['ohlc_errors_deleted']:,}")
        print(f"  過多零成交量: {results['results']['zero_volume_deleted']:,}")
        print(f"  總計刪除: {results['total_deleted']:,}")

        print(f"\n剩餘記錄數: {results['final_counts']['total_records']:,}")
        print(f"剩餘問題記錄: {results['final_counts']['negative_prices'] + results['final_counts']['ohlc_errors'] + results['final_counts']['zero_volume']:,}")

        return 0

    except Exception as e:
        print(f"\n[ERROR] 刪除操作失敗: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
