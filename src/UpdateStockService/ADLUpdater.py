"""
Legacy ADLUpdater module - Backward compatibility wrapper
==========================================================

Now delegates to datafetcher_core.adl_updater.
"""
import warnings

from datafetcher_core.adl_updater import ADLUpdater

warnings.warn(
    "src.UpdateStockService.ADLUpdater is deprecated. "
    "Use datafetcher_core.adl_updater directly.",
    DeprecationWarning,
    stacklevel=2,
)
