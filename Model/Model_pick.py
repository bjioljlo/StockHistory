from Controller.Controller import IController
from Model.Model import TModel

class Model_pick(TModel):
    def __init__(self,_interactiveController: IController):
        super().__init__()
        self._InteractiveController = _interactiveController

    @property
    def InteractiveController(self):
        if self._InteractiveController == None:
            raise
        return self._InteractiveController
    @InteractiveController.setter
    def InteractiveController(self,_interactiveController:IController):
        self._InteractiveController = _interactiveController

    def GetInteractiveController(self) -> IController:
        return self.InteractiveController