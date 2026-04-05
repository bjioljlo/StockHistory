"""
Filter Data Merger for Stock Pick Model

Extracted from Model_pick.py - single responsibility: merging filter dataframes
"""
import logging
import pandas as pd


logger = logging.getLogger(__name__)


class FilterDataMerger:
    """Merges filter results into base data"""

    @staticmethod
    def merge_filter_data(base_data: pd.DataFrame, filter_data: pd.DataFrame,
                          filter_name: str) -> pd.DataFrame:
        """
        Merge filter data into base dataframe

        Args:
            base_data: Base dataframe to merge into
            filter_data: Filter result dataframe
            filter_name: Name of the filter (used for suffix)

        Returns:
            Merged dataframe
        """
        if filter_data.empty:
            logger.debug(f"Filter {filter_name} returned empty data, skipping merge")
            return base_data

        merge_columns = ['stock_code', 'date']

        # Check if all merge columns exist in both dataframes
        for col in merge_columns:
            if col not in base_data.columns or col not in filter_data.columns:
                logger.warning(f"Missing column {col} for merge, cannot merge {filter_name}")
                return base_data

        # Rename conflicting columns
        filter_data = filter_data.add_suffix(f'_{filter_name}')
        for col in merge_columns:
            filter_data[col] = filter_data[f'{col}_{filter_name}']
            filter_data = filter_data.drop(columns=[f'{col}_{filter_name}'])

        # Perform merge
        merged = pd.merge(base_data, filter_data, on=merge_columns, how='left')
        logger.debug(f"Merged {filter_name} data: {len(merged)} records")

        return merged