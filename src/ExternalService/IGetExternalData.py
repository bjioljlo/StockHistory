"""
IGetExternalData - backward compatibility shim

Now re-exports from datafetcher_core.interfaces.
"""
import warnings

from datafetcher_core.interfaces import IGetExternalData

warnings.warn(
    "src.ExternalService.IGetExternalData is deprecated. "
    "Use datafetcher_core.interfaces.IGetExternalData directly.",
    DeprecationWarning,
    stacklevel=2,
)
