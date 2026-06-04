"""
效能監控服務單元測試

測試 PerformanceMonitor 類別的各項功能
針對重構後的新實作版本
"""

import unittest
import time
from unittest.mock import Mock, patch

from pyutils_core.performance import (
    PerformanceMonitor,
    PerformanceMetrics,
    TimedBlock,
    get_performance_monitor,
    performance_monitor,
    profile,
    timed_block
)


class TestPerformanceMetrics(unittest.TestCase):
    """測試 PerformanceMetrics 類別"""

    def setUp(self):
        self.metrics = PerformanceMetrics(max_history_size=10)

    def test_increment_counter(self):
        """測試計數器增加"""
        self.metrics.increment('test.counter')
        self.assertEqual(self.metrics.get_counter('test.counter'), 1)

        self.metrics.increment('test.counter', 5)
        self.assertEqual(self.metrics.get_counter('test.counter'), 6)

    def test_counter_for_nonexistent(self):
        """測試不存在的計數器傳回0"""
        self.assertEqual(self.metrics.get_counter('nonexistent'), 0)

    def test_start_stop_timer(self):
        """測試計時器啟動與停止"""
        self.metrics.start_timer('test.timer')
        time.sleep(0.01)
        duration = self.metrics.stop_timer('test.timer')

        self.assertGreater(duration, 0)
        self.assertLess(duration, 0.1)

        stats = self.metrics.get_timer_stats('test.timer')
        self.assertEqual(stats['count'], 1)
        self.assertGreater(stats['avg'], 0)

    def test_stop_nonexistent_timer(self):
        """測試停止不存在的計時器"""
        duration = self.metrics.stop_timer('nonexistent')
        self.assertEqual(duration, 0.0)

    def test_record_duration(self):
        """測試直接記錄時間"""
        self.metrics.record_duration('test.timer', 0.5)
        self.metrics.record_duration('test.timer', 1.5)

        stats = self.metrics.get_timer_stats('test.timer')
        self.assertEqual(stats['count'], 2)
        self.assertEqual(stats['avg'], 1.0)
        self.assertEqual(stats['min'], 0.5)
        self.assertEqual(stats['max'], 1.5)
        self.assertEqual(stats['total'], 2.0)

    def test_timer_stats_empty(self):
        """測試空計時器的統計資訊"""
        stats = self.metrics.get_timer_stats('empty')
        self.assertEqual(stats['count'], 0)
        self.assertEqual(stats['avg'], 0.0)
        self.assertEqual(stats['min'], 0.0)
        self.assertEqual(stats['max'], 0.0)
        self.assertEqual(stats['total'], 0.0)

    def test_get_all_metrics(self):
        """測試取得所有指標"""
        self.metrics.increment('test.counter', 3)
        self.metrics.record_duration('test.timer', 0.1)

        all_metrics = self.metrics.get_all_metrics()
        self.assertIn('counters', all_metrics)
        self.assertIn('timers', all_metrics)
        self.assertIn('timestamp', all_metrics)
        self.assertEqual(all_metrics['counters']['test.counter'], 3)

    def test_reset_metrics(self):
        """測試重設所有指標"""
        self.metrics.increment('test.counter', 5)
        self.metrics.record_duration('test.timer', 0.5)
        self.metrics.reset()

        self.assertEqual(self.metrics.get_counter('test.counter'), 0)
        stats = self.metrics.get_timer_stats('test.timer')
        self.assertEqual(stats['count'], 0)

    def test_max_history_size(self):
        """測試最大歷史記錄大小限制"""
        for i in range(15):
            self.metrics.record_duration('test.timer', float(i))

        stats = self.metrics.get_timer_stats('test.timer')
        self.assertEqual(stats['count'], 10)  # 應該只保留最後10筆


class TestPerformanceMonitor(unittest.TestCase):
    """測試 PerformanceMonitor 類別"""

    def setUp(self):
        """測試前重設單例實例"""
        PerformanceMonitor._instance = None
        self.monitor = PerformanceMonitor()

    def tearDown(self):
        """測試後清理"""
        PerformanceMonitor._instance = None

    def test_singleton_pattern(self):
        """測試單例模式"""
        monitor1 = PerformanceMonitor()
        monitor2 = PerformanceMonitor()
        self.assertIs(monitor1, monitor2)

    def test_get_performance_monitor_function(self):
        """測試 get_performance_monitor 相容性函式"""
        monitor = get_performance_monitor()
        self.assertIsInstance(monitor, PerformanceMonitor)
        self.assertIs(monitor, performance_monitor)

    def test_initialization(self):
        """測試初始化"""
        self.assertTrue(self.monitor.enabled)
        self.assertIsInstance(self.monitor.metrics, PerformanceMetrics)

    def test_profile_decorator(self):
        """測試 profile 裝飾器"""
        @self.monitor.profile('test.function')
        def test_func():
            time.sleep(0.01)
            return "result"

        result = test_func()
        self.assertEqual(result, "result")

        stats = self.monitor.metrics.get_timer_stats('test.function')
        self.assertEqual(stats['count'], 1)
        self.assertGreater(stats['avg'], 0)

    def test_profile_decorator_with_disabled(self):
        """測試關閉監控時的 profile 裝飾器"""
        self.monitor.enabled = False

        @self.monitor.profile('test.function')
        def test_func():
            return "result"

        result = test_func()
        self.assertEqual(result, "result")

        stats = self.monitor.metrics.get_timer_stats('test.function')
        self.assertEqual(stats['count'], 0)

    def test_timed_block_context_manager(self):
        """測試 timed_block 上下文管理器"""
        with self.monitor.timed_block('test.block'):
            time.sleep(0.01)

        stats = self.monitor.metrics.get_timer_stats('test.block')
        self.assertEqual(stats['count'], 1)
        self.assertGreater(stats['avg'], 0)

    def test_convenience_functions(self):
        """測試便利函式"""
        @profile('test.convenience')
        def test_func():
            return "result"

        result = test_func()
        self.assertEqual(result, "result")

        with timed_block('test.convenience_block'):
            pass

        stats1 = performance_monitor.metrics.get_timer_stats('test.convenience')
        stats2 = performance_monitor.metrics.get_timer_stats('test.convenience_block')
        self.assertEqual(stats1['count'], 1)
        self.assertEqual(stats2['count'], 1)

    def test_increment_counter(self):
        """測試遞增計數器"""
        self.monitor.increment_counter('test.counter')
        self.assertEqual(self.monitor.metrics.get_counter('test.counter'), 1)

    def test_cache_hit_miss_tracking(self):
        """測試快取命中/未命中追蹤"""
        self.monitor.record_cache_hit('L1')
        self.monitor.record_cache_hit('L1')
        self.monitor.record_cache_miss('L1')

        self.assertEqual(self.monitor.metrics.get_counter('cache.l1.hits'), 2)
        self.assertEqual(self.monitor.metrics.get_counter('cache.l1.misses'), 1)
        self.assertEqual(self.monitor.get_cache_hit_ratio('L1'), 2/3)

    def test_cache_hit_ratio_empty(self):
        """測試空快取的命中率"""
        self.assertEqual(self.monitor.get_cache_hit_ratio('L1'), 0.0)

    def test_get_report(self):
        """測試產生效能報告"""
        self.monitor.record_cache_hit('L1')
        self.monitor.record_cache_miss('L1')
        self.monitor.record_cache_hit('L2')

        report = self.monitor.get_report()
        self.assertIn('metrics', report)
        self.assertIn('cache_stats', report)
        self.assertIn('generated_at', report)
        self.assertEqual(report['cache_stats']['L1']['hit_ratio'], 0.5)
        self.assertEqual(report['cache_stats']['L2']['hit_ratio'], 1.0)

    def test_reset_metrics(self):
        """測試重設指標"""
        self.monitor.record_cache_hit('L1')
        self.monitor.reset_metrics()
        self.assertEqual(self.monitor.metrics.get_counter('cache.l1.hits'), 0)


class TestTimedBlock(unittest.TestCase):
    """測試 TimedBlock 類別"""

    def setUp(self):
        self.monitor = Mock(spec=PerformanceMonitor)
        self.monitor.metrics = Mock()

    def test_timed_block_execution(self):
        """測試 TimedBlock 執行"""
        block = TimedBlock(self.monitor, 'test.op')
        block.__enter__()
        time.sleep(0.01)
        block.__exit__(None, None, None)

        self.monitor.metrics.record_duration.assert_called_once()
        args = self.monitor.metrics.record_duration.call_args
        self.assertEqual(args[0][0], 'test.op')
        self.assertGreater(args[0][1], 0)

    def test_timed_block_does_not_suppress_exceptions(self):
        """測試 TimedBlock 不會抑制例外"""
        block = TimedBlock(self.monitor, 'test.op')
        block.__enter__()

        # TimedBlock.__exit__ returns False to not suppress exceptions
        result = block.__exit__(ValueError, ValueError("test error"), None)
        self.assertFalse(result)

        self.monitor.metrics.record_duration.assert_called_once()


if __name__ == '__main__':
    unittest.main()