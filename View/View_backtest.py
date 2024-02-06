from View.View import TWindow 
from PyQt5 import QtWidgets
from UI_backtest import Ui_MainWindow3

class BackTest_Window(TWindow):
    def __init__(self, Ui_Window:Ui_MainWindow3):
        super().__init__()
        self.FormUI = Ui_Window
    def GetFormUI(self) -> Ui_MainWindow3:
        return self.FormUI

#回測畫面
class MyBacktestWindow(QtWidgets.QMainWindow,Ui_MainWindow3):
    def __init__(self):
        super(MyBacktestWindow,self).__init__()
        self.setupUi(self)