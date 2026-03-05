"""
效能監控服務單元測試

測試 PerformanceMonitor 類別的各項功能
"""

import unittest
import time
from unittest.mock import Mock, patch

from src.Common.PerformanceMonitor import PerformanceMonitor, get_performance_monitor


class TestPerformanceMonitor(unittest.TestCase):

    def setUp(self):
        """測試前準備"""
        self.config = {
            'monitoring': {
                'enable_performance_monitoring': True,
                'slow_query_threshold': 1.0
            }
        }

    def tearDown(self):
        """測試後清理"""
        # 清理全域實例
        import src.Common.PerformanceMonitor
        src.Common.PerformanceMonitor._performance_monitor = None

    @patch('src.Common.PerformanceMonitor.yaml.safe_load')
    @patch('builtins.open')
    def test_initialization(self, mock_open, mock_yaml):
        """測試初始化"""
        mock_yaml.return_value = self.config

        monitor = PerformanceMonitor('config.yml')

        self.assertTrue(monitor.enabled)
        self.assertEqual(monitor.slow_query_threshold, 1.0)
        self.assertIsInstance(monitor.metrics, dict)
        self.assertIn('queries', monitor.metrics)
        self.assertIn('system', monitor.metrics)

    @patch('src.Common.PerformanceMonitor.yaml.safe_load')
    @patch('builtins.open')
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_collect_system_metrics(self, mock_disk, mock_memory, mock_cpu, mock_open, mock_yaml):
        """測試系統指標收集"""
        mock_yaml.return_value = self.config
        mock_cpu.return_value = 45.5
        mock_memory.return_value = Mock(percent=67.8, used=6871947673, total=10737418240)
        mock_disk.return_value = Mock(percent=23.4, used=107374182400, total=500000000000)

        monitor = PerformanceMonitor('config.yml')
        monitor.collect_system_metrics()

        self.assertEqual(len(monitor.metrics['system']), 1)
        system_metric = monitor.metrics['system'][0]

        self.assertEqual(system_metric['cpu_percent'], 45.5)
        self.assertEqual(system_metric['memory_percent'], 67.8)
        self.assertAlmostEqual(system_metric['memory_used_gb'], 6.4, places=1)
        self.assertAlmostEqual(system_metric['disk_percent'], 23.4)

    @patch('src.Common.PerformanceMonitor.yaml.safe_load')
    @patch('builtins.open')
    def test_monitor_query_context_manager(self, mock_open, mock_yaml):
        """測試查詢監控上下文管理器"""
        mock_yaml.return_value = self.config

        monitor = PerformanceMonitor('config.yml')

        # 測試正常執行
        with monitor.monitor_query("test_query", "SELECT * FROM test"):
            time.sleep(0.01)  # 短暫延遲

        self.assertEqual(len(monitor.metrics['queries']), 1)
        query_metric = monitor.metrics['queries'][0]

        self.assertEqual(query_metric['type'], "test_query")
        self.assertEqual(query_metric['details'], "SELECT * FROM test")
        self.assertGreater(query_metric['execution_time'], 0)
        self.assertIsInstance(query_metric['timestamp'], str)

    @patch('src.Common.PerformanceMonitor.yaml.safe_load')
    @patch('builtins.open')
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    def test_slow_query_detection(self, mock_memory, mock_cpu, mock_open, mock_yaml):
        """測試慢查詢檢測"""
        config = self.config.copy()
        config['monitoring']['slow_query_threshold'] = 0.1  # 設定較低的閾值
        mock_yaml.return_value = config

        mock_cpu.return_value = 10.0
        mock_memory.return_value = Mock(percent=50.0)

        monitor = PerformanceMonitor('config.yml')

        # 執行慢查詢
        with monitor.monitor_query("slow_query", "SELECT * FROM large_table"):
            time.sleep(0.2)  # 超過閾值

        self.assertEqual(len(monitor.metrics['slow_queries']), 1)
        slow_query = monitor.metrics['slow_queries'][0]

        self.assertEqual(slow_query['type'], "slow_query")
        self.assertGreater(slow_query['execution_time'], 0.1)
        self.assertEqual(slow_query['threshold'], 0.1)

    @patch('src.Common.PerformanceMonitor.yaml.safe_load')
    @patch('builtins.open')
    def test_performance_report_generation(self, mock_open, mock_yaml):
        """測試效能報告生成"""
        mock_yaml.return_value = self.config

        monitor = PerformanceMonitor('config.yml')

        # 添加一些測試資料
        monitor.metrics['queries'] = [
            {'execution_time': 0.5, 'cpu_usage': 10.0, 'memory_usage': 5.0},
            {'execution_time': 1.5, 'cpu_usage': 15.0, 'memory_usage': 8.0},
            {'execution_time': 2.5, 'cpu_usage': 20.0, 'memory_usage': 12.0}
        ]
        monitor.metrics['slow_queries'] = [
            {'execution_time': 2.5, 'cpu_usage': 20.0, 'memory_usage': 12.0}
        ]

        report = monitor.get_performance_report()

        self.assertIn('query_performance', report)
        self.assertIn('system_performance', report)
        self.assertIn('slow_queries_analysis', report)
        self.assertIn('recommendations', report)

        query_perf = report['query_performance']
        self.assertEqual(query_perf['total_queries'], 3)
        self.assertEqual(query_perf['slow_queries_count'], 1)
        self.assertAlmostEqual(query_perf['avg_execution_time'], 1.5, places=1)

    @patch('src.Common.PerformanceMonitor.yaml.safe_load')
    @patch('builtins.open')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_metrics_export(self, mock_file, mock_open, mock_yaml):
        """測試指標匯出"""
        mock_yaml.return_value = self.config

        monitor = PerformanceMonitor('config.yml')
        monitor.metrics['queries'] = [{'test': 'data'}]

        monitor.export_metrics('test_metrics.json')

        # 驗證檔案寫入
        mock_file.assert_called_once_with('test_metrics.json', 'w', encoding='utf-8')
        handle = mock_file()
        handle.write.assert_called_once()

    @patch('src.Common.PerformanceMonitor.yaml.safe_load')
    @patch('builtins.open')
    def test_metrics_cleanup(self, mock_open, mock_yaml):
        """測試指標清理"""
        mock_yaml.return_value = self.config

        monitor = PerformanceMonitor('config.yml')
        monitor.metrics['queries'] = [{'test': 'data'}]
        monitor.metrics['slow_queries'] = [{'slow': 'query'}]

        monitor.clear_metrics()

        self.assertEqual(len(monitor.metrics['queries']), 0)
        self.assertEqual(len(monitor.metrics['slow_queries']), 0)
        self.assertEqual(len(monitor.metrics['system']), 0)
        self.assertEqual(len(monitor.metrics['connections']), 0)

    @patch('src.Common.PerformanceMonitor.yaml.safe_load')
    @patch('builtins.open')
    def test_disabled_monitoring(self, mock_open, mock_yaml):
        """測試停用監控"""
        config = self.config.copy()
        config['monitoring']['enable_performance_monitoring'] = False
        mock_yaml.return_value = config

        monitor = PerformanceMonitor('config.yml')

        self.assertFalse(monitor.enabled)

        # 測試上下文管理器在停用時不收集指標
        with monitor.monitor_query("test", "SELECT 1"):
            pass

        self.assertEqual(len(monitor.metrics['queries']), 0)

    @patch('src.Common.PerformanceMonitor.yaml.safe_load')
    @patch('builtins.open')
    def test_get_performance_monitor_singleton(self, mock_open, mock_yaml):
        """測試單例模式"""
        mock_yaml.return_value = self.config

        monitor1 = get_performance_monitor('config.yml')
        monitor2 = get_performance_monitor('config.yml')

        self.assertIs(monitor1, monitor2)

    @patch('src.Common.PerformanceMonitor.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.PerformanceMonitor.PerformanceMonitor.collect_database_metrics')
    def test_monitoring_thread(self, mock_collect_db, mock_open, mock_yaml):
        """測試監控執行緒"""
        mock_yaml.return_value = self.config

        monitor = PerformanceMonitor('config.yml')

        # 等待一下讓監控執行緒運行
        time.sleep(0.1)

        # 停止監控
        monitor.stop_monitoring()

        # 驗證執行緒已停止
        self.assertIsNone(monitor.monitoring_thread)


if __name__ == '__main__':
    unittest.main()
