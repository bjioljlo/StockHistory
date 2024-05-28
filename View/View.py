from PyQt5 import QtWidgets
from abc import ABC, abstractmethod
import Parameter

class IWindow(ABC):
    @abstractmethod
    def GetFormUI()-> QtWidgets.QMainWindow:
        pass

class TWindow(IWindow):
    def __init__(self):
        super(TWindow,self).__init__()
        self._Parament = None

    @property
    def Parament(self):
        self._Parament = Parameter(self)
        return self._Parament

    @abstractmethod
    def GetFormUI()-> QtWidgets.QMainWindow:
        pass