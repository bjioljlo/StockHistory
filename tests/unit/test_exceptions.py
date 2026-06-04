"""
Unit tests for Exceptions module.
"""

import pytest
from pyutils_core.exceptions import (
    StockHistoryError,
    ConfigurationError,
    ConfigNotFoundError,
    InvalidConfigError,
    DataError,
    DataNotFoundError,
    InvalidDataError,
    DataValidationError,
    DataPersistanceError,
    ServiceError,
    ServiceUnavailableError,
    ExternalApiError,
    RateLimitExceededError,
    CacheError,
    CacheConnectionError,
    BusinessLogicError,
    InvalidOperationError,
    InfrastructureError,
    DatabaseError,
    NetworkError,
)


class TestExceptions:
    """Test exception classes hierarchy and functionality."""
    
    def test_base_exception_attributes(self):
        """Test base StockHistoryError attributes."""
        error = StockHistoryError("Test message", details={"key": "value"})
        
        assert error.message == "Test message"
        assert error.details == {"key": "value"}
        assert error.error_code == "SYSTEM_ERROR"
        assert error.status_code == 500
    
    def test_exception_to_dict(self):
        """Test to_dict() serialization."""
        error = StockHistoryError(
            "Test message",
            details={"key": "value", "count": 42}
        )
        
        result = error.to_dict()
        
        assert result["error_code"] == "SYSTEM_ERROR"
        assert result["message"] == "Test message"
        assert result["details"] == {"key": "value", "count": 42}
        assert result["status_code"] == 500
    
    def test_exception_string_representation(self):
        """Test string formatting."""
        error = InvalidConfigError("Invalid port value", details={"port": 99999})
        str_repr = str(error)
        
        assert "[INVALID_CONFIG]" in str_repr
        assert "Invalid port value" in str_repr
        assert "port" in str_repr
    
    def test_configuration_hierarchy(self):
        """Test ConfigurationError hierarchy."""
        assert issubclass(ConfigNotFoundError, ConfigurationError)
        assert issubclass(InvalidConfigError, ConfigurationError)
        
        assert ConfigNotFoundError.error_code == "CONFIG_NOT_FOUND"
        assert InvalidConfigError.error_code == "INVALID_CONFIG"
    
    def test_data_hierarchy(self):
        """Test DataError hierarchy."""
        assert issubclass(DataNotFoundError, DataError)
        assert issubclass(InvalidDataError, DataError)
        assert issubclass(DataValidationError, DataError)
        assert issubclass(DataPersistanceError, DataError)
    
    def test_service_hierarchy(self):
        """Test ServiceError hierarchy."""
        assert issubclass(ServiceUnavailableError, ServiceError)
        assert issubclass(ExternalApiError, ServiceError)
        assert issubclass(RateLimitExceededError, ServiceError)
    
    def test_cache_hierarchy(self):
        """Test CacheError hierarchy."""
        assert issubclass(CacheConnectionError, CacheError)
    
    def test_business_logic_hierarchy(self):
        """Test BusinessLogicError hierarchy."""
        assert issubclass(InvalidOperationError, BusinessLogicError)
    
    def test_infrastructure_hierarchy(self):
        """Test InfrastructureError hierarchy."""
        assert issubclass(DatabaseError, InfrastructureError)
        assert issubclass(NetworkError, InfrastructureError)
    
    def test_all_exceptions_inherit_from_base(self):
        """Test all exceptions inherit from StockHistoryError."""
        exception_classes = [
            ConfigurationError,
            DataError,
            ServiceError,
            CacheError,
            BusinessLogicError,
            InfrastructureError,
        ]
        
        for exc_class in exception_classes:
            assert issubclass(exc_class, StockHistoryError)
    
    def test_exception_with_cause(self):
        """Test exception with cause parameter."""
        cause = ValueError("Original error")
        error = DataPersistanceError("Save failed", cause=cause)
        
        assert error.cause is cause