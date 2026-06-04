"""
Daily Data Provider
Handles daily stock price, history and index data operations

Part of TGetExternalData refactoring
"""
from datetime import datetime
import pandas as pd
import logging

from pydb_core.sql_service import SqlService
from pydb_core.mongo_service import MongoService
from pydb_core.read_load_system import ReadLoadSystem
from pydb_core.cache_service import HybridCacheService


class DailyDataProvider:
    def __init__(self,
                 sql_service: SqlService,
                 mongo_service: MongoService,
                 read_load_system: ReadLoadSystem,
                 cache_service: HybridCacheService):
        self._sql_service = sql_service
        self._mongo_service = mongo_service
        self._read_load_system = read_load_system
        self._cache_service = cache_service
        self._logger = logging.getLogger(__name__)

    def get_allstock_daily_data(self, start: datetime, end: datetime) -> pd.DataFrame:
        """
        Get daily price data for all stocks in date range

        Args:
            start: Start date
            end: End date

        Returns:
            DataFrame with daily price data
        """
        self._logger.info(f"Getting daily price data: {start} ~ {end}")

        cache_key = f"daily_data_{start.date()}_{end.date()}"

        cached_data = self._cache_service.get(cache_key)
        if cached_data is not None:
            return cached_data

        sql_data = self._get_daily_data_from_sql(start, end)
        if not sql_data.empty:
            self._cache_service.set(cache_key, sql_data, ttl=3600)
            return sql_data

        daily_data = self._download_daily_data(start, end)
        self._save_daily_data_to_db(daily_data)
        self._cache_service.set(cache_key, daily_data, ttl=3600)

        return daily_data

    def get_stock_history(self, symbol: int | str, start_date: datetime | None = None, end_date: datetime | None = None) -> pd.DataFrame:
        """
        Get historical data for specific stock

        Args:
            symbol: Stock symbol (integer stock code or string format)
            start_date: Start date for history (optional)
            end_date: End date for history (optional)

        Returns:
            DataFrame with stock history
        """
        self._logger.info(f"Getting stock history: {symbol} from {start_date} to {end_date}")

        stock_count = symbol

        return self._get_stock_history_data(stock_count, start_date, end_date)

    def get_stock_info(self) -> pd.DataFrame:
        """
        Get basic stock information for all stocks

        Returns:
            DataFrame with stock information
        """
        self._logger.info("Getting stock information")

        cache_key = "stock_info"

        cached_data = self._cache_service.get(cache_key)
        if cached_data is not None:
            return cached_data

        stock_info = self._get_stock_info_data()
        self._cache_service.set(cache_key, stock_info, ttl=86400)

        return stock_info

    def get_index_data(self, start: datetime, end: datetime) -> pd.DataFrame:
        """
        Get market index historical data

        Args:
            start: Start date
            end: End date

        Returns:
            DataFrame with index data
        """
        self._logger.info(f"Getting index data: {start} ~ {end}")
        return self._get_index_history_data(start, end)

    def _get_daily_data_from_sql(self, start: datetime, end: datetime) -> pd.DataFrame:
        """Get daily price data from SQL database (stock_daily_prices table)"""
        try:
            with self._sql_service.server_flask.app_context():
                query = """
                SELECT symbol, date as Date, open as Open, high as High, low as Low,
                       close as Close, adj_close as `Adj Close`, volume as Volume
                FROM stock_daily_prices
                WHERE date BETWEEN :start_date AND :end_date
                ORDER BY date
                """

                params = {
                    'start_date': start.date(),
                    'end_date': end.date()
                }

                from sqlalchemy import text
                dataframe = pd.read_sql(
                    sql=text(query),
                    con=self._sql_service.MySql_server.engine,
                    params=params,
                    index_col=["symbol", "Date"]
                )

                return dataframe
        except Exception as e:
            self._logger.error(f"SQL Error when getting daily price data: {e}")
            return pd.DataFrame()

    def _download_daily_data(self, start: datetime, end: datetime) -> pd.DataFrame:
        """Download daily price data from external source"""
        try:
            import yfinance as yf

            self._logger.info(f"Downloading daily data from Yahoo Finance: {start.date()} ~ {end.date()}")

            # Get all stock symbols from stock info
            stock_info = self._get_stock_info_data()

            if stock_info.empty:
                self._logger.warning("No stock symbols found for download")
                return pd.DataFrame()

            # Format symbols for Yahoo Finance (TW stocks use .TW suffix)
            symbols = []
            for code in stock_info.index:
                # Convert to 4-digit string, add .TW suffix for Taiwan stocks
                symbol_str = str(code).zfill(4) + ".TW"
                symbols.append(symbol_str)

            self._logger.info(f"Downloading data for {len(symbols)} stocks")

            # Batch download all stocks
            all_data = yf.download(
                tickers=symbols,
                start=start,
                end=end,
                group_by='ticker',
                auto_adjust=False,
                progress=False
            )

            if all_data.empty:
                self._logger.warning("No data returned from Yahoo Finance")
                return pd.DataFrame()

            # Reshape data to match our database format
            result_rows = []

            for symbol in symbols:
                if symbol not in all_data.columns.get_level_values(0):
                    continue

                stock_data = all_data[symbol].dropna(how='all')

                if stock_data.empty:
                    continue

                # Extract base code without .TW suffix
                base_code = int(symbol.replace('.TW', ''))

                # Add symbol column and format
                stock_data = stock_data.copy()
                stock_data['symbol'] = base_code

                # Rename columns to match database schema
                stock_data = stock_data.rename(columns={
                    'Open': 'open',
                    'High': 'high',
                    'Low': 'low',
                    'Close': 'close',
                    'Adj Close': 'adj_close',
                    'Volume': 'volume'
                })

                # Reset index to get date as column
                stock_data = stock_data.reset_index().rename(columns={'Date': 'date'})

                result_rows.append(stock_data)

            if not result_rows:
                self._logger.warning("No valid stock data after processing")
                return pd.DataFrame()

            # Combine all data
            combined_data = pd.concat(result_rows, ignore_index=True)

            # Set index same as SQL query output
            combined_data = combined_data.set_index(['symbol', 'date'])

            self._logger.info(f"Successfully downloaded {len(combined_data)} daily records")

            return combined_data

        except Exception as e:
            self._logger.error(f"Error downloading daily data: {str(e)}", exc_info=True)
            return pd.DataFrame()

    def _save_daily_data_to_db(self, data: pd.DataFrame) -> None:
        """Save daily price data to database"""
        if data.empty:
            return

        try:
            # Reset index to get symbol and date as columns
            save_data = data.reset_index()

            # Use SqlService save method
            self._sql_service.saveTable('stock_daily_prices', save_data)
            self._logger.info(f"Saved {len(data)} daily price records to database")
        except Exception as e:
            self._logger.error(f"Error saving daily data to database: {e}")

    def _get_stock_history_data(self, stock_count: int, start_date: datetime | None = None, end_date: datetime | None = None) -> pd.DataFrame:
        """Get stock history data"""
        # Convert stock code to string format
        stock_symbol = str(stock_count)

        # Get all available data from database
        full_data = self._sql_service.readStockDay(stock_symbol)

        if full_data.empty:
            return pd.DataFrame()

        # Filter by date range
        filtered_data = full_data

        if start_date is not None:
            filtered_data = filtered_data[filtered_data.index >= start_date]

        if end_date is not None:
            filtered_data = filtered_data[filtered_data.index <= end_date]

        return filtered_data

    def _get_stock_info_data(self) -> pd.DataFrame:
        """Get stock basic information"""
        try:
            with self._sql_service.server_flask.app_context():
                from sqlalchemy import text
                query = text("SELECT code, name, group_code, group_name, market FROM stock_info")
                dataframe = pd.read_sql(
                    sql=query,
                    con=self._sql_service.MySql_server.engine,
                    index_col="code"
                )
                return dataframe
        except Exception as e:
            self._logger.error(f"SQL Error when getting stock info: {e}")
            return pd.DataFrame()

    def _get_index_history_data(self, start: datetime, end: datetime) -> pd.DataFrame:
        """Get market index history data"""
        try:
            import yfinance as yf
            index_symbol = "^TWII"  # Taiwan Weighted Index
            ticker = yf.Ticker(index_symbol)
            history = ticker.history(start=start, end=end)

            # Standardize column names
            history.columns = [col.title() for col in history.columns]

            return history
        except Exception as e:
            self._logger.error(f"Error getting index history: {e}")
            return pd.DataFrame()
