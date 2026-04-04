"""
StockHistory 資料歸檔服務

負責將歷史資料歸檔到低成本儲存，包括資料壓縮、移動和清理。
支援自動歸檔排程和手動歸檔操作。
"""

import os
import datetime
import gzip
import shutil
import logging
from pathlib import Path
import json
import argparse
from sqlalchemy import create_engine, text
import pymongo
import redis

class ArchivalService:
    """歸檔服務類別"""

    def __init__(self, config_path='config.yml'):
        self.config = self._load_config(config_path)
        self.archive_dir = Path('./archive')
        self.archive_dir.mkdir(exist_ok=True)

        # 設定日誌
        logging.basicConfig(
            filename='logs/archival.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _load_config(self, config_path):
        """載入配置檔案"""
        import yaml
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"載入配置檔案失敗: {e}")
            return {}

    def _get_mysql_connection(self):
        """獲取MySQL連線"""
        db_config = self.config.get('mysql', {})
        connection_string = (
            f"mysql+pymysql://{db_config.get('user', 'root')}:"
            f"{db_config.get('password', '')}@"
            f"{db_config.get('host', 'localhost')}:"
            f"{db_config.get('port', 3306)}/"
            f"{db_config.get('database', 'demo')}"
        )
        return create_engine(connection_string)

    def _get_mongo_connection(self):
        """獲取MongoDB連線"""
        db_config = self.config.get('mongodb', {})
        client = pymongo.MongoClient(
            host=db_config.get('host', 'localhost'),
            port=db_config.get('port', 27017)
        )
        return client[db_config.get('database', 'demo')]

    def _get_redis_connection(self):
        """獲取Redis連線"""
        db_config = self.config.get('redis', {})
        return redis.Redis(
            host=db_config.get('host', 'localhost'),
            port=db_config.get('port', 6379),
            decode_responses=True
        )

    def archive_mysql_data(self, table_name, date_column, cutoff_date, archive_table_name=None):
        """歸檔MySQL資料表中的舊資料"""
        self.logger.info(f"開始歸檔MySQL資料表 {table_name} 中 {cutoff_date} 之前的資料")

        engine = self._get_mysql_connection()

        try:
            with engine.connect() as conn:
                # 檢查表格是否存在
                result = conn.execute(text(f"SHOW TABLES LIKE '{table_name}'"))
                if not result.fetchone():
                    self.logger.error(f"資料表 {table_name} 不存在")
                    return False

                # 檢查日期欄位是否存在
                result = conn.execute(text(f"DESCRIBE {table_name}"))
                columns = [row[0] for row in result.fetchall()]
                if date_column not in columns:
                    self.logger.error(f"日期欄位 {date_column} 在資料表 {table_name} 中不存在")
                    return False

                # 建立歸檔表格（如果指定）
                if archive_table_name:
                    conn.execute(text(f"CREATE TABLE IF NOT EXISTS {archive_table_name} LIKE {table_name}"))
                    conn.commit()

                # 計算要歸檔的記錄數
                count_query = text(f"SELECT COUNT(*) FROM {table_name} WHERE {date_column} < :cutoff_date")
                result = conn.execute(count_query, {'cutoff_date': cutoff_date})
                record_count = result.fetchone()[0]

                if record_count == 0:
                    self.logger.info(f"沒有找到需要歸檔的資料")
                    return True

                self.logger.info(f"找到 {record_count} 條記錄需要歸檔")

                # 將資料移動到歸檔表格或匯出到檔案
                if archive_table_name:
                    # 移動資料到歸檔表格
                    move_query = text(f"""
                        INSERT INTO {archive_table_name}
                        SELECT * FROM {table_name}
                        WHERE {date_column} < :cutoff_date
                    """)
                    conn.execute(move_query, {'cutoff_date': cutoff_date})

                    # 刪除原始資料
                    delete_query = text(f"DELETE FROM {table_name} WHERE {date_column} < :cutoff_date")
                    conn.execute(delete_query, {'cutoff_date': cutoff_date})

                    conn.commit()
                    self.logger.info(f"成功歸檔 {record_count} 條記錄到 {archive_table_name}")
                else:
                    # 匯出到CSV檔案
                    archive_file = self.archive_dir / f"{table_name}_archive_{datetime.datetime.now().strftime('%Y%m%d')}.csv.gz"
                    export_query = text(f"""
                        SELECT * FROM {table_name}
                        WHERE {date_column} < :cutoff_date
                        INTO OUTFILE :file_path
                        FIELDS TERMINATED BY ','
                        ENCLOSED BY '"'
                        LINES TERMINATED BY '\n'
                    """)

                    # 由於MySQL的限制，我們需要手動匯出
                    select_query = text(f"SELECT * FROM {table_name} WHERE {date_column} < :cutoff_date")
                    result = conn.execute(select_query, {'cutoff_date': cutoff_date})

                    # 將結果寫入壓縮檔案
                    with gzip.open(archive_file, 'wt', encoding='utf-8') as f:
                        # 寫入欄位名稱
                        columns_str = ','.join([f'"{col}"' for col in result.keys()])
                        f.write(columns_str + '\n')

                        # 寫入資料
                        for row in result:
                            row_str = ','.join([f'"{str(val)}"' if val is not None else '""' for val in row])
                            f.write(row_str + '\n')

                    # 刪除已歸檔的資料
                    delete_query = text(f"DELETE FROM {table_name} WHERE {date_column} < :cutoff_date")
                    conn.execute(delete_query, {'cutoff_date': cutoff_date})

                    conn.commit()
                    self.logger.info(f"成功歸檔 {record_count} 條記錄到 {archive_file}")

                return True

        except Exception as e:
            self.logger.error(f"MySQL歸檔失敗: {e}")
            return False
        finally:
            engine.dispose()

    def archive_mongodb_data(self, collection_name, date_field, cutoff_date):
        """歸檔MongoDB集合中的舊資料"""
        self.logger.info(f"開始歸檔MongoDB集合 {collection_name} 中 {date_field} 早於 {cutoff_date} 的資料")

        try:
            db = self._get_mongo_connection()
            collection = db[collection_name]

            # 計算要歸檔的記錄數
            query = {date_field: {'$lt': cutoff_date}}
            record_count = collection.count_documents(query)

            if record_count == 0:
                self.logger.info(f"沒有找到需要歸檔的資料")
                return True

            self.logger.info(f"找到 {record_count} 條記錄需要歸檔")

            # 將資料匯出到檔案
            archive_file = self.archive_dir / f"{collection_name}_archive_{datetime.datetime.now().strftime('%Y%m%d')}.json.gz"

            with gzip.open(archive_file, 'wt', encoding='utf-8') as f:
                documents = collection.find(query)
                for doc in documents:
                    json.dump(doc, f, ensure_ascii=False, default=str)
                    f.write('\n')

            # 刪除已歸檔的資料
            result = collection.delete_many(query)
            self.logger.info(f"成功歸檔並刪除 {result.deleted_count} 條記錄到 {archive_file}")

            return True

        except Exception as e:
            self.logger.error(f"MongoDB歸檔失敗: {e}")
            return False

    def compress_old_logs(self, days_to_compress=30):
        """壓縮舊日誌檔案"""
        self.logger.info(f"開始壓縮 {days_to_compress} 天前的日誌檔案")

        logs_dir = Path('./logs')
        if not logs_dir.exists():
            return

        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_to_compress)

        for log_file in logs_dir.glob("*.log"):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                compressed_file = log_file.with_suffix('.log.gz')

                # 壓縮檔案
                with open(log_file, 'rb') as f_in:
                    with gzip.open(compressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)

                # 刪除原始檔案
                log_file.unlink()

                self.logger.info(f"壓縮日誌檔案: {log_file} -> {compressed_file}")

    def cleanup_old_archives(self, retention_days=365):
        """清理舊歸檔檔案"""
        self.logger.info(f"清理 {retention_days} 天前的歸檔檔案")

        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=retention_days)

        for archive_file in self.archive_dir.glob("*"):
            if archive_file.is_file() and archive_file.stat().st_mtime < cutoff_date.timestamp():
                archive_file.unlink()
                self.logger.info(f"刪除舊歸檔檔案: {archive_file}")

    def run_automated_archival(self):
        """執行自動歸檔"""
        self.logger.info("開始執行自動歸檔")

        # 歸檔MySQL資料（3年前的資料）
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=365*3)
        cutoff_date_str = cutoff_date.strftime('%Y-%m-%d')

        # 獲取所有股票資料表
        engine = self._get_mysql_connection()
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SHOW TABLES"))
                tables = [row[0] for row in result.fetchall()]

                for table in tables:
                    if table.startswith('stock_'):  # 假設股票資料表以stock_開頭
                        archive_table = f"archive_{table}"
                        self.archive_mysql_data(table, 'date', cutoff_date_str, archive_table)
        finally:
            engine.dispose()

        # 歸檔MongoDB資料
        try:
            db = self._get_mongo_connection()
            collections = db.list_collection_names()

            for collection in collections:
                if collection.startswith('stock_'):  # 假設相關集合以stock_開頭
                    self.archive_mongodb_data(collection, 'date', cutoff_date)
        except Exception as e:
            self.logger.error(f"MongoDB歸檔檢查失敗: {e}")

        # 壓縮舊日誌
        self.compress_old_logs()

        # 清理舊歸檔檔案
        self.cleanup_old_archives()

        self.logger.info("自動歸檔執行完成")

    def list_archived_files(self):
        """列出所有歸檔檔案"""
        archive_files = list(self.archive_dir.glob("*"))

        print("歸檔檔案列表:")
        for file in sorted(archive_files, key=lambda x: x.stat().st_mtime, reverse=True):
            size_mb = file.stat().st_size / (1024 * 1024)
            mtime = datetime.datetime.fromtimestamp(file.stat().st_mtime)
            print(".1f")

    def validate_archive_integrity(self, archive_file):
        """驗證歸檔檔案完整性"""
        if not os.path.exists(archive_file):
            return False, "檔案不存在"

        try:
            if archive_file.endswith('.gz'):
                with gzip.open(archive_file, 'rb') as f:
                    f.read(1024)  # 嘗試讀取前1KB
            else:
                with open(archive_file, 'rb') as f:
                    f.read(1024)  # 讀取前1KB

            return True, "檔案完整"
        except Exception as e:
            return False, f"檔案損壞: {str(e)}"

    def get_archival_stats(self):
        """獲取歸檔統計資訊"""
        stats = {
            'total_files': 0,
            'total_size': 0,
            'oldest_file': None,
            'newest_file': None,
            'file_types': {}
        }

        for file in self.archive_dir.glob("*"):
            if file.is_file():
                stats['total_files'] += 1
                stats['total_size'] += file.stat().st_size

                file_ext = file.suffix.lower()
                if file_ext not in stats['file_types']:
                    stats['file_types'][file_ext] = 0
                stats['file_types'][file_ext] += 1

                file_mtime = file.stat().st_mtime
                if stats['oldest_file'] is None or file_mtime < stats['oldest_file']:
                    stats['oldest_file'] = file_mtime
                if stats['newest_file'] is None or file_mtime > stats['newest_file']:
                    stats['newest_file'] = file_mtime

        # 轉換時間戳為可讀格式
        if stats['oldest_file']:
            stats['oldest_file'] = datetime.datetime.fromtimestamp(stats['oldest_file']).isoformat()
        if stats['newest_file']:
            stats['newest_file'] = datetime.datetime.fromtimestamp(stats['newest_file']).isoformat()

        # 轉換大小為MB
        stats['total_size_mb'] = stats['total_size'] / (1024 * 1024)

        return stats


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='StockHistory 歸檔服務')
    parser.add_argument('--config', default='config.yml', help='配置檔案路徑')
    parser.add_argument('--mysql-table', help='MySQL資料表名稱')
    parser.add_argument('--mysql-date-column', default='date', help='日期欄位名稱')
    parser.add_argument('--cutoff-date', help='截止日期 (YYYY-MM-DD)')
    parser.add_argument('--mongodb-collection', help='MongoDB集合名稱')
    parser.add_argument('--mongodb-date-field', default='date', help='日期欄位名稱')
    parser.add_argument('--auto', action='store_true', help='執行自動歸檔')
    parser.add_argument('--list', action='store_true', help='列出歸檔檔案')
    parser.add_argument('--stats', action='store_true', help='顯示歸檔統計')
    parser.add_argument('--validate', help='驗證歸檔檔案完整性')
    parser.add_argument('--compress-logs', action='store_true', help='壓縮舊日誌檔案')

    args = parser.parse_args()

    archival_service = ArchivalService(args.config)

    if args.list:
        archival_service.list_archived_files()
    elif args.stats:
        stats = archival_service.get_archival_stats()
        print("歸檔統計資訊:")
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    elif args.validate:
        is_valid, message = archival_service.validate_archive_integrity(args.validate)
        print(f"驗證結果: {'通過' if is_valid else '失敗'} - {message}")
    elif args.compress_logs:
        archival_service.compress_old_logs()
    elif args.auto:
        archival_service.run_automated_archival()
    elif args.mysql_table and args.cutoff_date:
        archive_table = f"archive_{args.mysql_table}"
        archival_service.archive_mysql_data(
            args.mysql_table,
            args.mysql_date_column,
            args.cutoff_date,
            archive_table
        )
    elif args.mongodb_collection and args.cutoff_date:
        cutoff_datetime = datetime.datetime.fromisoformat(args.cutoff_date)
        archival_service.archive_mongodb_data(
            args.mongodb_collection,
            args.mongodb_date_field,
            cutoff_datetime
        )
    else:
        print("請指定操作參數。使用 --help 查看可用選項。")


if __name__ == '__main__':
    main()
