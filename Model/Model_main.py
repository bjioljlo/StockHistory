from Controller.Controller import IController
from Model.Model import TModel

from datetime import datetime
import get_stock_history as gsh
import tools
import draw_figur as df
from IParameter import RecordMainParameter

class Model_main(TModel):
    def __init__(self, _interactiveController: IController):
        super().__init__()
        self._InteractiveController = _interactiveController
    
    @property
    def InteractiveController(self):
        if self._InteractiveController == None:
            raise
        return self._InteractiveController
    @InteractiveController.setter
    def InteractiveController(self,_interactiveController:IController):
        self._InteractiveController = _interactiveController

    def GetInteractiveController(self) -> IController:
        return self.InteractiveController
    
    def monthRP(self, RecordMainParameter: RecordMainParameter):
        """某股票月營收曲線"""
        if (RecordMainParameter.number == None):
            print('請輸入股票號碼')
            return
        if (RecordMainParameter.enddate.day == datetime.today().day):
            print("今天還沒過完無資資訊")
            return
        if (RecordMainParameter.enddate.month == datetime.today().month):
            print("本月還沒過完無資資訊")
            return
        if RecordMainParameter.enddate.month == tools.changeDateMonth(datetime.today(),-1).month and datetime.today().day < 15 :
            print("還沒15號沒有上個月的資料")
            return
        main_imge = gsh.All_imge(RecordMainParameter.startdate,
                                    RecordMainParameter.enddate,
                                    gsh.Month_index)
        data_result = main_imge.get_Chart(RecordMainParameter.number)
        df.draw_RP(data_result,
                RecordMainParameter.number,
                main_imge._report._name,
                main_imge._report._name,
                'Monthly Revenue(UNIT-->NTD:1000,000)')        
    def Dividend_yield(self, RecordMainParameter: RecordMainParameter):
        """某股票殖利率曲線"""
        if (RecordMainParameter.number == None):
            print('請輸入股票號碼')
            return
        if (int(RecordMainParameter.enddate.day()) == datetime.today().day):
            print("今天還沒過完無資資訊")
            return
        main_imge = gsh.All_imge(RecordMainParameter.startdate,
                                    RecordMainParameter.enddate,
                                    gsh.Yield_index)
        data_result = main_imge.get_Chart(RecordMainParameter.number)
        df.draw_RP(data_result,
                RecordMainParameter.number,
                main_imge._report._name,
                main_imge._report._name,
                'Dividend yield')           
    def Operating_Margin(self, RecordMainParameter: RecordMainParameter):
        """某股票營業利益率曲線"""
        if (RecordMainParameter.number == None):
            print('請輸入股票號碼')
            return
        if (RecordMainParameter.enddate.day == datetime.today().day):
            print("今天還沒過完無資資訊")
            return
        main_imge = gsh.All_imge(RecordMainParameter.startdate,
                                    RecordMainParameter.enddate,
                                    gsh.OM_index)
        data_result = main_imge.get_Chart(RecordMainParameter.number)
        df.draw_RP(data_result,
                RecordMainParameter.number,
                main_imge._report._name,
                main_imge._report._name,
                'Operating Margin Ratio')
    def Operating_Margin_Ratio(self, RecordMainParameter: RecordMainParameter):
        """#某股票營業利益成長率曲線"""
        if (RecordMainParameter.number == None):
            print('請輸入股票號碼')
            return
        if (RecordMainParameter.enddate.day == datetime.today().day):
            print("今天還沒過完無資資訊")
            return
        main_imge = gsh.All_imge(RecordMainParameter.startdate,
                                    RecordMainParameter.enddate,
                                    gsh.OM_Growth_index)
        #取得營業利益率成長率資料(與去年同季相比)
        data_result_up = main_imge.get_Chart(RecordMainParameter.number)
        df.draw_RP(data_result_up,
                RecordMainParameter.number,
                main_imge._report._name,
                main_imge._report._name,
                'Operating Margin Growth Up (season by season)(%)')
    def ROE_Ratio(self, RecordMainParameter: RecordMainParameter):
        """#某股票ROE曲線"""
        if (RecordMainParameter.number == None):
            print('請輸入股票號碼')
            return
        if (RecordMainParameter.enddate.day == datetime.today().day):
            print("今天還沒過完無資資訊")
            return
        #取得ROE資料
        main_imge = gsh.All_imge(RecordMainParameter.startdate,
                                    RecordMainParameter.enddate,
                                    gsh.ROE_index)
        data_result_up = main_imge.get_Chart(RecordMainParameter.number)
        df.draw_RP(data_result_up,
                RecordMainParameter.number,
                main_imge._report._name,
                main_imge._report._name,
                'Return On Equity Ratio(ROE)')
    def OCF(self, RecordMainParameter: RecordMainParameter):
        """某股票營業現金流"""
        if (RecordMainParameter.number == None):
            print('請輸入股票號碼')
            return
        if (RecordMainParameter.enddate.day == datetime.today().day):
            print("今天還沒過完無資資訊")
            return
        main_imge = gsh.All_imge(RecordMainParameter.startdate,
                                    RecordMainParameter.enddate,
                                    gsh.OCF_index)
        data_result = main_imge.get_Chart(RecordMainParameter.number)
        df.draw_RP(data_result,
                RecordMainParameter.number,
                main_imge._report._name,
                main_imge._report._name,
                'Operating cash flow')
    def ICF(self, RecordMainParameter: RecordMainParameter):
        """某股票投資現金流"""
        if (RecordMainParameter.number == None):
            print('請輸入股票號碼')
            return
        if (RecordMainParameter.enddate.day == datetime.today().day):
            print("今天還沒過完無資資訊")
            return
        main_imge = gsh.All_imge(RecordMainParameter.startdate,
                                    RecordMainParameter.enddate,
                                    gsh.ICF_index)
        data_result = main_imge.get_Chart(RecordMainParameter.number)
        df.draw_RP(data_result,
                RecordMainParameter.number,
                main_imge._report._name,
                main_imge._report._name,
                'Investment cash flow')
    def FreeSCF(self, RecordMainParameter: RecordMainParameter):
        """某股票自由現金流"""
        if (RecordMainParameter.number == None):
            print('請輸入股票號碼')
            return
        if (RecordMainParameter.enddate.day == datetime.today().day):
            print("今天還沒過完無資資訊")
            return
        main_imge = gsh.All_imge(RecordMainParameter.startdate,
                                    RecordMainParameter.enddate,
                                    gsh.FreeCF_index)
        data_result = main_imge.get_Chart(RecordMainParameter.number)
        df.draw_RP(data_result,
                RecordMainParameter.number,
                main_imge._report._name,
                main_imge._report._name,
                'Free cash flow')
    def PCF(self, RecordMainParameter: RecordMainParameter):
        """某股票股價現金流量比"""
        if (RecordMainParameter.number == None):
            print('請輸入股票號碼')
            return
        if (RecordMainParameter.enddate.day == datetime.today().day):
            print("今天還沒過完無資資訊")
            return
        main_imge = gsh.All_imge(RecordMainParameter.startdate,
                                    RecordMainParameter.enddate,
                                    gsh.PCF_index)
        data_result = main_imge.get_Chart(RecordMainParameter.number)
        df.draw_RP(data_result,
                RecordMainParameter.number,
                main_imge._report._name,
                main_imge._report._name,
                'Price to Cash Flow Ratio(P/CF)')
    def EPS(self, RecordMainParameter: RecordMainParameter):
        """某股票eps"""
        if(RecordMainParameter.number == None):
            print('請輸入股票號碼')
            return
        if (RecordMainParameter.enddate.day == datetime.today().day):
            print("今天還沒過完無資資訊")
            return
        main_imge = gsh.All_imge(RecordMainParameter.startdate,
                                    RecordMainParameter.enddate,
                                    gsh.EPS_index)
        data_result = main_imge.get_Chart(RecordMainParameter.number)
        df.draw_RP(data_result,
                RecordMainParameter.number,
                main_imge._report._name,
                main_imge._report._name,
                'Earnings Per Share(EPS)')
    def DebtRatio(self, RecordMainParameter: RecordMainParameter):
        """某股票資產負債比率"""
        if(RecordMainParameter.number == None):
            print('請輸入股票號碼')
            return
        if (RecordMainParameter.enddate.day == datetime.today().day):
            print("今天還沒過完無資資訊")
            return
        main_imge = gsh.All_imge(RecordMainParameter.startdate,
                                    RecordMainParameter.enddate,
                                    gsh.Debt_index)
        data_result = main_imge.get_Chart(RecordMainParameter.number)
        df.draw_RP(data_result,
                RecordMainParameter.number,
                main_imge._report._name,
                main_imge._report._name,
                'Debt Asset Ratio')
    def MonthRevenueGrowth(self, RecordMainParameter: RecordMainParameter):
        if(RecordMainParameter.number == None):
            print('請輸入股票號碼')
            return
        if (RecordMainParameter.enddate.day == datetime.today().day):
            print("今天還沒過完無資資訊")
            return
        main_imge = gsh.All_imge(RecordMainParameter.startdate,
                                    RecordMainParameter.enddate,
                                    gsh.MR_Growth_index)
        data_result = main_imge.get_Chart(RecordMainParameter.number)
        df.draw_RP(data_result,
                RecordMainParameter.number,
                main_imge._report._name,
                main_imge._report._name,
                'Month Revenue Growth')
    def SeasonRevenueGrowth(self, RecordMainParameter: RecordMainParameter):
        if(RecordMainParameter.number == None):
            print('請輸入股票號碼')
            return
        if (RecordMainParameter.enddate.day == datetime.today().day):
            print("今天還沒過完無資資訊")
            return
        main_imge = gsh.All_imge(RecordMainParameter.startdate,
                                    RecordMainParameter.enddate,
                                    gsh.SR_Growth_index)
        data_result = main_imge.get_Chart(RecordMainParameter.number)
        df.draw_RP(data_result,
                RecordMainParameter.number,
                main_imge._report._name,
                main_imge._report._name,
                'Season Revenue Growth') 