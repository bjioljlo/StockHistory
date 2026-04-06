"""
Stock Data Downloader Module

Responsible for:
- Downloading stock data with retry mechanism
- Exponential backoff with jitter
- Market detection
- Basic data cleanup and validation
"""
import time
import random
import pandas as pd
import numpy as np
import pytz
import yfinance as yf
from datetime import datetime, timedelta


class StockDataDownloader:
    def __init__(self, retry_attempts: int = 3, retry_delay: float = 1.0):
        self._retry_attempts = retry_attempts
        self._retry_delay = retry_delay

    def download_with_retry(self, stock_symbol: str, start_date: datetime, end_date: datetime, tz: str = None) -> pd.DataFrame:
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

    def determine_market(self, stock_name: str) -> str:
        """Determine market type"""
        name_lower = stock_name.lower()
        if name_lower.endswith('.tw') or (name_lower.replace('.tw', '').isdigit() and len(name_lower.replace('.tw', '')) >= 4):
            return 'TW'
        elif len(name_lower) <= 5 and not name_lower.replace('.', '').isdigit():
            return 'US'
        else:
            return 'OTHER'

    def basic_data_cleanup(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        """Basic data cleanup - performs validation and sanitization"""
        try:
            if df.empty:
                return df

            # Remove duplicate indices
            df = df[~df.index.duplicated(keep='last')]

            # Sort index
            df = df.sort_index()

            # Handle infinite values and NaN
            numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in numeric_columns:
                if col in df.columns:
                    # Replace infinite values with NaN
                    df[col] = df[col].replace([np.inf, -np.inf], np.nan)
                    # Forward fill NaN values (limit to 5 trading days)
                    df[col] = df[col].fillna(method='ffill', limit=5)

            # Remove rows where all values are NaN
            df = df.dropna(how='all')

            # Remove rows with negative volume
            if 'Volume' in df.columns:
                df = df[df['Volume'] >= 0]

            # Ensure price fields are positive
            price_columns = ['Open', 'High', 'Low', 'Close']
            for col in price_columns:
                if col in df.columns:
                    df = df[df[col] > 0]

            # Check if there are still NaN values after cleanup
            nan_counts = df.isna().sum()
            total_nans = nan_counts.sum()
            if total_nans > 0:
                print(f"Warning: {stock_code} still has {total_nans} NaN values after cleanup")
                # Fill remaining NaN values with 0
                df = df.fillna(0)

            return df

        except Exception as e:
            print(f"Error in basic data cleanup for {stock_code}: {e}")
            return df