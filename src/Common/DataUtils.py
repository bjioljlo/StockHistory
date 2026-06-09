"""
Data utilities module
=====================

Data processing and DataFrame manipulation functions.
"""

import pandas as pd
from typing import Dict, Optional
from indicator_core.Exceptions import InvalidDataError


def merge_dataframes(
    dataframes: Dict[str, pd.DataFrame],
    index_column: str = "code"
) -> pd.DataFrame:
    """
    Merge multiple DataFrames using inner join on specified index.

    Args:
        dataframes: Dictionary of DataFrames to merge (key: name, value: DataFrame)
        index_column: Column name to use as merge key

    Returns:
        Merged DataFrame

    Raises:
        InvalidDataError: If input is invalid or merge fails
    """
    if not dataframes:
        raise InvalidDataError("DataFrames dictionary cannot be empty")

    # Validate inputs
    valid_dfs = {}
    for name, df in dataframes.items():
        if df is None:
            raise InvalidDataError(f"DataFrame '{name}' is None")
        if not isinstance(df, pd.DataFrame):
            raise InvalidDataError(f"DataFrame '{name}' is not a valid DataFrame")
        if not df.empty:
            valid_dfs[name] = df

    if not valid_dfs:
        return pd.DataFrame()

    # Perform merge
    result = None

    for name, df in valid_dfs.items():
        if result is None:
            result = df.copy()
            continue

        try:
            # Check if both have the index column
            if index_column in result.columns and index_column in df.columns:
                result = pd.merge(
                    result, df, on=index_column, how="inner", suffixes=["", f"_{name}"]
                )
            elif result.index.name == df.index.name and result.index.name is not None:
                result = pd.merge(
                    result, df, left_index=True, right_index=True,
                    how="inner", suffixes=["", f"_{name}"]
                )
            else:
                result = pd.merge(
                    result, df, left_index=True, right_index=True,
                    how="inner", suffixes=["", f"_{name}"]
                )
        except pd.errors.MergeError as e:
            raise InvalidDataError(f"Failed to merge DataFrame '{name}': {str(e)}") from e
        except Exception as e:
            raise InvalidDataError(f"Unexpected error merging DataFrame '{name}': {str(e)}") from e

    return result


def TidyTicketData(df_result: pd.DataFrame, ticker_name: str) -> pd.DataFrame:
    """
    Tidy up Yahoo Finance ticker data - extract single ticker from multi-index DataFrame.

    Args:
        df_result: DataFrame from yfinance.download (may be multi-level columns)
        ticker_name: Ticker symbol to extract

    Returns:
        DataFrame with columns: Close, High, Low, Open, Volume
    """
    from indicator_core.data_utils import extract_ticker_data
    return extract_ticker_data(df_result, ticker_name)


def extract_ticker_data(df_result: pd.DataFrame, ticker_name: str) -> pd.DataFrame:
    """
    Extract OHLCV data for specific ticker from multi-index DataFrame.

    Args:
        df_result: DataFrame with multi-index columns (Indicator, Ticker)
        ticker_name: Name of ticker to extract

    Returns:
        DataFrame with columns: Close, High, Low, Open, Volume
    """
    df_out = pd.DataFrame(
        columns=["Close", "High", "Low", "Open", "Volume"],
        index=df_result.index
    )

    indicators = ["Close", "High", "Low", "Open", "Volume"]

    for indicator in indicators:
        df_out[indicator] = df_result[(indicator, ticker_name)]

    return df_out
