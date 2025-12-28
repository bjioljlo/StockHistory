"""
StockHistory 備份服務

負責系統資料的自動備份，包括MySQL、MongoDB和Redis資料庫。
支援本地備份和雲端備份。
"""

import os
import subprocess
import datetime
import gzip
import shutil
import logging
from pathlib import Path
import boto3
from azure.storage.blob import BlobServiceClient
import json

class BackupService:
    """備份服務類別"""

    def __init__(self, config_path='config.yml'):
        self.config = self._load_config(config_path)
        self.backup_dir = Path('./backups')
        self.backup_dir.mkdir(exist_ok=True)

        # 設定日誌
        logging.basicConfig(
            filename='logs/backup.log',
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

    def _run_command(self, command, cwd=None):
        """執行系統命令"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300  # 5分鐘超時
            )
            if result.returncode != 0:
                self.logger.error(f"命令執行失敗: {command}")
                self.logger.error(f"錯誤輸出: {result.stderr}")
                return False
            return True
        except subprocess.TimeoutExpired:
            self.logger.error(f"命令執行超時: {command}")
            return False
        except Exception as e:
            self.logger.error(f"命令執行異常: {e}")
            return False

    def backup_mysql(self, date_str):
        """備份MySQL資料庫"""
        self.logger.info("開始備份MySQL資料庫")

        backup_file = self.backup_dir / f"mysql_backup_{date_str}.sql"

        # 使用docker exec執行mysqldump
        command = (
            "docker exec mysqlserver mysqldump "
            f"-u{self.config.get('mysql_user', 'root')} "
            f"-p{self.config.get('mysql_password', '')} "
            f"{self.config.get('mysql_database', 'demo')} "
            "--single-transaction --routines --triggers "
            f"> {backup_file}"
        )

        if self._run_command(command):
            # 壓縮備份檔案
            compressed_file = backup_file.with_suffix('.sql.gz')
            with open(backup_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            backup_file.unlink()  # 刪除未壓縮檔案

            self.logger.info(f"MySQL備份完成: {compressed_file}")
            return compressed_file
        else:
            self.logger.error("MySQL備份失敗")
            return None

    def backup_mongodb(self, date_str):
        """備份MongoDB資料庫"""
        self.logger.info("開始備份MongoDB資料庫")

        backup_dir = self.backup_dir / f"mongodb_backup_{date_str}"

        # 使用docker exec執行mongodump
        command = (
            "docker exec mongoserver mongodump "
            f"--db {self.config.get('mongo_database', 'demo')} "
            f"--out /tmp/mongodb_backup_{date_str}"
        )

        if self._run_command(command):
            # 從容器複製到主機
            copy_command = f"docker cp mongoserver:/tmp/mongodb_backup_{date_str} {backup_dir}"
            if self._run_command(copy_command):
                # 壓縮備份目錄
                compressed_file = self.backup_dir / f"mongodb_backup_{date_str}.tar.gz"
                shutil.make_archive(
                    str(compressed_file.with_suffix('')),
                    'gztar',
                    backup_dir
                )
                shutil.rmtree(backup_dir)  # 刪除未壓縮目錄

                self.logger.info(f"MongoDB備份完成: {compressed_file}")
                return compressed_file
            else:
                self.logger.error("MongoDB備份檔案複製失敗")
                return None
        else:
            self.logger.error("MongoDB備份失敗")
            return None

    def backup_redis(self, date_str):
        """備份Redis資料"""
        self.logger.info("開始備份Redis資料")

        backup_file = self.backup_dir / f"redis_backup_{date_str}.rdb"

        # 從容器複製Redis RDB檔案
        copy_command = f"docker cp redisserver:/data/dump.rdb {backup_file}"

        if self._run_command(copy_command):
            self.logger.info(f"Redis備份完成: {backup_file}")
            return backup_file
        else:
            self.logger.error("Redis備份失敗")
            return None

    def backup_config_files(self, date_str):
        """備份設定檔案"""
        self.logger.info("開始備份設定檔案")

        config_files = ['config.yml', '.env']
        backup_dir = self.backup_dir / f"config_backup_{date_str}"

        backup_dir.mkdir(exist_ok=True)

        for config_file in config_files:
            if os.path.exists(config_file):
                shutil.copy2(config_file, backup_dir / config_file)

        # 壓縮設定檔案
        compressed_file = self.backup_dir / f"config_backup_{date_str}.tar.gz"
        shutil.make_archive(
            str(compressed_file.with_suffix('')),
            'gztar',
            backup_dir
        )
        shutil.rmtree(backup_dir)

        self.logger.info(f"設定檔案備份完成: {compressed_file}")
        return compressed_file

    def upload_to_s3(self, file_path, bucket_name, key_prefix='backups/'):
        """上傳檔案到AWS S3"""
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=self.config.get('aws_access_key_id'),
                aws_secret_access_key=self.config.get('aws_secret_access_key'),
                region_name=self.config.get('aws_region', 'us-east-1')
            )

            key = f"{key_prefix}{file_path.name}"
            s3_client.upload_file(str(file_path), bucket_name, key)
            self.logger.info(f"檔案上傳到S3成功: {key}")
            return True
        except Exception as e:
            self.logger.error(f"S3上傳失敗: {e}")
            return False

    def upload_to_azure(self, file_path, container_name, connection_string):
        """上傳檔案到Azure Blob Storage"""
        try:
            blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            blob_client = blob_service_client.get_blob_client(
                container=container_name,
                blob=f"backups/{file_path.name}"
            )

            with open(file_path, 'rb') as data:
                blob_client.upload_blob(data, overwrite=True)

            self.logger.info(f"檔案上傳到Azure成功: backups/{file_path.name}")
            return True
        except Exception as e:
            self.logger.error(f"Azure上傳失敗: {e}")
            return False

    def cleanup_old_backups(self, retention_days=7):
        """清理舊備份檔案"""
        self.logger.info(f"清理{retention_days}天前的備份檔案")

        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=retention_days)

        for file_path in self.backup_dir.glob("*"):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_date.timestamp():
                file_path.unlink()
                self.logger.info(f"刪除舊備份檔案: {file_path}")

    def run_full_backup(self):
        """執行完整備份"""
        self.logger.info("開始執行完整備份")

        date_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

        backup_files = []

        # 備份各個服務
        mysql_backup = self.backup_mysql(date_str)
        if mysql_backup:
            backup_files.append(mysql_backup)

        mongodb_backup = self.backup_mongodb(date_str)
        if mongodb_backup:
            backup_files.append(mongodb_backup)

        redis_backup = self.backup_redis(date_str)
        if redis_backup:
            backup_files.append(redis_backup)

        config_backup = self.backup_config_files(date_str)
        if config_backup:
            backup_files.append(config_backup)

        # 上傳到雲端
        cloud_config = self.config.get('cloud_backup', {})
        if cloud_config.get('enabled', False):
            provider = cloud_config.get('provider')
            for backup_file in backup_files:
                if provider == 'aws_s3':
                    self.upload_to_s3(
                        backup_file,
                        cloud_config.get('bucket_name'),
                        cloud_config.get('key_prefix', 'backups/')
                    )
                elif provider == 'azure_blob':
                    self.upload_to_azure(
                        backup_file,
                        cloud_config.get('container_name'),
                        cloud_config.get('connection_string')
                    )

        # 清理舊備份
        self.cleanup_old_backups(self.config.get('retention_days', 7))

        self.logger.info("完整備份執行完成")

        # 建立備份報告
        self._create_backup_report(date_str, backup_files)

        return backup_files

    def _create_backup_report(self, date_str, backup_files):
        """建立備份報告"""
        report = {
            'backup_date': date_str,
            'timestamp': datetime.datetime.now().isoformat(),
            'backup_files': [str(f) for f in backup_files],
            'total_size': sum(f.stat().st_size for f in backup_files if f.exists()),
            'status': 'success'
        }

        report_file = self.backup_dir / f"backup_report_{date_str}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        self.logger.info(f"備份報告已建立: {report_file}")


def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description='StockHistory 備份服務')
    parser.add_argument('--config', default='config.yml', help='配置檔案路徑')
    parser.add_argument('--type', choices=['full', 'mysql', 'mongodb', 'redis'],
                       default='full', help='備份類型')

    args = parser.parse_args()

    backup_service = BackupService(args.config)

    if args.type == 'full':
        backup_service.run_full_backup()
    elif args.type == 'mysql':
        date_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_service.backup_mysql(date_str)
    elif args.type == 'mongodb':
        date_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_service.backup_mongodb(date_str)
    elif args.type == 'redis':
        date_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_service.backup_redis(date_str)


if __name__ == '__main__':
    main()
