# non_blocking_threadpool/test_threadpool.py
import unittest
import time
from src.ThreadPool import ThreadPool


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
            print(f"[{time.strftime('%H:%M:%S')}] 執行 simple_task")
            time.sleep(0.1)
            return x * 2

        self.threadpool.submit_task(simple_task, None, x=5)
        timeout = 1.0
        start_time = time.time()
        results = []
        while time.time() - start_time < timeout:
            results = self.threadpool.check_completed()
            if results:
                print(f"[{time.strftime('%H:%M:%S')}] 任務完成，結果: {results}")
                break
            time.sleep(0.01)

        self.assertEqual(len(results), 1, "任務應該已經完成並返回一個結果")
        self.assertEqual(results[0], 10, "任務結果應為 5 * 2 = 10")

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
            print(f"[{time.strftime('%H:%M:%S')}] 執行 delayed_task")
            return "delayed"

        start_time = time.time()
        self.threadpool.submit_task(simple_task, delay=1)
        time.sleep(0.5)
        results = self.threadpool.check_completed()
        print(f"[{time.strftime('%H:%M:%S')}] 延遲 0.5 秒後檢查: {results}")
        self.assertEqual(len(results), 0, "任務尚未執行")

        time.sleep(1)
        results = self.threadpool.check_completed()
        print(f"[{time.strftime('%H:%M:%S')}] 延遲 1.5 秒後檢查: {results}")
        self.assertEqual(len(results), 1, "任務應該完成")
        self.assertEqual(results[0], "delayed", "結果應為 'delayed'")

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

    def test_queue_execution(self):
        """測試列隊執行是否按順序執行"""
        results = []
        execution_order = []

        def ordered_task(id):
            start_time = time.time()
            time.sleep(0.2)  # 模擬耗時
            end_time = time.time()
            execution_order.append((id, start_time, end_time))
            print(f"[{time.strftime('%H:%M:%S')}] 執行任務 {id}")
            return f"result_{id}"

        self.threadpool.enable_queue_mode(True)  # 啟用列隊模式
        for i in range(3):
            self.threadpool.submit_task(ordered_task, lambda r: results.append(r), id=i)

        time.sleep(1.0)  # 等待所有任務完成
        self.threadpool.enable_queue_mode(False)  # 停用列隊模式

        self.assertEqual(len(results), 3, "應完成 3 個任務")
        self.assertEqual(
            results, ["result_0", "result_1", "result_2"], "結果應按順序返回"
        )

        # 檢查執行時間是否符合順序結束
        for i in range(len(execution_order) - 1):
            self.assertGreaterEqual(
                execution_order[i + 1][1],
                execution_order[i][2],
                f"任務{i + 1} 應在任務 {i} 結束後開始",
            )

    def test_mixed_tasks(self):
        """測試混合使用非列隊、列隊和延遲任務"""
        results = []

        def task(id, type):
            print(f"[{time.strftime('%H:%M:%S')}] 執行任務 {id} ({type})")
            time.sleep(0.1)
            return f"result_{id}_{type}"

        # 非列隊任務
        self.threadpool.submit_task(
            task, lambda r: results.append(r), id=1, type="normal"
        )
        # 啟用列隊模式並提交列隊任務
        self.threadpool.enable_queue_mode(True)
        self.threadpool.submit_task(
            task, lambda r: results.append(r), id=2, type="queue"
        )
        self.threadpool.submit_task(
            task, lambda r: results.append(r), id=3, type="queue"
        )

        # 延遲任務
        self.threadpool.submit_task(
            task, lambda r: results.append(r), id=4, type="delayed", delay=0.5
        )

        timeout = 1.0
        start_time = time.time()
        while time.time() - start_time < timeout:
            completed = self.threadpool.check_completed()
            if completed:
                # 避免重複添加，檢查結果是否已存在
                for result in completed:
                    if result not in results:
                        results.append(result)
            time.sleep(0.01)
        self.threadpool.enable_queue_mode(False)
        self.assertEqual(len(results), 4, "應完成 4 個任務")
        expected = [
            "result_1_normal",
            "result_2_queue",
            "result_3_queue",
            "result_4_delayed",
        ]
        self.assertTrue(
            all(r in results for r in expected), f"結果應包含所有任務: {results}"
        )

    def test_queue_mode_switch(self):
        """測試列隊模式的啟用和停用"""
        results = []

        def task(id):
            print(f"[{time.strftime('%H:%M:%S')}] 執行任務 {id}")
            time.sleep(0.1)
            return f"result_{id}"

        # 先以非列隊模式提交
        self.threadpool.submit_task(task, lambda r: results.append(r), id=1)
        # 啟用列隊模式
        self.threadpool.enable_queue_mode(True)
        self.threadpool.submit_task(task, lambda r: results.append(r), id=2)
        self.threadpool.submit_task(task, lambda r: results.append(r), id=3)
        # 停用列隊模式並提交

        self.threadpool.submit_task(task, lambda r: results.append(r), id=4)

        timeout = 1.0
        start_time = time.time()
        while time.time() - start_time < timeout:
            completed = self.threadpool.check_completed()
            if completed:
                # 避免重複添加
                for result in completed:
                    if result not in results:
                        results.append(result)
            time.sleep(0.01)

        self.threadpool.enable_queue_mode(False)
        self.assertEqual(len(results), 4, "應完成 4 個任務")
        expected = ["result_1", "result_2", "result_3", "result_4"]
        self.assertTrue(
            all(r in results for r in expected), f"結果應包含所有任務: {results}"
        )


if __name__ == "__main__":
    unittest.main()
