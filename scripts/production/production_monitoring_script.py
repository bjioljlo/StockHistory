#!/usr/bin/env python3
"""
StockHistory 生產環境遷移監控腳本
監控資料庫效能、系統資源和遷移進度
"""

import sys
import os
import time
import psutil
import mysql.connector
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging
import json
import threading
from dataclasses import dataclass

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('production_monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MonitoringConfig:
    """監控配置"""
    host: str = "localhost"
    user: str = "demo"
    password: str = "~Demo123"
    database: str = "demo"
    port: int = 3307
    monitor_interval: int = 30  # 監控間隔（秒）
    alert_cpu_threshold: float = 80.0  # CPU 使用率告警閾值
    alert_memory_threshold: float = 85.0  # 記憶體使用率告警閾值
    alert_disk_threshold: float = 90.0  # 磁碟使用率告警閾值
    max_monitoring_time: int = 3600  # 最大監控時間（秒）
    log_file: str = "monitoring_report.json"

class SystemMonitor:
    """系統監控器"""

    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.monitoring_data = []
        self.is_monitoring = False
        self.start_time = None

    def start_monitoring(self):
        """開始監控"""
        logger.info("=== 開始生產環境監控 ===")
        self.is_monitoring = True
        self.start_time = datetime.now()

        # 啟動監控執行緒
        monitor_thread = threading.Thread(target=self._monitoring_loop)
        monitor_thread.daemon = True
        monitor_thread.start()

        logger.info(f"監控已啟動，間隔: {self.config.monitor_interval} 秒")

    def stop_monitoring(self):
        """停止監控"""
        logger.info("停止監控...")
        self.is_monitoring = False
        time.sleep(1)  # 等待最後一次監控完成

        # 生成報告
        self._generate_report()

    def _monitoring_loop(self):
        """監控循環"""
        end_time = datetime.now() + timedelta(seconds=self.config.max_monitoring_time)

        while self.is_monitoring and datetime.now() < end_time:
            try:
                # 收集系統指標
                system_metrics = self._collect_system_metrics()

                # 收集資料庫指標
                db_metrics = self._collect_database_metrics()

                # 合併指標
                metrics = {
                    'timestamp': datetime.now().isoformat(),
                    'system': system_metrics,
                    'database': db_metrics
                }

                self.monitoring_data.append(metrics)

                # 檢查告警條件
                self._check_alerts(system_metrics, db_metrics)

                # 等待下一次監控
                time.sleep(self.config.monitor_interval)

            except Exception as e:
                logger.error(f"監控循環出錯: {e}")
                time.sleep(self.config.monitor_interval)

        logger.info("監控循環結束")

    def _collect_system_metrics(self) -> Dict[str, Any]:
        """收集系統指標"""
        try:
            # CPU 使用率
            cpu_percent = psutil.cpu_percent(interval=1)

            # 記憶體使用情況
            memory = psutil.virtual_memory()
            memory_info = {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'percent': memory.percent
            }

            # 磁碟使用情況
            disk = psutil.disk_usage('/')
            disk_info = {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': disk.percent
            }

            # 網路 I/O
            network = psutil.net_io_counters()
            network_info = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }

            # 系統負載
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None

            return {
                'cpu_percent': cpu_percent,
                'memory': memory_info,
                'disk': disk_info,
                'network': network_info,
                'load_average': load_avg
            }

        except Exception as e:
            logger.error(f"收集系統指標失敗: {e}")
            return {}

    def _collect_database_metrics(self) -> Dict[str, Any]:
        """收集資料庫指標"""
        try:
            connection = mysql.connector.connect(
                host=self.config.host,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                port=self.config.port
            )

            cursor = connection.cursor()

            metrics = {}

            # 連線數量
            cursor.execute("SHOW PROCESSLIST")
            connections = cursor.fetchall()
            metrics['active_connections'] = len(connections)

            # 慢查詢統計
            cursor.execute("""
                SELECT COUNT(*) as slow_queries
                FROM information_schema.processlist
                WHERE time > 10
            """)
            slow_queries = cursor.fetchone()[0]
            metrics['slow_queries'] = slow_queries

            # 表格統計
            cursor.execute("""
                SELECT
                    COUNT(*) as table_count,
                    SUM(data_length + index_length) as total_size
                FROM information_schema.tables
                WHERE table_schema = %s
            """, (self.config.database,))
            table_stats = cursor.fetchone()
            metrics['table_count'] = table_stats[0]
            metrics['total_size_bytes'] = table_stats[1]

            # InnoDB 狀態
            cursor.execute("SHOW ENGINE INNODB STATUS")
            innodb_status = cursor.fetchone()
            if innodb_status:
                metrics['innodb_status'] = innodb_status[2][:1000]  # 只取前1000字元

            # 遷移進度（如果有統一表格）
            try:
                cursor.execute("SELECT COUNT(*) FROM stock_daily_prices")
                migration_rows = cursor.fetchone()[0]
                metrics['migration_rows'] = migration_rows
            except:
                metrics['migration_rows'] = 0

            cursor.close()
            connection.close()

            return metrics

        except Exception as e:
            logger.error(f"收集資料庫指標失敗: {e}")
            return {}

    def _check_alerts(self, system_metrics: Dict[str, Any], db_metrics: Dict[str, Any]):
        """檢查告警條件"""
        alerts = []

        # CPU 使用率告警
        cpu_percent = system_metrics.get('cpu_percent', 0)
        if cpu_percent > self.config.alert_cpu_threshold:
            alerts.append(f"CPU 使用率過高: {cpu_percent:.1f}%")

        # 記憶體使用率告警
        memory_percent = system_metrics.get('memory', {}).get('percent', 0)
        if memory_percent > self.config.alert_memory_threshold:
            alerts.append(f"記憶體使用率過高: {memory_percent:.1f}%")

        # 磁碟使用率告警
        disk_percent = system_metrics.get('disk', {}).get('percent', 0)
        if disk_percent > self.config.alert_disk_threshold:
            alerts.append(f"磁碟使用率過高: {disk_percent:.1f}%")

        # 資料庫連線數告警
        active_connections = db_metrics.get('active_connections', 0)
        if active_connections > 100:  # 假設最大連線數為100
            alerts.append(f"資料庫連線數過多: {active_connections}")

        # 慢查詢告警
        slow_queries = db_metrics.get('slow_queries', 0)
        if slow_queries > 5:
            alerts.append(f"慢查詢數量過多: {slow_queries}")

        # 記錄告警
        if alerts:
            logger.warning("🚨 系統告警:")
            for alert in alerts:
                logger.warning(f"  • {alert}")

    def _generate_report(self):
        """生成監控報告"""
        if not self.monitoring_data:
            logger.warning("沒有監控資料")
            return

        logger.info("生成監控報告...")

        # 計算統計資訊
        report = {
            'monitoring_period': {
                'start_time': self.start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration_seconds': (datetime.now() - self.start_time).total_seconds()
            },
            'summary': self._calculate_summary_stats(),
            'alerts_summary': self._analyze_alerts(),
            'performance_trends': self._analyze_performance_trends(),
            'recommendations': self._generate_recommendations(),
            'raw_data': self.monitoring_data
        }

        # 保存報告
        try:
            with open(self.config.log_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"監控報告已保存到: {self.config.log_file}")
        except Exception as e:
            logger.error(f"保存監控報告失敗: {e}")

        # 列印摘要報告
        self._print_summary_report(report)

    def _calculate_summary_stats(self) -> Dict[str, Any]:
        """計算摘要統計"""
        if not self.monitoring_data:
            return {}

        system_stats = []
        db_stats = []

        for data_point in self.monitoring_data:
            if 'system' in data_point:
                system_stats.append(data_point['system'])
            if 'database' in data_point:
                db_stats.append(data_point['database'])

        summary = {}

        # 系統統計
        if system_stats:
            cpu_values = [s.get('cpu_percent', 0) for s in system_stats if 'cpu_percent' in s]
            memory_values = [s.get('memory', {}).get('percent', 0) for s in system_stats if 'memory' in s]

            summary['system'] = {
                'cpu_avg': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                'cpu_max': max(cpu_values) if cpu_values else 0,
                'memory_avg': sum(memory_values) / len(memory_values) if memory_values else 0,
                'memory_max': max(memory_values) if memory_values else 0
            }

        # 資料庫統計
        if db_stats:
            connection_values = [d.get('active_connections', 0) for d in db_stats if 'active_connections' in d]
            migration_rows_values = [d.get('migration_rows', 0) for d in db_stats if 'migration_rows' in d]

            summary['database'] = {
                'avg_connections': sum(connection_values) / len(connection_values) if connection_values else 0,
                'max_connections': max(connection_values) if connection_values else 0,
                'final_migration_rows': migration_rows_values[-1] if migration_rows_values else 0,
                'migration_progress': len([r for r in migration_rows_values if r > 0]) / len(migration_rows_values) * 100 if migration_rows_values else 0
            }

        return summary

    def _analyze_alerts(self) -> Dict[str, Any]:
        """分析告警"""
        alerts_summary = {
            'total_alerts': 0,
            'alert_types': {},
            'critical_periods': []
        }

        # 簡單的告警分析邏輯
        for data_point in self.monitoring_data:
            system = data_point.get('system', {})
            db = data_point.get('database', {})

            alerts_in_period = []

            # 檢查各項指標
            if system.get('cpu_percent', 0) > self.config.alert_cpu_threshold:
                alerts_in_period.append('high_cpu')
            if system.get('memory', {}).get('percent', 0) > self.config.alert_memory_threshold:
                alerts_in_period.append('high_memory')
            if db.get('active_connections', 0) > 100:
                alerts_in_period.append('high_connections')

            if alerts_in_period:
                alerts_summary['total_alerts'] += 1
                for alert_type in alerts_in_period:
                    alerts_summary['alert_types'][alert_type] = alerts_summary['alert_types'].get(alert_type, 0) + 1

                alerts_summary['critical_periods'].append({
                    'timestamp': data_point['timestamp'],
                    'alerts': alerts_in_period
                })

        return alerts_summary

    def _analyze_performance_trends(self) -> Dict[str, Any]:
        """分析效能趨勢"""
        trends = {
            'cpu_trend': 'stable',
            'memory_trend': 'stable',
            'connection_trend': 'stable'
        }

        if len(self.monitoring_data) < 2:
            return trends

        # 簡單趨勢分析
        cpu_values = [d.get('system', {}).get('cpu_percent', 0) for d in self.monitoring_data[-10:]]  # 最後10個點
        memory_values = [d.get('system', {}).get('memory', {}).get('percent', 0) for d in self.monitoring_data[-10:]]
        connection_values = [d.get('database', {}).get('active_connections', 0) for d in self.monitoring_data[-10:]]

        # CPU 趨勢
        if len(cpu_values) >= 2:
            if cpu_values[-1] > cpu_values[0] + 10:
                trends['cpu_trend'] = 'increasing'
            elif cpu_values[-1] < cpu_values[0] - 10:
                trends['cpu_trend'] = 'decreasing'

        # 記憶體趨勢
        if len(memory_values) >= 2:
            if memory_values[-1] > memory_values[0] + 5:
                trends['memory_trend'] = 'increasing'
            elif memory_values[-1] < memory_values[0] - 5:
                trends['memory_trend'] = 'decreasing'

        # 連線趨勢
        if len(connection_values) >= 2:
            if connection_values[-1] > connection_values[0] + 10:
                trends['connection_trend'] = 'increasing'
            elif connection_values[-1] < connection_values[0] - 10:
                trends['connection_trend'] = 'decreasing'

        return trends

    def _generate_recommendations(self) -> List[str]:
        """生成建議"""
        recommendations = []

        if not self.monitoring_data:
            return recommendations

        summary = self._calculate_summary_stats()
        alerts = self._analyze_alerts()

        # 基於統計資料的建議
        system_stats = summary.get('system', {})
        if system_stats.get('cpu_max', 0) > 90:
            recommendations.append("考慮增加 CPU 資源或優化 CPU 密集型操作")

        if system_stats.get('memory_max', 0) > 95:
            recommendations.append("考慮增加記憶體或優化記憶體使用")

        # 基於告警的建議
        if alerts.get('total_alerts', 0) > 5:
            recommendations.append("系統負載過高，建議在低峰期執行遷移")

        # 基於趨勢的建議
        trends = self._analyze_performance_trends()
        if trends.get('cpu_trend') == 'increasing':
            recommendations.append("CPU 使用率持續上升，監控可能影響生產服務")

        if not recommendations:
            recommendations.append("系統運行正常，遷移可以繼續")

        return recommendations

    def _print_summary_report(self, report: Dict[str, Any]):
        """列印摘要報告"""
        print("\n" + "="*60)
        print("📊 生產環境監控報告")
        print("="*60)

        period = report['monitoring_period']
        print(f"監控期間: {period['start_time']} 至 {period['end_time']}")
        print(f"監控持續時間: {period['duration_seconds']:.1f} 秒")
        summary = report['summary']

        if 'system' in summary:
            sys_stats = summary['system']
            print("💻 系統資源:")
            print(f"  CPU 平均/最高: {sys_stats['cpu_avg']:.1f}% / {sys_stats['cpu_max']:.1f}%")
            print(f"  記憶體 平均/最高: {sys_stats['memory_avg']:.1f}% / {sys_stats['memory_max']:.1f}%")
        if 'database' in summary:
            db_stats = summary['database']
            print("🗄️  資料庫狀態:")
            print(f"  最終遷移行數: {db_stats.get('final_migration_rows', 0):,}")
        alerts = report['alerts_summary']
        print(f"🚨 告警統計: {alerts.get('total_alerts', 0)} 次")

        if alerts.get('alert_types'):
            print("告警類型:")
            for alert_type, count in alerts['alert_types'].items():
                print(f"  • {alert_type}: {count} 次")

        trends = report['performance_trends']
        print("📈 效能趨勢:")
        for metric, trend in trends.items():
            print(f"  • {metric}: {trend}")

        recommendations = report['recommendations']
        if recommendations:
            print("💡 建議:")
            for rec in recommendations:
                print(f"  • {rec}")

        print("\n詳細報告已保存至:", self.config.log_file)
        print("="*60)

def wait_for_migration_completion(timeout_seconds: int = 3600) -> bool:
    """等待遷移完成"""
    logger.info(f"等待遷移完成，最多等待 {timeout_seconds} 秒...")

    start_time = time.time()
    checkpoint_file = "migration_checkpoint.json"

    while time.time() - start_time < timeout_seconds:
        # 檢查檢查點檔案是否存在
        if not os.path.exists(checkpoint_file):
            logger.info("檢查點檔案不存在，遷移可能已完成")
            return True

        # 檢查檢查點檔案大小變化（簡單的活躍度檢查）
        try:
            stat = os.stat(checkpoint_file)
            if stat.st_mtime < time.time() - 300:  # 5分鐘沒有更新
                logger.info("檢查點檔案長時間未更新，遷移可能已完成")
                return True
        except:
            pass

        time.sleep(60)  # 每分鐘檢查一次

    logger.warning(f"等待遷移完成超時 ({timeout_seconds} 秒)")
    return False

def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description='StockHistory 生產環境監控工具')
    parser.add_argument('--host', default='localhost', help='資料庫主機')
    parser.add_argument('--port', type=int, default=3307, help='資料庫端口')
    parser.add_argument('--user', default='demo', help='資料庫用戶名')
    parser.add_argument('--password', default='~Demo123', help='資料庫密碼')
    parser.add_argument('--database', default='demo', help='資料庫名稱')
    parser.add_argument('--interval', type=int, default=30, help='監控間隔（秒）')
    parser.add_argument('--cpu-threshold', type=float, default=80.0, help='CPU 告警閾值')
    parser.add_argument('--memory-threshold', type=float, default=85.0, help='記憶體告警閾值')
    parser.add_argument('--disk-threshold', type=float, default=90.0, help='磁碟告警閾值')
    parser.add_argument('--max-time', type=int, default=3600, help='最大監控時間（秒）')
    parser.add_argument('--wait-for-migration', action='store_true', help='等待遷移完成後停止監控')

    args = parser.parse_args()

    config = MonitoringConfig(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database,
        monitor_interval=args.interval,
        alert_cpu_threshold=args.cpu_threshold,
        alert_memory_threshold=args.memory_threshold,
        alert_disk_threshold=args.disk_threshold,
        max_monitoring_time=args.max_time
    )

    monitor = SystemMonitor(config)
    monitor.start_monitoring()

    try:
        if args.wait_for_migration:
            # 等待遷移完成
            migration_completed = wait_for_migration_completion(args.max_time)
            if migration_completed:
                logger.info("檢測到遷移完成")
            else:
                logger.warning("遷移未在預期時間內完成")
        else:
            # 持續監控指定時間
            time.sleep(args.max_time)

    except KeyboardInterrupt:
        logger.info("收到中斷信號")

    finally:
        monitor.stop_monitoring()

    logger.info("監控完成")
    return 0

if __name__ == "__main__":
    sys.exit(main())
