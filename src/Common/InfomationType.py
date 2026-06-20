"""
Legacy InfomationType module - Backward compatibility wrapper
=============================================================

Now imports from extracted package: datafetcher-core.
Original definitions moved to datafetcher_core.types.
"""

import warnings

from datafetcher_core.types import (
    StrEnum,
    FS_type,
    CPL_type,
    BS_type,
    PLA_type,
    SCF_type,
    Month_type,
    Day_type,
    Price_type,
    local_type,
    stock_data_kind,
)

warnings.warn(
    "InfomationType module is deprecated. Use datafetcher_core.types instead.",
    DeprecationWarning,
    stacklevel=2
)
