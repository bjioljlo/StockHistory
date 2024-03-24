from View.View import TWindow 
from PyQt5 import QtWidgets
from UI.UI_main import Ui_MainWindow
from IParameter import RecordMainParameter
import tools



class Main_Window(TWindow):
    def __init__(self, Ui_Window:Ui_MainWindow):
        super().__init__()
        self.FormUI = Ui_Window

    def GetFormUI(self) -> Ui_MainWindow:
        return self.FormUI
    
    @property
    def Parament(self):
        self._Parament = MainParameter(self)
        return self._Parament

class MainParameter(RecordMainParameter):
    def __init__(self, _view: Main_Window):
        super().__init__()
        try:
            self.number = int(_view.GetFormUI().input_stockNumber.toPlainText())
            self.startdate = tools.QtDate2DateTime(_view.GetFormUI().date_startDate.date())
            self.enddate = tools.QtDate2DateTime(_view.GetFormUI().date_endDate.date())
        except ValueError as e:
            print("ValueError:", e)

#主畫面
class MyWindow(QtWidgets.QMainWindow,Ui_MainWindow):
    def __init__(self):
        super(MyWindow,self).__init__()
        self.setupUi(self) 