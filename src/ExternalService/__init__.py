"""
ExternalService Package

Refactored into modular components:
- TGetExternalData: Main service facade (backwards compatible)
- IGetExternalData: Service interface definition
- ExternalDataFactory: Service factory

Refactored at 2026-04-06 as part of project-refactoring-and-cleanup
"""

from .IGetExternalData import IGetExternalData
from .TGetExternalData import TGetExternalData
from .ExternalDataFactory import ExternalDataFactory, ExternalDataTypeEnum

__all__ = [
    'IGetExternalData',
    'TGetExternalData',
    'ExternalDataFactory',
    'ExternalDataTypeEnum',
]
