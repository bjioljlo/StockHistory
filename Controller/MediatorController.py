from abc import ABC, abstractmethod
from datetime import datetime

from FilterService.GetStockData import ReportServices
from Model.Model_backtest import Model_backtest
from Model.Model_main import Model_main
from Model.Model_pick import Model_pick
from ReadLoadSystem import ReadLoadSystem
from ScheduleService import ScheduleService
from SqlService import SqlService
from ThreadPool import ThreadPool
from View.View_backtest import BackTest_Window, MyBacktestWindow
from View.View_main import Main_Window, MyWindow
from View.View_pick import MyPickWindow, Pick_Window

from .Controller import IController, controllers
from .ControllerFactory import Controller_Factory
from DrawFigur import DrawFigur
from MongoService import MongoService


class IMediator_Controller(ABC):
    @abstractmethod
    def GetController(self, reciver: controllers) -> IController:
        raise NotImplementedError


class Mediator_Controller(IMediator_Controller):
    """controller的中介者"""

    def __init__(
        self,
        schedule: ScheduleService,
        sql_service: SqlService,
        mongo_service: MongoService,
        draw_figur_service: DrawFigur,
        thread_pool: ThreadPool,
        read_load_system: ReadLoadSystem,
        report_services: ReportServices,
    ) -> None:
        # 1. 將接收到的服務儲存為實例變數
        self._schedule = schedule
        self._sql_service = sql_service
        self._mongo_service = mongo_service
        self._draw_figur_service = draw_figur_service
        self._thread_pool = thread_pool
        self._read_load_system = read_load_system
        self._report_services = report_services

        # 2. 建立 Controller 時，將依賴傳遞給 Model
        self._main_controller: IController = Controller_Factory(
            controllers.Main,
            Main_Window(MyWindow(self._schedule.StopThreadSchedule)),
            Model_main(schedule=self._schedule, draw_figur_service=self._draw_figur_service, 
                        external_data_service= self._read_load_system, report_services=self._report_services),
            self.GetController,
            self._draw_figur_service,
            report_services=self._report_services
        )
        self._pick_controller: IController = Controller_Factory(
            controllers.Pick,
            Pick_Window(MyPickWindow()),
            # 將需要的服務傳給 Model_pick
            Model_pick(sql_service=self._sql_service, mongo_service=self._mongo_service, external_data_service= self._read_load_system),
            self.GetController,
        )
        self._backtest_controller: IController = Controller_Factory(
            controllers.BackTest,
            BackTest_Window(MyBacktestWindow()),
            # 將需要的服務傳給 Model_backtest
            Model_backtest(sql_service=self._sql_service, mongo_service=self._mongo_service,
                        external_data_service= self._read_load_system, draw_figur_service=self._draw_figur_service, 
                        thread_pool=self._thread_pool),
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
