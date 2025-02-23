from abc import ABC, abstractmethod
from .Controller import IController, controllers
from .ControllerFactory import Controller_Factory
from datetime import datetime
from View.View_main import Main_Window, MyWindow
from View.View_pick import Pick_Window, MyPickWindow
from View.View_backtest import BackTest_Window, MyBacktestWindow

from Model.Model_main import Model_main
from Model.Model_pick import Model_pick
from Model.Model_backtest import Model_backtest


class IMediator_Controller(ABC):
    @abstractmethod
    def ShowWindow(self, reciver: controllers):
        raise NotImplementedError

    @abstractmethod
    def GetEndDate(self, reciver: controllers) -> datetime:
        raise NotImplementedError

    @abstractmethod
    def GetStockNumber(self, reciver: controllers) -> str:
        raise NotImplementedError

    @abstractmethod
    def SetStockNumber(self, reciver: controllers, stockNumber: str):
        raise NotImplementedError

    @abstractmethod
    def GetController(self, reciver: controllers) -> IController:
        raise NotImplementedError


class Mediator_Controller(IMediator_Controller):
    """controller的中介者"""

    def __init__(self, Schedule) -> None:
        self._main_controller: IController = Controller_Factory(
            controllers.Main,
            Main_Window(MyWindow()),
            Model_main(Schedule),
            self.GetController,
        )
        self._pick_controller: IController = Controller_Factory(
            controllers.Pick,
            Pick_Window(MyPickWindow()),
            Model_pick(),
            self.GetController,
        )
        self._backtest_controller: IController = Controller_Factory(
            controllers.BackTest,
            BackTest_Window(MyBacktestWindow()),
            Model_backtest(),
            self.GetController,
        )

    def GetController(self, reciver: controllers) -> IController:
        if reciver == controllers.Main:
            return self._main_controller
        elif reciver == controllers.Pick:
            return self._pick_controller
        elif reciver == controllers.BackTest:
            return self._backtest_controller
        else:
            print("reciver 錯誤!!")

    def ShowWindow(self, reciver: controllers):
        if reciver == controllers.Main:
            self._main_controller.ShowWindow()
        elif reciver == controllers.Pick:
            self._pick_controller.ShowWindow()
        elif reciver == controllers.BackTest:
            self._backtest_controller.ShowWindow()
        else:
            print("reciver 錯誤!!")

    def GetEndDate(self, reciver: controllers) -> datetime:
        if reciver == controllers.Main:
            return self._main_controller.GetEndDate()
        elif reciver == controllers.Pick:
            return self._pick_controller.GetEndDate()
        elif reciver == controllers.BackTest:
            return self._backtest_controller.GetEndDate()
        else:
            print("reciver 錯誤!!")

    def GetStockNumber(self, reciver: controllers) -> str:
        if reciver == controllers.Main:
            return self._main_controller.GetStockNumber()
        elif reciver == controllers.Pick:
            return self._pick_controller.GetStockNumber()
        elif reciver == controllers.BackTest:
            return self._backtest_controller.GetStockNumber()
        else:
            print("reciver 錯誤!!")

    def SetStockNumber(self, reciver: controllers, stockNumber: str):
        if reciver == controllers.Main:
            return self._main_controller.SetStockNumber(stockNumber)
        elif reciver == controllers.Pick:
            return self._pick_controller.SetStockNumber(stockNumber)
        elif reciver == controllers.BackTest:
            return self._backtest_controller.SetStockNumber(stockNumber)
        else:
            print("reciver 錯誤!!")
