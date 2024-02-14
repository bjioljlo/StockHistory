from Controller.Controller import IController
from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime

class controllers(Enum):
    Main = 1
    Pick = 2
    BackTest = 3

class IMediator_Controller(ABC):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def ShowWindow(self, sender: IController , reciver: controllers):
        pass
    
    @abstractmethod
    def GetEndDate(self, sender: IController , reciver: controllers) -> datetime:
        pass

    @abstractmethod
    def GetStockNumber(self, sender: IController , reciver: controllers) -> str:
        pass

    @abstractmethod
    def SetStockNumber(self, sender: IController , reciver: controllers, stockNumber:str):
        pass

class Mediator_Controller(IMediator_Controller):
    def __init__(self) -> None:
        self._main_controller:IController = None
        self._pick_controller:IController = None
        self._backtest_controller:IController = None

    def CheckControllerIsSelf(self, sender: IController , reciver: controllers) -> bool:
        _controller = None
        if reciver == controllers.Main:
            _controller = self._main_controller
        elif reciver == controllers.Pick:
            _controller = self._pick_controller
        elif reciver == controllers.BackTest:
            _controller = self._backtest_controller
        else:
            print("reciver 錯誤!!")

        if sender == _controller:
            return True
        else:
            return False

    def ShowWindow(self, sender: IController , reciver: controllers):
        if reciver == controllers.Main:
            self._main_controller.ShowWindow()
        elif reciver == controllers.Pick:
            self._pick_controller.ShowWindow()
        elif reciver == controllers.BackTest:
            self._backtest_controller.ShowWindow()
        else:
            print("reciver 錯誤!!")

    def GetEndDate(self, sender: IController , reciver: controllers) -> datetime:
        if reciver == controllers.Main:
            return self._main_controller.GetEndDate()
        elif reciver == controllers.Pick:
            return self._pick_controller.GetEndDate()
        elif reciver == controllers.BackTest:
            return self._backtest_controller.GetEndDate()
        else:
            print("reciver 錯誤!!")

    def GetStockNumber(self, sender: IController , reciver: controllers) -> str:
        if reciver == controllers.Main:
            return self._main_controller.GetStockNumber()
        elif reciver == controllers.Pick:
            return self._pick_controller.GetStockNumber()
        elif reciver == controllers.BackTest:
            return self._backtest_controller.GetStockNumber()
        else:
            print("reciver 錯誤!!")

    def SetStockNumber(self, sender: IController , reciver: controllers, stockNumber:str):
        if reciver == controllers.Main:
            return self._main_controller.SetStockNumber(stockNumber)
        elif reciver == controllers.Pick:
            return self._pick_controller.SetStockNumber(stockNumber)
        elif reciver == controllers.BackTest:
            return self._backtest_controller.SetStockNumber(stockNumber)
        else:
            print("reciver 錯誤!!")
    
    