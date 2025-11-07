import os
from datetime import datetime, timedelta
import queue
import threading
import time

import pandas as pd
import pytz
import twstock
import yfinance as yf
from sqlalchemy import text

import Common.InfomationType as info
import Common.Tools as Tools
from ExternalService.ExternalDataFactory import ExternalDataFactory
from MongoService import MongoService
from ReadLoadSystem import ReadLoadSystem
from SqlService import SqlService
from StockInfos import UserInfoDatas


class UpdateStockService:
    def __init__(self, sql_service:SqlService, mongo_service: MongoService, read_load_system:ReadLoadSystem) -> None:
        self.isUpdating: bool = False
        self._sql_service = sql_service
        self._mongo_service = mongo_service
        self._read_load_system = read_load_system
        self._getExternalFactory = ExternalDataFactory( 
            self._sql_service, self._mongo_service, self._read_load_system)

    def UpdateSP500StocksHandle(self, MainUserInfoDatas: UserInfoDatas):
        self.__RunUpdate_sp500(MainUserInfoDatas)

    def UpdateTaiwanStocksHandle(self, MainUserInfoDatas: UserInfoDatas):
        self.__runUpdate(MainUserInfoDatas)

    def UpdateADLHandle(self):
        self.__RunUpDateADL()
        
    def UpdateMongoHandle(self):
        all_tables = self._sql_service.get_all_table_names()
        
        for table_name in all_tables:
            self._sync_table_to_mongo(table_name)

    def _sync_table_to_mongo(self, table_name: str):
        """
        Reads a table from MySQL and saves it to MongoDB.
        """
        print(f"Syncing table {table_name} to MongoDB...")
        df = self._sql_service.readStockDay(table_name)
        if not df.empty:
            self._mongo_service.saveTable(table_name, df)
            print(f"Successfully synced table {table_name} to MongoDB.")
        else:
            print(f"Skipping empty table: {table_name}")
    
    def _replace_stock_data(self, stock_name: str, df_result: pd.DataFrame) -> bool:
        """
        Saves a DataFrame to a MySQL table using pandas.to_sql, overwriting the existing table.
        """
        table_name = stock_name.lower()
        df_to_write = df_result.reset_index()
        df_to_write.columns = [c.replace(' ', '_') for c in df_to_write.columns]

        if df_to_write.empty:
            print(f"No data to replace for {stock_name}.")
            return True

        try:
            with self._sql_service.MySql_server.engine.connect() as connection:
                with connection.begin():
                    df_to_write.to_sql(
                        name=table_name,
                        con=connection,
                        if_exists='replace',
                        index=False
                    )
                    connection.execute(text(f'ALTER TABLE `{table_name}` ADD PRIMARY KEY (`Date`);'))
            return True
        except Exception as e:
            print(f"Error during table replace for {stock_name}: {e}")
            return False

    def _upsert_stock_data(self, stock_name: str, df_result: pd.DataFrame) -> bool:
        """
        Upserts stock data into a MySQL table using INSERT ... ON DUPLICATE KEY UPDATE.
        """
        table_name = stock_name.lower()
        df_upsert = df_result.reset_index()
        df_upsert.columns = [c.replace(' ', '_') for c in df_upsert.columns]

        if df_upsert.empty:
            print(f"No data to upsert for {stock_name}.")
            return True

        try:
            with self._sql_service.MySql_server.engine.connect() as connection:
                with connection.begin():
                    if not connection.dialect.has_table(connection, table_name):
                        df_upsert.head(0).to_sql(table_name, connection, if_exists='fail', index=False)
                        connection.execute(text(f'ALTER TABLE `{table_name}` ADD PRIMARY KEY (`Date`);'))
                        print(f"Created table `{table_name}` with primary key on `Date`.")

                    columns = df_upsert.columns.tolist()
                    update_columns = [col for col in columns if col.lower() != 'date']

                    if not update_columns:
                        sql_statement = text(f"INSERT IGNORE INTO `{table_name}` (`Date`) VALUES (:Date)")
                    else:
                        cols_str = ", ".join([f"`{col}`" for col in columns])
                        placeholders = ", ".join([f":{col}" for col in columns])
                        update_clause = ", ".join([f"`{col}` = VALUES(`{col}`)" for col in update_columns])
                        sql_statement = text(
                            f"INSERT INTO `{table_name}` ({cols_str}) "
                            f"VALUES ({placeholders}) "
                            f"ON DUPLICATE KEY UPDATE {update_clause}"
                        )

                    data_dict = df_upsert.to_dict(orient='records')
                    connection.execute(sql_statement, data_dict)
            return True
        except Exception as e:
            print(f"Error during upsert for {stock_name}: {e}")
            return False

    def _save_stock_data_to_db(self, data_queue: queue.Queue):
        print("Starting database save thread...")
        while True:
            item = data_queue.get()
            if item is None:
                data_queue.task_done()
                break

            stock_name, df_result, fetch_start_date = item

            try:
                is_initial_fetch = (fetch_start_date.year == 2005 and fetch_start_date.month == 1 and fetch_start_date.day == 1)
                
                with self._sql_service.server_flask.app_context():
                    save_ok = False
                    if is_initial_fetch:
                        print(f"Performing replace for {stock_name} (initial fetch).")
                        save_ok = self._replace_stock_data(stock_name, df_result)
                    else:
                        print(f"Performing upsert for {stock_name}.")
                        save_ok = self._upsert_stock_data(stock_name, df_result)

                    if save_ok:
                        print("Saved " + stock_name + " to DB OK!")
                    else:
                        print(f"Failed to save {stock_name} to SQL DB.")

            except Exception as e:
                print(f"An unexpected error occurred while saving {stock_name}: {e}")
            finally:
                data_queue.task_done()

        print("Database save thread finished.")

    def __runUpdate(self, MainUserInfoDatas: UserInfoDatas, callback=None):
        print("Update all TW stocks start! Fetching and Saving will run concurrently.")  
        MainUserInfoDatas.UpdateDate = str(datetime(2025, 10, 23))[0:10]
        data_queue = queue.Queue()
        save_thread = threading.Thread(
            target=self._save_stock_data_to_db, args=(data_queue,)
        )
        save_thread.daemon = True
        save_thread.start()

        start_date = datetime.strptime(MainUserInfoDatas.UpdateDate, "%Y-%m-%d")
        end_date = datetime.today()
        
        codes = [value for key, value in twstock.codes.items() if value.market == "上市" and len(value.code) >= 4 and not (len(value.code) >= 5 and Tools.check_ETF_stock(value.code) is False)]
        total_stocks = len(codes)
        for i, value in enumerate(codes):
            if not self.isUpdating:
                print("Update stocks " + value.code + info.local_type.Taiwan + " be Stop")
                data_queue.put(None)
                break
            
            df_check = self._getExternalFactory.Get_instance(self).get_stock_history(
                value.code, start=start_date
            )
            if not df_check.empty or start_date in df_check.index:
                fetch_start_date = start_date
            else:
                fetch_start_date = datetime(2005, 1, 1)
            
            if fetch_start_date >= end_date:
                print("Date time is same " + str(value.code) + " " + str(fetch_start_date))
                continue
            
            stock_name = value.code + info.local_type.Taiwan
            df_result = yf.download([stock_name], start=fetch_start_date, end=end_date)

            if df_result.empty:
                print("yahoo no data:" + str(stock_name))
                if callback:
                    progress = int((i + 1) / total_stocks * 100)
                    callback(progress)
                continue

            df_result = Tools.TidyTicketData(df_result, value.code + ".TW")
            data_queue.put((stock_name, df_result, fetch_start_date))

            self._read_load_system.load_memery[
                os.getcwd() + "/" + "stockInfo" + "/" + value.code
            ] = df_result
            print("Download stocks " + stock_name + " OK!")
            if callback:
                progress = int((i + 1) / total_stocks * 100)
                callback(progress)
            time.sleep(0.3)

        data_queue.put(None)
        MainUserInfoDatas.UpdateDate = str(datetime.today())[0:10]
        self._read_load_system.clear_memery()
        print("TW stocks update process initiated. Fetching and saving are running in the background.")

    def __RunUpdate_sp500(self, MainUserInfoDatas: UserInfoDatas):
        print("Update all sp500 stocks start! Fetching and Saving will run concurrently.")
        data_queue = queue.Queue()
        save_thread = threading.Thread(
            target=self._save_stock_data_to_db, args=(data_queue,)
        )
        save_thread.daemon = True
        save_thread.start()
        
        start_date = datetime.strptime(MainUserInfoDatas.UpdateDate, "%Y-%m-%d")
        end_date = datetime.today() - timedelta(days=1)

        sp500 = Tools.get_SP500_list()
        for temp in sp500:
            if not self.isUpdating:
                print("Update stocks " + temp + " be Stop")
                data_queue.put(None)
                break
            
            df_check = self._getExternalFactory.Get_instance(self).get_stock_history(
                temp, start=start_date
            )
            if not df_check.empty or start_date in df_check.index:
                fetch_start_date = start_date
            else:
                fetch_start_date = datetime(2005, 1, 1)
            
            if fetch_start_date >= end_date:
                print("Date time is same " + str(temp) + " " + str(fetch_start_date))
                continue
            
            tz = pytz.timezone("America/New_York")
            start_date_localized = tz.localize(fetch_start_date)
            end_date_localized = tz.localize(end_date)

            df_result = yf.download([temp], start=start_date_localized, end=end_date_localized)
            if df_result.empty:
                print("yahoo no data:" + str(temp))
                continue

            df_result = Tools.TidyTicketData(df_result, temp)
            data_queue.put((temp, df_result, start_date))

            self._read_load_system.load_memery[
                os.getcwd() + "/" + "stockInfo" + "/" + temp
            ] = df_result
            print("Update stocks " + temp + " OK!")
            time.sleep(0.3)

        data_queue.put(None)
        print("SP500 stocks update process initiated. Fetching and saving are running in the background.")

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