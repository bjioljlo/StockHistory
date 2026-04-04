"""
StockHistory Standard Exception Classes
=====================================

Standard error hierarchy for consistent error handling across the system.
All custom exceptions should inherit from these base classes.
"""

from typing import Optional, Dict, Any


class StockHistoryError(Exception):
    """Base exception class for all StockHistory application errors."""
    
    error_code: str = "SYSTEM_ERROR"
    status_code: int = 500
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.cause = cause
    
    def __str__(self) -> str:
        base_msg = f"[{self.error_code}] {self.message}"
        if self.details:
            base_msg += f" | Details: {self.details}"
        return base_msg
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging and serialization."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "status_code": self.status_code
        }


# ============= Configuration Errors =============

class ConfigurationError(StockHistoryError):
    """Error related to application configuration."""
    error_code = "CONFIG_ERROR"
    status_code = 500


class ConfigNotFoundError(ConfigurationError):
    """Configuration file or key not found."""
    error_code = "CONFIG_NOT_FOUND"
    status_code = 404


class InvalidConfigError(ConfigurationError):
    """Invalid configuration value."""
    error_code = "INVALID_CONFIG"
    status_code = 400


# ============= Data Errors =============

class DataError(StockHistoryError):
    """Base class for data-related errors."""
    error_code = "DATA_ERROR"
    status_code = 500


class DataNotFoundError(DataError):
    """Requested data not found."""
    error_code = "DATA_NOT_FOUND"
    status_code = 404


class InvalidDataError(DataError):
    """Invalid data format or content."""
    error_code = "INVALID_DATA"
    status_code = 400


class DataValidationError(DataError):
    """Data validation failed."""
    error_code = "VALIDATION_ERROR"
    status_code = 400


class DataPersistanceError(DataError):
    """Error saving or loading data from storage."""
    error_code = "DATA_PERSISTANCE_ERROR"
    status_code = 500


# ============= Service Errors =============

class ServiceError(StockHistoryError):
    """Base class for service layer errors."""
    error_code = "SERVICE_ERROR"
    status_code = 500


class ServiceUnavailableError(ServiceError):
    """External service or dependency unavailable."""
    error_code = "SERVICE_UNAVAILABLE"
    status_code = 503


class ExternalApiError(ServiceError):
    """Error calling external API."""
    error_code = "EXTERNAL_API_ERROR"
    status_code = 502


class RateLimitExceededError(ServiceError):
    """Rate limit exceeded for external service."""
    error_code = "RATE_LIMIT_EXCEEDED"
    status_code = 429


# ============= Cache Errors =============

class CacheError(StockHistoryError):
    """Base class for cache-related errors."""
    error_code = "CACHE_ERROR"
    status_code = 500


class CacheConnectionError(CacheError):
    """Cache connection failed."""
    error_code = "CACHE_CONNECTION_ERROR"
    status_code = 503


# ============= Business Logic Errors =============

class BusinessLogicError(StockHistoryError):
    """Base class for business rule violations."""
    error_code = "BUSINESS_ERROR"
    status_code = 400


class InvalidOperationError(BusinessLogicError):
    """Invalid operation requested."""
    error_code = "INVALID_OPERATION"
    status_code = 400


# ============= Infrastructure Errors =============

class InfrastructureError(StockHistoryError):
    """Base class for infrastructure errors."""
    error_code = "INFRASTRUCTURE_ERROR"
    status_code = 500


class DatabaseError(InfrastructureError):
    """Database operation error."""
    error_code = "DATABASE_ERROR"
    status_code = 500


class NetworkError(InfrastructureError):
    """Network communication error."""
    error_code = "NETWORK_ERROR"
    status_code = 503