"""
Legacy Tools module - Backward compatibility wrapper
===================================================

Now imports from extracted packages: indicator-core, pyutils-core.
Original definitions moved to standalone repos.
"""

import warnings

from indicator_core import DateUtils as _DateUtils
from indicator_core.financial_utils import (
    calculate_total_with_fees, calculate_max_shares, smooth_data,
)

# Re-export date_utils functions via DateUtils module
change_date_month = _DateUtils.change_date_month
check_month_date = _DateUtils.check_month_date
back_work_days = _DateUtils.back_work_days
qt_date_to_datetime = _DateUtils.qt_date_to_datetime
datetime_to_string = _DateUtils.datetime_to_string
check_fs_season = _DateUtils.check_fs_season
have_month_rp = _DateUtils.have_month_rp
have_day_rp = _DateUtils.have_day_rp
get_latest_season_report_date = _DateUtils.get_latest_season_report_date
get_latest_monthly_report_date = _DateUtils.get_latest_monthly_report_date
get_latest_daily_report_date = _DateUtils.get_latest_daily_report_date
SEASON_RP_TIME_MONTH = _DateUtils.SEASON_RP_TIME_MONTH
SEASON_RP_TIME_DAY = _DateUtils.SEASON_RP_TIME_DAY

# Legacy camelCase aliases for backward compatibility
changeDateMonth = change_date_month
check_monthDate = check_month_date
QtDate2DateTime = qt_date_to_datetime
DateTime2String = datetime_to_string
backWorkDays = back_work_days
CheckFS_season = check_fs_season
Have_MonthRP = have_month_rp
Have_DayRP = have_day_rp
Total_with_Handling_fee_and_Tax = calculate_total_with_fees
Count_Stock_Amount = calculate_max_shares

from src.Common.DataUtils import TidyTicketData

from indicator_core import DataUtils
merge_dataframes = DataUtils.merge_dataframes
extract_ticker_data = DataUtils.extract_ticker_data

from indicator_core import NetworkUtils
get_random_user_agent = NetworkUtils.get_random_user_agent
get_random_headers = NetworkUtils.get_random_headers
get_sp500_tickers = NetworkUtils.get_sp500_tickers
_USER_AGENTS = getattr(NetworkUtils, "USER_AGENTS", getattr(NetworkUtils, "_USER_AGENTS", []))

from indicator_core import StockUtils
is_excluded_stock = StockUtils.is_excluded_stock
is_etf_stock = StockUtils.is_etf_stock
EXCLUDED_STOCKS = StockUtils.EXCLUDED_STOCKS
ETF_LIST = StockUtils.ETF_LIST

warnings.warn(
    "Tools module is deprecated. Use indicator_core.*, pyutils_core.*",
    DeprecationWarning,
    stacklevel=2
)
