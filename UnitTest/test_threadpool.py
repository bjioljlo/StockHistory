# test_concurrent_utils.py
import unittest
import time
from src.Common.ConcurrentUtils import ConcurrentUtils


class TestConcurrentUtils(unittest.TestCase):
    def setUp(self):
        """在每個測試之前初始化併發工具"""
        self.concurrent_utils = ConcurrentUtils(max_workers=3)

    def tearDown(self):
        """在每個測試之後關閉執行緒池"""
        self.concurrent_utils.shutdown()

    def test_task_execution(self):
        """測試任務是否能正確執行並返回結果"""

        def simple_task(x):
            print(f"[{time.strftime('%H:%M:%S')}] 執行 simple_task")
            time.sleep(0.1)
            return x * 2

        future = self.concurrent_utils.submit_task(simple_task, None, x=5)
        result = future.result(timeout=1.0)
        print(f"[{time.strftime('%H:%M:%S')}] 任務完成，結果: {result}")

        self.assertEqual(result, 10, "任務結果應為 5 * 2 = 10")

    def test_callback_execution(self):
        """測試回調函數是否正確執行"""
        callback_result = []

        def callback(result):
            callback_result.append(result)

        def simple_task(x):
            time.sleep(0.1)
            return x * 2

        self.concurrent_utils.submit_task(simple_task, callback, x=5)
        time.sleep(0.2)  # 給予足夠時間完成
        self.assertEqual(len(callback_result), 1)
        self.assertEqual(callback_result[0], 10)

    def test_non_blocking_behavior(self):
        """測試提交任務是否為非阻塞"""
        start_time = time.time()

        def long_task():
            time.sleep(0.5)  # 模擬長耗時任務

        self.concurrent_utils.submit_task(long_task)
        elapsed_time = time.time() - start_time

        # 提交任務應該幾乎立即完成（非阻塞）
        self.assertLess(elapsed_time, 0.1)

    def test_multiple_tasks(self):
        """測試多個任務是否都能正確執行"""

        def simple_task(x):
            time.sleep(0.1)
            return x * 2

        futures = []
        tasks = [1, 2, 3, 4]
        for i in tasks:
            future = self.concurrent_utils.submit_task(simple_task, None, x=i)
            futures.append(future)

        self.concurrent_utils.wait_all()
        results = [f.result() for f in futures]

        self.assertEqual(len(results), len(tasks))
        expected_results = [i * 2 for i in tasks]
        self.assertEqual(sorted(results), sorted(expected_results))

    def test_wait_all(self):
        """測試 wait_all 是否能等待所有任務完成"""

        def long_task():
            time.sleep(0.2)

        futures = []
        for _ in range(3):
            future = self.concurrent_utils.submit_task(long_task)
            futures.append(future)

        start_time = time.time()
        self.concurrent_utils.wait_all()
        elapsed_time = time.time() - start_time

        # 應該等待所有任務完成，時間應大於最長任務時間
        self.assertGreaterEqual(elapsed_time, 0.2)

    def test_exception_handling(self):
        """測試任務拋出異常時是否能正確處理"""

        def failing_task():
            time.sleep(0.1)
            raise ValueError("模擬錯誤")

        future1 = self.concurrent_utils.submit_task(failing_task)
        time.sleep(0.2)  # 給予足夠時間完成

        # 檢查是否能繼續處理其他任務
        def normal_task():
            return "正常"

        future2 = self.concurrent_utils.submit_task(normal_task)
        time.sleep(0.2)
        result = future2.result()
        self.assertEqual(result, "正常")

        # 第一個任務應該拋出異常
        with self.assertRaises(ValueError):
            future1.result()


if __name__ == "__main__":
    unittest.main()
