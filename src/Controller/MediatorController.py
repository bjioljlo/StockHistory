from abc import ABC, abstractmethod

from src.ExternalService.ExternalDataFactory import ExternalDataFactory
from src.FilterService.StockReportHistory import SeasonReportFactory
from src.Model.Model_backtest import Model_backtest
from src.Model.Model_main import Model_main
from src.Model.Pick import PickModel
from src.ScheduleService import ScheduleService
from src.SqlService import SqlService
from src.Common.ConcurrentUtils import ConcurrentUtils
from src.View.View_backtest import BackTest_Window, MyBacktestWindow
from src.View.View_main import Main_Window, MyWindow
from src.View.View_pick import MyPickWindow, Pick_Window

from .Controller import IController, controllers
from .ControllerFactory import Controller_Factory
from src.DrawFigur import DrawFigur
from src.MongoService import MongoService


class IMediator_Controller(ABC):
    @abstractmethod
    def get_controller(self, receiver: controllers) -> IController:
        """取得指定類型的 Controller 實例"""
        raise NotImplementedError
    
    @abstractmethod
    def send_message(self, receiver: controllers, message_type: str, **kwargs):
        """傳送訊息給指定 Controller"""
        raise NotImplementedError
    
    @abstractmethod
    def broadcast_message(self, message_type: str, **kwargs):
        """廣播訊息給所有 Controller"""
        raise NotImplementedError


class Mediator_Controller(IMediator_Controller):
    """controller的中介者"""

    def __init__(
        self,
        schedule: ScheduleService,
        sql_service: SqlService,
        mongo_service: MongoService,
        draw_figur_service: DrawFigur,
        concurrent_utils: ConcurrentUtils,
        report_factory: SeasonReportFactory,
        external_data_factory: ExternalDataFactory
    ) -> None:
        # 1. 將接收到的服務儲存為實例變數
        self._schedule = schedule
        self._sql_service = sql_service
        self._mongo_service = mongo_service
        self._draw_figur_service = draw_figur_service
        self._concurrent_utils = concurrent_utils
        self._report_factory = report_factory
        self._external_data_factory = external_data_factory

        # 2. 建立 Controller 時，將依賴傳遞給 Model
        self._main_controller: IController = Controller_Factory(
            controllers.Main,
            Main_Window(MyWindow(self._schedule.StopThreadSchedule)),
            Model_main(schedule=self._schedule, draw_figur_service=self._draw_figur_service, 
                        external_data_service=self._external_data_factory.Get_instance(), report_factory=self._report_factory),
            self.get_controller,
            self._draw_figur_service,
            report_factory=self._report_factory
        )
        self._pick_controller: IController = Controller_Factory(
            controllers.Pick,
            Pick_Window(MyPickWindow()),
            # 將需要的服務傳給 PickModel
            PickModel(external_data_factory= self._external_data_factory),
            self.get_controller,
        )
        self._backtest_controller: IController = Controller_Factory(
            controllers.BackTest,
            BackTest_Window(MyBacktestWindow()),
            # 將需要的服務傳給 Model_backtest
            Model_backtest(sql_service=self._sql_service, draw_figur_service=self._draw_figur_service,
                        concurrent_utils=self._concurrent_utils, external_data_factory=self._external_data_factory),
            self.get_controller,
        )

    def get_controller(self, receiver: controllers) -> IController:
        """取得指定類型的 Controller 實例"""
        controller_map = {
            controllers.Main: self._main_controller,
            controllers.Pick: self._pick_controller,
            controllers.BackTest: self._backtest_controller
        }
        
        if receiver not in controller_map:
            raise ValueError(f"Invalid controller type: {receiver}")
        
        return controller_map[receiver]
    
    
    def send_message(self, receiver: controllers, message_type: str, **kwargs):
        """
        傳送訊息給指定 Controller
        標準化 Controller 間通訊機制
        """
        controller = self.get_controller(receiver)
        if hasattr(controller, 'handle_message'):
            return controller.handle_message(message_type, **kwargs)
        return None
    
    def broadcast_message(self, message_type: str, **kwargs):
        """廣播訊息給所有註冊的 Controller"""
        results = {}
        for controller_type in controllers:
            controller = self.get_controller(controller_type)
            if hasattr(controller, 'handle_message'):
                results[controller_type] = controller.handle_message(message_type, **kwargs)
        return results
