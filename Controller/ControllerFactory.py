from View.View import IWindow
from Model.Model import IModel
from .Controller_pick import Controller_pick
from .Controller_main import Controller_main
from .Controller_backTest import Controller_backTest
from .Controller import IController, controllers, GetControllerEvent

@staticmethod
def Controller_Factory(windowType: controllers, _view: IWindow, _model: IModel, _event: GetControllerEvent) -> IController:
    controller = None
    match windowType:
        case controllers.Main:
            controller = Controller_main(_view, _model)
        case controllers.Pick:
            controller = Controller_pick(_view, _model)        
        case controllers.BackTest:
            controller = Controller_backTest(_view, _model)        
        case _:
            return None
    controller.GetController = _event
    return controller