import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from sqlalchemy import text, inspect
import threading
import time

logger = logging.getLogger(__name__)

class DataCleanupService:
    """
    資料清理服務 - 定期清理無效或重複的資料
    """

    def __init__(self, sql_service, mongo_service=None, config: Dict[str, Any] = None):
        self.sql_service = sql_service
        self.mongo_service = mongo_service
        self.config = config or {}
        self.cleanup_interval_days = self.config.get('data_processing', {}).get('cleanup_interval_days', 30)
        self.is_running = False
        self.cleanup_thread = None

    def start_cleanup_scheduler(self):
        """啟動定期清理排程"""
        if self.is_running:
            logger.warning("Cleanup scheduler is already running")
            return

        self.is_running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_scheduler_loop, daemon=True)
        self.cleanup_thread.start()
        logger.info("Data cleanup scheduler started")

    def stop_cleanup_scheduler(self):
        """停止定期清理排程"""
        self.is_running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
        logger.info("Data cleanup scheduler stopped")

    def _cleanup_scheduler_loop(self):
        """清理排程循環"""
        while self.is_running:
            try:
                self.perform_full_cleanup()
            except Exception as e:
                logger.error(f"Error during scheduled cleanup: {e}")

            # 等待下一個清理間隔
            time.sleep(self.cleanup_interval_days * 24 * 60 * 60)  # 轉換為秒

    def perform_full_cleanup(self):
        """執行完整的資料清理"""
        logger.info("Starting full data cleanup...")

        try:
            # 清理MySQL資料
            mysql_cleaned = self._cleanup_mysql_data()

            # 清理MongoDB資料（如果有）
            mongo_cleaned = 0
            if self.mongo_service:
                mongo_cleaned = self._cleanup_mongo_data()

            logger.info(f"Full cleanup completed. MySQL: {mysql_cleaned} records cleaned, MongoDB: {mongo_cleaned} records cleaned")

        except Exception as e:
            logger.error(f"Error during full cleanup: {e}")

    def _cleanup_mysql_data(self) -> int:
        """清理MySQL資料"""
        total_cleaned = 0

        try:
            with self.sql_service.server_flask.app_context():
                with self.sql_service.MySql_server.engine.connect() as connection:
                    # 獲取所有表格
                    inspector = inspect(connection)
                    table_names = inspector.get_table_names()

                    for table_name in table_names:
                        try:
                            cleaned_count = self._cleanup_single_table(connection, table_name)
                            total_cleaned += cleaned_count
                            if cleaned_count > 0:
                                logger.info(f"Cleaned {cleaned_count} records from table {table_name}")
                        except Exception as e:
                            logger.error(f"Error cleaning table {table_name}: {e}")

        except Exception as e:
            logger.error(f"Error during MySQL cleanup: {e}")

        return total_cleaned

    def _cleanup_single_table(self, connection, table_name: str) -> int:
        """清理單個表格"""
        cleaned_count = 0

        try:
            # 檢查是否為股票資料表（不清理系統表）
            if not self._is_stock_table(table_name):
                return 0

            with connection.begin():
                # 1. 移除重複的日期記錄，保留最新的
                duplicate_query = text(f"""
                    DELETE t1 FROM `{table_name}` t1
                    INNER JOIN `{table_name}` t2
                    WHERE t1.Date < t2.Date AND t1.Date = t2.Date
                """)
                result = connection.execute(duplicate_query)
                cleaned_count += result.rowcount

                # 2. 移除無效的價格資料（負數或極端值）
                invalid_price_query = text(f"""
                    DELETE FROM `{table_name}`
                    WHERE Open <= 0 OR High <= 0 OR Low <= 0 OR Close <= 0
                       OR Volume < 0
                       OR High < Low
                       OR ABS((Close - Open) / NULLIF(Open, 0)) > 0.5  -- 單日漲跌幅超過50%
                """)
                result = connection.execute(invalid_price_query)
                cleaned_count += result.rowcount

                # 3. 移除過期的資料（可選，根據配置）
                if self.config.get('app', {}).get('enable_data_archiving', False):
                    cutoff_date = datetime.now() - timedelta(days=365*10)  # 保留10年資料
                    archive_query = text(f"""
                        DELETE FROM `{table_name}`
                        WHERE Date < :cutoff_date
                    """)
                    result = connection.execute(archive_query, {'cutoff_date': cutoff_date})
                    cleaned_count += result.rowcount

                # 4. 優化表格
                connection.execute(text(f"OPTIMIZE TABLE `{table_name}`"))

        except Exception as e:
            logger.error(f"Error cleaning table {table_name}: {e}")

        return cleaned_count

    def _cleanup_mongo_data(self) -> int:
        """清理MongoDB資料"""
        total_cleaned = 0

        try:
            # MongoDB清理邏輯（如果需要）
            # 這裡可以添加MongoDB特定的清理邏輯
            pass
        except Exception as e:
            logger.error(f"Error during MongoDB cleanup: {e}")

        return total_cleaned

    def _is_stock_table(self, table_name: str) -> bool:
        """判斷是否為股票資料表"""
        # 股票表名通常以股票代碼命名，不包含特殊字元
        if table_name.startswith(('backup_', 'temp_', 'system_')):
            return False

        # 檢查是否包含股票代碼特徵（數字+字母組合）
        import re
        if re.match(r'^[a-zA-Z0-9]+$', table_name):
            return True

        return False

    def cleanup_old_data(self, days_to_keep: int = 365*5) -> int:
        """清理舊資料（超過指定天數的資料）"""
        total_cleaned = 0
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        try:
            with self.sql_service.server_flask.app_context():
                with self.sql_service.MySql_server.engine.connect() as connection:
                    inspector = inspect(connection)
                    table_names = inspector.get_table_names()

                    for table_name in table_names:
                        if self._is_stock_table(table_name):
                            try:
                                with connection.begin():
                                    delete_query = text(f"""
                                        DELETE FROM `{table_name}`
                                        WHERE Date < :cutoff_date
                                    """)
                                    result = connection.execute(delete_query, {'cutoff_date': cutoff_date})
                                    cleaned_count = result.rowcount
                                    total_cleaned += cleaned_count

                                    if cleaned_count > 0:
                                        logger.info(f"Cleaned {cleaned_count} old records from {table_name}")

                            except Exception as e:
                                logger.error(f"Error cleaning old data from {table_name}: {e}")

        except Exception as e:
            logger.error(f"Error during old data cleanup: {e}")

        logger.info(f"Old data cleanup completed. Total records cleaned: {total_cleaned}")
        return total_cleaned

    def remove_duplicate_records(self) -> int:
        """移除所有表格中的重複記錄"""
        total_cleaned = 0

        try:
            with self.sql_service.server_flask.app_context():
                with self.sql_service.MySql_server.engine.connect() as connection:
                    inspector = inspect(connection)
                    table_names = inspector.get_table_names()

                    for table_name in table_names:
                        if self._is_stock_table(table_name):
                            try:
                                with connection.begin():
                                    # 創建臨時表存儲唯一的記錄
                                    dedup_query = text(f"""
                                        CREATE TEMPORARY TABLE temp_{table_name} AS
                                        SELECT DISTINCT * FROM `{table_name}`
                                        ORDER BY Date DESC;

                                        DELETE FROM `{table_name}`;

                                        INSERT INTO `{table_name}`
                                        SELECT * FROM temp_{table_name};

                                        DROP TEMPORARY TABLE temp_{table_name};
                                    """)

                                    # 由於SQLAlchemy對多語句支援有限，分別執行
                                    connection.execute(text(f"CREATE TEMPORARY TABLE temp_{table_name} AS SELECT DISTINCT * FROM `{table_name}` ORDER BY Date DESC"))
                                    connection.execute(text(f"SELECT COUNT(*) FROM `{table_name}`"))
                                    original_count = connection.execute(text(f"SELECT COUNT(*) FROM `{table_name}`")).scalar()

                                    connection.execute(text(f"DELETE FROM `{table_name}`"))
                                    connection.execute(text(f"INSERT INTO `{table_name}` SELECT * FROM temp_{table_name}`"))
                                    connection.execute(text(f"DROP TEMPORARY TABLE temp_{table_name}`"))

                                    new_count = connection.execute(text(f"SELECT COUNT(*) FROM `{table_name}`")).scalar()
                                    cleaned_count = original_count - new_count
                                    total_cleaned += cleaned_count

                                    if cleaned_count > 0:
                                        logger.info(f"Removed {cleaned_count} duplicate records from {table_name}")

                            except Exception as e:
                                logger.error(f"Error removing duplicates from {table_name}: {e}")

        except Exception as e:
            logger.error(f"Error during duplicate removal: {e}")

        logger.info(f"Duplicate removal completed. Total records cleaned: {total_cleaned}")
        return total_cleaned

    def optimize_database(self):
        """優化資料庫效能"""
        try:
            with self.sql_service.server_flask.app_context():
                with self.sql_service.MySql_server.engine.connect() as connection:
                    # 分析所有表格
                    inspector = inspect(connection)
                    table_names = inspector.get_table_names()

                    for table_name in table_names:
                        if self._is_stock_table(table_name):
                            try:
                                connection.execute(text(f"ANALYZE TABLE `{table_name}`"))
                                connection.execute(text(f"OPTIMIZE TABLE `{table_name}`"))
                                logger.info(f"Optimized table {table_name}")
                            except Exception as e:
                                logger.error(f"Error optimizing table {table_name}: {e}")

            logger.info("Database optimization completed")

        except Exception as e:
            logger.error(f"Error during database optimization: {e}")

    def get_cleanup_stats(self) -> Dict[str, Any]:
        """獲取清理統計資訊"""
        stats = {
            'total_tables': 0,
            'total_records': 0,
            'oldest_record': None,
            'newest_record': None,
            'tables_with_duplicates': 0
        }

        try:
            with self.sql_service.server_flask.app_context():
                with self.sql_service.MySql_server.engine.connect() as connection:
                    inspector = inspect(connection)
                    table_names = inspector.get_table_names()
                    stats['total_tables'] = len([t for t in table_names if self._is_stock_table(t)])

                    for table_name in table_names:
                        if self._is_stock_table(table_name):
                            try:
                                # 獲取記錄數
                                count_query = text(f"SELECT COUNT(*) FROM `{table_name}`")
                                count = connection.execute(count_query).scalar()
                                stats['total_records'] += count

                                # 獲取日期範圍
                                date_query = text(f"SELECT MIN(Date), MAX(Date) FROM `{table_name}`")
                                result = connection.execute(date_query).first()
                                if result and result[0]:
                                    if stats['oldest_record'] is None or result[0] < stats['oldest_record']:
                                        stats['oldest_record'] = result[0]
                                    if stats['newest_record'] is None or result[1] > stats['newest_record']:
                                        stats['newest_record'] = result[1]

                                # 檢查重複記錄
                                dup_query = text(f"""
                                    SELECT COUNT(*) - COUNT(DISTINCT Date) as duplicates
                                    FROM `{table_name}`
                                """)
                                duplicates = connection.execute(dup_query).scalar()
                                if duplicates > 0:
                                    stats['tables_with_duplicates'] += 1

                            except Exception as e:
                                logger.error(f"Error getting stats for table {table_name}: {e}")

        except Exception as e:
            logger.error(f"Error getting cleanup stats: {e}")

        return stats
