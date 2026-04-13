from src.FilterService.StockReportHistory import SeasonReportFactory
from src.Model.Model import IModel
from src.View.View import IWindow

from .Controller import GetControllerEvent, IController, controllers
from .Controller_backTest import Controller_backTest
from .Controller_main import Controller_main
from .Controller_pick import Controller_pick


@staticmethod
def Controller_Factory(
    windowType: controllers, _view: IWindow, _model: IModel, _event: GetControllerEvent, draw_figur_service=None, report_factory: SeasonReportFactory = None
) -> IController:
    controller = None
    match windowType:
        case controllers.Main:
            controller = Controller_main(
                draw_figur_service=draw_figur_service,
                report_factory=report_factory,
                _view=_view,
                _model=_model
            )
        case controllers.Pick:
            controller = Controller_pick(_view, _model)
        case controllers.BackTest:
            controller = Controller_backTest(_view, _model)
        case _:
            return None
    controller.GetController = _event
    return controller
