from abc import ABC, abstractmethod

class IModel(ABC):
    @abstractmethod
    def GetInteractiveController(self): 
        pass

class TModel(IModel):
    def __init__(self):
        super(TModel,self).__init__()

    @abstractmethod
    def GetInteractiveController(self):
        pass
    