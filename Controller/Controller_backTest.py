from Model.Model import IModel
from View.View import IWindow
from View.View_backtest import BackTest_Window
from Controller.Controller import TController
from datetime import datetime
from PyQt5 import QtCore
import draw_figur as df
import backtest_stock
import tools

class Controller_backTest(TController):
    def __init__(self, _view: IWindow = None, _model: IModel = None) -> None:
        super().__init__(_view, _model)
        self.Init_Window()

    def __GetView(self) -> BackTest_Window:
        return self.View

    def Init_Window(self):
        UI_form = self.__GetView().GetFormUI()
        UI_form.button_backtest.clicked.connect(self.button_backtest_click)#設定button功能
        UI_form.button_backtest_2.clicked.connect(self.button_backtest_click2)
        UI_form.button_backtest_3.clicked.connect(self.button_backtest_click3)
        UI_form.button_backtest_4.clicked.connect(self.button_backtest_click4)
        UI_form.button_backtest_5.clicked.connect(self.button_backtest_click5)
        UI_form.button_backtest_6.clicked.connect(self.button_backtest_click6)
        date = QtCore.QDate(datetime.today().year,datetime.today().month,datetime.today().day) 

        UI_form.date_end.setMaximumDate(date)
        UI_form.date_end.setMinimumDate(QtCore.QDate(2013,1,1))
        date = date.addMonths(0)
        UI_form.date_end.setDate(date)

        UI_form.date_start.setMaximumDate(date)
        UI_form.date_start.setMinimumDate(QtCore.QDate(2013,1,1))
        date = date.addYears(-1)
        UI_form.date_start.setDate(date)

        UI_form.input_startMoney.setPlainText('100000')
        UI_form.input_changeDays.setPlainText('20')
        UI_form.input_monthRP_smoothAVG.setPlainText('0')
        UI_form.input_monthRP_UpMpnth.setPlainText('0')
        UI_form.input_PER_start.setPlainText('0')
        UI_form.input_PER_end.setPlainText('0')
        UI_form.input_volume_money.setPlainText('0')
        UI_form.input_volumeAVG_days.setPlainText('0')
        UI_form.input_price_high.setPlainText('0')
        UI_form.input_price_low.setPlainText("0")
        UI_form.input_PBR_start.setPlainText('0')
        UI_form.input_PBR_end.setPlainText('0')
        UI_form.input_ROE_start.setPlainText('0')
        UI_form.input_ROE_end.setPlainText('0')
        UI_form.input_StockAmount.setPlainText('0')
        UI_form.input_stockNumber.setPlainText('2330')
        UI_form.input_yield_start.setPlainText('0')
        UI_form.input_yield_end.setPlainText('0')
        UI_form.input_buyDay.setPlainText('15')
        UI_form.input_RecordHigh.setPlainText('60')

    #第3頁的UI
    def button_backtest_click(self):#月營收回測開始紐
        UI_form = self.__GetView().GetFormUI()
        if UI_form.check_monthRP_pick.isChecked() == UI_form.check_PER_pick.isChecked() == UI_form.check_volume_pick.isChecked() == False:
            print("都沒選是要回測個毛線！")
            return
        else:
            backtest_stock.set_check(self.__GetView().GetFormUI().check_monthRP_pick.isChecked(),
                UI_form.check_PER_pick.isChecked(),
                UI_form.check_volume_pick.isChecked(),
                UI_form.check_pickOneStock.isChecked(),
                UI_form.check_price_pick.isChecked(),
                UI_form.check_PBR_pick.isChecked(),
                UI_form.check_ROE_pick.isChecked())
        _data = backtest_stock.backtest_monthRP_Up_Fast(BackTestParameter(self.__GetView()))
        df.draw_backtest(_data)
    def button_backtest_click2(self):#PER PBR 回測開始紐
        UI_form = self.__GetView().GetFormUI()
        backtest_stock.set_check(UI_form.check_monthRP_pick.isChecked(),
                                    UI_form.check_PER_pick.isChecked(),
                                    UI_form.check_volume_pick.isChecked(),
                                    UI_form.check_pickOneStock.isChecked(),
                                    UI_form.check_price_pick.isChecked(),
                                    UI_form.check_PBR_pick.isChecked(),
                                    UI_form.check_ROE_pick.isChecked())
        _data = backtest_stock.backtest_PERandPBR_Fast(BackTestParameter(self.__GetView()))
        df.draw_backtest(_data)
    def button_backtest_click3(self):#定期定額
        _data = backtest_stock.backtest_Regular_quota_Fast(BackTestParameter(self.__GetView()))
        df.draw_backtest(_data)
    def button_backtest_click4(self):#創新高
        UI_form = self.__GetView().GetFormUI()
        backtest_stock.set_check(UI_form.check_monthRP_pick.isChecked(),
                                    UI_form.check_PER_pick.isChecked(),
                                    UI_form.check_volume_pick.isChecked(),
                                    UI_form.check_pickOneStock.isChecked(),
                                    UI_form.check_price_pick.isChecked(),
                                    UI_form.check_PBR_pick.isChecked(),
                                    UI_form.check_ROE_pick.isChecked())
        _data = backtest_stock.backtest_Record_high_Fast(BackTestParameter(self.__GetView()))
        df.draw_backtest(_data)
    def button_backtest_click5(self):#KD篩選
        UI_form = self.__GetView().GetFormUI()
        backtest_stock.set_check(UI_form.check_monthRP_pick.isChecked(),
                                    UI_form.check_PER_pick.isChecked(),
                                    UI_form.check_volume_pick.isChecked(),
                                    UI_form.check_pickOneStock.isChecked(),
                                    UI_form.check_price_pick.isChecked(),
                                    UI_form.check_PBR_pick.isChecked(),
                                    UI_form.check_ROE_pick.isChecked())
        _data = backtest_stock.backtest_KD_pick(BackTestParameter(self.__GetView()))
        df.draw_backtest(_data)
    def button_backtest_click6(self):#PEG篩選
        UI_form = self.__GetView().GetFormUI()
        backtest_stock.set_check(UI_form.check_monthRP_pick.isChecked(),
                                    UI_form.check_PER_pick.isChecked(),
                                    UI_form.check_volume_pick.isChecked(),
                                    UI_form.check_pickOneStock.isChecked(),
                                    UI_form.check_price_pick.isChecked(),
                                    UI_form.check_PBR_pick.isChecked(),
                                    UI_form.check_ROE_pick.isChecked())
        _data = backtest_stock.backtest_PEG_pick_Fast(BackTestParameter(self.__GetView()))
        df.draw_backtest(_data)

class BackTestParameter(backtest_stock.VirturlBackTestParameter):
    def __init__(self, _view: BackTest_Window):
        UI_form = _view.GetFormUI()
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