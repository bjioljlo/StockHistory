#!/usr/bin/env python3
"""
遷移效能監控腳本

此腳本用於監控資料遷移過程中的效能指標和系統資源使用情況。

監控項目：
1. CPU使用率
2. 記憶體使用量
3. 磁碟I/O
4. 網路I/O
5. 資料庫連接數
6. 遷移進度
7. 錯誤統計
"""

import os
import sys
import time
import psutil
import logging
from datetime import datetime
from typing import Dict, Any, List
import threading
import json

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from pyutils_core.config import load_config

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration_monitor.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class MigrationMonitor:
    """遷移效能監控器"""

    def __init__(self, config_path: str = None, output_file: str = 'migration_metrics.json'):
        """初始化監控器"""
        self.config = load_config(config_path)
        self.output_file = output_file
        self.monitoring = False
        self.metrics_history = []
        self.start_time = None

        # 效能閾值設定
        self.thresholds = {
            'cpu_percent': 80.0,      # CPU使用率閾值
            'memory_percent': 85.0,   # 記憶體使用率閾值
            'disk_io_mb': 100.0,      # 磁碟I/O速率閾值 (MB/s)
            'migration_errors': 10    # 遷移錯誤數量閾值
        }

        logger.info("MigrationMonitor initialized")

    def start_monitoring(self, interval: int = 5):
        """開始監控"""
        self.monitoring = True
        self.start_time = datetime.now()
        self.metrics_history = []

        logger.info(f"Starting monitoring with {interval}s interval")

        # 啟動監控線程
        monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        monitor_thread.daemon = True
        monitor_thread.start()

        return monitor_thread

    def stop_monitoring(self):
        """停止監控"""
        self.monitoring = False
        logger.info("Monitoring stopped")

        # 保存最終報告
        self.save_report()

    def get_current_metrics(self) -> Dict[str, Any]:
        """獲取當前系統指標"""
        try:
            # CPU資訊
            cpu_percent = psutil.cpu_percent(interval=1)

            # 記憶體資訊
            memory = psutil.virtual_memory()
            memory_info = {
                'total_gb': round(memory.total / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'percent': memory.percent
            }

            # 磁碟I/O
            disk_io = psutil.disk_io_counters()
            if disk_io:
                disk_io_info = {
                    'read_mb': round(disk_io.read_bytes / (1024**2), 2),
                    'write_mb': round(disk_io.write_bytes / (1024**2), 2),
                    'read_count': disk_io.read_count,
                    'write_count': disk_io.write_count
                }
            else:
                disk_io_info = {'error': 'Disk I/O counters not available'}

            # 網路I/O
            net_io = psutil.net_io_counters()
            if net_io:
                net_io_info = {
                    'bytes_sent_mb': round(net_io.bytes_sent / (1024**2), 2),
                    'bytes_recv_mb': round(net_io.bytes_recv / (1024**2), 2),
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv
                }
            else:
                net_io_info = {'error': 'Network I/O counters not available'}

            # 進程資訊
            current_process = psutil.Process()
            process_info = {
                'cpu_percent': current_process.cpu_percent(),
                'memory_mb': round(current_process.memory_info().rss / (1024**2), 2),
                'threads': current_process.num_threads(),
                'open_files': len(current_process.open_files()) if current_process.open_files() else 0
            }

            # 系統負載 (Linux)
            load_average = {}
            try:
                load_avg = os.getloadavg()
                load_average = {
                    '1min': load_avg[0],
                    '5min': load_avg[1],
                    '15min': load_avg[2]
                }
            except (AttributeError, OSError):
                # Windows 不支援 getloadavg
                load_average = {'not_available': 'Load average not supported on this platform'}

            metrics = {
                'timestamp': datetime.now().isoformat(),
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory': memory_info,
                    'disk_io': disk_io_info,
                    'network_io': net_io_info,
                    'load_average': load_average
                },
                'process': process_info,
                'migration': {
                    'elapsed_time': str(datetime.now() - self.start_time) if self.start_time else None,
                    'warnings': self._check_thresholds({
                        'cpu_percent': cpu_percent,
                        'memory_percent': memory_info['percent']
                    })
                }
            }

            return metrics

        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

    def record_migration_event(self, event_type: str, details: Dict[str, Any]):
        """記錄遷移事件"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'details': details
        }

        logger.info(f"Migration event: {event_type} - {details}")

        # 如果正在監控，添加到歷史記錄
        if self.monitoring:
            # 找到最新的指標記錄並添加事件
            if self.metrics_history:
                self.metrics_history[-1]['migration']['events'] = \
                    self.metrics_history[-1]['migration'].get('events', [])
                self.metrics_history[-1]['migration']['events'].append(event)

    def _monitor_loop(self, interval: int):
        """監控循環"""
        logger.info("Monitor loop started")

        while self.monitoring:
            try:
                metrics = self.get_current_metrics()
                self.metrics_history.append(metrics)

                # 檢查是否有警告
                warnings = metrics.get('migration', {}).get('warnings', [])
                if warnings:
                    for warning in warnings:
                        logger.warning(f"Threshold exceeded: {warning}")

                # 限制歷史記錄大小（保留最近1000個記錄）
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-1000:]

                time.sleep(interval)

            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(interval)

        logger.info("Monitor loop stopped")

    def _check_thresholds(self, current_values: Dict[str, float]) -> List[str]:
        """檢查是否超過閾值"""
        warnings = []

        for metric, value in current_values.items():
            if metric in self.thresholds and value > self.thresholds[metric]:
                warnings.append(f"{metric} exceeded threshold: {value} > {self.thresholds[metric]}")

        return warnings

    def save_report(self):
        """保存監控報告"""
        if not self.metrics_history:
            logger.warning("No metrics data to save")
            return

        report = {
            'monitoring_period': {
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'end_time': datetime.now().isoformat(),
                'duration': str(datetime.now() - self.start_time) if self.start_time else None
            },
            'summary': self._generate_summary(),
            'metrics_history': self.metrics_history,
            'thresholds': self.thresholds
        }

        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"Monitoring report saved to {self.output_file}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")

    def _generate_summary(self) -> Dict[str, Any]:
        """生成總結報告"""
        if not self.metrics_history:
            return {}

        # 計算統計數據
        cpu_usage = [m['system']['cpu_percent'] for m in self.metrics_history if 'system' in m]
        memory_usage = [m['system']['memory']['percent'] for m in self.metrics_history
                       if 'system' in m and 'memory' in m['system']]

        summary = {
            'total_measurements': len(self.metrics_history),
            'cpu_stats': {
                'average': round(sum(cpu_usage) / len(cpu_usage), 2) if cpu_usage else 0,
                'max': max(cpu_usage) if cpu_usage else 0,
                'min': min(cpu_usage) if cpu_usage else 0
            },
            'memory_stats': {
                'average': round(sum(memory_usage) / len(memory_usage), 2) if memory_usage else 0,
                'max': max(memory_usage) if memory_usage else 0,
                'min': min(memory_usage) if memory_usage else 0
            },
            'warnings_count': sum(len(m.get('migration', {}).get('warnings', []))
                                 for m in self.metrics_history),
            'migration_events': []
        }

        # 收集遷移事件
        for metrics in self.metrics_history:
            events = metrics.get('migration', {}).get('events', [])
            summary['migration_events'].extend(events)

        return summary

    def print_real_time_stats(self):
        """列印即時統計資訊"""
        metrics = self.get_current_metrics()

        print("\n" + "="*60)
        print("即時系統監控統計")
        print("="*60)

        if 'error' in metrics:
            print(f"錯誤: {metrics['error']}")
            return

        system = metrics['system']
        process = metrics['process']

        print(f"時間: {metrics['timestamp']}")
        print(f"監控持續時間: {metrics.get('migration', {}).get('elapsed_time', 'N/A')}")

        print(f"\n系統資源:")
        print(f"  CPU使用率: {system['cpu_percent']}%")
        print(f"  記憶體使用: {system['memory']['used_gb']}GB / {system['memory']['total_gb']}GB ({system['memory']['percent']}%)")

        if 'disk_io' in system and 'error' not in system['disk_io']:
            print(f"  磁碟讀取: {system['disk_io']['read_mb']}MB")
            print(f"  磁碟寫入: {system['disk_io']['write_mb']}MB")

        print(f"\n進程資源:")
        print(f"  CPU使用率: {process['cpu_percent']}%")
        print(f"  記憶體使用: {process['memory_mb']}MB")
        print(f"  執行緒數: {process['threads']}")
        print(f"  開啟檔案數: {process['open_files']}")

        warnings = metrics.get('migration', {}).get('warnings', [])
        if warnings:
            print(f"\n⚠️  警告:")
            for warning in warnings:
                print(f"  - {warning}")

        events = metrics.get('migration', {}).get('events', [])
        if events:
            print(f"\n📝 最新事件:")
            for event in events[-3:]:  # 顯示最近3個事件
                print(f"  - {event['event_type']}: {event['details']}")


class MigrationProgressTracker:
    """遷移進度追蹤器"""

    def __init__(self):
        self.progress = {
            'dividend_yield': {'total_files': 0, 'processed_files': 0, 'total_records': 0, 'inserted_records': 0},
            'monthly_reports': {'total_files': 0, 'processed_files': 0, 'total_records': 0, 'inserted_records': 0},
            'quarterly_reports': {'total_files': 0, 'processed_files': 0, 'total_records': 0, 'inserted_records': 0}
        }
        self.errors = []
        self.start_time = None

    def start_migration(self, migration_type: str, total_files: int):
        """開始遷移"""
        if migration_type in self.progress:
            self.progress[migration_type]['total_files'] = total_files
            self.progress[migration_type]['processed_files'] = 0
            self.progress[migration_type]['total_records'] = 0
            self.progress[migration_type]['inserted_records'] = 0

        if not self.start_time:
            self.start_time = datetime.now()

        logger.info(f"Started migration for {migration_type} with {total_files} files")

    def update_progress(self, migration_type: str, processed_files: int = None,
                       total_records: int = None, inserted_records: int = None):
        """更新進度"""
        if migration_type not in self.progress:
            return

        if processed_files is not None:
            self.progress[migration_type]['processed_files'] = processed_files

        if total_records is not None:
            self.progress[migration_type]['total_records'] += total_records

        if inserted_records is not None:
            self.progress[migration_type]['inserted_records'] += inserted_records

    def add_error(self, migration_type: str, error: str):
        """添加錯誤"""
        self.errors.append({
            'migration_type': migration_type,
            'error': error,
            'timestamp': datetime.now().isoformat()
        })
        logger.error(f"Migration error in {migration_type}: {error}")

    def get_progress_summary(self) -> Dict[str, Any]:
        """獲取進度總結"""
        total_files = sum(p['total_files'] for p in self.progress.values())
        processed_files = sum(p['processed_files'] for p in self.progress.values())
        total_records = sum(p['total_records'] for p in self.progress.values())
        inserted_records = sum(p['inserted_records'] for p in self.progress.values())

        elapsed_time = datetime.now() - self.start_time if self.start_time else None

        return {
            'overall_progress': {
                'files_processed': processed_files,
                'files_total': total_files,
                'records_processed': inserted_records,
                'records_total': total_records,
                'completion_percentage': round(processed_files / total_files * 100, 2) if total_files > 0 else 0,
                'elapsed_time': str(elapsed_time) if elapsed_time else None
            },
            'detailed_progress': self.progress,
            'errors': self.errors,
            'error_count': len(self.errors)
        }


def main():
    """主程式"""
    import argparse

    parser = argparse.ArgumentParser(description='遷移效能監控腳本')
    parser.add_argument('--config', help='配置文件路徑')
    parser.add_argument('--output', default='migration_metrics.json', help='輸出檔案路徑')
    parser.add_argument('--interval', type=int, default=5, help='監控間隔（秒）')
    parser.add_argument('--duration', type=int, help='監控持續時間（秒），不指定則手動停止')
    parser.add_argument('--real-time', action='store_true', help='顯示即時統計')

    args = parser.parse_args()

    try:
        # 初始化監控器
        monitor = MigrationMonitor(args.config, args.output)

        if args.real_time:
            # 即時監控模式
            monitor.start_monitoring(args.interval)

            try:
                while True:
                    if args.duration:
                        time.sleep(min(args.interval, args.duration))
                        args.duration -= args.interval
                        if args.duration <= 0:
                            break
                    else:
                        time.sleep(args.interval)

                    monitor.print_real_time_stats()

            except KeyboardInterrupt:
                print("\n收到中斷信號，正在停止監控...")
            finally:
                monitor.stop_monitoring()

        else:
            # 標準監控模式
            monitor_thread = monitor.start_monitoring(args.interval)

            try:
                if args.duration:
                    monitor_thread.join(args.duration)
                else:
                    print("監控已啟動，按 Ctrl+C 停止...")
                    monitor_thread.join()

            except KeyboardInterrupt:
                print("\n收到中斷信號，正在停止監控...")
            finally:
                monitor.stop_monitoring()

        print(f"\n監控完成，報告已保存到: {args.output}")

    except Exception as e:
        logger.error(f"Monitoring failed: {e}")
        print(f"Monitoring failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
