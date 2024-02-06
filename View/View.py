from PyQt5 import QtWidgets
from abc import ABC, abstractmethod

class IWindow(ABC):
    @abstractmethod
    def GetFormUI()-> QtWidgets.QMainWindow:
        pass

class TWindow(IWindow):
    def __init__(self):
        super(TWindow,self).__init__()

    @abstractmethod
    def GetFormUI()-> QtWidgets.QMainWindow:
        pass
        