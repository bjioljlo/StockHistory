"""
StockHistory 資料壓縮服務

提供資料壓縮、優化和儲存優化功能。
支援資料表壓縮、資料清理和儲存空間優化。
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import yaml
from sqlalchemy import text, create_engine
import pandas as pd
import gzip
import json
import os
from pathlib import Path


class DataCompressionService:
    """資料壓縮服務類別"""

    def __init__(self, config_path='config.yml'):
        self.config = self._load_config(config_path)
        self.db_config = self.config.get('database', {}).get('mysql', {})

        # 設定日誌
        logging.basicConfig(
            filename='logs/data_compression.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # 壓縮配置
        self.compression_config = {
            'archive_threshold_days': 365,  # 壓縮超過1年的資料
            'compression_level': 6,  # gzip壓縮等級
            'batch_size': 1000,  # 批次處理大小
            'max_compressed_size_mb': 100  # 單個壓縮檔案最大大小
        }

    def _load_config(self, config_path):
        """載入配置檔案"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"載入配置檔案失敗: {e}")
            return {}

    def _get_mysql_connection(self):
        """獲取MySQL連線"""
        connection_string = (
            f"mysql+pymysql://{self.db_config.get('user', 'root')}:"
            f"{self.db_config.get('password', '')}@"
            f"{self.db_config.get('host', 'localhost')}:"
            f"{self.db_config.get('port', 3306)}/"
            f"{self.db_config.get('databasename', 'demo')}"
        )
        return create_engine(connection_string)

    def analyze_table_compression_potential(self, table_name: str) -> Dict[str, Any]:
        """分析資料表壓縮潛力"""
        try:
            engine = self._get_mysql_connection()

            with engine.connect() as conn:
                # 獲取資料表統計資訊
                stats_query = text("""
                    SELECT
                        TABLE_ROWS,
                        AVG_ROW_LENGTH,
                        DATA_LENGTH,
                        INDEX_LENGTH,
                        DATA_FREE
                    FROM information_schema.TABLES
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME = :table_name
                """)

                result = conn.execute(stats_query, {'table_name': table_name})
                stats = result.fetchone()

                if not stats:
                    return {'error': f'資料表 {table_name} 不存在'}

                # 計算壓縮潛力
                table_rows = stats[0] or 0
                avg_row_length = stats[1] or 0
                data_length = stats[2] or 0
                index_length = stats[3] or 0
                data_free = stats[4] or 0

                # 估計壓縮後大小（基於經驗值）
                estimated_compression_ratio = 0.3  # 假設壓縮比為70%
                estimated_compressed_size = data_length * estimated_compression_ratio

                # 分析舊資料量
                old_data_query = text(f"""
                    SELECT COUNT(*) as old_records
                    FROM {table_name}
                    WHERE date < DATE_SUB(NOW(), INTERVAL {self.compression_config['archive_threshold_days']} DAY)
                """)

                old_result = conn.execute(old_data_query)
                old_records = old_result.fetchone()[0] or 0

                return {
                    'table_name': table_name,
                    'total_rows': table_rows,
                    'old_records': old_records,
                    'data_size_mb': data_length / (1024 * 1024),
                    'index_size_mb': index_length / (1024 * 1024),
                    'free_space_mb': data_free / (1024 * 1024),
                    'estimated_compressed_size_mb': estimated_compressed_size / (1024 * 1024),
                    'compression_ratio': estimated_compression_ratio,
                    'compression_potential_mb': (data_length - estimated_compressed_size) / (1024 * 1024),
                    'recommendations': self._generate_compression_recommendations(
                        table_rows, old_records, data_length, data_free
                    )
                }

        except Exception as e:
            self.logger.error(f"分析資料表壓縮潛力失敗: {e}")
            return {'error': str(e)}

    def _generate_compression_recommendations(self, total_rows: int, old_records: int,
                                            data_size: int, free_space: int) -> List[str]:
        """生成壓縮建議"""
        recommendations = []

        # 檢查是否有大量舊資料
        if old_records > total_rows * 0.5:  # 超過50%的資料是舊的
            recommendations.append(f"建議壓縮 {old_records} 條舊記錄（超過總記錄50%）")

        # 檢查資料大小
        data_size_mb = data_size / (1024 * 1024)
        if data_size_mb > 1000:  # 大於1GB
            recommendations.append(f"資料表大小為 {data_size_mb:.1f} MB，建議考慮壓縮或分區")
        # 檢查可用空間
        free_space_mb = free_space / (1024 * 1024)
        if free_space_mb > data_size_mb * 0.2:  # 可用空間超過20%
            recommendations.append(f"可用空間為 {free_space_mb:.1f} MB，建議進行碎片整理")
        if not recommendations:
            recommendations.append("資料表結構良好，當前無需壓縮")

        return recommendations

    def compress_old_data(self, table_name: str, archive_table: str = None) -> Dict[str, Any]:
        """壓縮舊資料"""
        try:
            engine = self._get_mysql_connection()

            with engine.connect() as conn:
                # 檢查是否有舊資料
                old_data_query = text(f"""
                    SELECT COUNT(*) as old_records
                    FROM {table_name}
                    WHERE date < DATE_SUB(NOW(), INTERVAL {self.compression_config['archive_threshold_days']} DAY)
                """)

                result = conn.execute(old_data_query)
                old_records = result.fetchone()[0] or 0

                if old_records == 0:
                    return {
                        'status': 'no_old_data',
                        'message': f'資料表 {table_name} 沒有需要壓縮的舊資料',
                        'compressed_records': 0
                    }

                # 創建壓縮檔案
                archive_file = self._create_compressed_archive(table_name, conn)

                if not archive_file:
                    return {
                        'status': 'error',
                        'message': '創建壓縮檔案失敗',
                        'compressed_records': 0
                    }

                # 可選：移動資料到歸檔表
                if archive_table:
                    self._move_to_archive_table(table_name, archive_table, conn)

                # 刪除舊資料（如果已經壓縮）
                delete_query = text(f"""
                    DELETE FROM {table_name}
                    WHERE date < DATE_SUB(NOW(), INTERVAL {self.compression_config['archive_threshold_days']} DAY)
                    LIMIT {self.compression_config['batch_size']}
                """)

                # 批次刪除以避免鎖定過久
                deleted_records = 0
                while True:
                    result = conn.execute(delete_query)
                    batch_deleted = result.rowcount
                    deleted_records += batch_deleted

                    if batch_deleted < self.compression_config['batch_size']:
                        break

                    conn.commit()  # 定期提交

                conn.commit()

                return {
                    'status': 'success',
                    'message': f'成功壓縮 {deleted_records} 條記錄',
                    'compressed_records': deleted_records,
                    'archive_file': str(archive_file)
                }

        except Exception as e:
            self.logger.error(f"壓縮舊資料失敗: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'compressed_records': 0
            }

    def _create_compressed_archive(self, table_name: str, connection) -> Optional[Path]:
        """創建壓縮檔案"""
        try:
            # 創建壓縮目錄
            archive_dir = Path('./compressed_data')
            archive_dir.mkdir(exist_ok=True)

            # 產生檔案名稱
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_file = archive_dir / f"{table_name}_compressed_{timestamp}.json.gz"

            # 查詢舊資料
            old_data_query = f"""
                SELECT * FROM {table_name}
                WHERE date < DATE_SUB(NOW(), INTERVAL {self.compression_config['archive_threshold_days']} DAY)
                ORDER BY date
            """

            # 批次處理資料以節省記憶體
            offset = 0
            batch_size = self.compression_config['batch_size']

            with gzip.open(archive_file, 'wt', encoding='utf-8',
                          compresslevel=self.compression_config['compression_level']) as f:

                while True:
                    batch_query = f"{old_data_query} LIMIT {batch_size} OFFSET {offset}"
                    result = connection.execute(text(batch_query))

                    rows = result.fetchall()
                    if not rows:
                        break

                    # 將批次資料寫入壓縮檔案
                    for row in rows:
                        record = dict(row._mapping)
                        # 將日期轉換為字串以確保JSON序列化
                        if 'date' in record and hasattr(record['date'], 'isoformat'):
                            record['date'] = record['date'].isoformat()
                        json.dump(record, f, ensure_ascii=False)
                        f.write('\n')

                    offset += batch_size

                    # 檢查檔案大小限制
                    if archive_file.stat().st_size > self.compression_config['max_compressed_size_mb'] * 1024 * 1024:
                        self.logger.warning(f"壓縮檔案超過大小限制: {archive_file}")
                        break

            self.logger.info(f"創建壓縮檔案成功: {archive_file}")
            return archive_file

        except Exception as e:
            self.logger.error(f"創建壓縮檔案失敗: {e}")
            return None

    def _move_to_archive_table(self, source_table: str, archive_table: str, connection):
        """將資料移動到歸檔表"""
        try:
            # 創建歸檔表（如果不存在）
            create_table_query = f"""
                CREATE TABLE IF NOT EXISTS {archive_table} LIKE {source_table}
            """
            connection.execute(text(create_table_query))

            # 移動資料
            move_query = f"""
                INSERT INTO {archive_table}
                SELECT * FROM {source_table}
                WHERE date < DATE_SUB(NOW(), INTERVAL {self.compression_config['archive_threshold_days']} DAY)
            """
            connection.execute(text(move_query))

            self.logger.info(f"資料移動到歸檔表成功: {source_table} -> {archive_table}")

        except Exception as e:
            self.logger.error(f"移動資料到歸檔表失敗: {e}")

    def optimize_table_storage(self, table_name: str) -> Dict[str, Any]:
        """優化資料表儲存空間"""
        try:
            engine = self._get_mysql_connection()

            with engine.connect() as conn:
                # 分析資料表碎片
                analyze_query = text(f"ANALYZE TABLE {table_name}")
                conn.execute(analyze_query)

                # 優化資料表
                optimize_query = text(f"OPTIMIZE TABLE {table_name}")
                result = conn.execute(optimize_query)

                # 獲取優化結果
                optimization_info = result.fetchone()

                # 檢查是否可以使用壓縮
                compression_query = text(f"""
                    ALTER TABLE {table_name}
                    ROW_FORMAT=COMPRESSED,
                    KEY_BLOCK_SIZE=8
                """)

                try:
                    conn.execute(compression_query)
                    compression_applied = True
                except Exception:
                    compression_applied = False

                conn.commit()

                return {
                    'status': 'success',
                    'table_name': table_name,
                    'optimization_info': str(optimization_info),
                    'compression_applied': compression_applied,
                    'message': f"資料表 {table_name} 儲存優化完成"
                }

        except Exception as e:
            self.logger.error(f"優化資料表儲存空間失敗: {e}")
            return {
                'status': 'error',
                'table_name': table_name,
                'message': str(e)
            }

    def compress_database_logs(self) -> Dict[str, Any]:
        """壓縮資料庫日誌檔案"""
        try:
            logs_dir = Path('./logs')
            if not logs_dir.exists():
                return {'status': 'no_logs_dir', 'message': '日誌目錄不存在'}

            compressed_files = []
            total_original_size = 0
            total_compressed_size = 0

            # 壓縮舊日誌檔案（超過7天的）
            cutoff_date = datetime.now() - timedelta(days=7)

            for log_file in logs_dir.glob("*.log"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    compressed_file = log_file.with_suffix('.log.gz')

                    # 壓縮檔案
                    original_size = log_file.stat().st_size
                    total_original_size += original_size

                    with open(log_file, 'rb') as f_in:
                        with gzip.open(compressed_file, 'wb',
                                     compresslevel=self.compression_config['compression_level']) as f_out:
                            f_out.writelines(f_in)

                    compressed_size = compressed_file.stat().st_size
                    total_compressed_size += compressed_size

                    # 刪除原始檔案
                    log_file.unlink()

                    compressed_files.append({
                        'original_file': str(log_file),
                        'compressed_file': str(compressed_file),
                        'original_size': original_size,
                        'compressed_size': compressed_size,
                        'compression_ratio': compressed_size / original_size if original_size > 0 else 0
                    })

            compression_ratio = total_compressed_size / total_original_size if total_original_size > 0 else 0

            return {
                'status': 'success',
                'compressed_files': compressed_files,
                'total_original_size_mb': total_original_size / (1024 * 1024),
                'total_compressed_size_mb': total_compressed_size / (1024 * 1024),
                'overall_compression_ratio': compression_ratio,
                'space_saved_mb': (total_original_size - total_compressed_size) / (1024 * 1024)
            }

        except Exception as e:
            self.logger.error(f"壓縮資料庫日誌失敗: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def get_compression_statistics(self) -> Dict[str, Any]:
        """獲取壓縮統計資訊"""
        try:
            compressed_dir = Path('./compressed_data')
            archive_dir = Path('./archive')

            stats = {
                'compressed_files_count': 0,
                'total_compressed_size_mb': 0,
                'archived_files_count': 0,
                'total_archive_size_mb': 0,
                'compression_stats': []
            }

            # 統計壓縮檔案
            if compressed_dir.exists():
                for file in compressed_dir.glob("*.gz"):
                    stats['compressed_files_count'] += 1
                    stats['total_compressed_size_mb'] += file.stat().st_size / (1024 * 1024)

            # 統計歸檔檔案
            if archive_dir.exists():
                for file in archive_dir.glob("*"):
                    stats['archived_files_count'] += 1
                    stats['total_archive_size_mb'] += file.stat().st_size / (1024 * 1024)

            return stats

        except Exception as e:
            self.logger.error(f"獲取壓縮統計失敗: {e}")
            return {'error': str(e)}

    def cleanup_old_compressed_files(self, retention_days: int = 365) -> Dict[str, Any]:
        """清理舊的壓縮檔案"""
        try:
            compressed_dir = Path('./compressed_data')
            archive_dir = Path('./archive')

            cutoff_date = datetime.now() - timedelta(days=retention_days)
            deleted_files = []

            # 清理壓縮檔案
            if compressed_dir.exists():
                for file in compressed_dir.glob("*"):
                    if file.stat().st_mtime < cutoff_date.timestamp():
                        size_mb = file.stat().st_size / (1024 * 1024)
                        file.unlink()
                        deleted_files.append({
                            'file': str(file),
                            'size_mb': size_mb,
                            'type': 'compressed'
                        })

            # 清理歸檔檔案
            if archive_dir.exists():
                for file in archive_dir.glob("*"):
                    if file.stat().st_mtime < cutoff_date.timestamp():
                        size_mb = file.stat().st_size / (1024 * 1024)
                        file.unlink()
                        deleted_files.append({
                            'file': str(file),
                            'size_mb': size_mb,
                            'type': 'archive'
                        })

            total_space_freed = sum(f['size_mb'] for f in deleted_files)

            return {
                'status': 'success',
                'deleted_files_count': len(deleted_files),
                'space_freed_mb': total_space_freed,
                'deleted_files': deleted_files
            }

        except Exception as e:
            self.logger.error(f"清理舊壓縮檔案失敗: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def run_compression_maintenance(self) -> Dict[str, Any]:
        """執行壓縮維護任務"""
        self.logger.info("開始執行壓縮維護任務")

        results = {
            'timestamp': datetime.now().isoformat(),
            'tasks': []
        }

        try:
            # 1. 壓縮資料庫日誌
            log_compression = self.compress_database_logs()
            results['tasks'].append({
                'task': 'log_compression',
                'result': log_compression
            })

            # 2. 清理舊壓縮檔案
            cleanup = self.cleanup_old_compressed_files()
            results['tasks'].append({
                'task': 'cleanup_old_files',
                'result': cleanup
            })

            # 3. 獲取壓縮統計
            stats = self.get_compression_statistics()
            results['tasks'].append({
                'task': 'compression_stats',
                'result': stats
            })

            results['status'] = 'success'
            results['message'] = '壓縮維護任務完成'

        except Exception as e:
            results['status'] = 'error'
            results['message'] = str(e)
            self.logger.error(f"壓縮維護任務失敗: {e}")

        self.logger.info("壓縮維護任務完成")
        return results
