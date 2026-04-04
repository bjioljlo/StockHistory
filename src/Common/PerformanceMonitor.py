"""
StockHistory 效能監控服務

提供資料庫查詢效能監控、慢查詢分析和效能指標收集功能。
支援 MySQL、MongoDB 和 Redis 的效能監控。
"""

import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from contextlib import contextmanager
import psutil
import yaml
from sqlalchemy import text, create_engine
import pymongo
import redis
from concurrent.futures import ThreadPoolExecutor
import json


class PerformanceMonitor:
    """效能監控服務類別"""

    def __init__(self, config_path='config.yml'):
        self.config = self._load_config(config_path)
        self.monitoring_config = self.config.get('monitoring', {})
        self.enabled = self.monitoring_config.get('enable_performance_monitoring', False)
        self.slow_query_threshold = self.monitoring_config.get('slow_query_threshold', 2.0)

        # 效能指標存儲
        self.metrics = {
            'queries': [],
            'system': [],
            'connections': {},
            'slow_queries': []
        }

        # 設定日誌
        logging.basicConfig(
            filename='logs/performance.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # 監控執行緒
        self.monitoring_thread = None
        self.stop_monitoring = False

        if self.enabled:
            self.start_monitoring()

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
        db_config = self.config.get('database', {}).get('mysql', {})
        connection_string = (
            f"mysql+pymysql://{db_config.get('user', 'root')}:"
            f"{db_config.get('password', '')}@"
            f"{db_config.get('host', 'localhost')}:"
            f"{db_config.get('port', 3306)}/"
            f"{db_config.get('databasename', 'demo')}"
        )
        return create_engine(connection_string)

    def _get_mongo_connection(self):
        """獲取MongoDB連線"""
        db_config = self.config.get('database', {}).get('mongodb', {})
        client = pymongo.MongoClient(
            host=db_config.get('host', 'localhost'),
            port=db_config.get('port', 27017)
        )
        return client[db_config.get('databasename', 'demo')]

    def _get_redis_connection(self):
        """獲取Redis連線"""
        return redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True
        )

    @contextmanager
    def monitor_query(self, query_type: str, query_details: str = ""):
        """查詢效能監控上下文管理器"""
        if not self.enabled:
            yield
            return

        start_time = time.time()
        start_cpu = psutil.cpu_percent(interval=None)
        start_memory = psutil.virtual_memory().percent

        try:
            yield
        finally:
            end_time = time.time()
            end_cpu = psutil.cpu_percent(interval=None)
            end_memory = psutil.virtual_memory().percent

            execution_time = end_time - start_time
            cpu_usage = end_cpu - start_cpu
            memory_usage = end_memory - start_memory

            # 記錄查詢指標
            query_metric = {
                'timestamp': datetime.now().isoformat(),
                'type': query_type,
                'details': query_details,
                'execution_time': execution_time,
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage
            }

            self.metrics['queries'].append(query_metric)

            # 檢查是否為慢查詢
            if execution_time > self.slow_query_threshold:
                slow_query = {
                    **query_metric,
                    'threshold': self.slow_query_threshold
                }
                self.metrics['slow_queries'].append(slow_query)
                self.logger.warning(f"慢查詢檢測: {query_type} - {execution_time:.2f}s")

            # 限制指標存儲大小
            if len(self.metrics['queries']) > 1000:
                self.metrics['queries'] = self.metrics['queries'][-500:]

    def collect_system_metrics(self):
        """收集系統效能指標"""
        if not self.enabled:
            return

        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            system_metric = {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used_gb': memory.used / (1024**3),
                'memory_total_gb': memory.total / (1024**3),
                'disk_percent': disk.percent,
                'disk_used_gb': disk.used / (1024**3),
                'disk_total_gb': disk.total / (1024**3)
            }

            self.metrics['system'].append(system_metric)

            # 限制系統指標存儲大小
            if len(self.metrics['system']) > 100:
                self.metrics['system'] = self.metrics['system'][-50:]

        except Exception as e:
            self.logger.error(f"收集系統指標失敗: {e}")

    def collect_database_metrics(self):
        """收集資料庫效能指標"""
        if not self.enabled:
            return

        try:
            # MySQL 連線數
            engine = self._get_mysql_connection()
            with engine.connect() as conn:
                result = conn.execute(text("SHOW PROCESSLIST"))
                mysql_connections = len(result.fetchall())

                result = conn.execute(text("SHOW ENGINE INNODB STATUS"))
                innodb_status = result.fetchone()

            # MongoDB 連線數
            mongo_client = self._get_mongo_connection()
            mongo_connections = len(mongo_client.server_info().get('connections', {}))

            # Redis 連線數
            redis_client = self._get_redis_connection()
            redis_info = redis_client.info()
            redis_connections = redis_info.get('connected_clients', 0)

            db_metric = {
                'timestamp': datetime.now().isoformat(),
                'mysql_connections': mysql_connections,
                'mongodb_connections': mongo_connections,
                'redis_connections': redis_connections,
                'redis_memory_used': redis_info.get('used_memory_human', '0B')
            }

            self.metrics['connections'] = db_metric

        except Exception as e:
            self.logger.error(f"收集資料庫指標失敗: {e}")

    def analyze_slow_queries(self) -> List[Dict[str, Any]]:
        """分析慢查詢"""
        slow_queries = self.metrics['slow_queries'][-100:]  # 最近100個慢查詢

        analysis = []
        for query in slow_queries:
            analysis.append({
                'timestamp': query['timestamp'],
                'query_type': query['type'],
                'execution_time': query['execution_time'],
                'cpu_usage': query['cpu_usage'],
                'memory_usage': query['memory_usage'],
                'recommendations': self._generate_recommendations(query)
            })

        return analysis

    def _generate_recommendations(self, query_metric: Dict[str, Any]) -> List[str]:
        """根據查詢指標生成優化建議"""
        recommendations = []

        execution_time = query_metric.get('execution_time', 0)
        cpu_usage = query_metric.get('cpu_usage', 0)
        memory_usage = query_metric.get('memory_usage', 0)

        if execution_time > 10:
            recommendations.append("查詢執行時間過長，建議檢查索引使用情況")
        if cpu_usage > 50:
            recommendations.append("CPU 使用率過高，建議優化查詢邏輯或增加硬體資源")
        if memory_usage > 20:
            recommendations.append("記憶體使用率過高，建議檢查資料大小或分頁處理")

        if query_metric.get('type') == 'mysql':
            recommendations.append("考慮使用 EXPLAIN 分析查詢執行計劃")

        return recommendations

    def get_performance_report(self) -> Dict[str, Any]:
        """生成效能報告"""
        if not self.enabled:
            return {"status": "disabled"}

        # 計算平均效能指標
        queries = self.metrics['queries'][-100:]
        if queries:
            avg_execution_time = sum(q['execution_time'] for q in queries) / len(queries)
            avg_cpu_usage = sum(q['cpu_usage'] for q in queries) / len(queries)
            avg_memory_usage = sum(q['memory_usage'] for q in queries) / len(queries)
        else:
            avg_execution_time = avg_cpu_usage = avg_memory_usage = 0

        # 系統資源使用情況
        system_metrics = self.metrics['system'][-10:]
        if system_metrics:
            avg_system_cpu = sum(m['cpu_percent'] for m in system_metrics) / len(system_metrics)
            avg_system_memory = sum(m['memory_percent'] for m in system_metrics) / len(system_metrics)
        else:
            avg_system_cpu = avg_system_memory = 0

        report = {
            'timestamp': datetime.now().isoformat(),
            'status': 'enabled',
            'query_performance': {
                'total_queries': len(self.metrics['queries']),
                'slow_queries_count': len(self.metrics['slow_queries']),
                'avg_execution_time': avg_execution_time,
                'avg_cpu_usage': avg_cpu_usage,
                'avg_memory_usage': avg_memory_usage
            },
            'system_performance': {
                'avg_cpu_percent': avg_system_cpu,
                'avg_memory_percent': avg_system_memory,
                'connections': self.metrics['connections']
            },
            'slow_queries_analysis': self.analyze_slow_queries(),
            'recommendations': self._generate_overall_recommendations()
        }

        return report

    def _generate_overall_recommendations(self) -> List[str]:
        """生成整體優化建議"""
        recommendations = []

        # 基於整體指標的建議
        query_count = len(self.metrics['queries'])
        slow_query_count = len(self.metrics['slow_queries'])

        if slow_query_count > query_count * 0.1:  # 慢查詢佔比超過10%
            recommendations.append("慢查詢比例過高，建議進行索引優化和查詢優化")

        if self.metrics['connections'].get('mysql_connections', 0) > 50:
            recommendations.append("MySQL 連線數過多，建議優化連線池配置")

        if self.metrics['connections'].get('redis_connections', 0) > 100:
            recommendations.append("Redis 連線數過多，建議檢查連線管理")

        return recommendations

    def start_monitoring(self):
        """啟動效能監控"""
        if not self.enabled:
            return

        def monitoring_loop():
            while not self.stop_monitoring:
                try:
                    self.collect_system_metrics()
                    self.collect_database_metrics()
                    time.sleep(60)  # 每分鐘收集一次
                except Exception as e:
                    self.logger.error(f"監控循環錯誤: {e}")
                    time.sleep(30)

        self.monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        self.logger.info("效能監控已啟動")

    def stop_monitoring(self):
        """停止效能監控"""
        if self.monitoring_thread:
            self.stop_monitoring = True
            self.monitoring_thread.join(timeout=5)
            self.logger.info("效能監控已停止")

    def export_metrics(self, filepath: str):
        """匯出效能指標"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.metrics, f, indent=2, ensure_ascii=False)
            self.logger.info(f"效能指標已匯出到 {filepath}")

        except Exception as e:
            self.logger.error(f"匯出效能指標失敗: {e}")

    def clear_metrics(self):
        """清除效能指標"""
        self.metrics = {
            'queries': [],
            'system': [],
            'connections': {},
            'slow_queries': []
        }
        self.logger.info("效能指標已清除")


# 全域效能監控實例
_performance_monitor = None


def get_performance_monitor(config_path='config.yml') -> PerformanceMonitor:
    """獲取效能監控實例"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor(config_path)
    return _performance_monitor


def monitor_query(query_type: str, query_details: str = ""):
    """查詢監控裝飾器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            with monitor.monitor_query(query_type, query_details):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# 方便使用的上下文管理器
def performance_monitor(query_type: str, query_details: str = ""):
    """效能監控上下文管理器"""
    monitor = get_performance_monitor()
    return monitor.monitor_query(query_type, query_details)
