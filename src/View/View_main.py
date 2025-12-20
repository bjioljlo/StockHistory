from PyQt5 import QtWidgets, uic

from src.Common import Tools
from src.Common.Parameter import RecordMainParameter
from src.View.View import TWindow


class Main_Window(TWindow):
    def __init__(self, Ui_Window: QtWidgets.QMainWindow):
        super().__init__()
        self.FormUI = Ui_Window

    def set_progress(self, value):
        if value >= 0 and self.FormUI.progressBar_UpdateStock.isHidden():
            self.FormUI.progressBar_UpdateStock.setVisible(True)

        self.FormUI.progressBar_UpdateStock.setValue(value)

    def GetFormUI(self) -> QtWidgets.QMainWindow:
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
class MyWindow(QtWidgets.QMainWindow):
    def __init__(self, _closeEvent):
        super(MyWindow, self).__init__()
        uic.loadUi('UI/UI_main.ui', self)
        self.closeFuction = _closeEvent

    def closeEvent(self, event):
        self.closeFuction()
