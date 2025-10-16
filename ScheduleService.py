from StockInfos import UserInfoDatas
from ThreadPool import ThreadPool
from UpdateStockService import UpdateStockService


class ScheduleService:
    def __init__(self, thread_pool: ThreadPool, update_stockService: UpdateStockService) -> None:
        self.updateStockService = update_stockService
        self.thread_pool = thread_pool

    def RunUpdateInfoNow(self, MainUserInfoDatas: UserInfoDatas):
        self.updateStockService.isUpdating = True
        self.thread_pool.enable_queue_mode(True)
        self.thread_pool.submit_task(
            self.updateStockService.UpdateTaiwanStocksHandle,
            MainUserInfoDatas=MainUserInfoDatas,
        )
        self.thread_pool.submit_task(self.updateStockService.UpdateSP500StocksHandle)
        self.thread_pool.submit_task(self.updateStockService.UpdateADLHandle)
        self.thread_pool.enable_queue_mode(False)
        
    def RunOtherInfoNow(self):
        self.updateStockService.isUpdating = True
        self.thread_pool.submit_task(self.updateStockService.UpdateADLHandle)

    def StopThreadSchedule(self):
        print("開始清理異步內存")
        self.thread_pool.shutdown()
        print("thread all stop")
