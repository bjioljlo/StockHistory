"""
ExternalDataFactory - backward compatibility wrapper

Now delegates to datafetcher_core.external_data_factory.
"""
import warnings

from datafetcher_core.external_data_factory import (
    ExternalDataFactory,
    ExternalDataTypeEnum,
)

warnings.warn(
    "src.ExternalService.ExternalDataFactory is deprecated. "
    "Use datafetcher_core.external_data_factory directly.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["ExternalDataFactory", "ExternalDataTypeEnum"]
