"""
Base Model Class

All concrete Model classes inherit from this base class
"""
from abc import ABC
from typing import Any, Dict
from .Interfaces.IModel import IModel


class TModel(IModel, ABC):
    """
    Abstract base class for all Model implementations.
    Implements common functionality for all Models.
    """

    def __init__(self) -> None:
        super().__init__()
        self._name = "BaseModel"

    def get_name(self) -> str:
        """Get model name"""
        return self._name

    def validate_parameters(self, parameters: Any) -> bool:
        """
        Default parameter validation.
        Override this method in concrete classes.

        Args:
            parameters: Parameters to validate

        Returns:
            True by default
        """
        return True

    def execute(self, parameters: Any) -> Any:
        """
        Default execute method.
        Override this method in concrete classes.

        Args:
            parameters: Execution parameters

        Returns:
            None by default
        """
        return None

    def get_status(self) -> Dict[str, Any]:
        """
        Get model status.
        Override this method in concrete classes.

        Returns:
            Empty dictionary by default
        """
        return {}

    def reset(self) -> None:
        """
        Default reset method.
        Override this method in concrete classes.
        """
        pass

    def GetInteractiveController(self):
        """
        Legacy method for backward compatibility.
        Deprecated - will be removed in future versions.
        """
        pass
