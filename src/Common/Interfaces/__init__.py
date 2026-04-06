"""
Service Interfaces Package

All service interfaces defined here:
- IService: Base service interface
- IUpdateService: Stock update service interface
- IBackTestService: Backtesting service interface  
- IFilterService: Stock filtering service interface
- IGetExternalData: External data service interface

Part of Task 4.5: Service interfaces and dependency injection.
"""

from .IService import IService
from .IUpdateService import IUpdateService
from .IBackTestService import IBackTestService
from .IFilterService import IFilterService

__all__ = [
    'IService',
    'IUpdateService', 
    'IBackTestService',
    'IFilterService',
]