#!/usr/bin/env python3
"""
資料庫分區管理工具
用於管理 stock_daily_prices 表格的分區
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
class PartitionConfig:
    """分區配置"""
    host: str = "localhost"
    user: str = "demo"
    password: str = "~Demo123"
    database: str = "demo"
    port: int = 3307

class PartitionManager:
    """分區管理器"""

    def __init__(self, config: PartitionConfig):
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
                port=self.config.port
            )
            logger.info("資料庫連接成功")
        except Exception as e:
            logger.error(f"資料庫連接失敗: {e}")
            raise

    def check_partition_status(self) -> Dict[str, Any]:
        """檢查分區狀態"""
        logger.info("檢查分區狀態...")

        cursor = self.connection.cursor()

        try:
            # 檢查表格是否有分區
            cursor.execute("""
                SELECT COUNT(*) as partition_count
                FROM information_schema.partitions
                WHERE table_schema = %s AND table_name = 'stock_daily_prices'
            """, (self.config.database,))

            partition_count = cursor.fetchone()[0]

            if partition_count == 0:
                return {'partitioned': False, 'message': '表格未分區'}

            # 獲取分區資訊
            cursor.execute("""
                SELECT partition_name, partition_description, table_rows
                FROM information_schema.partitions
                WHERE table_schema = %s AND table_name = 'stock_daily_prices'
                ORDER BY partition_ordinal_position
            """, (self.config.database,))

            partitions = cursor.fetchall()

            partition_info = []
            total_rows = 0
            for partition in partitions:
                name, description, rows = partition
                partition_info.append({
                    'name': name,
                    'description': description,
                    'rows': rows
                })
                total_rows += rows

            return {
                'partitioned': True,
                'total_partitions': len(partitions),
                'total_rows': total_rows,
                'partitions': partition_info
            }

        finally:
            cursor.close()

    def add_new_year_partition(self, year: int):
        """添加新年份分區"""
        logger.info(f"添加 {year} 年分區...")

        cursor = self.connection.cursor()

        try:
            # 重新組織分區，添加新年份
            alter_sql = f"""
            ALTER TABLE stock_daily_prices
            ADD PARTITION (PARTITION p{year} VALUES LESS THAN ({year + 1}))
            """

            cursor.execute(alter_sql)
            self.connection.commit()

            logger.info(f"成功添加 {year} 年分區")

        except Exception as e:
            logger.error(f"添加分區失敗: {e}")
            raise
        finally:
            cursor.close()

    def reorganize_partitions(self, current_year: int):
        """重新組織分區，添加未來年份"""
        logger.info("重新組織分區...")

        cursor = self.connection.cursor()

        try:
            # 重新定義所有分區
            partitions = []
            for year in range(2015, current_year + 3):  # 到後年
                partitions.append(f"PARTITION p{year} VALUES LESS THAN ({year + 1})")
            partitions.append("PARTITION p_future VALUES LESS THAN MAXVALUE")

            alter_sql = f"""
            ALTER TABLE stock_daily_prices
            PARTITION BY RANGE (YEAR(date)) (
                {', '.join(partitions)}
            )
            """

            cursor.execute(alter_sql)
            self.connection.commit()

            logger.info("分區重新組織完成")

        except Exception as e:
            logger.error(f"重新組織分區失敗: {e}")
            raise
        finally:
            cursor.close()

    def optimize_partitions(self):
        """優化分區效能"""
        logger.info("優化分區...")

        cursor = self.connection.cursor()

        try:
            # 分析分區
            cursor.execute("ANALYZE TABLE stock_daily_prices")
            logger.info("分區分析完成")

            # 優化分區（如果支援）
            try:
                cursor.execute("OPTIMIZE TABLE stock_daily_prices")
                logger.info("分區優化完成")
            except Exception as e:
                logger.warning(f"OPTIMIZE TABLE 不支援: {e}")

        finally:
            cursor.close()

    def get_partition_statistics(self) -> Dict[str, Any]:
        """獲取分區統計資訊"""
        logger.info("獲取分區統計...")

        cursor = self.connection.cursor()

        try:
            stats = {}

            # 各分區資料量
            cursor.execute("""
                SELECT partition_name, table_rows, data_length, index_length
                FROM information_schema.partitions
                WHERE table_schema = %s AND table_name = 'stock_daily_prices'
                ORDER BY partition_ordinal_position
            """, (self.config.database,))

            partitions = cursor.fetchall()
            stats['partition_stats'] = []

            for partition in partitions:
                name, rows, data_len, idx_len = partition
                stats['partition_stats'].append({
                    'partition': name,
                    'rows': rows,
                    'data_size_mb': round(data_len / (1024 * 1024), 2) if data_len else 0,
                    'index_size_mb': round(idx_len / (1024 * 1024), 2) if idx_len else 0
                })

            # 查詢效能測試
            cursor.execute("SELECT COUNT(*) FROM stock_daily_prices PARTITION (p2023)")
            p2023_count = cursor.fetchone()[0]
            stats['sample_query'] = f"p2023 分區有 {p2023_count} 行資料"

            return stats

        finally:
            cursor.close()

    def create_partition_maintenance_procedures(self):
        """建立分區維護預存程序"""
        logger.info("建立分區維護預存程序...")

        cursor = self.connection.cursor()

        procedures = [
            # 自動添加下一年分區的程序
            """
            CREATE PROCEDURE add_next_year_partition()
            BEGIN
                DECLARE next_year INT;
                SET next_year = YEAR(CURDATE()) + 1;

                SET @sql = CONCAT(
                    'ALTER TABLE stock_daily_prices ADD PARTITION (PARTITION p',
                    next_year,
                    ' VALUES LESS THAN (',
                    next_year + 1,
                    '))'
                );

                PREPARE stmt FROM @sql;
                EXECUTE stmt;
                DEALLOCATE PREPARE stmt;
            END
            """,

            # 清理舊分區的程序（保留最近5年）
            """
            CREATE PROCEDURE cleanup_old_partitions()
            BEGIN
                DECLARE cutoff_year INT;
                SET cutoff_year = YEAR(CURDATE()) - 5;

                -- 獲取要刪除的分區名稱
                SELECT GROUP_CONCAT(partition_name) INTO @partitions_to_drop
                FROM information_schema.partitions
                WHERE table_schema = DATABASE()
                  AND table_name = 'stock_daily_prices'
                  AND partition_name REGEXP '^p[0-9]+$'
                  AND CAST(SUBSTRING(partition_name, 2) AS UNSIGNED) < cutoff_year;

                IF @partitions_to_drop IS NOT NULL THEN
                    SET @sql = CONCAT('ALTER TABLE stock_daily_prices DROP PARTITION ', @partitions_to_drop);
                    PREPARE stmt FROM @sql;
                    EXECUTE stmt;
                    DEALLOCATE PREPARE stmt;
                END IF;
            END
            """
        ]

        try:
            for procedure in procedures:
                try:
                    cursor.execute(procedure)
                    self.connection.commit()
                    logger.info("預存程序建立成功")
                except Exception as e:
                    logger.warning(f"預存程序建立失敗: {e}")

        finally:
            cursor.close()

    def print_partition_report(self, status: Dict[str, Any], stats: Dict[str, Any] = None):
        """列印分區報告"""
        print("\n" + "="*60)
        print("📊 分區管理報告")
        print("="*60)

        if not status.get('partitioned', False):
            print(f"❌ {status.get('message', '表格未分區')}")
            print("\n💡 建議:")
            print("  1. 執行遷移腳本建立分區表格")
            print("  2. 或手動添加分區到現有表格")
            return

        print(f"✅ 表格已分區: {status['total_partitions']} 個分區")
        print(f"📈 總資料量: {status['total_rows']:,} 行")

        print("\n📋 分區詳情:")
        for partition in status['partitions']:
            print(f"  {partition['name']}: {partition['rows']:,} 行")

        if stats and 'partition_stats' in stats:
            print("\n💾 分區大小統計:")
            for stat in stats['partition_stats']:
                total_size = stat['data_size_mb'] + stat['index_size_mb']
                print(f"  {stat['partition']}: {total_size:.1f}MB ({stat['rows']:,} 行)")

        if stats and 'sample_query' in stats:
            print(f"\n⚡ 效能測試: {stats['sample_query']}")

        print("\n🛠️ 維護建議:")
        print("  • 每年年初檢查並添加下一年分區")
        print("  • 定期清理5年前的舊資料")
        print("  • 監控分區大小和查詢效能")

        print("\n" + "="*60)

def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description='資料庫分區管理工具')
    parser.add_argument('action', choices=['status', 'add_year', 'reorganize', 'optimize', 'create_procedures'],
                       help='執行的動作')
    parser.add_argument('--year', type=int, help='要添加的年份 (用於 add_year)')
    parser.add_argument('--host', default='localhost', help='資料庫主機')
    parser.add_argument('--port', type=int, default=3307, help='資料庫端口')
    parser.add_argument('--user', default='demo', help='資料庫用戶名')
    parser.add_argument('--password', default='~Demo123', help='資料庫密碼')
    parser.add_argument('--database', default='demo', help='資料庫名稱')

    args = parser.parse_args()

    config = PartitionConfig(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database
    )

    manager = PartitionManager(config)

    try:
        manager.connect()

        if args.action == 'status':
            status = manager.check_partition_status()
            stats = manager.get_partition_statistics() if status.get('partitioned') else None
            manager.print_partition_report(status, stats)

        elif args.action == 'add_year':
            if not args.year:
                print("❌ 需要指定年份: --year YYYY")
                return 1
            manager.add_new_year_partition(args.year)
            print(f"✅ 成功添加 {args.year} 年分區")

        elif args.action == 'reorganize':
            current_year = datetime.now().year
            manager.reorganize_partitions(current_year)
            print("✅ 分區重新組織完成")

        elif args.action == 'optimize':
            manager.optimize_partitions()
            print("✅ 分區優化完成")

        elif args.action == 'create_procedures':
            manager.create_partition_maintenance_procedures()
            print("✅ 維護預存程序建立完成")

        return 0

    except Exception as e:
        print(f"❌ 操作失敗: {e}")
        return 1
    finally:
        if manager.connection:
            manager.connection.close()

if __name__ == "__main__":
    sys.exit(main())
