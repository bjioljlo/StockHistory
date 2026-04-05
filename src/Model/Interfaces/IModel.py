"""
Standard Model Interface

All Model classes MUST implement this interface
"""
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict


class IModel(ABC):
    """
    Standard interface for all Model classes in the system.
    All Model implementations MUST inherit from this interface and implement all methods.
    """

    @abstractmethod
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the model with required dependencies.
        All dependencies should be injected through constructor.
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        Get the human-readable name of this model.

        Returns:
            String identifier for this model
        """
        pass

    @abstractmethod
    def validate_parameters(self, parameters: Any) -> bool:
        """
        Validate input parameters before executing operations.

        Args:
            parameters: Input parameters object to validate

        Returns:
            True if parameters are valid, False otherwise

        Raises:
            ValueError: If parameters are invalid with detailed message
        """
        pass

    @abstractmethod
    def execute(self, parameters: Any) -> Any:
        """
        Execute the main operation of this model.

        Args:
            parameters: Validated input parameters

        Returns:
            Operation result
        """
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status and metrics of this model.

        Returns:
            Dictionary containing status information, metrics, and statistics
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """
        Reset model state to initial conditions.
        Clear any cached data or temporary state.
        """
        pass