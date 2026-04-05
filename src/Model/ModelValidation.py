"""
Model Validation Service

Standard validation mechanisms for all Model classes
"""
from functools import wraps
from typing import Any, Callable, Optional, Dict
import logging


logger = logging.getLogger(__name__)


class ModelValidationError(ValueError):
    """Exception raised for model validation errors"""
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        self.field = field
        self.value = value
        super().__init__(message)


def validate_parameters(validator_func: Callable[[Any], bool]) -> Callable:
    """
    Decorator to validate parameters before executing a model method.

    Args:
        validator_func: Function that validates parameters and returns bool

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self: Any, parameters: Any, *args: Any, **kwargs: Any) -> Any:
            try:
                is_valid = validator_func(parameters)
                if not is_valid:
                    raise ModelValidationError(f"Parameter validation failed for {func.__name__}")
                return func(self, parameters, *args, **kwargs)
            except ModelValidationError:
                raise
            except Exception as e:
                logger.error(f"Validation error in {func.__name__}: {e}")
                raise ModelValidationError(f"Invalid parameters: {str(e)}") from e
        return wrapper
    return decorator


class ModelValidator:
    """
    Standard validator utilities for Model layer
    """

    @staticmethod
    def required(value: Any, field_name: str) -> None:
        """
        Validate that a value is not None or empty

        Args:
            value: Value to check
            field_name: Name of field for error message

        Raises:
            ModelValidationError: If value is None or empty
        """
        if value is None:
            raise ModelValidationError(f"{field_name} is required", field_name, value)

        if isinstance(value, str) and value.strip() == "":
            raise ModelValidationError(f"{field_name} cannot be empty", field_name, value)

    @staticmethod
    def numeric_range(value: float, field_name: str, min_val: Optional[float] = None,
                      max_val: Optional[float] = None) -> None:
        """
        Validate numeric value is within range

        Args:
            value: Numeric value to check
            field_name: Name of field for error message
            min_val: Minimum allowed value (inclusive)
            max_val: Maximum allowed value (inclusive)

        Raises:
            ModelValidationError: If value is outside range
        """
        if min_val is not None and value < min_val:
            raise ModelValidationError(
                f"{field_name} must be >= {min_val}, got {value}",
                field_name,
                value
            )

        if max_val is not None and value > max_val:
            raise ModelValidationError(
                f"{field_name} must be <= {max_val}, got {value}",
                field_name,
                value
            )

    @staticmethod
    def integer(value: Any, field_name: str) -> int:
        """
        Validate and convert value to integer

        Args:
            value: Value to convert
            field_name: Name of field for error message

        Returns:
            Converted integer value

        Raises:
            ModelValidationError: If value cannot be converted to integer
        """
        try:
            return int(value)
        except (ValueError, TypeError) as e:
            raise ModelValidationError(
                f"{field_name} must be an integer, got {type(value).__name__}",
                field_name,
                value
            ) from e

    @staticmethod
    def float(value: Any, field_name: str) -> float:
        """
        Validate and convert value to float

        Args:
            value: Value to convert
            field_name: Name of field for error message

        Returns:
            Converted float value

        Raises:
            ModelValidationError: If value cannot be converted to float
        """
        try:
            return float(value)
        except (ValueError, TypeError) as e:
            raise ModelValidationError(
                f"{field_name} must be a number, got {type(value).__name__}",
                field_name,
                value
            ) from e

    @staticmethod
    def positive(value: float, field_name: str) -> None:
        """
        Validate value is positive

        Args:
            value: Numeric value to check
            field_name: Name of field for error message

        Raises:
            ModelValidationError: If value is <= 0
        """
        if value <= 0:
            raise ModelValidationError(
                f"{field_name} must be positive, got {value}",
                field_name,
                value
            )

    @staticmethod
    def non_negative(value: float, field_name: str) -> None:
        """
        Validate value is non-negative

        Args:
            value: Numeric value to check
            field_name: Name of field for error message

        Raises:
            ModelValidationError: If value is < 0
        """
        if value < 0:
            raise ModelValidationError(
                f"{field_name} must be non-negative, got {value}",
                field_name,
                value
            )