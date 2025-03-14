from concurrent.futures import ThreadPoolExecutor
from typing import Any, List, Callable
import threading
import time


class ScheduledTask:
    """表示一個排程任務的類"""

    def __init__(
        self,
        task: Callable,
        callback: Callable[[Any], None] = None,
        delay: float = None,
        interval: float = None,
        repeat: bool = False,
        *args,
        **kwargs,
    ):
        self.task = task
        self.callback = callback
        self.delay = delay
        self.interval = interval
        self.repeat = repeat
        self.args = args
        self.kwargs = kwargs
        # 如果有 delay，則 next_run 為當前時間加上 delay；否則為當前時間
        self.next_run = time.time() + delay if delay is not None else time.time()
        self.timer = None


class ThreadPool:

    def __init__(self, max_workers: int = 5):
        """
        初始化非阻塞線程池。

        Args:
            max_workers (int): 線程池中最大工作線程數，預設為 5。
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.futures: List[Any] = []  # 用於儲存 Future 物件
        self.scheduled_tasks: List[ScheduledTask] = []  # 用於儲存排程任務
        self.lock = threading.RLock()  # 用於保護 futures 列表
        self.running = True  # 控制排程器是否運行
        # 啟動排程檢查線程
        self.scheduler_thread = threading.Thread(
            target=self._run_scheduler, daemon=True
        )
        self.scheduler_thread.start()

    def submit_task(
        self,
        task: Callable,
        callback: Callable[[Any], None] = None,
        delay: float = None,
        interval: float = None,
        repeat: bool = False,
        *args,
        **kwargs,
    ) -> None:
        """
        提交一個任務到線程池，並允許指定回調函數。

        Args:
            task (Callable): 要執行的任務（函數）。
            callback (Callable): 任務完成後的回調函數（可選）。
            delay (float): 延遲多少秒後執行（可選）。
            interval (float): 定期執行的間隔秒數（可選）。
            repeat (bool): 是否定期重複執行（需要指定 interval）。
            *args, **kwargs: 傳遞給任務的參數。
        """
        scheduled_task = ScheduledTask(
            task, callback, delay, interval, repeat, *args, **kwargs
        )
        with self.lock:
            self.scheduled_tasks.append(scheduled_task)
        if delay is None and not repeat:
            # 如果沒有延遲且不定期執行，立即執行任務
            self._execute_task(scheduled_task)
        if delay and not repeat:
            # 如果有延遲但不定期執行，使用 Timer 延遲執行
            scheduled_task.timer = threading.Timer(
                delay, self._execute_task, [scheduled_task]
            )
            scheduled_task.timer.start()

    def _execute_task(self, scheduled_task: ScheduledTask) -> None:
        """執行一個排程任務，並提交到線程池"""
        # 提交任務到線程池
        future = self.executor.submit(
            self._wrap_task,
            scheduled_task.task,
            *scheduled_task.args,
            **scheduled_task.kwargs,
        )
        # 如果有回調函數，則添加完成時的回調
        if scheduled_task.callback:
            future.add_done_callback(lambda f: scheduled_task.callback(f.result()))
        # 將 future 儲存起來，以便後續檢查
        with self.lock:
            self.futures.append(future)

    def _wrap_task(self, task: Callable, *args, **kwargs) -> Any:
        """
        包裝任務，執行並返回結果。

        Args:
            task (Callable): 要執行的任務。
            *args, **kwargs: 傳遞給任務的參數。

        Returns:
            Any: 任務的執行結果。
        """
        try:
            return task(*args, **kwargs)
        except Exception as e:
            print(f"任務執行失敗: {e}")
            raise

    def _run_scheduler(self):
        """排程器主迴圈，檢查並執行定期任務"""
        while self.running:
            now = time.time()
            tasks_to_execute = []
            with self.lock:
                for scheduled_task in self.scheduled_tasks:
                    if scheduled_task.repeat and now >= scheduled_task.next_run:
                        self._execute_task(scheduled_task)
                        scheduled_task.next_run = now + scheduled_task.interval
            # 在鎖外執行任務，避免嵌套鎖
            for task in tasks_to_execute:
                print(f"[{time.strftime('%H:%M:%S')}] 執行定期任務")
                self._execute_task(task)
            time.sleep(0.05)  # 避免過高的 CPU 使用率

    def wait_all(self) -> None:
        """
        等待所有任務完成（阻塞方法）。
        """
        for future in self.futures:
            future.result()  # 等待每個 future 完成

    def check_completed(self) -> List[Any]:
        """
        檢查已完成的任務並返回結果，清空已完成的 future。

        Returns:
            List[Any]: 已完成任務的結果列表。
        """
        completed_results = []
        remaining_futures = []

        with self.lock:
            for future in self.futures:
                if future.done():
                    try:
                        result = future.result()
                        completed_results.append(result)
                    except Exception as e:
                        print(f"獲取結果時出錯: {e}")
                else:
                    remaining_futures.append(future)

            # 更新 futures 列表，只保留未完成的
            self.futures = remaining_futures

        return completed_results

    def shutdown(self) -> None:
        """
        關閉線程池，釋放資源。
        """
        self.running = False  # 停止排程器
        with self.lock:
            # 取消所有定時器
            for scheduled_task in self.scheduled_tasks:
                if scheduled_task.timer:
                    scheduled_task.timer.cancel()
        self.executor.shutdown(wait=True)
