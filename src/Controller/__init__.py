"""
Controller 模組
負責協調 View 與 Model 之間的互動
"""

from .Controller import (
    IController,
    TController,
    controllers,
    GetControllerEvent,
    MAIN_TITALLIST,
    PICK__TITALLIST,
)

from .ControllerFactory import Controller_Factory
from .MediatorController import IMediator_Controller, Mediator_Controller

__all__ = [
    "IController",
    "TController", 
    "controllers",
    "GetControllerEvent",
    "MAIN_TITALLIST",
    "PICK__TITALLIST",
    "Controller_Factory",
    "IMediator_Controller",
    "Mediator_Controller",
]