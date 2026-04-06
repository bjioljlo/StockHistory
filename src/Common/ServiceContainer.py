"""
Dependency Injection Service Container

Part of Task 4.5: Service interfaces and dependency injection.

Provides service registration, resolution, and lifetime management.
"""
from typing import Dict, Type, Any, Optional, Callable
import logging

from src.Common.Interfaces.IService import IService


class ServiceContainer:
    """
    Simple dependency injection container for service management
    
    Supports:
    - Singleton services
    - Transient services
    - Factory function registration
    - Interface to implementation mapping
    """
    
    _instance: Optional['ServiceContainer'] = None
    _services: Dict[Type, Any] = {}
    _factories: Dict[Type, Callable] = {}
    _singletons: Dict[Type, Any] = {}
    
    def __new__(cls) -> 'ServiceContainer':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._logger = logging.getLogger(__name__)
        return cls._instance
    
    def register(self, interface_type: Type, implementation: Any) -> None:
        """Register a singleton service instance"""
        self._services[interface_type] = implementation
        self._logger.debug(f"Registered service: {interface_type.__name__}")
    
    def register_factory(self, interface_type: Type, factory: Callable) -> None:
        """Register a factory function for transient services"""
        self._factories[interface_type] = factory
        self._logger.debug(f"Registered factory: {interface_type.__name__}")
    
    def register_singleton(self, interface_type: Type, factory: Callable) -> None:
        """Register a singleton service with factory function"""
        self._singletons[interface_type] = None
        self._factories[interface_type] = factory
        self._logger.debug(f"Registered singleton factory: {interface_type.__name__}")
    
    def resolve(self, interface_type: Type) -> Any:
        """Resolve a service instance"""
        # Check for already instantiated singleton
        if interface_type in self._singletons and self._singletons[interface_type] is not None:
            return self._singletons[interface_type]
        
        # Check for registered instance
        if interface_type in self._services:
            return self._services[interface_type]
        
        # Check for factory
        if interface_type in self._factories:
            instance = self._factories[interface_type]()
            
            # If it's a singleton, cache it
            if interface_type in self._singletons:
                self._singletons[interface_type] = instance
                self._logger.debug(f"Created singleton instance: {interface_type.__name__}")
            
            return instance
        
        raise ValueError(f"Service not registered: {interface_type.__name__}")
    
    def is_registered(self, interface_type: Type) -> bool:
        """Check if a service is registered"""
        return (
            interface_type in self._services 
            or interface_type in self._factories
            or (interface_type in self._singletons and self._singletons[interface_type] is not None)
        )
    
    def clear(self) -> None:
        """Clear all registered services"""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
        self._logger.debug("Service container cleared")