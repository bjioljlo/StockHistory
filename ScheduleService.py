from StockInfos import UserInfoDatas
from ThreadPool import ThreadPool
from UpdateStockService import UpdateStockService


class ScheduleService:
    def __init__(self, thread_pool: ThreadPool, update_stockService: UpdateStockService) -> None:
        self.updateStockService = update_stockService
        self.thread_pool = thread_pool

    def RunUpdateInfoNow(self, MainUserInfoDatas: UserInfoDatas, progress_callback=None):
        self.updateStockService.isUpdating = True
        self.thread_pool.enable_queue_mode(True)
        self.thread_pool.submit_task(
            self.updateStockService.UpdateTaiwanStocksHandle,
            MainUserInfoDatas=MainUserInfoDatas,
            callback=progress_callback
        )
        self.thread_pool.enable_queue_mode(False)
        
    def RunUpdateInfoNow_sp500(self, MainUserInfoDatas: UserInfoDatas, progress_callback=None):
        self.updateStockService.isUpdating = True
        self.thread_pool.enable_queue_mode(True)
        self.thread_pool.submit_task(
            self.updateStockService.UpdateSP500StocksHandle,
            MainUserInfoDatas=MainUserInfoDatas,
            callback=progress_callback
        )
        self.thread_pool.enable_queue_mode(False)

    def RunSyncToMongo(self, progress_callback=None):
        self.updateStockService.isUpdating = True
        self.thread_pool.enable_queue_mode(True)
        self.thread_pool.submit_task(
            self.updateStockService.UpdateMongoHandle,
            callback=progress_callback
        )
        self.thread_pool.enable_queue_mode(False)

    def RunUpdateADLNow(self, progress_callback=None):
        self.updateStockService.isUpdating = True
        self.thread_pool.submit_task(self.updateStockService.UpdateADLHandle, callback=progress_callback)

    def StopThreadSchedule(self):
        print("開始清理異步內存")
        self.thread_pool.shutdown()
        print("thread all stop")