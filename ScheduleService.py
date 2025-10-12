import Common.Globals as Globals
from StockInfos import UserInfoDatas
from UpdateStockService import UpdateStockService


class ScheduleService:
    def __init__(self) -> None:
        self.updateStockService: UpdateStockService = UpdateStockService()

    def RunUpdateInfoNow(self, MainUserInfoDatas: UserInfoDatas):
        self.updateStockService.isUpdating = True
        Globals.THREADPOOL.enable_queue_mode(True)
        Globals.THREADPOOL.submit_task(
            self.updateStockService.UpdateTaiwanStocksHandle,
            MainUserInfoDatas=MainUserInfoDatas,
        )
        Globals.THREADPOOL.submit_task(self.updateStockService.UpdateSP500StocksHandle)
        Globals.THREADPOOL.submit_task(self.updateStockService.UpdateADLHandle)
        Globals.THREADPOOL.enable_queue_mode(False)
        
    def RunOtherInfoNow(self):
        self.updateStockService.isUpdating = True
        Globals.THREADPOOL.submit_task(self.updateStockService.UpdateADLHandle)

    def StopThreadSchedule(self):
        print("開始清理異步內存")
        Globals.THREADPOOL.shutdown()
        print("thread all stop")
