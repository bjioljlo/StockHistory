from View.View import TWindow 
from PyQt5 import QtWidgets
from UI_pick import Ui_MainWindow2

class Pick_Window(TWindow):
    def __init__(self, Ui_Window:Ui_MainWindow2):
        super().__init__()
        self.FormUI = Ui_Window
    def GetFormUI(self) -> Ui_MainWindow2:
        return self.FormUI
    
#挑股票畫面
class MyPickWindow(QtWidgets.QMainWindow,Ui_MainWindow2):
    def __init__(self):
        super(MyPickWindow,self).__init__()
        self.setupUi(self)