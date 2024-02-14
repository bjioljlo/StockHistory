from View.View import TWindow 
from PyQt5 import QtWidgets
from UI_backtest import Ui_MainWindow3
from IParameter import RecordBackTestParameter
import tools

class BackTest_Window(TWindow):
    def __init__(self, Ui_Window:Ui_MainWindow3):
        super().__init__()
        self.FormUI = Ui_Window
    def GetFormUI(self) -> Ui_MainWindow3:
        return self.FormUI
    
    @property
    def Parament(self):
        self._Parament = BackTestParameter(self)
        return self._Parament

class BackTestParameter(RecordBackTestParameter):
    def __init__(self, _view: BackTest_Window) -> None:
        super().__init__()
        try:
            UI_form = _view.GetFormUI()
            self.check_monthRP_pick = bool(UI_form.check_monthRP_pick.isChecked())
            self.check_PER_pick:bool = bool(UI_form.check_PER_pick.isChecked())
            self.check_volume_pick:bool = bool(UI_form.check_volume_pick.isChecked())
            self.check_pickOneStock:bool = bool(UI_form.check_pickOneStock.isChecked())
            self.check_price_pick:bool = bool(UI_form.check_price_pick.isChecked())
            self.check_PBR_pick:bool = bool(UI_form.check_PBR_pick.isChecked())
            self.check_ROE_pick:bool = bool(UI_form.check_ROE_pick.isChecked())
            self.date_start = tools.QtDate2DateTime(UI_form.date_start.date())
            self.date_end = tools.QtDate2DateTime(UI_form.date_end.date())
            self.money_start = int(UI_form.input_startMoney.toPlainText())
            self.change_days = int(UI_form.input_changeDays.toPlainText())
            self.smoothAVG = int(UI_form.input_monthRP_smoothAVG.toPlainText())
            self.upMonth = int(UI_form.input_monthRP_UpMpnth.toPlainText())
            self.PER_start = float(UI_form.input_PER_start.toPlainText())
            self.PER_end = float(UI_form.input_PER_end.toPlainText())
            self.volumeAVG = int(UI_form.input_volume_money.toPlainText())
            self.volumeDays = int(UI_form.input_volumeAVG_days.toPlainText())
            self.price_high = int(UI_form.input_price_high.toPlainText())
            self.price_low = int(UI_form.input_price_low.toPlainText())
            self.PBR_end = float(UI_form.input_PBR_end.toPlainText())
            self.PBR_start = float(UI_form.input_PBR_start.toPlainText())
            self.ROE_end = float(UI_form.input_ROE_end.toPlainText())
            self.ROE_start = float(UI_form.input_ROE_start.toPlainText())
            self.Pick_amount = int(UI_form.input_StockAmount.toPlainText())
            self.buy_number = str(UI_form.input_stockNumber.toPlainText())
            self.Dividend_yield_high = float(UI_form.input_yield_start.toPlainText())
            self.Dividend_yield_low = float(UI_form.input_yield_end.toPlainText())
            self.buy_day = int(UI_form.input_buyDay.toPlainText())
            self.Record_high_day = int(UI_form.input_RecordHigh.toPlainText())  
        except ValueError as e:
            print("ValueError:", e)

#回測畫面
class MyBacktestWindow(QtWidgets.QMainWindow,Ui_MainWindow3):
    def __init__(self):
        super(MyBacktestWindow,self).__init__()
        self.setupUi(self)