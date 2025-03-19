import Globals
from StockInfos import UserInfoDatas
from UpdateStockService import UpdateStockService


class ScheduleService:
    def __init__(self) -> None:
        self.updateStockService: UpdateStockService = UpdateStockService()

    def RunScheduleNow(self, MainUserInfoDatas: UserInfoDatas):
        self.updateStockService.isUpdating = True
        Globals.THREADPOOL.submit_task(
            self.updateStockService.UpdateAllStocksHandle,
            MainUserInfoDatas=MainUserInfoDatas,
        )
        Globals.THREADPOOL.submit_task(self.updateStockService.UpdateStocksHandle, delay=1800)
        Globals.THREADPOOL.submit_task(self.updateStockService.UpdateADLHandle, delay=1800)

    def StopThreadSchedule(self):
        Globals.THREADPOOL.shutdown()
        print("thread all stop")
