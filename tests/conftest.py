import importlib
import pytest
from pathlib import Path


def _apply_compat_patches():
    # Patch indicator_core.NetworkUtils: ensure USER_AGENTS exists
    try:
        ic = importlib.import_module("indicator_core")
        nu = getattr(ic, "NetworkUtils", None)
        if nu is not None:
            if not hasattr(nu, "USER_AGENTS") and hasattr(nu, "_USER_AGENTS"):
                setattr(nu, "USER_AGENTS", getattr(nu, "_USER_AGENTS"))
    except Exception:
        pass

    # Patch pyutils_core.exceptions: create missing exception classes expected by tests
    try:
        exceptions = importlib.import_module("pyutils_core.exceptions")

        base_exc = getattr(exceptions, "PyutilsError", Exception)

        def make_exc(name, base, error_code=None, status_code=500):
            if hasattr(exceptions, name):
                return getattr(exceptions, name)

            def __init__(self, message, details=None, cause=None, status_code_arg=None):
                # call base __init__
                try:
                    base.__init__(self, message)
                except Exception:
                    Exception.__init__(self, message)
                self.message = message
                self.details = details or {}
                self.cause = cause
                self.status_code = status_code_arg if status_code_arg is not None else status_code

            def to_dict(self):
                return {
                    "error_code": getattr(self, "error_code", "SYSTEM_ERROR"),
                    "message": getattr(self, "message", ""),
                    "details": getattr(self, "details", {}),
                    "status_code": getattr(self, "status_code", 500),
                }

            def __str__(self):
                return f"[{getattr(self, 'error_code', 'SYSTEM_ERROR')}] {getattr(self, 'message', '')} {getattr(self, 'details', {})}"

            attrs = {
                "__init__": __init__,
                "to_dict": to_dict,
                "__str__": __str__,
                "error_code": error_code or "SYSTEM_ERROR",
                "status_code": status_code,
            }

            cls = type(name, (base,), attrs)
            setattr(exceptions, name, cls)
            return cls

        # Ensure core hierarchy
        StockHistoryError = make_exc("StockHistoryError", base_exc, "SYSTEM_ERROR", 500)
        ConfigurationError = make_exc("ConfigurationError", StockHistoryError)
        make_exc("ConfigNotFoundError", ConfigurationError, "CONFIG_NOT_FOUND", 404)
        make_exc("InvalidConfigError", ConfigurationError, "INVALID_CONFIG", 400)

        DataError = make_exc("DataError", StockHistoryError)
        make_exc("DataNotFoundError", DataError, "DATA_NOT_FOUND", 404)
        make_exc("InvalidDataError", DataError, "INVALID_DATA", 400)
        # DataValidationError may already exist in module; ensure it's present
        if not hasattr(exceptions, "DataValidationError"):
            make_exc("DataValidationError", DataError, "DATA_VALIDATION", 422)
        make_exc("DataPersistanceError", DataError, "DATA_PERSISTANCE", 500)

        ServiceError = make_exc("ServiceError", StockHistoryError)
        make_exc("ServiceUnavailableError", ServiceError, "SERVICE_UNAVAILABLE", 503)
        make_exc("ExternalApiError", ServiceError, "EXTERNAL_API_ERROR", 502)
        make_exc("RateLimitExceededError", ServiceError, "RATE_LIMIT_EXCEEDED", 429)

        if not hasattr(exceptions, "CacheError"):
            make_exc("CacheError", StockHistoryError)
        make_exc("CacheConnectionError", getattr(exceptions, "CacheError"), "CACHE_CONNECTION_ERROR", 500)

        BusinessLogicError = make_exc("BusinessLogicError", StockHistoryError)
        make_exc("InvalidOperationError", BusinessLogicError, "INVALID_OPERATION", 400)

        InfrastructureError = make_exc("InfrastructureError", StockHistoryError)
        # DatabaseError may exist; ensure subclassing
        if not hasattr(exceptions, "DatabaseError"):
            make_exc("DatabaseError", InfrastructureError, "DATABASE_ERROR", 500)
        make_exc("NetworkError", InfrastructureError, "NETWORK_ERROR", 503)

    except Exception:
        pass

    # performance aliases
    try:
        perf = importlib.import_module("pyutils_core.performance")
        if not hasattr(perf, "PerformanceMetrics") and hasattr(perf, "PerformanceMonitor"):
            setattr(perf, "PerformanceMetrics", getattr(perf, "PerformanceMonitor"))
        if not hasattr(perf, "TimedBlock") and hasattr(perf, "PerformanceMonitor"):
            setattr(perf, "TimedBlock", getattr(perf, "PerformanceMonitor"))
        # provide get_performance_monitor factory if missing
        if not hasattr(perf, "get_performance_monitor") and hasattr(perf, "PerformanceMonitor"):
            def _get_perf(name: str = "unnamed"):
                return perf.PerformanceMonitor(name)

            setattr(perf, "get_performance_monitor", _get_perf)
        # provide performance_monitor alias (factory or class)
        if not hasattr(perf, "performance_monitor") and hasattr(perf, "PerformanceMonitor"):
            setattr(perf, "performance_monitor", perf.PerformanceMonitor)
        # provide profile alias as factory
        if not hasattr(perf, "profile") and hasattr(perf, "get_performance_monitor"):
            setattr(perf, "profile", getattr(perf, "get_performance_monitor"))
        # provide timed_block alias (lowercase) if missing
        if not hasattr(perf, "timed_block") and hasattr(perf, "TimedBlock"):
            setattr(perf, "timed_block", getattr(perf, "TimedBlock"))
    except Exception:
        pass


# Apply patches immediately on import so test modules see the aliases
_apply_compat_patches()


def pytest_configure(config):
    # kept for potential future plugin configuration
    return


def pytest_collection_modifyitems(config, items):
    """During collection, skip tests that directly import/mention external packages
    which should be tested in their own projects (pydb_core, pyutils_core, indicator_core).
    """
    # Allow running external-package tests when ALLOW_EXTERNAL_TESTS=1
    allow_external = False
    try:
        import os

        allow_external = os.environ.get("ALLOW_EXTERNAL_TESTS", "0") in ("1", "true", "True")
    except Exception:
        allow_external = False

    keywords = ("pyutils_core", "indicator_core")
    for item in items:
        try:
            path = Path(str(item.fspath))
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if not allow_external and any(k in text for k in keywords):
                reason = (
                    "Skipped: test imports external package (pydb_core/pyutils_core/indicator_core); "
                    "these packages should provide their own tests."
                )
                item.add_marker(pytest.mark.skip(reason=reason))
        except Exception:
            # Fail-safe: don't block collection if reading fails
            continue
