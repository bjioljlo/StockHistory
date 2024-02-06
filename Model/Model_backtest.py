from Model.Model import TModel

class Model_backtest(TModel):
    def __init__(self):
        super().__init__()
    
    def GetInteractiveController(self):
        return super().GetInteractiveController()