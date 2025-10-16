import os
from datetime import datetime, timedelta
import queue
import threading
import time

import pytz
import twstock
import yfinance as yf

import Common.InfomationType as info
import Common.Tools as Tools
from ExternalService.ExternalDataFactory import ExternalDataFactory
from MongoService import MongoService
from ReadLoadSystem import ReadLoadSystem
from SqlService import SqlService
from StockInfos import UserInfoDatas


class UpdateStockService:
    def __init__(self, sql_service:SqlService, mongo_service:MongoService, read_load_system:ReadLoadSystem) -> None:
        self.isUpdating: bool = False
        self._sql_service = sql_service
        self._mongo_service = mongo_service
        self._read_load_system = read_load_system
        self._getExternalFactory = ExternalDataFactory( 
            self._sql_service, self._mongo_service, self._read_load_system)

    def UpdateSP500StocksHandle(self):
        self.__RunUpdate_sp500()

    def UpdateTaiwanStocksHandle(self, MainUserInfoDatas: UserInfoDatas):
        self.__runUpdate(MainUserInfoDatas)

    def UpdateADLHandle(self):
        self.__RunUpDateADL()

    def _save_stock_data_to_db(self, data_queue: queue.Queue):
        print("Starting database save thread...")
        while True:
            item = data_queue.get()
            if item is None:
                # Sentinel value received, exit the loop
                data_queue.task_done()
                break

            stock_name, df_result = item

            try:
                with self._sql_service.server_flask.app_context():
                    df_result.to_sql(
                        name=stock_name,
                        con=self._sql_service.MySql_server.engine,
                        if_exists="replace",
                    )
                self._mongo_service.saveTable(stock_name, df_result)
                print("Saved " + stock_name + " to DB OK!")
            except Exception as e:
                print(f"Error saving {stock_name} to DB: {e}")
            finally:
                data_queue.task_done()

        print("Database save thread finished.")

    def __runUpdate(self, MainUserInfoDatas: UserInfoDatas):
        print("Update all TW stocks start! Fetching and Saving will run concurrently.")

        data_queue = queue.Queue()
        save_thread = threading.Thread(
            target=self._save_stock_data_to_db, args=(data_queue,)
        )
        save_thread.daemon = True  # Allows main program to exit
        save_thread.start()

        # Producer loop to fetch data
        for key, value in twstock.codes.items():
            if not self.isUpdating:
                print(
                    "Update stocks " + value.code + info.local_type.Taiwan + " be Stop"
                )
                data_queue.put(None)
                break  # Exit the loop
            if value.market == "上市" and len(value.code) >= 4:
                if len(value.code) >= 5 and Tools.check_ETF_stock(value.code) is False:
                    continue

                stock_name = value.code + info.local_type.Taiwan

                start_date = datetime(2005, 1, 1)
                end_date = datetime.today()
                df_result = yf.download([stock_name], start=start_date, end=end_date)

                if df_result.empty:
                    print("yahoo no data:" + str(stock_name))
                    continue

                df_result = Tools.TidyTicketData(df_result, value.code + ".TW")
                data_queue.put((stock_name, df_result))

                self._read_load_system.load_memery[
                    os.getcwd() + "/" + "stockInfo" + "/" + value.code
                ] = df_result
                print("Download stocks " + stock_name + " OK!")
                time.sleep(0.3)

        # Signal the consumer to end
        data_queue.put(None)

        MainUserInfoDatas.UpdateDate = str(datetime.today())[0:10]
        print(
            "TW stocks update process initiated. Fetching and saving are running in the background."
        )

    def __RunUpdate_sp500(self):
        print(
            "Update all sp500 stocks start! Fetching and Saving will run concurrently."
        )

        data_queue = queue.Queue()
        save_thread = threading.Thread(
            target=self._save_stock_data_to_db, args=(data_queue,)
        )
        save_thread.daemon = True
        save_thread.start()

        sp500 = Tools.get_SP500_list()
        for temp in sp500:
            if not self.isUpdating:
                print("Update stocks " + temp + " be Stop")
                data_queue.put(None)
                break

            start_date = datetime(2005, 1, 1)
            end_date = datetime.today() - timedelta(days=1)
            tz = pytz.timezone("America/New_York")
            start_date = tz.localize(start_date)
            end_date = tz.localize(end_date)

            df_result = yf.download([temp], start=start_date, end=end_date)
            if df_result.empty:
                print("yahoo no data:" + str(temp))
                continue

            df_result = Tools.TidyTicketData(df_result, temp)
            data_queue.put((temp, df_result))

            self._read_load_system.load_memery[
                os.getcwd() + "/" + "stockInfo" + "/" + temp
            ] = df_result
            print("Update stocks " + temp + " OK!")
            time.sleep(0.3)

        data_queue.put(None)
        print(
            "SP500 stocks update process initiated. Fetching and saving are running in the background."
        )

    def __RunUpDateADL(self):
        print("Update stocks other Info start!")
        end_date = datetime(
            datetime.today().year, datetime.today().month, datetime.today().day
        )  # 設定資料起訖日期

        # 取得近一年的交易日曆 (以2330為基準)
        print("Fetching trading day calendar for the last year...")
        start_date_for_calendar = end_date - timedelta(days=366)
        trading_days_df = self._getExternalFactory.Get_instance(self).get_stock_history(
            "2330", start=start_date_for_calendar
        )
        if trading_days_df.empty:
            print("Could not fetch trading day calendar. Aborting ADL update.")
            print("Update stocks other Info end!")
            return

        # The index is a DatetimeIndex, which is efficient for lookups.
        trading_days = trading_days_df.index

        for i in range(366):
            date_to_check = end_date - timedelta(days=i)

            # 檢查是否為交易日
            if date_to_check in trading_days:
                # 更新騰落，get_stock_AD_index 內部會處理已存在資料的跳過邏輯
                print(f"Updating ADL for {date_to_check.strftime('%Y-%m-%d')}")
                self._getExternalFactory.Get_instance(self).get_stock_AD_index(date_to_check)
            else:
                print(f"Skipping non-trading day: {date_to_check.strftime('%Y-%m-%d')}")

        print("Update stocks other Info end!")
