from View.View import TWindow 
from PyQt5 import QtWidgets
from UI.UI_pick import Ui_MainWindow2
from IParameter import IParameter

class Pick_Window(TWindow):
    def __init__(self, Ui_Window:Ui_MainWindow2):
        super().__init__()
        self.FormUI = Ui_Window

    def GetFormUI(self) -> Ui_MainWindow2:
        return self.FormUI
    
    @property
    def Parament(self):
        self._Parament = PickParameter(self)
        return self._Parament

class PickParameter(IParameter):
    def __init__(self, _view: Pick_Window):
        super().__init__()
        try:
            self.EPS = float(_view.GetFormUI().input_EPS.value())
            self.GPM = float(_view.GetFormUI().input_GPM.value())
            self.OPR = float(_view.GetFormUI().input_OPR.value())
            self.RPS = float(_view.GetFormUI().input_RPS.value())
            self.OMGR = int(_view.GetFormUI().input_OMGR.value())
            self.monthRP_UpMpnth = int(_view.GetFormUI().input_monthRP_UpMpnth.value()) 
            self.volum = int(_view.GetFormUI().input_volum.value())
            self.price_high = int(_view.GetFormUI().input_price_high.value())
            self.price_low = int(_view.GetFormUI().input_price_low.value())
            self.PBR_high = float(_view.GetFormUI().input_PBR_high.value())
            self.PBR_low = float(_view.GetFormUI().input_PBR_low.value())
            self.PER_high = float(_view.GetFormUI().input_PER_high.value())
            self.PER_low = float(_view.GetFormUI().input_PER_low.value())
            self.ROE_high = float(_view.GetFormUI().input_ROE_high.value())
            self.ROE_low = float(_view.GetFormUI().input_ROE_low.value())
            self.yiled_high = float(_view.GetFormUI().input_yiled_high.value())
            self.yiled_low = float(_view.GetFormUI().input_yiled_low.value())
            self.flash_Day = int(_view.GetFormUI().input_flash_Day.value())
            self.record_Day = int(_view.GetFormUI().input_record_Day.value())
            self.PEG_high = float(_view.GetFormUI().input_PEG_high.value())
            self.PEG_low = float(_view.GetFormUI().input_PEG_low.value())
            self.FCF = int(_view.GetFormUI().input_FCF.value())
            self.ROE = int(_view.GetFormUI().input_ROE.value())
            self.SRGR = int(_view.GetFormUI().input_SRGR.value())
            self.MRGR = int(_view.GetFormUI().input_MRGR.value())
            self.monthRP_smoothAVG = int(_view.GetFormUI().input_monthRP_smoothAVG.value())
            self.EPS_up = int(_view.GetFormUI().input_EPS_up.value())
            self.BetterMA = int(_view.GetFormUI().input_BetterMA.value())
        except ValueError as e:
            print("ValueError:", e)

#挑股票畫面
class MyPickWindow(QtWidgets.QMainWindow,Ui_MainWindow2):
    def __init__(self):
        super(MyPickWindow,self).__init__()
        self.setupUi(self)