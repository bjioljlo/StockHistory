from src.StockInfos import UserInfoDatas
from src.Common.ConcurrentUtils import ConcurrentUtils
from src.UpdateStockService import UpdateStockService
from src.Common.CacheService import HybridCacheService



class ScheduleService:
    def __init__(self, concurrent_utils: ConcurrentUtils, update_stockService: UpdateStockService, cache_service: HybridCacheService=None) -> None:
        self.updateStockService = update_stockService
        self.concurrent_utils = concurrent_utils
        self.cache_service = cache_service

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

    def RunOtherSchedule(self, progress_callback=None):
        """執行其他排程任務，包括快取維護"""
        print("Update stocks other Info start!")

        # 新增：快取維護
        if self.cache_service:
            print("Performing cache maintenance...")

            # 更新快取
            self.cache_service.update_mongo_cache()

            # 清理冷門快取（每週執行一次）
            import datetime
            if datetime.datetime.now().weekday() == 6:  # 星期日
                self.cache_service.cleanup_cold_mongo_cache()

            print("Cache maintenance completed!")

        # 現有的 ADL 更新邏輯
        self.updateStockService.isUpdating = True
        self.concurrent_utils.submit_task(
            self.updateStockService.UpdateADLHandle,
            progress_callback
        )

        print("Update stocks other Info end!")

    def StopThreadSchedule(self):
        print("開始清理異步內存")
        self.concurrent_utils.shutdown()
        print("thread all stop")
