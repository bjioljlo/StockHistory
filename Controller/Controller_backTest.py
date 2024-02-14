from Model.Model import IModel
from View.View import IWindow
from View.View_backtest import BackTest_Window
from Controller.Controller import TController
from Model.Model_backtest import Model_backtest
from datetime import datetime
from PyQt5 import QtCore
from Mediator_Controller import IMediator_Controller

class Controller_backTest(TController):
    def __init__(self, _view: IWindow = None, _model: IModel = None) -> None:
        super().__init__(_view, _model)
        self.Init_Window()
        self.mediator:IMediator_Controller = None

    def __GetView(self) -> BackTest_Window:
        return self.View
    
    def __GetModel(self) -> Model_backtest:
        return self.Model

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

    def GetEndDate(self) -> datetime:
        return super().GetEndDate()

    def GetStockNumber(self) -> str:
        return super().GetStockNumber()
    
    def SetStockNumber(self, stockNumber: str):
        return super().SetStockNumber(stockNumber)

    #第3頁的UI
    def button_backtest_click(self):#月營收回測開始紐
        self.__GetModel().backtest(self.__GetView().Parament)

    def button_backtest_click2(self):#PER PBR 回測開始紐
        self.__GetModel().backtest2(self.__GetView().Parament)

    def button_backtest_click3(self):#定期定額
        self.__GetModel().backtest3(self.__GetView().Parament)

    def button_backtest_click4(self):#創新高
        self.__GetModel().backtest4(self.__GetView().Parament)
        
    def button_backtest_click5(self):#KD篩選
        self.__GetModel().backtest5(self.__GetView().Parament) 

    def button_backtest_click6(self):#PEG篩選
        self.__GetModel().backtest6(self.__GetView().Parament)