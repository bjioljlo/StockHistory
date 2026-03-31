from PyQt5 import QtWidgets, uic

from src.Common import Tools
from src.Common.Parameter import RecordMainParameter
from src.View.View import TWindow


class Main_Window(TWindow):
    def __init__(self, Ui_Window: QtWidgets.QMainWindow):
        super().__init__()
        self.FormUI = Ui_Window
        self._Parament = None  # 初始化參數對象

    def set_progress(self, value):
        if value >= 0 and self.FormUI.progressBar_UpdateStock.isHidden():
            self.FormUI.progressBar_UpdateStock.setVisible(True)

        self.FormUI.progressBar_UpdateStock.setValue(value)

    def GetFormUI(self) -> QtWidgets.QMainWindow:
        return self.FormUI

    @property
    def Parament(self):
        """獲取當前主畫面的參數，每次都會從 UI 重新讀取最新值"""
        try:
            # 每次訪問時都重新創建參數對象以獲取最新值
            self._Parament = MainParameter(self)
            return self._Parament
        except Exception as e:
            print(f"獲取參數時發生錯誤: {e}")
            # 返回一個空的參數對象，避免程式崩潰
            if self._Parament is None:
                self._Parament = RecordMainParameter()
            return self._Parament


class MainParameter(RecordMainParameter):
    def __init__(self, _view: Main_Window):
        super().__init__()
        try:
            # 獲取股票號碼
            stock_number_text = _view.GetFormUI().input_stockNumber.toPlainText().strip()
            if stock_number_text:
                try:
                    self.number = int(stock_number_text)
                except ValueError:
                    print(f"警告：股票號碼格式錯誤 '{stock_number_text}'，將使用 None")
                    self.number = None
            else:
                self.number = None
            
            # 獲取開始日期
            try:
                self.startdate = Tools.QtDate2DateTime(
                    _view.GetFormUI().date_startDate.date()
                )
            except Exception as e:
                print(f"警告：無法獲取開始日期: {e}")
                self.startdate = None
            
            # 獲取結束日期
            try:
                self.enddate = Tools.QtDate2DateTime(
                    _view.GetFormUI().date_endDate.date()
                )
            except Exception as e:
                print(f"警告：無法獲取結束日期: {e}")
                self.enddate = None
                
        except Exception as e:
            print(f"MainParameter 初始化時發生錯誤: {e}")
            # 確保即使發生錯誤，對象仍然可以被創建
            if not hasattr(self, 'number'):
                self.number = None
            if not hasattr(self, 'startdate'):
                self.startdate = None
            if not hasattr(self, 'enddate'):
                self.enddate = None


# 主畫面
class MyWindow(QtWidgets.QMainWindow):
    def __init__(self, _closeEvent):
        super(MyWindow, self).__init__()
        uic.loadUi('UI/UI_main.ui', self)
        self.closeFuction = _closeEvent

    def closeEvent(self, event):
        self.closeFuction()
