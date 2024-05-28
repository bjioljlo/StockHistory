from datetime import datetime
import threading
import schedule
import time
from StockInfos import UserInfoDatas
from ReadLoadSystem import ReadLoadSystem
from SqlService import SqlService
from UpdateStockService import UpdateStockService

class ScheduleService():
    def __init__(self, sql: SqlService, readLoad: ReadLoadSystem) -> None:
        self.updateStockService:UpdateStockService = UpdateStockService()
        self.threads = []
   
    def RunScheduleNow(self, MainUserInfoDatas: UserInfoDatas):
        self.__RunSchedule(self.updateStockService.UpdateAllStocksHandle,str(datetime.today().hour).zfill(2)+ ":" + str(datetime.today().minute + 1).zfill(2)+ ":01", MainUserInfoDatas)
    
    def StopThreadSchedule(self):
        for thread in self.threads:
            thread.do_run = False
        self.threads.clear()
        self.updateStockService.isUpdating = False
        print("thread all stop")
        
    def __RunSchedule(self, func, UpdateTime:str, _args:tuple = None):
        print("RunSchedule at:" + UpdateTime)
        schedule.every().day.at(UpdateTime).do(func,_args)
        temp_thread = threading.Thread(target=self.__ScheduleStart, args=["",])
        temp_thread.start()
        self.threads.append(temp_thread)      
        self.updateStockService.isUpdating = True
        
    def __ScheduleStart(self, input):
        t = threading.currentThread()
        while getattr(t, "do_run", True):
            schedule.run_pending()
            time.sleep(0.5)