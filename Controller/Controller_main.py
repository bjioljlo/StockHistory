import Controller.Controller as Controller
from Controller.Controller import TController
from View.View_main import Main_Window
from Model.Model_main import Model_main
from Model.Model import IModel
from View.View import IWindow

import get_stock_info   
import get_stock_history as gsh
import update_stock_info
import tools
import draw_figur as df
import threading
from datetime import datetime
from PyQt5 import QtCore

class Controller_main(TController):
    def __init__(self, _view: IWindow = None, _model: IModel = None) -> None:
        super().__init__(_view, _model)
        self.Init_Window()
        self.lock = threading.Lock()
    
    def __GetView(self) -> Main_Window:
        return self.View
    
    def __GetModel(self) -> Model_main:
        return self.Model
        
    def Init_Window(self):#初始化mainwindow
        UI_form = self.__GetView().GetFormUI()
        UI_form.button_addStock.clicked.connect(self.button_addStock_click)#設定button功能
        UI_form.button_deletStock.clicked.connect(self.button_deletStock_click)#設定button功能
        UI_form.treeView.setModel(Controller.creat_treeView_model(UI_form.treeView,Controller.main_titalList,False))#設定treeView功能
        UI_form.button_moveToInput.clicked.connect(self.button_moveToInput_click)#設定button功能
        UI_form.button_getStockHistory.clicked.connect(self.button_getStockHistory)#設定button功能
        UI_form.button_openPickWindow.clicked.connect(self.button_openPickWindow_click)#設定button功能
        UI_form.button_getMonthRP.clicked.connect(self.button_monthRP_click)#設定button功能
        UI_form.button_getDividend_yield.clicked.connect(self.button_Dividend_yield_click)#設定button功能
        UI_form.button_runSchedule.clicked.connect(update_stock_info.RunScheduleNow)#設定button功能
        UI_form.button_stopSchedule.clicked.connect(update_stock_info.stopThreadSchedule)#設定button功能
        UI_form.button_getOperating_Margin.clicked.connect(self.button_Operating_Margin_click)#設定button功能
        UI_form.button_Operating_Margin_Ratio.clicked.connect(self.button_Operating_Margin_Ratio_click)
        UI_form.button_getROE.clicked.connect(self.button_ROE_Ratio_click)
        UI_form.button_getFreeCF.clicked.connect(self.button_FreeSCF_click)
        UI_form.button_getSCF.clicked.connect(self.button_OCF_click)
        UI_form.button_getICF.clicked.connect(self.button_ICF_click)
        UI_form.button_getPCF.clicked.connect(self.button_PCF_click)
        UI_form.button_getEPS.clicked.connect(self.button_EPS_click)
        UI_form.button_getDebtRatio.clicked.connect(self.button_DebtRatio_click)
        UI_form.button_getMonth_Growth.clicked.connect(self.button_MonthRevenueGrowth_click)
        UI_form.button_getSeason_Growth.clicked.connect(self.button_SeasonRevenueGrowth_click)
        # #設定日期
        Date = datetime.strptime(get_stock_info.Update_date[0:10],"%Y-%m-%d")
        date = QtCore.QDate(Date.year,Date.month,Date.day)
        today = QtCore.QDate(datetime.today().year,datetime.today().month,datetime.today().day)
        UI_form.date_startDate.setMaximumDate(today)
        UI_form.date_startDate.setMinimumDate(QtCore.QDate(2000,1,1))
        enddate = tools.changeDateMonth(tools.QtDate2DateTime(date),-6)
        yesterday = tools.backWorkDays(datetime.today(),1)
        end_yesterday = tools.changeDateMonth(yesterday,-6)
        UI_form.date_startDate.setDate(QtCore.QDate((end_yesterday.year),(end_yesterday.month),(end_yesterday.day)))
        UI_form.date_endDate.setMaximumDate(today)
        UI_form.date_endDate.setMinimumDate(QtCore.QDate(2001,1,1))
        UI_form.date_endDate.setDate(QtCore.QDate((yesterday.year),(yesterday.month),(yesterday.day)))
        UI_form.input_SMA1.setPlainText("5")
        UI_form.input_SMA2.setPlainText("20")
        UI_form.input_SMA3.setPlainText("60")

    def button_openPickWindow_click(self):
        self.Model.GetInteractiveController().ShowWindow()
    def button_addStock_click(self):
        stocknum = self.__GetView().GetFormUI().input_stockNumber.toPlainText()
        get_stock_info.Add_stock_info(stocknum)
        self.__GetView().GetFormUI().treeView.setModel(Controller.creat_treeView_model(self.__GetView().GetFormUI().treeView,Controller.main_titalList,False))#設定treeView功能
    def button_deletStock_click(self):
        UI_form = self.__GetView().GetFormUI()
        stocknum = UI_form.input_stockNumber.toPlainText()
        get_stock_info.Delet_stock_info(stocknum)
        UI_form.treeView.setModel(Controller.creat_treeView_model(UI_form.treeView,Controller.main_titalList,False))#設定treeView功能
    def button_moveToInput_click(self):
        Index = self.__GetView().GetFormUI().treeView.currentIndex()
        mModel = self.__GetView().GetFormUI().treeView.model()
        try:
            data = mModel.item(Index.row(),0).text()
            text = str(data)
            self.__GetView().GetFormUI().input_stockNumber.setPlainText(text)
        except:
            print("")
    def button_monthRP_click(self):#某股票月營收曲線
        self.__GetModel().monthRP(self.__GetView().GetFormUI().input_stockNumber.toPlainText(),
                                  self.__GetView().GetFormUI().date_startDate.date(),
                                  self.__GetView().GetFormUI().date_endDate.date())
        
    def button_Dividend_yield_click(self):#某股票殖利率曲線
        self.__GetModel().Dividend_yield(self.__GetView().GetFormUI().input_stockNumber.toPlainText(),
                                        self.__GetView().GetFormUI().date_startDate.date(),
                                        self.__GetView().GetFormUI().date_endDate.date())
        
    def button_Operating_Margin_click(self):#某股票營業利益率曲線
        if (self.__GetView().GetFormUI().input_stockNumber.toPlainText() == ''):
            print('請輸入股票號碼')
            return
        if (int(self.__GetView().GetFormUI().date_endDate.date().day()) == int(datetime.today().day)):
            print("今天還沒過完無資資訊")
            return
        main_imge = gsh.All_imge(tools.QtDate2DateTime(self.__GetView().GetFormUI().date_startDate.date()),
                                    tools.QtDate2DateTime(self.__GetView().GetFormUI().date_endDate.date()),
                                    gsh.OM_index)
        data_result = main_imge.get_Chart(int(self.__GetView().GetFormUI().input_stockNumber.toPlainText()))
        df.draw_RP(data_result,
                self.__GetView().GetFormUI().input_stockNumber.toPlainText(),
                main_imge._report._name,
                main_imge._report._name,
                'Operating Margin Ratio')
    def button_Operating_Margin_Ratio_click(self):#某股票營業利益成長率曲線
        if (self.__GetView().GetFormUI().input_stockNumber.toPlainText() == ''):
            print('請輸入股票號碼')
            return
        if (int(self.__GetView().GetFormUI().date_endDate.date().day()) == int(datetime.today().day)):
            print("今天還沒過完無資資訊")
            return
        main_imge = gsh.All_imge(tools.QtDate2DateTime(self.__GetView().GetFormUI().date_startDate.date()),
                                    tools.QtDate2DateTime(self.__GetView().GetFormUI().date_endDate.date()),
                                    gsh.OM_Growth_index)
        #取得營業利益率成長率資料(與去年同季相比)
        data_result_up = main_imge.get_Chart(int(self.__GetView().GetFormUI().input_stockNumber.toPlainText()))
        df.draw_RP(data_result_up,
                self.__GetView().GetFormUI().input_stockNumber.toPlainText(),
                main_imge._report._name,
                main_imge._report._name,
                'Operating Margin Growth Up (season by season)(%)')
    def button_ROE_Ratio_click(self):#某股票ROE曲線
        if (self.__GetView().GetFormUI().input_stockNumber.toPlainText() == ''):
            print('請輸入股票號碼')
            return
        if (int(self.__GetView().GetFormUI().date_endDate.date().day()) == int(datetime.today().day)):
            print("今天還沒過完無資資訊")
            return
        #取得ROE資料
        main_imge = gsh.All_imge(tools.QtDate2DateTime(self.__GetView().GetFormUI().date_startDate.date()),
                                    tools.QtDate2DateTime(self.__GetView().GetFormUI().date_endDate.date()),
                                    gsh.ROE_index)
        data_result_up = main_imge.get_Chart(int(self.__GetView().GetFormUI().input_stockNumber.toPlainText()))
        df.draw_RP(data_result_up,
                self.__GetView().GetFormUI().input_stockNumber.toPlainText(),
                main_imge._report._name,
                main_imge._report._name,
                'Return On Equity Ratio(ROE)')
    def button_OCF_click(self):#某股票營業現金流
        if (self.__GetView().GetFormUI().input_stockNumber.toPlainText() == ''):
            print('請輸入股票號碼')
            return
        if (int(self.__GetView().GetFormUI().date_endDate.date().day()) == int(datetime.today().day)):
            print("今天還沒過完無資資訊")
            return
        main_imge = gsh.All_imge(tools.QtDate2DateTime(self.__GetView().GetFormUI().date_startDate.date()),
                                    tools.QtDate2DateTime(self.__GetView().GetFormUI().date_endDate.date()),
                                    gsh.OCF_index)
        data_result = main_imge.get_Chart(int(self.__GetView().GetFormUI().input_stockNumber.toPlainText()))
        df.draw_RP(data_result,
                self.__GetView().GetFormUI().input_stockNumber.toPlainText(),
                main_imge._report._name,
                main_imge._report._name,
                'Operating cash flow')
    def button_ICF_click(self):#某股票投資現金流
        if (self.__GetView().GetFormUI().input_stockNumber.toPlainText() == ''):
            print('請輸入股票號碼')
            return
        if (int(self.__GetView().GetFormUI().date_endDate.date().day()) == int(datetime.today().day)):
            print("今天還沒過完無資資訊")
            return
        main_imge = gsh.All_imge(tools.QtDate2DateTime(self.__GetView().GetFormUI().date_startDate.date()),
                                    tools.QtDate2DateTime(self.__GetView().GetFormUI().date_endDate.date()),
                                    gsh.ICF_index)
        data_result = main_imge.get_Chart(int(self.__GetView().GetFormUI().input_stockNumber.toPlainText()))
        df.draw_RP(data_result,
                self.__GetView().GetFormUI().input_stockNumber.toPlainText(),
                main_imge._report._name,
                main_imge._report._name,
                'Investment cash flow')
    def button_FreeSCF_click(self):#某股票自由現金流
        if (self.__GetView().GetFormUI().input_stockNumber.toPlainText() == ''):
            print('請輸入股票號碼')
            return
        if (int(self.__GetView().GetFormUI().date_endDate.date().day()) == int(datetime.today().day)):
            print("今天還沒過完無資資訊")
            return
        main_imge = gsh.All_imge(tools.QtDate2DateTime(self.__GetView().GetFormUI().date_startDate.date()),
                                    tools.QtDate2DateTime(self.__GetView().GetFormUI().date_endDate.date()),
                                    gsh.FreeCF_index)
        data_result = main_imge.get_Chart(int(self.__GetView().GetFormUI().input_stockNumber.toPlainText()))
        df.draw_RP(data_result,
                self.__GetView().GetFormUI().input_stockNumber.toPlainText(),
                main_imge._report._name,
                main_imge._report._name,
                'Free cash flow')
    def button_PCF_click(self):#某股票股價現金流量比
        if (self.__GetView().GetFormUI().input_stockNumber.toPlainText() == ''):
            print('請輸入股票號碼')
            return
        if (int(self.__GetView().GetFormUI().date_endDate.date().day()) == int(datetime.today().day)):
            print("今天還沒過完無資資訊")
            return
        main_imge = gsh.All_imge(tools.QtDate2DateTime(self.__GetView().GetFormUI().date_startDate.date()),
                                    tools.QtDate2DateTime(self.__GetView().GetFormUI().date_endDate.date()),
                                    gsh.PCF_index)
        data_result = main_imge.get_Chart(int(self.__GetView().GetFormUI().input_stockNumber.toPlainText()))
        df.draw_RP(data_result,
                self.__GetView().GetFormUI().input_stockNumber.toPlainText(),
                main_imge._report._name,
                main_imge._report._name,
                'Price to Cash Flow Ratio(P/CF)')
    def button_EPS_click(self):#某股票eps
        if(self.__GetView().GetFormUI().input_stockNumber.toPlainText() == ''):
            print('請輸入股票號碼')
            return
        if (int(self.__GetView().GetFormUI().date_endDate.date().day()) == int(datetime.today().day)):
            print("今天還沒過完無資資訊")
            return
        main_imge = gsh.All_imge(tools.QtDate2DateTime(self.__GetView().GetFormUI().date_startDate.date()),
                                    tools.QtDate2DateTime(self.__GetView().GetFormUI().date_endDate.date()),
                                    gsh.EPS_index)
        data_result = main_imge.get_Chart(int(self.__GetView().GetFormUI().input_stockNumber.toPlainText()))
        df.draw_RP(data_result,
                self.__GetView().GetFormUI().input_stockNumber.toPlainText(),
                main_imge._report._name,
                main_imge._report._name,
                'Earnings Per Share(EPS)')
    def button_DebtRatio_click(self):#某股票資產負債比率
        if(self.__GetView().GetFormUI().input_stockNumber.toPlainText() == ''):
            print('請輸入股票號碼')
            return
        if (int(self.__GetView().GetFormUI().date_endDate.date().day()) == int(datetime.today().day)):
            print("今天還沒過完無資資訊")
            return
        main_imge = gsh.All_imge(tools.QtDate2DateTime(self.__GetView().GetFormUI().date_startDate.date()),
                                    tools.QtDate2DateTime(self.__GetView().GetFormUI().date_endDate.date()),
                                    gsh.Debt_index)
        data_result = main_imge.get_Chart(int(self.__GetView().GetFormUI().input_stockNumber.toPlainText()))
        df.draw_RP(data_result,
                self.__GetView().GetFormUI().input_stockNumber.toPlainText(),
                main_imge._report._name,
                main_imge._report._name,
                'Debt Asset Ratio')
    def button_MonthRevenueGrowth_click(self):
        if(self.__GetView().GetFormUI().input_stockNumber.toPlainText() == ''):
            print('請輸入股票號碼')
            return
        if (int(self.__GetView().GetFormUI().date_endDate.date().day()) == int(datetime.today().day)):
            print("今天還沒過完無資資訊")
            return
        main_imge = gsh.All_imge(tools.QtDate2DateTime(self.__GetView().GetFormUI().date_startDate.date()),
                                    tools.QtDate2DateTime(self.__GetView().GetFormUI().date_endDate.date()),
                                    gsh.MR_Growth_index)
        data_result = main_imge.get_Chart(int(self.__GetView().GetFormUI().input_stockNumber.toPlainText()))
        df.draw_RP(data_result,
                self.__GetView().GetFormUI().input_stockNumber.toPlainText(),
                main_imge._report._name,
                main_imge._report._name,
                'Month Revenue Growth')
    def button_SeasonRevenueGrowth_click(self):
        if(self.__GetView().GetFormUI().input_stockNumber.toPlainText() == ''):
            print('請輸入股票號碼')
            return
        if (int(self.__GetView().GetFormUI().date_endDate.date().day()) == int(datetime.today().day)):
            print("今天還沒過完無資資訊")
            return
        main_imge = gsh.All_imge(tools.QtDate2DateTime(self.__GetView().GetFormUI().date_startDate.date()),
                                    tools.QtDate2DateTime(self.__GetView().GetFormUI().date_endDate.date()),
                                    gsh.SR_Growth_index)
        data_result = main_imge.get_Chart(int(self.__GetView().GetFormUI().input_stockNumber.toPlainText()))
        df.draw_RP(data_result,
                self.__GetView().GetFormUI().input_stockNumber.toPlainText(),
                main_imge._report._name,
                main_imge._report._name,
                'Season Revenue Growth') 
    def button_getStockHistory(self):#某股票蠟燭圖
        #存更新日期
        date = tools.QtDate2DateTime(self.__GetView().GetFormUI().date_startDate.date())
        end_date = tools.QtDate2DateTime(self.__GetView().GetFormUI().date_endDate.date())
        str_date = tools.DateTime2String(date)
        df.Clear_PICS()
        if self.__GetView().GetFormUI().input_stockNumber.toPlainText() == "":
            for key,value in get_stock_info.stock_list.items():
                m_history = gsh.get_stock_history(key,str_date)
            return
        elif self.__GetView().GetFormUI().input_stockNumber.toPlainText() == "Update":
            str_date = [str_date]
            new_thread = threading.Thread(target= self.Update_StockData_threading,args=str_date)
            new_thread.setDaemon(True)
            new_thread.start()
            return  
        else:
            stock_number = self.__GetView().GetFormUI().input_stockNumber.toPlainText()
            gsh.Stock_RangeDate.number = int(stock_number)
            gsh.Stock_RangeDate.StartDate = date
            m_history = gsh.Stock_RangeDate.get_ALL()
            if self.__GetView().GetFormUI().check_ADL.isChecked() or self.__GetView().GetFormUI().check_ADLs.isChecked():
                mask = m_history.index <= end_date
                m_history = m_history[mask]
            self.check_SMA_isCheck(m_history,get_stock_info.Get_stock_info(stock_number),date)
            self.check_Volume_isCheck(m_history,get_stock_info.Get_stock_info(stock_number))  
            self.check_KD_isCheck(m_history,get_stock_info.Get_stock_info(stock_number))
            self.check_BollingerBands_isCheck(m_history,get_stock_info.Get_stock_info(stock_number))
            self.check_RSI_isCheck(m_history,get_stock_info.Get_stock_info(stock_number))
            self.Check_ADL_isCheck()
            self.Check_ADLs_isCheck()
            self.Check_MACD_isCheck(m_history)
            self.check_price_isCheck(m_history,get_stock_info.Get_stock_info(stock_number))#壹定要在最後面檢查 
    #異步更新所有台股資料
    def Update_StockData_threading(self,str_date):
        self.lock.acquire()
        for key,value in get_stock_info.ts.codes.items():
            if value.market == "上市" and len(value.code) == 4:
                if gsh.check_no_use_stock(value.code) == True:
                    print('get_stock_price: ' + str(value.code) + ' in no use')
                    continue
                m_history = gsh.get_stock_history(value.code,str_date)
                print("get " + str(value.code) + " info susess!")
        #存更新日期
        get_stock_info.Update_date = str(datetime.today())[0:10]
        get_stock_info.Save_Update_date()    
        self.lock.acquire()
    def check_SMA_isCheck(self,m_history,stockInfo,startdate):
        if self.__GetView().GetFormUI().check_SMA.isChecked() == True:
            input_SMA_list = [self.__GetView().GetFormUI().input_SMA1,self.__GetView().GetFormUI().input_SMA2,self.__GetView().GetFormUI().input_SMA3]
            for i in input_SMA_list:
                if i.toPlainText() != "":
                    df.draw_SMA(m_history,int(i.toPlainText()),stockInfo)
    def check_price_isCheck(self,m_history,stockInfo):
        if type(stockInfo) == str:
            print("請先存檔!")
            return
        if self.__GetView().GetFormUI().check_stock.isChecked():
            df.draw_stock(m_history,stockInfo)
        else:
            df.draw_stock(m_history,stockInfo)
    def check_Volume_isCheck(self,m_history,stockInfo):
        if self.__GetView().GetFormUI().check_volume.isChecked():
            df.draw_Volume(m_history,stockInfo)
    def check_KD_isCheck(self,m_history,stockInfo):
        if self.__GetView().GetFormUI().check_KD.isChecked():
            df.draw_KD(m_history,stockInfo)
    def check_BollingerBands_isCheck(self,m_history,stockInfo):
        if self.__GetView().GetFormUI().check_BollingerBands.isChecked() == True:
            df.draw_BollingerBands(m_history,12,stockInfo)
    def check_RSI_isCheck(self,m_history,stockInfo):
        if self.__GetView().GetFormUI().check_RSI.isChecked() == True:
            df.draw_RSI(m_history,stockInfo)
    def Check_ADL_isCheck(self):
        if self.__GetView().GetFormUI().check_ADL.isChecked() == True:
            Data_ADL = gsh.get_ADL(tools.QtDate2DateTime(self.__GetView().GetFormUI().date_startDate.date()),tools.QtDate2DateTime(self.__GetView().GetFormUI().date_endDate.date()))
            df.draw_ADL(Data_ADL)
    def Check_ADLs_isCheck(self):
        if self.__GetView().GetFormUI().check_ADLs.isChecked() == True:
            Data_ADLs = gsh.get_ADLs(tools.QtDate2DateTime(self.__GetView().GetFormUI().date_startDate.date()),tools.QtDate2DateTime(self.__GetView().GetFormUI().date_endDate.date()))
            df.draw_ADLs(Data_ADLs)
    def Check_MACD_isCheck(self,m_history):
        if self.__GetView().GetFormUI().check_MACD.isChecked() == True:
            df.draw_MACD(m_history)
