"""
StockHistory 恢復服務

負責從備份檔案恢復系統資料，包括MySQL、MongoDB和Redis資料庫。
支援完整恢復和部分恢復。
"""

import os
import subprocess
import datetime
import gzip
import tarfile
import shutil
import logging
from pathlib import Path
import json
import argparse

class RestoreService:
    """恢復服務類別"""

    def __init__(self, config_path='config.yml'):
        self.config = self._load_config(config_path)
        self.backup_dir = Path('./backups')

        # 設定日誌
        logging.basicConfig(
            filename='logs/restore.log',
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
                timeout=600  # 10分鐘超時
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

    def restore_mysql(self, backup_file):
        """從備份檔案恢復MySQL資料庫"""
        self.logger.info(f"開始從 {backup_file} 恢復MySQL資料庫")

        if not os.path.exists(backup_file):
            self.logger.error(f"備份檔案不存在: {backup_file}")
            return False

        # 如果是壓縮檔案，先解壓縮
        if backup_file.endswith('.gz'):
            decompressed_file = backup_file[:-3]  # 移除.gz
            with gzip.open(backup_file, 'rb') as f_in:
                with open(decompressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            backup_file = decompressed_file

        # 使用docker exec執行mysql還原
        command = (
            "docker exec -i mysqlserver mysql "
            f"-u{self.config.get('mysql_user', 'root')} "
            f"-p{self.config.get('mysql_password', '')} "
            f"{self.config.get('mysql_database', 'demo')} "
            f"< {backup_file}"
        )

        success = self._run_command(command)

        if success:
            self.logger.info("MySQL資料庫恢復完成")
        else:
            self.logger.error("MySQL資料庫恢復失敗")

        # 清理臨時檔案
        if backup_file.endswith('.sql') and backup_file != backup_file + '.gz':
            os.unlink(backup_file)

        return success

    def restore_mongodb(self, backup_file):
        """從備份檔案恢復MongoDB資料庫"""
        self.logger.info(f"開始從 {backup_file} 恢復MongoDB資料庫")

        if not os.path.exists(backup_file):
            self.logger.error(f"備份檔案不存在: {backup_file}")
            return False

        # 如果是壓縮檔案，先解壓縮
        if backup_file.endswith('.tar.gz'):
            extract_dir = backup_file[:-7]  # 移除.tar.gz
            with tarfile.open(backup_file, 'r:gz') as tar:
                tar.extractall(extract_dir)

            # 複製到容器
            copy_command = f"docker cp {extract_dir} mongoserver:/tmp/restore_mongo"
            if not self._run_command(copy_command):
                self.logger.error("MongoDB備份檔案複製到容器失敗")
                return False

            # 使用docker exec執行mongorestore
            restore_command = (
                "docker exec mongoserver mongorestore "
                f"--db {self.config.get('mongo_database', 'demo')} "
                "--drop "  # 先刪除現有資料
                "/tmp/restore_mongo"
            )

            success = self._run_command(restore_command)

            # 清理容器臨時檔案
            clean_command = "docker exec mongoserver rm -rf /tmp/restore_mongo"
            self._run_command(clean_command)

            # 清理本地臨時檔案
            shutil.rmtree(extract_dir)

        else:
            self.logger.error(f"不支援的MongoDB備份檔案格式: {backup_file}")
            return False

        if success:
            self.logger.info("MongoDB資料庫恢復完成")
        else:
            self.logger.error("MongoDB資料庫恢復失敗")

        return success

    def restore_redis(self, backup_file):
        """從備份檔案恢復Redis資料"""
        self.logger.info(f"開始從 {backup_file} 恢復Redis資料")

        if not os.path.exists(backup_file):
            self.logger.error(f"備份檔案不存在: {backup_file}")
            return False

        # 複製RDB檔案到容器
        copy_command = f"docker cp {backup_file} redisserver:/data/dump.rdb"

        if self._run_command(copy_command):
            # 重啟Redis服務以載入新資料
            restart_command = "docker restart redisserver"
            if self._run_command(restart_command):
                self.logger.info("Redis資料恢復完成")
                return True
            else:
                self.logger.error("Redis服務重啟失敗")
                return False
        else:
            self.logger.error("Redis備份檔案複製失敗")
            return False

    def restore_config_files(self, backup_file):
        """恢復設定檔案"""
        self.logger.info(f"開始從 {backup_file} 恢復設定檔案")

        if not os.path.exists(backup_file):
            self.logger.error(f"備份檔案不存在: {backup_file}")
            return False

        # 解壓縮設定檔案
        if backup_file.endswith('.tar.gz'):
            extract_dir = backup_file[:-7]  # 移除.tar.gz
            with tarfile.open(backup_file, 'r:gz') as tar:
                tar.extractall(extract_dir)

            # 恢復設定檔案
            config_files = ['config.yml', '.env']
            for config_file in config_files:
                src_file = os.path.join(extract_dir, config_file)
                if os.path.exists(src_file):
                    shutil.copy2(src_file, f"{config_file}.backup")
                    self.logger.info(f"設定檔案已備份到: {config_file}.backup")

            # 清理臨時檔案
            shutil.rmtree(extract_dir)
            self.logger.info("設定檔案恢復完成")
            return True
        else:
            self.logger.error(f"不支援的設定檔案格式: {backup_file}")
            return False

    def find_backup_files(self, date_str=None):
        """查找備份檔案"""
        backup_files = {}

        if date_str:
            # 查找特定日期的備份
            mysql_pattern = f"mysql_backup_{date_str}.sql.gz"
            mongo_pattern = f"mongodb_backup_{date_str}.tar.gz"
            redis_pattern = f"redis_backup_{date_str}.rdb"
            config_pattern = f"config_backup_{date_str}.tar.gz"
        else:
            # 查找最新的備份
            mysql_files = list(self.backup_dir.glob("mysql_backup_*.sql.gz"))
            mongo_files = list(self.backup_dir.glob("mongodb_backup_*.tar.gz"))
            redis_files = list(self.backup_dir.glob("redis_backup_*.rdb"))
            config_files = list(self.backup_dir.glob("config_backup_*.tar.gz"))

            if mysql_files:
                backup_files['mysql'] = max(mysql_files, key=lambda x: x.stat().st_mtime)
            if mongo_files:
                backup_files['mongodb'] = max(mongo_files, key=lambda x: x.stat().st_mtime)
            if redis_files:
                backup_files['redis'] = max(redis_files, key=lambda x: x.stat().st_mtime)
            if config_files:
                backup_files['config'] = max(config_files, key=lambda x: x.stat().st_mtime)

        return backup_files

    def run_full_restore(self, date_str=None, services=None):
        """執行完整恢復"""
        self.logger.info("開始執行完整恢復")

        if services is None:
            services = ['mysql', 'mongodb', 'redis', 'config']

        backup_files = self.find_backup_files(date_str)

        restore_results = {}

        # 停止相關服務（如果需要）
        self._stop_services(services)

        # 恢復各個服務
        for service in services:
            if service == 'mysql' and 'mysql' in backup_files:
                restore_results['mysql'] = self.restore_mysql(str(backup_files['mysql']))
            elif service == 'mongodb' and 'mongodb' in backup_files:
                restore_results['mongodb'] = self.restore_mongodb(str(backup_files['mongodb']))
            elif service == 'redis' and 'redis' in backup_files:
                restore_results['redis'] = self.restore_redis(str(backup_files['redis']))
            elif service == 'config' and 'config' in backup_files:
                restore_results['config'] = self.restore_config_files(str(backup_files['config']))

        # 重啟服務
        self._start_services(services)

        self.logger.info("完整恢復執行完成")

        # 建立恢復報告
        self._create_restore_report(date_str, restore_results)

        return restore_results

    def _stop_services(self, services):
        """停止服務"""
        services_to_stop = []
        if 'mysql' in services:
            services_to_stop.append('mysqlserver')
        if 'mongodb' in services:
            services_to_stop.append('mongoserver')
        if 'redis' in services:
            services_to_stop.append('redisserver')

        for service in services_to_stop:
            self.logger.info(f"停止服務: {service}")
            self._run_command(f"docker stop {service}")

    def _start_services(self, services):
        """啟動服務"""
        services_to_start = []
        if 'mysql' in services:
            services_to_start.append('mysqlserver')
        if 'mongodb' in services:
            services_to_start.append('mongoserver')
        if 'redis' in services:
            services_to_start.append('redisserver')

        for service in services_to_start:
            self.logger.info(f"啟動服務: {service}")
            self._run_command(f"docker start {service}")

    def _create_restore_report(self, date_str, restore_results):
        """建立恢復報告"""
        report = {
            'restore_date': date_str or 'latest',
            'timestamp': datetime.datetime.now().isoformat(),
            'restore_results': restore_results,
            'status': 'success' if all(restore_results.values()) else 'partial_failure'
        }

        report_file = self.backup_dir / f"restore_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        self.logger.info(f"恢復報告已建立: {report_file}")

    def list_backup_files(self):
        """列出所有備份檔案"""
        backup_files = {
            'mysql': list(self.backup_dir.glob("mysql_backup_*.sql.gz")),
            'mongodb': list(self.backup_dir.glob("mongodb_backup_*.tar.gz")),
            'redis': list(self.backup_dir.glob("redis_backup_*.rdb")),
            'config': list(self.backup_dir.glob("config_backup_*.tar.gz")),
            'reports': list(self.backup_dir.glob("backup_report_*.json"))
        }

        print("可用的備份檔案:")
        for service, files in backup_files.items():
            print(f"\n{service.upper()}:")
            for file in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True):
                size_mb = file.stat().st_size / (1024 * 1024)
                mtime = datetime.datetime.fromtimestamp(file.stat().st_mtime)
                print(".1f")

    def validate_backup_integrity(self, backup_file):
        """驗證備份檔案完整性"""
        if not os.path.exists(backup_file):
            return False, "檔案不存在"

        try:
            if backup_file.endswith('.gz'):
                with gzip.open(backup_file, 'rb') as f:
                    f.read(1024)  # 嘗試讀取前1KB
            elif backup_file.endswith('.tar.gz'):
                with tarfile.open(backup_file, 'r:gz') as tar:
                    tar.getmembers()  # 檢查tar檔案結構
            else:
                with open(backup_file, 'rb') as f:
                    f.read(1024)  # 讀取前1KB

            return True, "檔案完整"
        except Exception as e:
            return False, f"檔案損壞: {str(e)}"


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='StockHistory 恢復服務')
    parser.add_argument('--config', default='config.yml', help='配置檔案路徑')
    parser.add_argument('--type', choices=['full', 'mysql', 'mongodb', 'redis', 'config'],
                       default='full', help='恢復類型')
    parser.add_argument('--date', help='備份日期字串 (YYYYMMDD_HHMMSS)')
    parser.add_argument('--file', help='指定備份檔案路徑')
    parser.add_argument('--list', action='store_true', help='列出所有備份檔案')
    parser.add_argument('--validate', help='驗證備份檔案完整性')

    args = parser.parse_args()

    restore_service = RestoreService(args.config)

    if args.list:
        restore_service.list_backup_files()
    elif args.validate:
        is_valid, message = restore_service.validate_backup_integrity(args.validate)
        print(f"驗證結果: {'通過' if is_valid else '失敗'} - {message}")
    elif args.type == 'full':
        restore_service.run_full_restore(args.date)
    elif args.file:
        # 從指定檔案恢復
        if args.type == 'mysql':
            restore_service.restore_mysql(args.file)
        elif args.type == 'mongodb':
            restore_service.restore_mongodb(args.file)
        elif args.type == 'redis':
            restore_service.restore_redis(args.file)
        elif args.type == 'config':
            restore_service.restore_config_files(args.file)
    else:
        print("請指定 --file 參數以指定備份檔案，或使用 --date 參數從最新備份恢復")


if __name__ == '__main__':
    main()
