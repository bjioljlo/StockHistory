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
        
    def RunSyncToMongo(self):
        self.updateStockService.isUpdating = True
        all_tables = self.updateStockService._sql_service.get_all_table_names()
        
        for table_name in all_tables:
            self.thread_pool.submit_task(self._sync_table_to_mongo, table_name=table_name)

    def _sync_table_to_mongo(self, table_name: str):
        """
        Reads a table from MySQL and saves it to MongoDB.
        """
        print(f"Syncing table {table_name} to MongoDB...")
        df = self.updateStockService._sql_service.readStockDay(table_name)
        if not df.empty:
            self.updateStockService._mongo_service.saveTable(table_name, df)
            print(f"Successfully synced table {table_name} to MongoDB.")
        else:
            print(f"Skipping empty table: {table_name}")
        
        
    def RunOtherInfoNow(self):
        self.updateStockService.isUpdating = True
        self.thread_pool.submit_task(self.updateStockService.UpdateADLHandle)

    def StopThreadSchedule(self):
        print("開始清理異步內存")
        self.thread_pool.shutdown()
        print("thread all stop")