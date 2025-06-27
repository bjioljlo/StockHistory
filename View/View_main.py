from PyQt5 import QtWidgets

import Tools
from Parameter import RecordMainParameter
from UI.UI_main import Ui_MainWindow
from View.View import TWindow


class Main_Window(TWindow):
    def __init__(self, Ui_Window: Ui_MainWindow):
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
            self.startdate = Tools.QtDate2DateTime(
                _view.GetFormUI().date_startDate.date()
            )
            self.enddate = Tools.QtDate2DateTime(_view.GetFormUI().date_endDate.date())
        except ValueError as e:
            print("ValueError:", e)


# 主畫面
class MyWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, _closeEvent):
        super(MyWindow, self).__init__()
        self.setupUi(self)
        self.closeFuction = _closeEvent

    def closeEvent(self, event):
        self.closeFuction()
