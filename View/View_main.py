from View.View import TWindow 
from PyQt5 import QtWidgets
from UI_main import Ui_MainWindow

class Main_Window(TWindow):
    def __init__(self, Ui_Window:Ui_MainWindow):
        super().__init__()
        self.FormUI = Ui_Window
    def GetFormUI(self) -> Ui_MainWindow:
        return self.FormUI
    
#主畫面
class MyWindow(QtWidgets.QMainWindow,Ui_MainWindow):
    def __init__(self):
        super(MyWindow,self).__init__()
        self.setupUi(self) 