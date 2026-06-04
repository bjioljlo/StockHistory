import queue
import time
from datetime import datetime, timedelta
import requests
from io import StringIO
import pandas as pd
import logging

from src.StockInfos import UserInfoDatas
from src.Common import Tools
from pyutils_core.concurrent import ConcurrentUtils
from src.UpdateStockService.StockDataDownloader import StockDataDownloader
from src.UpdateStockService.StockDataSynchronizer import StockDataSynchronizer
from src.UpdateStockService.ADLUpdater import ADLUpdater
from pydb_core.cache_service import HybridCacheService
from src.ExternalService.ExternalDataFactory import ExternalDataFactory, ExternalDataTypeEnum
from pydb_core.mongo_service import MongoService
from pydb_core.sql_service import SqlService
from pydb_core.read_load_system import ReadLoadSystem
from src.Common import InfomationType as info
from src.ExternalService.providers.DividendYieldProvider import DividendYieldProvider

class ScheduleService:
    def __init__(self, concurrent_utils: ConcurrentUtils,
                 stock_data_downloader: StockDataDownloader,
                 stock_data_synchronizer: StockDataSynchronizer,
                 adl_updater: ADLUpdater,
                 external_data_factory: ExternalDataFactory,
                 sql_service: SqlService,
                 mongo_service: MongoService,
                 read_load_system: ReadLoadSystem,
                 config: dict = None,
                 cache_service: HybridCacheService=None) -> None:
        self.concurrent_utils = concurrent_utils
        self.stock_data_downloader = stock_data_downloader
        self.stock_data_synchronizer = stock_data_synchronizer
        self.adl_updater = adl_updater
        self.external_data_factory = external_data_factory
        self.sql_service = sql_service
        self.mongo_service = mongo_service
        self.read_load_system = read_load_system
        self.config = config
        self.cache_service = cache_service
        self.isUpdating: bool = False
        self.dividend_yield_provider = DividendYieldProvider(
            sql_service=self.sql_service,
            mongo_service=self.mongo_service,
            read_load_system=self.read_load_system,
            cache_service=self.cache_service
        )

    def RunUpdateInfoNow(self, MainUserInfoDatas: UserInfoDatas, progress_callback=None):
        self.isUpdating = True
        self.concurrent_utils.submit_task(
            self._update_taiwan_stocks_and_yield,
            progress_callback,
            MainUserInfoDatas=MainUserInfoDatas
        )

    def RunUpdateInfoNow_sp500(self, MainUserInfoDatas: UserInfoDatas, progress_callback=None):
        self.isUpdating = True
        self.concurrent_utils.submit_task(
            self._update_sp500_stocks,
            progress_callback,
            MainUserInfoDatas=MainUserInfoDatas
        )

    def RunSyncToMongo(self, progress_callback=None):
        self.isUpdating = True
        self.concurrent_utils.submit_task(
            self._sync_to_mongo,
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
        self.isUpdating = True
        self.concurrent_utils.submit_task(
            self.adl_updater.run_update_adl,
            progress_callback
        )

        print("Update stocks other Info end!")

    def StopThreadSchedule(self):
        print("開始清理異步內存")
        self.concurrent_utils.shutdown()
        print("thread all stop")

    def _update_taiwan_stocks(self, MainUserInfoDatas: UserInfoDatas, callback=None):
        """Update Taiwan stocks"""
        print("Update all TW stocks start! Fetching and Saving will run concurrently.")

        # Get Taiwan listed stock list
        import twstock
        from src.Common import Tools
        codes = []
        for key, value in twstock.codes.items():
            if value.market == "上市":
                if value.type == "股票" or (value.type == "ETF" and Tools.is_etf_stock(value.code)):
                    codes.append(value)

        # Use common method
        self._update_stocks_common(
            mainUserInfoDatas=MainUserInfoDatas,
            stock_list=codes,
            update_date_attr="TW_UpdateDate",
            initial_date=datetime(2009, 1, 1),
            callback=callback
        )
        print("TW stocks update completed successfully.")

    def _update_taiwan_stocks_and_yield(self, MainUserInfoDatas: UserInfoDatas, callback=None):
        """Update Taiwan stocks and then dividend yield data"""
        self._update_dividend_yield_data(MainUserInfoDatas)
        self._update_taiwan_stocks(MainUserInfoDatas, callback)

    def _update_dividend_yield_data(self, MainUserInfoDatas: UserInfoDatas):
        """Update dividend yield data after Taiwan stocks update"""
        print("Update dividend yield data start!")

        try:
            # Use the same date range as Taiwan stocks update
            tw_update_date = datetime.strptime(getattr(MainUserInfoDatas, "TW_UpdateDate"), "%Y-%m-%d")
            end_date = datetime.today()

            # Check if we have any dividend yield data in SQL after TW_UpdateDate
            latest_saved_date = self.sql_service.get_latest_dividend_yield_date()
            if latest_saved_date:
                latest_saved_date = pd.to_datetime(latest_saved_date).date()
                sql_latest_date = datetime(latest_saved_date.year, latest_saved_date.month, latest_saved_date.day)

                # If SQL has data newer than TW_UpdateDate, start from next trade date after SQL latest
                if sql_latest_date > tw_update_date:
                    start_date = self._next_trade_date(sql_latest_date)
                    print(f"SQL has newer data than TW_UpdateDate. Starting dividend yield update from next trade date after latest SQL record: {start_date.date()}")
                else:
                    # SQL data is not newer than TW_UpdateDate, start from TW_UpdateDate
                    start_date = sql_latest_date
                    print(f"Starting dividend yield update from TW_UpdateDate: {start_date.date()}")
            else:
                # No dividend yield data in SQL, start from TW_UpdateDate
                start_date = tw_update_date
                print(f"No existing dividend yield records found in SQL. Starting from TW_UpdateDate: {start_date.date()}")

            if start_date.date() >= end_date.date():
                print("Dividend yield data is up to date.")
                return

            # Download yield data using the provider's logic
            download_data = self._download_yield_data(start_date, end_date)
            if not download_data.empty:
                self._save_yield_to_db(download_data)
                print(f"Successfully updated {len(download_data)} dividend yield records.")
            else:
                print("No new dividend yield data to update.")

        except Exception as e:
            print(f"Error updating dividend yield data: {e}")

        print("Dividend yield data update completed.")

    def _update_sp500_stocks(self, MainUserInfoDatas: UserInfoDatas, callback=None):
        """Update S&P 500 stocks"""
        print("Update all sp500 stocks start! Fetching and Saving will run concurrently.")

        # Get S&P 500 stock list
        from src.Common import Tools
        sp500 = Tools.get_SP500_list()

        # Use common method
        self._update_stocks_common(
            mainUserInfoDatas=MainUserInfoDatas,
            stock_list=sp500,
            update_date_attr="US_UpdateDate",
            initial_date=datetime(2005, 1, 1),
            timezone="America/New_York",
            callback=callback
        )
        print("SP500 stocks update completed successfully.")

    def _sync_to_mongo(self, callback=None):
        all_tables = self.sql_service.get_all_table_names()
        total_tables = len(all_tables)
        for i, table_name in enumerate(all_tables):
            self.stock_data_synchronizer.sync_table_to_mongo(table_name)
            if callback:
                progress = int((i + 1) / total_tables * 100)
                callback(progress)

    def _update_stocks_common(self, mainUserInfoDatas: UserInfoDatas, stock_list, update_date_attr, initial_date, timezone=None, callback=None, areacode=None):
        """
        Common stock update method for handling different market stock updates

        Args:
            MainUserInfoDatas: User info object
            stock_list: Stock list (can be codes or sp500 list)
            update_date_attr: Update date attribute name in user info
            initial_date: Initial date (used when no historical data exists)
            timezone: Timezone setting (optional)
            callback: Progress callback function (optional)
        """
        print(f"Update all stocks start! Fetching and Saving will run concurrently.")
        import queue
        import threading
        import time
        from datetime import datetime, timedelta

        data_queue = queue.Queue()
        update_adl_flag = {'should_update': False}  # Track if ADL index needs to be updated

        save_thread = threading.Thread(
            target=self._save_stock_data_to_db, args=(data_queue, update_adl_flag)
        )
        save_thread.daemon = False  # Non-daemon thread to ensure data save completes
        save_thread.start()

        start_date = datetime.strptime(getattr(mainUserInfoDatas, update_date_attr), "%Y-%m-%d")
        end_date = datetime.today()

        total_stocks = len(stock_list)
        for i, stock_item in enumerate(stock_list):
            if not self.isUpdating:
                stock_name = stock_item if isinstance(stock_item, str) else stock_item.code
                print(f"Update stocks {stock_name} be Stop")
                data_queue.put(None)
                break

            # Get stock code and name
            if isinstance(stock_item, str):
                stock_code = stock_item
                stock_name = stock_item
            else:
                stock_code = stock_item.code
                stock_name = stock_code + info.local_type.Taiwan

            # Check local data - 每次建立獨立實例避免多執行緒問題 (使用 Normal 模式真實資料)
            external_data = self.external_data_factory.Get_instance(ExternalDataTypeEnum.Normal)

            df_check = external_data.get_stock_history(
                stock_code, start_date
            )
            if not df_check.empty:
                # Has local data, start from latest date +1 day to avoid duplicate downloads
                latest_date = df_check.index.max()
                fetch_start_date = latest_date + timedelta(days=1)
            else:
                # Check if really no historical data, or just weekend/holiday
                # If weekend/holiday, try to find most recent trading day
                print(f"No local data found for {stock_code}, checking for recent trading days...")

                # Try to get last month data to determine if there are trading days
                recent_start = end_date - timedelta(days=30)
                df_recent = external_data.get_stock_history(
                    stock_code, recent_start
                )

                if not df_recent.empty:
                    # Has recent data, start from latest date +1 day
                    latest_date = df_recent.index.max()
                    fetch_start_date = latest_date + timedelta(days=1)
                    print(f"Found recent data for {stock_code}, starting from {fetch_start_date}")
                else:
                    # Really no historical data, use initial date
                    fetch_start_date = initial_date
                    print(f"No historical data found for {stock_code}, using initial date")

            if fetch_start_date >= end_date:
                print(f"Date time is same {stock_code} {fetch_start_date}")
                if callback:
                    progress = int((i + 1) / total_stocks * 100)
                    callback(progress)
                continue

            # Download data
            if timezone:
                df_result = self.stock_data_downloader.download_with_retry(stock_name, fetch_start_date, end_date, tz=timezone)
            else:
                df_result = self.stock_data_downloader.download_with_retry(stock_name, fetch_start_date, end_date)

            if df_result.empty:
                print(f"yahoo no data: {stock_name}")
                if callback:
                    progress = int((i + 1) / total_stocks * 100)
                    callback(progress)
                continue

            # Process data
            from src.Common import DataUtils
            if isinstance(stock_item, str):
                df_result = DataUtils.extract_ticker_data(df_result, stock_code)
            else:
                df_result = DataUtils.extract_ticker_data(df_result, stock_code + ".TW")

            data_queue.put((stock_name, df_result, fetch_start_date))

            print(f"Update stocks {stock_name} OK!")
            if callback:
                progress = int((i + 1) / total_stocks * 100)
                callback(progress)
            time.sleep(0.3)

        data_queue.put(None)
        # Wait for save thread to complete
        save_thread.join()

        # Check if ADL index needs to be updated
        adl_update_enabled = self.config.get('app', {}).get('auto_adl_update', True) if self.config else True
        if adl_update_enabled and update_adl_flag.get('should_update', False):
            print("Detected new trading day data, updating ADL index and persisted ADL...")
            adl_refresh_ok = self.adl_updater.run_update_adl()
            if not adl_refresh_ok:
                print("ADL refresh failed after stock update, but stock data update remains committed.")
        else:
            print("No new trading day data detected, skipping ADL update.")

        setattr(mainUserInfoDatas, update_date_attr, str(datetime.today())[0:10])
        print("Stocks update completed successfully.")

    def _save_stock_data_to_db(self, data_queue: queue.Queue, update_adl_flag: dict):
        """
        Save stock data to database, and track if new trading day data has been updated

        Args:
            data_queue: Data queue
            update_adl_flag: Dictionary for flagging if ADL index needs to be updated
        """
        print("Starting database save thread...")
        new_trading_day_updated = False
        from datetime import datetime, timedelta
        from src.Common.DataValidationService import DataValidationService

        while True:
            item = data_queue.get()
            if item is None:
                data_queue.task_done()
                break

            stock_name, df_result, fetch_start_date = item

            try:
                # Data validation and cleanup
                default_config = self.config if self.config else {'app': {'data_validation': True}}
                data_validator = DataValidationService(default_config)

                if data_validator:
                    is_valid, errors, cleaned_df = data_validator.validate_stock_data(
                        stock_name, df_result, source='yahoo'
                    )
                    if not is_valid:
                        print(f"Data validation failed for {stock_name}: {errors}")
                        # Still try to save cleaned data, but log warning
                        df_result = cleaned_df
                    else:
                        df_result = cleaned_df
                        print(f"Data validation passed for {stock_name}")
                else:
                    # If no data validator available, perform basic cleanup manually
                    print(f"No data validator available for {stock_name}, performing basic cleanup")
                    df_result = self.stock_data_downloader.basic_data_cleanup(df_result, stock_name)

                is_initial_fetch = (fetch_start_date.year == 2009 and fetch_start_date.month == 1 and fetch_start_date.day == 1)

                with self.sql_service.server_flask.app_context():
                    save_ok = False
                    if is_initial_fetch:
                        print(f"Performing replace for {stock_name} (initial fetch).")
                        save_ok = self.stock_data_synchronizer.replace_stock_data(stock_name, df_result)
                    else:
                        print(f"Performing upsert for {stock_name}.")
                        save_ok = self.stock_data_synchronizer.upsert_stock_data(stock_name, df_result)

                    if save_ok:
                        print("Saved " + stock_name + " to DB OK!")

                        # Check if latest trading day data was updated
                        if not is_initial_fetch and not df_result.empty:
                            # Get latest trading day
                            latest_date = df_result.index.max()
                            today = datetime.today().date()

                            # If updated data includes today or recent trading day, flag for ADL update
                            if latest_date.date() == today or (latest_date.date() > today - timedelta(days=3)):
                                new_trading_day_updated = True
                                print(f"Updated data for recent trading day: {latest_date.date()}")

                        # Update cache to ensure latest data is read
                        if self.cache_service:
                            try:
                                # Clear Redis cache for this stock
                                stock_symbol = stock_name.upper().replace('.TW', '').replace('.US', '').replace('.HK', '')
                                self.cache_service.invalidate_stock_cache(stock_symbol)

                                print(f"Updated cache for {stock_name} with new data")
                            except Exception as e:
                                print(f"Failed to update cache for {stock_name}: {e}")
                    else:
                        print(f"Failed to save {stock_name} to SQL DB.")

            except Exception as e:
                print(f"An unexpected error occurred while saving {stock_name}: {e}")
            finally:
                data_queue.task_done()

        # Set ADL index update flag
        update_adl_flag['should_update'] = new_trading_day_updated
        print("Database save thread finished.")

    def _download_yield_data(self, start: datetime, end: datetime) -> pd.DataFrame:
        """
        Download yield data from TWSE (copied from DividendYieldProvider)
        """
        logger = logging.getLogger(__name__)
        logger.info(f"Downloading yield data from TWSE: {start.date()} ~ {end.date()}")

        all_data = []
        current_date = start

        while current_date <= end:
            date_str = f"{current_date.year}{current_date.month:02d}{current_date.day:02d}"
            url = (
                "https://www.twse.com.tw/exchangeReport/BWIBBU_d"
                f"?response=csv&date={date_str}&selectType=ALL"
            )

            logger.debug(f"Downloading yield data for {date_str}")

            try:
                response = requests.get(url, headers=Tools.get_random_headers(), timeout=30)

                if response.status_code != 200:
                    logger.warning(f"TWSE returned status {response.status_code} for {date_str}")
                    current_date = self._next_trade_date(current_date)
                    continue

                # Parse CSV response (TWSE uses ANSI/CP950 encoding)
                try:
                    # Skip first 1-2 lines (metadata) and last few lines (footer)
                    lines = response.text.split('\n')

                    # Find the header line
                    csv_start = 0
                    for i, line in enumerate(lines):
                        if '證券代號' in line:
                            csv_start = i
                            break

                    # Find the data end (stop at empty lines or footer)
                    csv_end = len(lines)
                    for i in range(csv_start, len(lines)):
                        if not lines[i].strip() or lines[i].startswith('-'):
                            csv_end = i
                            break

                    # Join the CSV portion
                    csv_text = '\n'.join(lines[csv_start:csv_end])

                    if not csv_text.strip():
                        logger.debug(f"No data in TWSE response for {date_str}")
                        current_date = self._next_trade_date(current_date)
                        continue

                    # Parse CSV
                    for encoding in ['cp950', 'big5', 'ANSI', 'utf-8']:
                        try:
                            df = pd.read_csv(StringIO(csv_text), encoding=encoding)
                            break
                        except (UnicodeDecodeError, UnicodeError):
                            continue
                    else:
                        logger.warning(f"Could not decode TWSE data for {date_str}")
                        current_date = self._next_trade_date(current_date)
                        continue

                    if df.empty:
                        logger.debug(f"Empty TWSE response for {date_str}")
                        current_date = self._next_trade_date(current_date)
                        continue

                    # Rename columns to match our schema
                    column_mapping = {
                        '證券代號': 'symbol',
                        '證券名稱': 'company_name',
                        '本益比': 'pe_ratio',
                        '殖利率(%)': 'dividend_yield',
                        '股價淨值比': 'pb_ratio'
                    }

                    # Find matching columns
                    rename_map = {}
                    for old_col in df.columns:
                        col_clean = old_col.strip().replace('=', '').replace('"', '')
                        if col_clean in column_mapping:
                            rename_map[old_col] = column_mapping[col_clean]

                    # if 'symbol' not in rename_map:
                    #     logger.warning(f"No recognizable columns in TWSE data for {date_str}")
                    #     current_date = self._next_trade_date(current_date)
                    #     continue

                    df = df.rename(columns=rename_map)

                    # Keep only mapped columns
                    keep_cols = [v for v in rename_map.values() if v in df.columns]
                    df = df[keep_cols]

                    # Add date column
                    df['date'] = current_date

                    # Convert numeric columns
                    numeric_cols = ['pe_ratio', 'dividend_yield', 'pb_ratio']
                    for col in numeric_cols:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')

                    # Remove rows with no valid symbol
                    df = df[df['symbol'].notna()]

                    # Clean symbol (remove quotes, non-digit chars)
                    df['symbol'] = df['symbol'].astype(str).str.replace(r'[^0-9]', '', regex=True)

                    # Remove non-numeric symbols
                    df = df[df['symbol'].str.match(r'^\d+$')]
                    df['symbol'] = df['symbol'].astype(int)

                    if not df.empty:
                        all_data.append(df)
                        logger.debug(f"Got {len(df)} records for {date_str}")

                    # Throttle to avoid TWSE rate limiting
                    time.sleep(3)

                except Exception as parse_err:
                    logger.warning(f"Error parsing TWSE response for {date_str}: {parse_err}")

            except requests.exceptions.RequestException as req_err:
                logger.warning(f"Request failed for {date_str}: {req_err}")
                time.sleep(5)

            current_date = self._next_trade_date(current_date)

        if not all_data:
            logger.warning("No yield data downloaded from TWSE")
            return pd.DataFrame()

        # Combine all dates
        combined = pd.concat(all_data, ignore_index=True)

        # Standardize column order
        column_order = ['symbol', 'date', 'company_name', 'pe_ratio', 'dividend_yield', 'pb_ratio']
        available_cols = [c for c in column_order if c in combined.columns]
        combined = combined[available_cols]

        logger.info(f"Successfully downloaded {len(combined)} yield records from TWSE "
                    f"for {len(all_data)} trading days")

        return combined

    def _save_yield_to_db(self, data: pd.DataFrame) -> None:
        """Save yield data to dividend_yield table (copied from DividendYieldProvider)"""
        if data.empty:
            return

        try:
            self.sql_service.upsert_dividend_yield(data)
            print(f"Saved {len(data)} yield records to dividend_yield table")
        except Exception as e:
            print(f"Error saving yield data to database: {e}")

    @staticmethod
    def _next_trade_date(current_date: datetime) -> datetime:
        """Move to next calendar date (skip weekends) (copied from DividendYieldProvider)"""
        next_date = current_date + timedelta(days=1)
        # Skip weekends (Saturday=5, Sunday=6 in Python weekday)
        while next_date.weekday() >= 5:
            next_date += timedelta(days=1)
        return next_date
