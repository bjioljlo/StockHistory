import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class DataValidationService:
    """
    資料驗證服務 - 在儲存前驗證爬取資料的完整性和準確性
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.validation_enabled = config.get('app', {}).get('data_validation', True)
        self.max_date_range_days = 365 * 20  # 最多20年資料
        self.min_required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']

    def validate_stock_data(self, stock_code: str, df: pd.DataFrame,
                          source: str = 'yahoo') -> Tuple[bool, List[str], pd.DataFrame]:
        """
        驗證股票資料

        Args:
            stock_code: 股票代碼
            df: 股票資料DataFrame
            source: 資料來源

        Returns:
            Tuple[bool, List[str], pd.DataFrame]: (是否通過驗證, 錯誤訊息列表, 清理後的資料)
        """
        if not self.validation_enabled:
            return True, [], df

        errors = []
        cleaned_df = df.copy()

        # 1. 基本結構驗證
        is_valid, struct_errors = self._validate_data_structure(df)
        errors.extend(struct_errors)

        if not is_valid:
            return False, errors, cleaned_df

        # 2. 資料清理
        cleaned_df = self._clean_data(cleaned_df, stock_code)

        # 3. 數值驗證
        num_errors = self._validate_numeric_values(cleaned_df, stock_code)
        errors.extend(num_errors)

        # 4. 時間序列驗證
        time_errors = self._validate_time_series(cleaned_df, stock_code)
        errors.extend(time_errors)

        # 5. 業務邏輯驗證
        business_errors = self._validate_business_logic(cleaned_df, stock_code, source)
        errors.extend(business_errors)

        is_valid = len(errors) == 0

        if not is_valid:
            logger.warning(f"Data validation failed for {stock_code}: {errors}")

        return is_valid, errors, cleaned_df

    def _validate_data_structure(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """驗證資料結構"""
        errors = []

        if df.empty:
            errors.append("DataFrame is empty")
            return False, errors

        # 檢查必要的欄位
        missing_columns = []
        for col in self.min_required_columns:
            if col not in df.columns:
                missing_columns.append(col)

        if missing_columns:
            errors.append(f"Missing required columns: {missing_columns}")
            return False, errors

        # 檢查索引類型
        if not isinstance(df.index, pd.DatetimeIndex):
            errors.append("DataFrame index must be DatetimeIndex")

        # 檢查資料類型
        numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in numeric_columns:
            if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
                errors.append(f"Column {col} must be numeric")

        return len(errors) == 0, errors

    def _clean_data(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        """清理資料"""
        try:
            # 移除重複的索引
            df = df[~df.index.duplicated(keep='last')]

            # 排序索引
            df = df.sort_index()

            # 處理無限值和NaN
            numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in numeric_columns:
                if col in df.columns:
                    # 將無限值替換為NaN
                    df[col] = df[col].replace([np.inf, -np.inf], np.nan)
                    # 向前填充NaN值（限制為5個交易日）
                    df[col] = df[col].fillna(method='ffill', limit=5)

            # 移除所有值都是NaN的行
            df = df.dropna(how='all')

            # 移除成交量為負數的行
            if 'Volume' in df.columns:
                df = df[df['Volume'] >= 0]

            # 確保價格欄位為正數
            price_columns = ['Open', 'High', 'Low', 'Close']
            for col in price_columns:
                if col in df.columns:
                    df = df[df[col] > 0]

        except Exception as e:
            logger.error(f"Error cleaning data for {stock_code}: {e}")

        return df

    def _validate_numeric_values(self, df: pd.DataFrame, stock_code: str) -> List[str]:
        """驗證數值範圍"""
        errors = []

        try:
            # 檢查價格範圍（假設股票價格不會超過100萬）
            price_columns = ['Open', 'High', 'Low', 'Close']
            for col in price_columns:
                if col in df.columns:
                    invalid_prices = df[(df[col] <= 0) | (df[col] > 1000000)]
                    if not invalid_prices.empty:
                        errors.append(f"Invalid {col} prices found: {len(invalid_prices)} rows")

            # 檢查High >= Low
            if 'High' in df.columns and 'Low' in df.columns:
                invalid_hl = df[df['High'] < df['Low']]
                if not invalid_hl.empty:
                    errors.append(f"High < Low found: {len(invalid_hl)} rows")

            # 檢查成交量範圍
            if 'Volume' in df.columns:
                # 成交量通常不會超過10億
                invalid_volume = df[df['Volume'] > 1000000000]
                if not invalid_volume.empty:
                    errors.append(f"Suspiciously high volume: {len(invalid_volume)} rows")

        except Exception as e:
            errors.append(f"Error in numeric validation: {e}")

        return errors

    def _validate_time_series(self, df: pd.DataFrame, stock_code: str) -> List[str]:
        """驗證時間序列"""
        errors = []

        try:
            if len(df) < 2:
                return errors  # 單筆資料不做時間序列驗證

            # 檢查日期範圍
            date_range = df.index.max() - df.index.min()
            if date_range.days > self.max_date_range_days:
                errors.append(f"Date range too large: {date_range.days} days")

            # 檢查是否有未來日期
            today = datetime.now().date()
            future_dates = df[df.index.date > today]
            if not future_dates.empty:
                errors.append(f"Future dates found: {len(future_dates)} rows")

            # 檢查資料間隔（不應該有太長的空白期）
            date_diffs = df.index.to_series().diff().dropna()
            max_gap_days = 30  # 最多30天空白
            large_gaps = date_diffs[date_diffs > timedelta(days=max_gap_days)]
            if len(large_gaps) > 10:  # 允許一些空白
                errors.append(f"Too many large date gaps: {len(large_gaps)} gaps > {max_gap_days} days")

        except Exception as e:
            errors.append(f"Error in time series validation: {e}")

        return errors

    def _validate_business_logic(self, df: pd.DataFrame, stock_code: str, source: str) -> List[str]:
        """驗證業務邏輯"""
        errors = []

        try:
            # 檢查收盤價不能為0
            if 'Close' in df.columns:
                zero_closes = df[df['Close'] == 0]
                if not zero_closes.empty:
                    errors.append(f"Zero closing prices found: {len(zero_closes)} rows")

            # 檢查成交量不能長期為0
            if 'Volume' in df.columns:
                zero_volume_streak = 0
                max_zero_streak = 5  # 最多5天連續0成交量
                for idx, row in df.iterrows():
                    if row['Volume'] == 0:
                        zero_volume_streak += 1
                        if zero_volume_streak > max_zero_streak:
                            errors.append(f"Too many consecutive zero volumes: {zero_volume_streak} days")
                            break
                    else:
                        zero_volume_streak = 0

            # 檢查價格變動合理性（單日漲跌幅不超過50%）
            if len(df) > 1 and 'Close' in df.columns:
                pct_change = df['Close'].pct_change().abs()
                extreme_changes = pct_change[pct_change > 0.5]  # 50%漲跌幅
                if not extreme_changes.empty:
                    errors.append(f"Extreme price changes detected: {len(extreme_changes)} days")

        except Exception as e:
            errors.append(f"Error in business logic validation: {e}")

        return errors

    def validate_batch_data(self, data_dict: Dict[str, pd.DataFrame],
                          source: str = 'yahoo') -> Dict[str, Tuple[bool, List[str], pd.DataFrame]]:
        """
        批次驗證多檔股票資料

        Args:
            data_dict: {stock_code: dataframe} 的字典
            source: 資料來源

        Returns:
            Dict[str, Tuple[bool, List[str], pd.DataFrame]]: 驗證結果
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
            'error_details': all_errors[:100]  # 限制錯誤詳情數量
        }
