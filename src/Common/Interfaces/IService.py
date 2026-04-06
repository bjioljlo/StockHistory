"""
Common Service Interface Base

Defines standard interface for all services in the system.
Part of Task 4.5: Service interfaces and dependency injection.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class IService(ABC):
    """Base interface for all services"""
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize service resources"""
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Cleanup service resources"""
        pass
    
    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if service is properly initialized"""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get service status information"""
        pass