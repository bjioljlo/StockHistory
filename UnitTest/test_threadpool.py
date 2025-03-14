# non_blocking_threadpool/test_threadpool.py
import unittest
import time
from ThreadPool import ThreadPool


class TestNonBlockingThreadPool(unittest.TestCase):
    def setUp(self):
        """在每個測試之前初始化線程池"""
        self.threadpool = ThreadPool(max_workers=3)

    def tearDown(self):
        """在每個測試之後關閉線程池"""
        self.threadpool.shutdown()

    def test_task_execution(self):
        """測試任務是否能正確執行並返回結果"""

        def simple_task(x):
            time.sleep(0.1)  # 模擬短暫耗時
            return x * 2

        self.threadpool.submit_task(simple_task, None, x=5)
        time.sleep(0.2)  # 給予足夠時間完成
        results = self.threadpool.check_completed()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], 10)

    def test_callback_execution(self):
        """測試回調函數是否正確執行"""
        callback_result = []

        def callback(result):
            callback_result.append(result)

        def simple_task(x):
            time.sleep(0.1)
            return x * 2

        self.threadpool.submit_task(simple_task, callback, x=5)
        time.sleep(0.2)  # 給予足夠時間完成
        self.assertEqual(len(callback_result), 1)
        self.assertEqual(callback_result[0], 10)

    def test_non_blocking_behavior(self):
        """測試提交任務是否為非阻塞"""
        start_time = time.time()

        def long_task():
            time.sleep(0.5)  # 模擬長耗時任務

        self.threadpool.submit_task(long_task)
        elapsed_time = time.time() - start_time

        # 提交任務應該幾乎立即完成（非阻塞）
        self.assertLess(elapsed_time, 0.1)

    def test_multiple_tasks(self):
        """測試多個任務是否都能正確執行"""

        def simple_task(x):
            time.sleep(0.1)
            return x * 2

        tasks = [1, 2, 3, 4]
        for i in tasks:
            self.threadpool.submit_task(simple_task, None, x=i)

        self.threadpool.wait_all()
        results = self.threadpool.check_completed()

        self.assertEqual(len(results), len(tasks))
        expected_results = [i * 2 for i in tasks]
        self.assertEqual(sorted(results), sorted(expected_results))

    def test_wait_all(self):
        """測試 wait_all 是否能等待所有任務完成"""

        def long_task():
            time.sleep(0.2)

        for _ in range(3):
            self.threadpool.submit_task(long_task)

        start_time = time.time()
        self.threadpool.wait_all()
        elapsed_time = time.time() - start_time

        # 應該等待所有任務完成，時間應大於最長任務時間
        self.assertGreaterEqual(elapsed_time, 0.2)
        results = self.threadpool.check_completed()
        self.assertEqual(len(results), 3)

    def test_exception_handling(self):
        """測試任務拋出異常時是否能正確處理"""

        def failing_task():
            time.sleep(0.1)
            raise ValueError("模擬錯誤")

        self.threadpool.submit_task(failing_task)
        time.sleep(0.2)  # 給予足夠時間完成

        # 檢查是否能繼續處理其他任務
        def normal_task():
            return "正常"

        self.threadpool.submit_task(normal_task)
        time.sleep(0.2)
        results = self.threadpool.check_completed()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], "正常")

    def test_check_completed_empty(self):
        """測試當沒有任務完成時，check_completed 是否返回空列表"""

        def long_task():
            time.sleep(0.5)

        self.threadpool.submit_task(long_task)
        results = self.threadpool.check_completed()

        self.assertEqual(len(results), 0)

    def test_delayed_task(self):
        """測試延遲執行是否正常"""

        def simple_task():
            return "delayed"

        start_time = time.time()
        self.threadpool.submit_task(simple_task, delay=1)
        time.sleep(0.5)  # 等待 0.5 秒，任務尚未執行
        results = self.threadpool.check_completed()
        self.assertEqual(len(results), 0)  # 任務應該尚未完成

        time.sleep(1)  # 再等待 1 秒，總共 1.5 秒，任務應該完成
        results = self.threadpool.check_completed()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], "delayed")

    def test_periodic_task(self):
        """測試定期執行是否正常"""
        results = []

        def callback(result):
            results.append(result)

        def simple_task():
            return "periodic"

        self.threadpool.submit_task(simple_task, callback, interval=0.5, repeat=True)
        time.sleep(2.0)  # 等待 1.6 秒，應該執行 3 次（0.5, 1.0, 1.5 秒）
        self.assertGreaterEqual(len(results), 3)  # 至少執行 3 次
        self.assertTrue(all(r == "periodic" for r in results))


if __name__ == "__main__":
    unittest.main()
