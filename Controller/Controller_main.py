import threading
from datetime import datetime

from PyQt5 import QtCore

import Common.Globals as Globals
import StockInfos as MainUserDataInfo
import Common.Tools as Tools
from DrawFigur import DrawFigur
from FilterService.GetStockData import Stock_RangeDate
from ExternalService.TGetExternalData import TGetExternalData
from Model.Model import IModel
from Model.Model_main import Model_main
from View.View import IWindow
from View.View_main import Main_Window

from .Controller import MAIN_TITALLIST, TController, controllers, creat_treeView_model

# TODO telegram 要重新寫新版改太多了....telegram_bot


class Controller_main(TController):
    def __init__(self, _view: IWindow = None, _model: IModel = None) -> None:
        super().__init__(_view, _model)
        self.Init_Window()
        self.lock = threading.Lock()
        self.df: DrawFigur = Globals.DRAWFIGUR

    def __GetView(self) -> Main_Window:
        return self.View

    def __GetModel(self) -> Model_main:
        return self.Model

    def Init_Window(self):  # 初始化mainwindow
        UI_form = self.__GetView().GetFormUI()
        UI_form.button_addStock.clicked.connect(
            self.button_addStock_click
        )  # 設定button功能
        UI_form.button_deletStock.clicked.connect(
            self.button_deletStock_click
        )  # 設定button功能
        UI_form.treeView.setModel(
            creat_treeView_model(
                UI_form.treeView, MAIN_TITALLIST, self.__GetModel().MainUserInfoData
            )
        )  # 設定treeView功能
        UI_form.button_moveToInput.clicked.connect(
            self.button_moveToInput_click
        )  # 設定button功能
        UI_form.button_getStockHistory.clicked.connect(
            self.button_getStockHistory
        )  # 設定button功能
        UI_form.button_openPickWindow.clicked.connect(
            self.button_openPickWindow_click
        )  # 設定button功能
        UI_form.button_getMonthRP.clicked.connect(
            self.button_monthRP_click
        )  # 設定button功能
        UI_form.button_getDividend_yield.clicked.connect(
            self.button_Dividend_yield_click
        )  # 設定button功能
        UI_form.button_runSchedule.clicked.connect(
            self.button_RunSchedule_click
        )  # 設定button功能
        UI_form.button_runOtherSchedule.clicked.connect(
            self.button_RunOtherSchedule_click
        )  # 設定button功能
        UI_form.button_stopSchedule.clicked.connect(
            self.button_StopThreadSchedule_click
        )  # 設定button功能
        UI_form.button_getOperating_Margin.clicked.connect(
            self.button_Operating_Margin_click
        )  # 設定button功能
        UI_form.button_Operating_Margin_Ratio.clicked.connect(
            self.button_Operating_Margin_Ratio_click
        )
        UI_form.button_getROE.clicked.connect(self.button_ROE_Ratio_click)
        UI_form.button_getFreeCF.clicked.connect(self.button_FreeSCF_click)
        UI_form.button_getSCF.clicked.connect(self.button_OCF_click)
        UI_form.button_getICF.clicked.connect(self.button_ICF_click)
        UI_form.button_getPCF.clicked.connect(self.button_PCF_click)
        UI_form.button_getEPS.clicked.connect(self.button_EPS_click)
        UI_form.button_getDebtRatio.clicked.connect(self.button_DebtRatio_click)
        UI_form.button_getMonth_Growth.clicked.connect(
            self.button_MonthRevenueGrowth_click
        )
        UI_form.button_getSeason_Growth.clicked.connect(
            self.button_SeasonRevenueGrowth_click
        )
        UI_form.button_getADLs.clicked.connect(self.button_ADLs_click)
        # #設定日期
        Date = datetime.strptime(
            self.__GetModel().MainUserInfoData.UpdateDate[0:10], "%Y-%m-%d"
        )
        date = QtCore.QDate(Date.year, Date.month, Date.day)
        today = QtCore.QDate(
            datetime.today().year, datetime.today().month, datetime.today().day
        )
        UI_form.date_startDate.setMaximumDate(today)
        UI_form.date_startDate.setMinimumDate(QtCore.QDate(2000, 1, 1))
        enddate = Tools.changeDateMonth(Tools.QtDate2DateTime(date), -6)
        yesterday = Tools.backWorkDays(datetime.today(), 1)
        end_yesterday = Tools.changeDateMonth(yesterday, -6)
        UI_form.date_startDate.setDate(
            QtCore.QDate(
                (end_yesterday.year), (end_yesterday.month), (end_yesterday.day)
            )
        )
        UI_form.date_endDate.setMaximumDate(today)
        UI_form.date_endDate.setMinimumDate(QtCore.QDate(2001, 1, 1))
        UI_form.date_endDate.setDate(
            QtCore.QDate((yesterday.year), (yesterday.month), (yesterday.day))
        )
        UI_form.input_SMA1.setPlainText("5")
        UI_form.input_SMA2.setPlainText("20")
        UI_form.input_SMA3.setPlainText("60")

    def GetEndDate(self) -> datetime:
        endDate = Tools.QtDate2DateTime(
            self.__GetView().GetFormUI().date_endDate.date()
        )
        return endDate

    def GetStockNumber(self) -> str:
        stockNumber = self.__GetView().GetFormUI().input_stockNumber.toPlainText()
        return stockNumber

    def SetStockNumber(self, stockNumber: str):
        self.__GetView().GetFormUI().input_stockNumber.setText(stockNumber)

    def button_openPickWindow_click(self):
        self.GetController(controllers.Pick).ShowWindow()

    def button_addStock_click(self):
        stocknum = self.__GetView().GetFormUI().input_stockNumber.toPlainText()
        self.__GetModel().MainUserInfoData.AddStockInfo(stocknum)
        self.__GetView().GetFormUI().treeView.setModel(
            creat_treeView_model(
                self.__GetView().GetFormUI().treeView,
                MAIN_TITALLIST,
                self.__GetModel().MainUserInfoData,
            )
        )  # 設定treeView功能

    def button_deletStock_click(self):
        UI_form = self.__GetView().GetFormUI()
        stocknum = UI_form.input_stockNumber.toPlainText()
        self.__GetModel().MainUserInfoData.DeletStockInfo(stocknum)
        UI_form.treeView.setModel(
            creat_treeView_model(
                UI_form.treeView, MAIN_TITALLIST, self.__GetModel().MainUserInfoData
            )
        )  # 設定treeView功能

    def button_moveToInput_click(self):
        Index = self.__GetView().GetFormUI().treeView.currentIndex()
        mModel = self.__GetView().GetFormUI().treeView.model()
        item = mModel.item(Index.row(), 0)
        if item is not None:
            data = item.text()
            self.__GetView().GetFormUI().input_stockNumber.setPlainText(data)

    def button_monthRP_click(self):  # 某股票月營收曲線
        self.__GetModel().monthRP(self.__GetView().Parament)

    def button_Dividend_yield_click(self):  # 某股票殖利率曲線
        self.__GetModel().Dividend_yield(self.__GetView().Parament)

    def button_Operating_Margin_click(self):  # 某股票營業利益率曲線
        self.__GetModel().Operating_Margin(self.__GetView().Parament)

    def button_Operating_Margin_Ratio_click(self):  # 某股票營業利益成長率曲線
        self.__GetModel().Operating_Margin_Ratio(self.__GetView().Parament)

    def button_ROE_Ratio_click(self):  # 某股票ROE曲線
        self.__GetModel().ROE_Ratio(self.__GetView().Parament)

    def button_OCF_click(self):  # 某股票營業現金流
        self.__GetModel().OCF(self.__GetView().Parament)

    def button_ICF_click(self):  # 某股票投資現金流
        self.__GetModel().ICF(self.__GetView().Parament)

    def button_FreeSCF_click(self):  # 某股票自由現金流
        self.__GetModel().FreeSCF(self.__GetView().Parament)

    def button_PCF_click(self):  # 某股票股價現金流量比
        self.__GetModel().PCF(self.__GetView().Parament)

    def button_EPS_click(self):  # 某股票eps
        self.__GetModel().EPS(self.__GetView().Parament)

    def button_DebtRatio_click(self):  # 某股票資產負債比率
        self.__GetModel().DebtRatio(self.__GetView().Parament)

    def button_MonthRevenueGrowth_click(self):
        self.__GetModel().MonthRevenueGrowth(self.__GetView().Parament)

    def button_SeasonRevenueGrowth_click(self):
        self.__GetModel().SeasonRevenueGrowth(self.__GetView().Parament)

    def button_ADLs_click(self):
        self.__GetModel().ADLs(self.__GetView().Parament)

    def button_RunSchedule_click(self):
        self.__GetModel().RunSchedule()

    def button_RunOtherSchedule_click(self):
        self.__GetModel().RunOtherSchedule()
    
    def button_StopThreadSchedule_click(self):
        self.__GetModel().StopThreadSchedule()

    def button_getStockHistory(self):  # 某股票蠟燭圖
        # 存更新日期
        date = Tools.QtDate2DateTime(self.__GetView().GetFormUI().date_startDate.date())
        end_date = Tools.QtDate2DateTime(
            self.__GetView().GetFormUI().date_endDate.date()
        )
        str_date = Tools.DateTime2String(date)
        self.df.Clear_PICS()
        if self.__GetView().GetFormUI().input_stockNumber.toPlainText() == "":
            for key, value in self.__GetModel().MainUserInfoData.StockList.items():
                TGetExternalData().get_stock_history(key, str_date)
        elif self.__GetView().GetFormUI().input_stockNumber.toPlainText() == "Update":
            str_date = [str_date]
            new_thread = threading.Thread(
                target=self.Update_StockData_threading, args=str_date
            )
            new_thread.setDaemon(True)
            new_thread.start()
        else:
            stock_number = self.__GetView().GetFormUI().input_stockNumber.toPlainText()
            Stock_RangeDate.number = stock_number
            Stock_RangeDate.StartDate = date
            m_history = Stock_RangeDate.get_ALL()
            if (
                self.__GetView().GetFormUI().check_ADL.isChecked()
                or self.__GetView().GetFormUI().check_ADLs.isChecked()
            ):
                mask = m_history.index <= end_date
                m_history = m_history[mask]
            self.check_SMA_isCheck(m_history)
            self.check_Volume_isCheck(m_history)
            self.check_KD_isCheck(m_history)
            self.check_BollingerBands_isCheck(m_history)
            self.check_RSI_isCheck(m_history)
            self.Check_ADL_isCheck()
            self.Check_ADLs_isCheck()
            self.Check_MACD_isCheck(m_history)
            self.check_price_isCheck(
                m_history, self.__GetModel().MainUserInfoData.GetStockInfo(stock_number)
            )  # 壹定要在最後面檢查

    # 異步更新所有台股資料
    def Update_StockData_threading(self, str_date):
        self.lock.acquire()
        for key, value in MainUserDataInfo.ts.codes.items():
            if value.market == "上市" and len(value.code) == 4:
                if Tools.check_no_use_stock(value.code):
                    print("get_stock_price: " + str(value.code) + " in no use")
                    continue
                TGetExternalData().get_stock_history(value.code, str_date)
                print("get " + str(value.code) + " info susess!")
        # 存更新日期
        self.__GetModel().MainUserInfoData.UpdateDate = str(datetime.today())[0:10]
        self.lock.acquire()

    def check_SMA_isCheck(self, m_history):
        if self.__GetView().GetFormUI().check_SMA.isChecked():
            input_SMA_list = [
                self.__GetView().GetFormUI().input_SMA1,
                self.__GetView().GetFormUI().input_SMA2,
                self.__GetView().GetFormUI().input_SMA3,
            ]
            for i in input_SMA_list:
                if i.toPlainText() != "":
                    self.df.draw_SMA(m_history, int(i.toPlainText()))

    def check_price_isCheck(self, m_history, stockInfo):
        if type(stockInfo) is str:
            print("請先存檔!")
            return
        if stockInfo is None:
            print("請先存檔!")
            return
        if self.__GetView().GetFormUI().check_stock.isChecked():
            self.df.draw_stock(m_history, stockInfo.number)
        else:
            self.df.draw_stock(m_history, stockInfo.number)

    def check_Volume_isCheck(self, m_history):
        if self.__GetView().GetFormUI().check_volume.isChecked():
            self.df.draw_Volume()

    def check_KD_isCheck(self, m_history):
        if self.__GetView().GetFormUI().check_KD.isChecked():
            self.df.draw_KD(m_history)

    def check_BollingerBands_isCheck(self, m_history):
        if self.__GetView().GetFormUI().check_BollingerBands.isChecked():
            self.df.draw_BollingerBands(m_history)

    def check_RSI_isCheck(self, m_history):
        if self.__GetView().GetFormUI().check_RSI.isChecked():
            self.df.draw_RSI(m_history)

    def Check_ADL_isCheck(self):
        if self.__GetView().GetFormUI().check_ADL.isChecked():
            Data_ADL = self.__GetModel().ADL(self.__GetView().Parament)
            Data_ADL.sort_index(ascending=True, inplace=True)
            self.df.draw_ADL(Data_ADL)

    def Check_ADLs_isCheck(self):
        if self.__GetView().GetFormUI().check_ADLs.isChecked():
            self.__GetModel().ADLs(self.__GetView().Parament)

    def Check_MACD_isCheck(self, m_history):
        if self.__GetView().GetFormUI().check_MACD.isChecked():
            self.df.draw_MACD(m_history)
