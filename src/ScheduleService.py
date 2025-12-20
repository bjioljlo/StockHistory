from src.StockInfos import UserInfoDatas
from src.Common.ConcurrentUtils import ConcurrentUtils
from src.UpdateStockService import UpdateStockService


class ScheduleService:
    def __init__(self, concurrent_utils: ConcurrentUtils, update_stockService: UpdateStockService) -> None:
        self.updateStockService = update_stockService
        self.concurrent_utils = concurrent_utils

    def RunUpdateInfoNow(self, MainUserInfoDatas: UserInfoDatas, progress_callback=None):
        self.updateStockService.isUpdating = True
        self.concurrent_utils.submit_task(
            self.updateStockService.UpdateTaiwanStocksHandle,
            progress_callback,
            MainUserInfoDatas=MainUserInfoDatas
        )
        
    def RunUpdateInfoNow_sp500(self, MainUserInfoDatas: UserInfoDatas, progress_callback=None):
        self.updateStockService.isUpdating = True
        self.concurrent_utils.submit_task(
            self.updateStockService.UpdateSP500StocksHandle,
            progress_callback,
            MainUserInfoDatas=MainUserInfoDatas
        )

    def RunSyncToMongo(self, progress_callback=None):
        self.updateStockService.isUpdating = True
        self.concurrent_utils.submit_task(
            self.updateStockService.UpdateMongoHandle,
            progress_callback
        )

    def RunUpdateADLNow(self, progress_callback=None):
        self.updateStockService.isUpdating = True
        self.concurrent_utils.submit_task(
            self.updateStockService.UpdateADLHandle,
            progress_callback
        )

    def StopThreadSchedule(self):
        print("開始清理異步內存")
        self.concurrent_utils.shutdown()
        print("thread all stop")
