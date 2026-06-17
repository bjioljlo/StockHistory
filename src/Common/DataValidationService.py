"""
DataValidationService - backward compatibility wrapper

Delegates to datafetcher_core.data_validation.DataValidationService
for core functionality, while preserving config-based initialization.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import logging

from datafetcher_core.data_validation import DataValidationService as _DataValidationService

logger = logging.getLogger(__name__)


class DataValidationService:
    """
    資料驗證服務 - 在儲存前驗證爬取資料的完整性和準確性

    委託 datafetcher_core.data_validation.DataValidationService 提供核心驗證功能。
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.validation_enabled = config.get('app', {}).get('data_validation', True)
        self.max_date_range_days = 365 * 20  # 最多20年資料
        self.min_required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        # Core validation delegate
        self._delegate = _DataValidationService()

    def validate_stock_data(self, stock_code: str, df: pd.DataFrame,
                          source: str = 'yahoo') -> Tuple[bool, List[str], pd.DataFrame]:
        """
        驗證股票資料
        """
        if not self.validation_enabled:
            return True, [], df

        return self._delegate.validate_stock_data(stock_code, df, source)

    def validate_batch_data(self, data_dict: Dict[str, pd.DataFrame],
                          source: str = 'yahoo') -> Dict[str, Tuple[bool, List[str], pd.DataFrame]]:
        """
        批次驗證多檔股票資料
        """
        results = {}
        for stock_code, df in data_dict.items():
            is_valid, errors, cleaned_df = self.validate_stock_data(stock_code, df, source)
            results[stock_code] = (is_valid, errors, cleaned_df)
        return results

    def get_validation_summary(self, validation_results: Dict[str, Tuple[bool, List[str], pd.DataFrame]]) -> Dict[str, Any]:
        """獲取驗證摘要"""
        total_stocks = len(validation_results)
        valid_stocks = sum(1 for result in validation_results.values() if result[0])
        invalid_stocks = total_stocks - valid_stocks

        all_errors = []
        for stock_code, (is_valid, errors, _) in validation_results.items():
            if not is_valid:
                all_errors.extend([f"{stock_code}: {error}" for error in errors])

        return {
            'total_stocks': total_stocks,
            'valid_stocks': valid_stocks,
            'invalid_stocks': invalid_stocks,
            'validation_rate': valid_stocks / total_stocks if total_stocks > 0 else 0,
            'total_errors': len(all_errors),
            'error_details': all_errors[:100]
        }
