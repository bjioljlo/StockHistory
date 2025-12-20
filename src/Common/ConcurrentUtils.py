from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Any, List
import threading


class ConcurrentUtils:
    """簡化的併發工具類，基於 concurrent.futures"""

    def __init__(self, max_workers: int = 5):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.futures: List[Future] = []
        self.futures_lock = threading.RLock()

    def submit_task(self, task: Callable, callback: Callable[[Any], None] = None, *args, **kwargs) -> Future:
        """
        提交任務到執行緒池，可選回調函數。

        Args:
            task (Callable): 要執行的任務函數
            callback (Callable): 回調函數，可選（會作為 'callback' 參數傳遞給任務函數，讓任務在執行過程中調用）
            *args, **kwargs: 傳遞給任務的參數

        Returns:
            Future: 任務的 Future 物件
        """
        # 將callback作為參數傳遞給任務函數，讓任務在執行過程中調用
        if callback:
            kwargs['callback'] = callback

        future = self.executor.submit(task, *args, **kwargs)
        with self.futures_lock:
            self.futures.append(future)
        return future

    def submit_task_with_result_callback(self, task: Callable, result_callback: Callable[[Any], None] = None, *args, **kwargs) -> Future:
        """
        提交任務到執行緒池，任務完成後調用結果回調函數。

        Args:
            task (Callable): 要執行的任務函數
            result_callback (Callable): 任務完成後的回調函數，可選
            *args, **kwargs: 傳遞給任務的參數

        Returns:
            Future: 任務的 Future 物件
        """
        future = self.executor.submit(task, *args, **kwargs)
        if result_callback:
            def callback_wrapper(f):
                try:
                    result = f.result()
                    result_callback(result)
                except Exception as e:
                    print(f"Error in task callback: {e}")
                    import traceback
                    traceback.print_exc()
            future.add_done_callback(callback_wrapper)
        with self.futures_lock:
            self.futures.append(future)
        return future

    def submit_task_with_callback(self, task: Callable, callback: Callable[[Future], None] = None, *args, **kwargs) -> Future:
        """
        提交任務到執行緒池，可選 Future 回調函數。

        Args:
            task (Callable): 要執行的任務函數
            callback (Callable): Future 完成後的回調函數，可選（接收 Future 物件）
            *args, **kwargs: 傳遞給任務的參數

        Returns:
            Future: 任務的 Future 物件
        """
        future = self.executor.submit(task, *args, **kwargs)
        if callback:
            future.add_done_callback(callback)
        with self.futures_lock:
            self.futures.append(future)
        return future

    def submit_sequential(self, tasks: List[tuple]) -> List[Future]:
        """
        按順序提交任務，每個任務包含 (task_func, callback, *args, **kwargs)

        Args:
            tasks (List[tuple]): 任務列表，每個元組為 (task, callback, *args, **kwargs)

        Returns:
            List[Future]: Future 列表
        """
        futures = []
        for task_info in tasks:
            task, callback, *args = task_info
            kwargs = {}
            if args and callable(args[-1]):
                # 如果最後一個參數是函數，假設是 callback
                callback = args[-1]
                args = args[:-1]
            future = self.submit_task(task, callback, *args, **kwargs)
            futures.append(future)
            # 等待當前任務完成再提交下一個
            future.result()
        return futures

    def wait_all(self) -> None:
        """等待所有任務完成"""
        for future in self.futures:
            future.result()

    def shutdown(self) -> None:
        """關閉執行緒池"""
        self.executor.shutdown(wait=True)
