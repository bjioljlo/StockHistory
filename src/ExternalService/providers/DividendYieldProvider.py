"""
Dividend Yield Provider
Handles dividend yield, PER and PBR data operations

Part of TGetExternalData refactoring
"""
from io import StringIO
import os
import time
from datetime import datetime
import pandas as pd
import logging
import requests

from src.SqlService import SqlService
from src.MongoService import MongoService
from src.ReadLoadSystem import ReadLoadSystem
from src.Common.CacheService import HybridCacheService
from src.Common import Tools


class DividendYieldProvider:
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
        self._file_path = os.getcwd()

    def get_allstock_yield(self, symbol: str, start: datetime, end: datetime | None = None) -> pd.DataFrame:
        """
        Get all stock yield data (PER, dividend yield, PBR) for specific date range

        Follows DailyDataProvider pattern: cache -> SQL only (no download)

        Args:
            symbol: Stock symbol (optional, if None, query all stocks)
            start: Start date (if end is None, only query this date)
            end: End date (optional, query date range if provided)

        Returns:
            DataFrame with yield data (columns: symbol, date, company_name,
                    pe_ratio, dividend_yield, pb_ratio)
        """
        if end is None:
            end = start

        self._logger.info(f"Getting stock yield data: {symbol} --> {start.date()} ~ {end.date()}")

        cache_key = f"stock_yield_{symbol}_{start.date()}_{end.date()}"

        # 1. Check cache first
        cached = self._cache_service.get(cache_key)
        if cached is not None:
            self._logger.debug(f"Cache HIT for {cache_key}")
            return cached

        # 2. Get from SQL database only (no download)
        sql_data = self._get_yield_from_sql(symbol=symbol, start=start, end=end)
        if not sql_data.empty:
            self._logger.debug(f"Loaded yield data from SQL database")
            self._cache_service.set(cache_key, sql_data, ttl=3600)
            return sql_data

        # No data available in SQL
        self._logger.warning(f"No yield data available in SQL for {start.date()} ~ {end.date()}")
        empty_result = pd.DataFrame()
        self._cache_service.set(cache_key, empty_result, ttl=600)
        return empty_result

    def get_allstock_dividend_yield(self) -> pd.DataFrame:
        """
        Get all stock dividend yield data from database (backward compatibility)

        Returns all records from dividend_yield table without date filter.

        Returns:
            DataFrame with dividend yield data (columns: symbol, date, company_name,
                    pe_ratio, dividend_yield, pb_ratio)
        """
        self._logger.info("Getting all dividend yield data from database")

        cache_key = "dividend_yield_all"

        cached = self._cache_service.get(cache_key)
        if cached is not None:
            return cached

        try:
            result = self._sql_service.read_dividend_yield(limit=10000)

            if not result.empty:
                self._cache_service.set(cache_key, result, ttl=86400)
                return result

            self._logger.warning("No dividend yield data found in database")
            empty_result = pd.DataFrame()
            self._cache_service.set(cache_key, empty_result, ttl=3600)
            return empty_result

        except Exception as e:
            self._logger.error(f"Error getting dividend yield data: {e}")
            empty_result = pd.DataFrame()
            self._cache_service.set(cache_key, empty_result, ttl=3600)
            return empty_result

    def _get_yield_from_sql(self, symbol: str, start: datetime, end: datetime) -> pd.DataFrame:
        """Get yield data from SQL dividend_yield table for date range"""
        try:
            start_str = start.strftime('%Y-%m-%d')
            end_str = end.strftime('%Y-%m-%d')

            result = self._sql_service.read_dividend_yield(
                symbol=symbol,
                start_date=start_str,
                end_date=end_str,
                limit=10000
            )

            if not result.empty:
                self._logger.debug(f"Found {len(result)} yield records from SQL for {start_str} ~ {end_str}")

            return result

        except Exception as e:
            self._logger.error(f"SQL Error when getting yield data: {e}")
            return pd.DataFrame()

    def _download_yield_data(self, start: datetime, end: datetime) -> pd.DataFrame:
        """
        Download yield data from TWSE (臺灣證券交易所)

        Uses the same endpoint as the original get_allstock_yield implementation:
        https://www.twse.com.tw/exchangeReport/BWIBBU_d?response=csv&date=YYYYMMDD&selectType=ALL

        This endpoint returns CSV with columns:
        證券代號, 證券名稱, 本益比, 殖利率(%), 股價淨值比

        Downloads data for each date in the range and combines results.
        """
        try:
            self._logger.info(f"Downloading yield data from TWSE: {start.date()} ~ {end.date()}")

            all_data = []
            current_date = start

            while current_date <= end:
                date_str = f"{current_date.year}{current_date.month:02d}{current_date.day:02d}"
                url = (
                    "https://www.twse.com.tw/exchangeReport/BWIBBU_d"
                    f"?response=csv&date={date_str}&selectType=ALL"
                )

                self._logger.debug(f"Downloading yield data for {date_str}")

                try:
                    response = requests.get(url, headers=Tools.get_random_headers(), timeout=30)

                    if response.status_code != 200:
                        self._logger.warning(f"TWSE returned status {response.status_code} for {date_str}")
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
                            self._logger.debug(f"No data in TWSE response for {date_str}")
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
                            self._logger.warning(f"Could not decode TWSE data for {date_str}")
                            current_date = self._next_trade_date(current_date)
                            continue

                        if df.empty:
                            self._logger.debug(f"Empty TWSE response for {date_str}")
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

                        if 'symbol' not in rename_map:
                            self._logger.warning(f"No recognizable columns in TWSE data for {date_str}")
                            current_date = self._next_trade_date(current_date)
                            continue

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
                            self._logger.debug(f"Got {len(df)} records for {date_str}")

                        # Throttle to avoid TWSE rate limiting
                        time.sleep(3)

                    except Exception as parse_err:
                        self._logger.warning(f"Error parsing TWSE response for {date_str}: {parse_err}")

                except requests.exceptions.RequestException as req_err:
                    self._logger.warning(f"Request failed for {date_str}: {req_err}")
                    time.sleep(5)

                current_date = self._next_trade_date(current_date)

            if not all_data:
                self._logger.warning("No yield data downloaded from TWSE")
                return pd.DataFrame()

            # Combine all dates
            combined = pd.concat(all_data, ignore_index=True)

            # Standardize column order
            column_order = ['symbol', 'date', 'company_name', 'pe_ratio', 'dividend_yield', 'pb_ratio']
            available_cols = [c for c in column_order if c in combined.columns]
            combined = combined[available_cols]

            self._logger.info(f"Successfully downloaded {len(combined)} yield records from TWSE "
                            f"for {len(all_data)} trading days")

            return combined

        except Exception as e:
            self._logger.error(f"Error downloading yield data from TWSE: {str(e)}", exc_info=True)
            return pd.DataFrame()

    def _save_yield_to_db(self, data: pd.DataFrame) -> None:
        """Save yield data to dividend_yield table"""
        if data.empty:
            return

        try:
            self._sql_service.upsert_dividend_yield(data)
            self._logger.info(f"Saved {len(data)} yield records to dividend_yield table")
        except Exception as e:
            self._logger.error(f"Error saving yield data to database: {e}")

    @staticmethod
    def _next_trade_date(current_date: datetime) -> datetime:
        """Move to next calendar date (skip weekends)"""
        from datetime import timedelta
        next_date = current_date + timedelta(days=1)
        # Skip weekends (Saturday=5, Sunday=6 in Python weekday)
        while next_date.weekday() >= 5:
            next_date += timedelta(days=1)
        return next_date
