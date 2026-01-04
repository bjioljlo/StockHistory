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

from src.Common import InfomationType as info
from src.Common import Tools
from src.Common.DataValidationService import DataValidationService
from src.ExternalService.ExternalDataFactory import ExternalDataFactory
from src.MongoService import MongoService
from src.ReadLoadSystem import ReadLoadSystem
from src.SqlService import SqlService
from src.StockInfos import UserInfoDatas
import time
import random


class UpdateStockService:
    def __init__(self, sql_service:SqlService, mongo_service: MongoService, read_load_system:ReadLoadSystem, config: dict = None, cache_service=None) -> None:
        self.isUpdating: bool = False
        self._sql_service = sql_service
        self._mongo_service = mongo_service
        self._read_load_system = read_load_system
        self._cache_service = cache_service
        self._getExternalFactory = ExternalDataFactory(
            self._sql_service, self._mongo_service, self._read_load_system, cache_service)
        self._data_validator = DataValidationService(config) if config else None
        # Get retry settings from config
        self._retry_attempts = self._data_validator.config.get('external_apis', {}).get('yahoo_finance', {}).get('retry_attempts', 3) if self._data_validator else 3
        self._retry_delay = 1.0  # Base delay in seconds

    def _download_with_retry(self, stock_symbol: str, start_date: datetime, end_date: datetime, tz: str = None) -> pd.DataFrame:
        """
        Download stock data with retry mechanism and exponential backoff.

        Args:
            stock_symbol: Stock symbol to download
            start_date: Start date for data
            end_date: End date for data
            tz: Timezone for localization (optional)

        Returns:
            pd.DataFrame: Downloaded stock data
        """
        last_exception = None

        for attempt in range(self._retry_attempts):
            try:
                if tz:
                    # For international stocks, localize dates
                    timezone = pytz.timezone(tz)
                    start_date_localized = timezone.localize(start_date)
                    end_date_localized = timezone.localize(end_date)
                    df_result = yf.download([stock_symbol], start=start_date_localized, end=end_date_localized)
                else:
                    df_result = yf.download([stock_symbol], start=start_date, end=end_date)

                if not df_result.empty:
                    return df_result
                else:
                    print(f"Attempt {attempt + 1}: Empty data for {stock_symbol}")

            except Exception as e:
                last_exception = e
                print(f"Attempt {attempt + 1} failed for {stock_symbol}: {e}")

                if attempt < self._retry_attempts - 1:  # Don't sleep after last attempt
                    # Exponential backoff with jitter
                    delay = self._retry_delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f"Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)

        # All attempts failed
        print(f"All {self._retry_attempts} attempts failed for {stock_symbol}. Last error: {last_exception}")
        return pd.DataFrame()  # Return empty DataFrame

    def UpdateSP500StocksHandle(self, MainUserInfoDatas: UserInfoDatas, callback=None):
        self.__RunUpdate_sp500(MainUserInfoDatas, callback)

    def UpdateTaiwanStocksHandle(self, MainUserInfoDatas: UserInfoDatas, callback=None):
        self.__runUpdate(MainUserInfoDatas, callback)

    def UpdateADLHandle(self, callback=None):
        self.__RunUpDateADL(callback)
        
    def UpdateMongoHandle(self, callback=None):
        all_tables = self._sql_service.get_all_table_names()
        total_tables = len(all_tables)
        for i, table_name in enumerate(all_tables):
            self._sync_table_to_mongo(table_name)
            if callback:
                progress = int((i + 1) / total_tables * 100)
                callback(progress)

    def _sync_table_to_mongo(self, table_name: str):
        """
        Reads a table from MySQL and saves it to MongoDB.
        """
        print(f"Syncing table {table_name} to MongoDB...")

        df = pd.DataFrame()

        # 特殊處理股票資料表格
        if table_name.lower() == 'stock_daily_prices':
            # 對於統一的股票表格，我們需要為每個股票創建單獨的集合
            print("Syncing unified stock_daily_prices table to MongoDB collections...")
            self._sync_unified_stock_table_to_mongo()
            return
        elif table_name.lower() in ['ad_index']:
            # AD_index 是特殊的索引表格
            df = self._sql_service.readDividendYield(table_name)
        else:
            # 其他非股票表格使用原有的邏輯
            df = self._sql_service.readStockDay(table_name)
            if df.empty:
                df = self._sql_service.readDividendYield(table_name)

        if not df.empty:
            self._mongo_service.saveTable(table_name, df)
            print(f"Successfully synced table {table_name} to MongoDB.")

        else:
            print(f"Skipping empty table: {table_name}")

    def _sync_unified_stock_table_to_mongo(self):
        """
        將統一的 stock_daily_prices 表格同步到 MongoDB 的各個股票集合中
        """
        try:
            # 從統一表格獲取所有唯一的股票代碼
            query = "SELECT DISTINCT symbol FROM stock_daily_prices"
            with self._sql_service.server_flask.app_context():
                unique_symbols_df = pd.read_sql(query, con=self._sql_service.MySql_server.engine)

            if unique_symbols_df.empty:
                print("No symbols found in stock_daily_prices table")
                return

            total_symbols = len(unique_symbols_df)
            print(f"Found {total_symbols} unique symbols to sync")

            for i, row in unique_symbols_df.iterrows():
                symbol = row['symbol']
                print(f"Syncing symbol {symbol} ({i+1}/{total_symbols})...")

                # 從統一表格讀取該股票的所有資料
                df = self._sql_service.readStockDay(symbol)
                if not df.empty:
                    self._mongo_service.saveTable(symbol.lower(), df)
                    print(f"Successfully synced {symbol} to MongoDB")
                else:
                    print(f"No data found for symbol {symbol}")

        except Exception as e:
            print(f"Error syncing unified stock table to MongoDB: {e}")
    
    def _replace_stock_data(self, stock_name: str, df_result: pd.DataFrame) -> bool:
        """
        Saves a DataFrame to the unified stock_daily_prices table, overwriting existing data for this stock.
        """
        if df_result.empty:
            print(f"No data to replace for {stock_name}.")
            return True

        try:
            # 準備資料格式以適應統一表格
            symbol = stock_name.upper().replace('.TW', '').replace('.US', '').replace('.HK', '')
            market = self._determine_market(stock_name)

            df_to_write = df_result.reset_index()
            df_to_write['symbol'] = symbol
            df_to_write['market'] = market
            df_to_write = df_to_write.rename(columns={
                'Date': 'date',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Adj Close': 'adj_close',
                'Volume': 'volume'
            })

            # 使用SqlService的新方法插入資料
            return self._sql_service._insert_stock_data_to_unified_table(df_to_write)

        except Exception as e:
            print(f"Error during table replace for {stock_name}: {e}")
            return False

    def _upsert_stock_data(self, stock_name: str, df_result: pd.DataFrame) -> bool:
        """
        Upsert stock data to the unified stock_daily_prices table.
        """
        if df_result.empty:
            print(f"No data to upsert for {stock_name}.")
            return True

        try:
            # 準備資料格式以適應統一表格
            symbol = stock_name.upper().replace('.TW', '').replace('.US', '').replace('.HK', '')
            market = self._determine_market(stock_name)

            df_upsert = df_result.reset_index()
            df_upsert['symbol'] = symbol
            df_upsert['market'] = market
            df_upsert = df_upsert.rename(columns={
                'Date': 'date',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Adj Close': 'adj_close',
                'Volume': 'volume'
            })

            # 使用SqlService的新方法插入資料（它會處理重複鍵更新）
            return self._sql_service._insert_stock_data_to_unified_table(df_upsert)

        except Exception as e:
            print(f"Error during upsert for {stock_name}: {e}")
            return False

    def _determine_market(self, stock_name: str) -> str:
        """確定市場類型"""
        name_lower = stock_name.lower()
        if name_lower.endswith('.tw') or (name_lower.replace('.tw', '').isdigit() and len(name_lower.replace('.tw', '')) >= 4):
            return 'TW'
        elif len(name_lower) <= 5 and not name_lower.replace('.', '').isdigit():
            return 'US'
        else:
            return 'OTHER'

    def _save_stock_data_to_db(self, data_queue: queue.Queue):
        print("Starting database save thread...")
        while True:
            item = data_queue.get()
            if item is None:
                data_queue.task_done()
                break

            stock_name, df_result, fetch_start_date = item

            try:
                # 資料驗證
                if self._data_validator:
                    is_valid, errors, cleaned_df = self._data_validator.validate_stock_data(
                        stock_name, df_result, source='yahoo'
                    )
                    if not is_valid:
                        print(f"Data validation failed for {stock_name}: {errors}")
                        # 仍然嘗試儲存清理後的資料，但記錄警告
                        df_result = cleaned_df
                    else:
                        df_result = cleaned_df
                        print(f"Data validation passed for {stock_name}")

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

                        # 更新 MongoDB 快取（如果是熱門股票）
                        if self._cache_service:
                            hot_stocks = self._cache_service.get_hot_stocks()
                            if stock_name.upper().replace('.TW', '').replace('.US', '').replace('.HK', '') in hot_stocks:
                                try:
                                    # 確保 DataFrame 索引是 DatetimeIndex，避免 datetime.date 編碼問題
                                    df_to_cache = df_result.copy()
                                    if not isinstance(df_to_cache.index, pd.DatetimeIndex):
                                        df_to_cache.index = pd.to_datetime(df_to_cache.index)
                                    self._mongo_service.saveTable(stock_name.lower(), df_to_cache)
                                    print(f"Updated cache for hot stock: {stock_name}")
                                except Exception as e:
                                    print(f"Failed to update cache for {stock_name}: {e}")
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
            df_result = self._download_with_retry(stock_name, fetch_start_date, end_date)

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

    def __RunUpdate_sp500(self, MainUserInfoDatas: UserInfoDatas, callback=None):
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
        total_stocks = len(sp500)
        for i, temp in enumerate(sp500):
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
                if callback:
                    progress = int((i + 1) / total_stocks * 100)
                    callback(progress)
                continue
            
            df_result = self._download_with_retry(temp, fetch_start_date, end_date, tz="America/New_York")
            if df_result.empty:
                print("yahoo no data:" + str(temp))
                if callback:
                    progress = int((i + 1) / total_stocks * 100)
                    callback(progress)
                continue

            df_result = Tools.TidyTicketData(df_result, temp)
            data_queue.put((temp, df_result, start_date))

            self._read_load_system.load_memery[
                os.getcwd() + "/" + "stockInfo" + "/" + temp
            ] = df_result
            print("Update stocks " + temp + " OK!")
            if callback:
                progress = int((i + 1) / total_stocks * 100)
                callback(progress)
            time.sleep(0.3)

        data_queue.put(None)
        print("SP500 stocks update process initiated. Fetching and saving are running in the background.")

    def __RunUpDateADL(self, callback=None):
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
            
            if callback:
                progress = int((i + 1) / 366 * 100)
                callback(progress)

        print("Update stocks other Info end!")
