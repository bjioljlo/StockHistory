"""
Legacy Tools module - Backward compatibility wrapper
===================================================

⚠️  DEPRECATED: This module is maintained for backward compatibility only.
Please import directly from the new utility modules:

- DateUtils: date and time handling functions
- FinancialUtils: financial and trading calculations
- DataUtils: DataFrame and data processing functions
- NetworkUtils: HTTP and network functions
- StockUtils: stock classification utilities

All functions are re-exported here for existing code.
New code should import directly from the specialized modules.
"""

import warnings

# Re-export all functions from new modules
from .DateUtils import (
    change_date_month,
    check_month_date,
    back_work_days,
    qt_date_to_datetime,
    datetime_to_string,
    check_fs_season,
    have_month_rp,
    have_day_rp,
    get_latest_season_report_date,
    get_latest_monthly_report_date,
    get_latest_daily_report_date,
    SEASON_RP_TIME_MONTH,
    SEASON_RP_TIME_DAY,
)

from .FinancialUtils import (
    calculate_total_with_fees,
    calculate_max_shares,
    smooth_data,
)

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

from .DataUtils import (
    merge_dataframes,
    extract_ticker_data,
)

from .NetworkUtils import (
    get_random_user_agent,
    get_random_headers,
    get_sp500_tickers,
    _USER_AGENTS,
)

from .StockUtils import (
    is_excluded_stock,
    is_etf_stock,
    EXCLUDED_STOCKS,
    ETF_LIST,
)



# Show deprecation warning when module is imported
warnings.warn(
    "Tools module is deprecated. Please import from specialized utility modules: "
    "DateUtils, FinancialUtils, DataUtils, NetworkUtils, StockUtils",
    DeprecationWarning,
    stacklevel=2
)