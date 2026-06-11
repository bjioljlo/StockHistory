"""
Data utilities module - backward compatibility wrapper
=====================================================

Now delegates to indicator_core.
"""
import warnings

from indicator_core import DataUtils as _DataUtils

merge_dataframes = _DataUtils.merge_dataframes
extract_ticker_data = _DataUtils.extract_ticker_data

# TidyTicketData is an alias for extract_ticker_data
TidyTicketData = extract_ticker_data

warnings.warn(
    "DataUtils module is deprecated. Use indicator_core directly.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["merge_dataframes", "extract_ticker_data", "TidyTicketData"]
