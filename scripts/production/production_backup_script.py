#!/usr/bin/env python3
"""
StockHistory 生產環境資料庫備份腳本
支援完整備份和增量備份，適用於生產環境遷移前後
"""

import sys
import os
import subprocess
import shutil
from datetime import datetime
from typing import Dict, List, Any
import logging
import json
from dataclasses import dataclass

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('production_backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class BackupConfig:
    """備份配置"""
    host: str = "localhost"
    user: str = "demo"
    password: str = "~Demo123"
    database: str = "demo"
    port: int = 3307
    backup_dir: str = "backups/production"
    retention_days: int = 30
    compression: bool = True
    verify_backup: bool = True

class ProductionBackupManager:
    """生產環境備份管理器"""

    def __init__(self, config: BackupConfig):
        self.config = config
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_path = os.path.join(config.backup_dir, f"backup_{self.timestamp}")
        self.metadata_file = os.path.join(self.backup_path, "backup_metadata.json")

    def create_backup_directory(self):
        """建立備份目錄"""
        os.makedirs(self.backup_path, exist_ok=True)
        logger.info(f"建立備份目錄: {self.backup_path}")

    def get_database_info(self) -> Dict[str, Any]:
        """獲取資料庫資訊"""
        try:
            import mysql.connector

            connection = mysql.connector.connect(
                host=self.config.host,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                port=self.config.port
            )

            cursor = connection.cursor()

            # 獲取表格資訊
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]

            # 獲取資料庫大小
            cursor.execute("""
                SELECT
                    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) as size_mb,
                    COUNT(*) as table_count
                FROM information_schema.tables
                WHERE table_schema = %s
            """, (self.config.database,))

            size_info = cursor.fetchone()

            db_info = {
                'database': self.config.database,
                'tables': tables,
                'total_size_mb': size_info[0],
                'table_count': size_info[1],
                'backup_timestamp': self.timestamp
            }

            cursor.close()
            connection.close()

            return db_info

        except Exception as e:
            logger.error(f"獲取資料庫資訊失敗: {e}")
            raise

    def perform_full_backup(self) -> bool:
        """執行完整備份"""
        logger.info("=== 開始完整資料庫備份 ===")

        try:
            # 建立備份目錄
            self.create_backup_directory()

            # 獲取資料庫資訊
            db_info = self.get_database_info()

            # 使用 mysqldump 進行備份
            dump_file = os.path.join(self.backup_path, "full_backup.sql")

            cmd = [
                "mysqldump",
                f"--host={self.config.host}",
                f"--port={self.config.port}",
                f"--user={self.config.user}",
                f"--password={self.config.password}",
                "--single-transaction",  # 確保一致性
                "--routines",  # 包含存儲過程
                "--triggers",  # 包含觸發器
                "--all-databases" if self.config.database == "all" else self.config.database,
                f"--result-file={dump_file}"
            ]

            # 設定環境變數避免密碼提示
            env = os.environ.copy()
            env['MYSQL_PWD'] = self.config.password

            logger.info(f"執行備份命令: {' '.join(cmd)}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"備份失敗: {result.stderr}")
                return False

            # 壓縮備份檔案
            if self.config.compression:
                compressed_file = dump_file + ".gz"
                self._compress_file(dump_file, compressed_file)
                os.remove(dump_file)  # 刪除未壓縮檔案
                dump_file = compressed_file

            # 保存元資料
            metadata = {
                'backup_type': 'full',
                'timestamp': self.timestamp,
                'database_info': db_info,
                'dump_file': os.path.basename(dump_file),
                'original_size': os.path.getsize(dump_file) if os.path.exists(dump_file) else 0
            }

            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            # 驗證備份
            if self.config.verify_backup:
                if not self._verify_backup(dump_file, metadata):
                    return False

            logger.info("✅ 完整備份成功完成")
            return True

        except Exception as e:
            logger.error(f"備份過程出錯: {e}")
            return False

    def perform_incremental_backup(self, last_backup_path: str = None) -> bool:
        """執行增量備份"""
        logger.info("=== 開始增量資料庫備份 ===")

        try:
            # 建立備份目錄
            self.create_backup_directory()

            # 獲取變更的表格
            changed_tables = self._get_changed_tables(last_backup_path)

            if not changed_tables:
                logger.info("沒有檢測到資料變更，跳過增量備份")
                return True

            # 備份變更的表格
            for table in changed_tables:
                if not self._backup_single_table(table):
                    return False

            # 保存元資料
            metadata = {
                'backup_type': 'incremental',
                'timestamp': self.timestamp,
                'changed_tables': changed_tables,
                'last_backup_path': last_backup_path
            }

            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            logger.info("✅ 增量備份成功完成")
            return True

        except Exception as e:
            logger.error(f"增量備份過程出錯: {e}")
            return False

    def _get_changed_tables(self, last_backup_path: str) -> List[str]:
        """獲取自上次備份以來變更的表格"""
        if not last_backup_path or not os.path.exists(last_backup_path):
            # 如果沒有上次備份，備份所有表格
            return self.get_database_info()['tables']

        try:
            # 讀取上次備份的元資料
            last_metadata_file = os.path.join(last_backup_path, "backup_metadata.json")
            if not os.path.exists(last_metadata_file):
                return self.get_database_info()['tables']

            with open(last_metadata_file, 'r', encoding='utf-8') as f:
                last_metadata = json.load(f)

            last_timestamp = last_metadata.get('timestamp')
            if not last_timestamp:
                return self.get_database_info()['tables']

            # 查詢自上次備份以來有更新的表格
            import mysql.connector
            connection = mysql.connector.connect(
                host=self.config.host,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                port=self.config.port
            )

            cursor = connection.cursor()

            # 檢查哪些表格在指定時間後有更新
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s
                AND update_time > %s
            """, (self.config.database, last_timestamp))

            changed_tables = [row[0] for row in cursor.fetchall()]

            cursor.close()
            connection.close()

            return changed_tables

        except Exception as e:
            logger.warning(f"無法確定變更表格: {e}")
            return self.get_database_info()['tables']

    def _backup_single_table(self, table_name: str) -> bool:
        """備份單個表格"""
        try:
            dump_file = os.path.join(self.backup_path, f"{table_name}.sql")

            cmd = [
                "mysqldump",
                f"--host={self.config.host}",
                f"--port={self.config.port}",
                f"--user={self.config.user}",
                f"--password={self.config.password}",
                self.config.database,
                table_name,
                f"--result-file={dump_file}"
            ]

            env = os.environ.copy()
            env['MYSQL_PWD'] = self.config.password

            result = subprocess.run(cmd, env=env, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"備份表格 {table_name} 失敗: {result.stderr}")
                return False

            # 壓縮
            if self.config.compression:
                compressed_file = dump_file + ".gz"
                self._compress_file(dump_file, compressed_file)
                os.remove(dump_file)

            return True

        except Exception as e:
            logger.error(f"備份表格 {table_name} 出錯: {e}")
            return False

    def _compress_file(self, src_file: str, dst_file: str):
        """壓縮檔案"""
        import gzip
        with open(src_file, 'rb') as f_in:
            with gzip.open(dst_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        logger.info(f"壓縮完成: {src_file} -> {dst_file}")

    def _verify_backup(self, dump_file: str, metadata: Dict[str, Any]) -> bool:
        """驗證備份檔案"""
        try:
            logger.info("驗證備份檔案...")

            # 檢查檔案是否存在
            if not os.path.exists(dump_file):
                logger.error(f"備份檔案不存在: {dump_file}")
                return False

            # 檢查檔案大小
            file_size = os.path.getsize(dump_file)
            if file_size == 0:
                logger.error("備份檔案為空")
                return False

            logger.info(f"備份檔案大小: {file_size:,} bytes")

            # 簡單的語法檢查（如果有 mysql 客戶端）
            try:
                cmd = [
                    "mysql",
                    f"--host={self.config.host}",
                    f"--port={self.config.port}",
                    f"--user={self.config.user}",
                    f"--password={self.config.password}",
                    "--execute=SELECT 1;"
                ]

                env = os.environ.copy()
                env['MYSQL_PWD'] = self.config.password

                result = subprocess.run(cmd, env=env, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning("無法驗證資料庫連接，但備份檔案存在")
                else:
                    logger.info("資料庫連接驗證成功")

            except Exception as e:
                logger.warning(f"無法進行資料庫連接驗證: {e}")

            return True

        except Exception as e:
            logger.error(f"備份驗證失敗: {e}")
            return False

    def cleanup_old_backups(self):
        """清理舊備份"""
        try:
            import glob

            # 獲取所有備份目錄
            backup_pattern = os.path.join(self.config.backup_dir, "backup_*")
            backup_dirs = glob.glob(backup_pattern)

            # 排序並保留最新的備份
            backup_dirs.sort(reverse=True)

            if len(backup_dirs) > self.config.retention_days:
                dirs_to_remove = backup_dirs[self.config.retention_days:]

                for backup_dir in dirs_to_remove:
                    logger.info(f"刪除舊備份: {backup_dir}")
                    shutil.rmtree(backup_dir)

                logger.info(f"清理完成，刪除了 {len(dirs_to_remove)} 個舊備份")

        except Exception as e:
            logger.error(f"清理舊備份失敗: {e}")

    def run_backup(self, backup_type: str = "full", last_backup_path: str = None) -> bool:
        """執行備份"""
        logger.info(f"開始 {backup_type} 備份")

        try:
            if backup_type == "full":
                success = self.perform_full_backup()
            elif backup_type == "incremental":
                success = self.perform_incremental_backup(last_backup_path)
            else:
                logger.error(f"不支援的備份類型: {backup_type}")
                return False

            if success:
                # 清理舊備份
                self.cleanup_old_backups()

                logger.info(f"✅ {backup_type} 備份完成")
                logger.info(f"備份位置: {self.backup_path}")

                return True
            else:
                logger.error(f"❌ {backup_type} 備份失敗")
                return False

        except Exception as e:
            logger.error(f"備份過程出錯: {e}")
            return False

def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description='StockHistory 生產環境備份工具')
    parser.add_argument('--type', choices=['full', 'incremental'], default='full', help='備份類型')
    parser.add_argument('--host', default='localhost', help='資料庫主機')
    parser.add_argument('--port', type=int, default=3307, help='資料庫端口')
    parser.add_argument('--user', default='demo', help='資料庫用戶名')
    parser.add_argument('--password', default='~Demo123', help='資料庫密碼')
    parser.add_argument('--database', default='demo', help='資料庫名稱')
    parser.add_argument('--backup-dir', default='backups/production', help='備份目錄')
    parser.add_argument('--retention-days', type=int, default=30, help='保留天數')
    parser.add_argument('--no-compression', action='store_true', help='不壓縮備份檔案')
    parser.add_argument('--no-verify', action='store_true', help='不驗證備份')
    parser.add_argument('--last-backup', help='上次備份路徑（增量備份時需要）')

    args = parser.parse_args()

    config = BackupConfig(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database,
        backup_dir=args.backup_dir,
        retention_days=args.retention_days,
        compression=not args.no_compression,
        verify_backup=not args.no_verify
    )

    backup_manager = ProductionBackupManager(config)
    success = backup_manager.run_backup(args.type, args.last_backup)

    if success:
        print(f"✅ 備份成功完成: {backup_manager.backup_path}")
        return 0
    else:
        print("❌ 備份失敗")
        return 1

if __name__ == "__main__":
    sys.exit(main())
