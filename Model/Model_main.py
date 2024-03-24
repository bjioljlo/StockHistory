from Controller.Controller import IController
from Model.Model import TModel

from datetime import datetime
import GetStockData
import tools
import draw_figur as df
from IParameter import RecordMainParameter
from StockInfos import UserInfoDatas

class Model_main(TModel):
    def __init__(self, _interactiveController: IController):
        super().__init__()
        self._InteractiveController:IController = _interactiveController
        self._MainUserInfoData:UserInfoDatas = UserInfoDatas('stock_info_list.npy', 'Update_date.npy')
        self._MainUserInfoData._Show_all_stock_info()
    
    @property
    def InteractiveController(self):
        if self._InteractiveController == None:
            raise
        return self._InteractiveController
    @InteractiveController.setter
    def InteractiveController(self,_interactiveController:IController):
        self._InteractiveController = _interactiveController

    @property
    def MainUserInfoData(self):
        if self._MainUserInfoData == None:
            raise
        return self._MainUserInfoData

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
        main_imge = GetStockData.All_imge(RecordMainParameter.startdate,
                                    RecordMainParameter.enddate,
                                    GetStockData.Month_index)
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
        if (RecordMainParameter.enddate.day == datetime.today().day):
            print("今天還沒過完無資資訊")
            return
        main_imge = GetStockData.All_imge(RecordMainParameter.startdate,
                                    RecordMainParameter.enddate,
                                    GetStockData.Yield_index)
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
        main_imge = GetStockData.All_imge(RecordMainParameter.startdate,
                                    RecordMainParameter.enddate,
                                    GetStockData.OM_index)
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
        main_imge = GetStockData.All_imge(RecordMainParameter.startdate,
                                    RecordMainParameter.enddate,
                                    GetStockData.OM_Growth_index)
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
        main_imge = GetStockData.All_imge(RecordMainParameter.startdate,
                                    RecordMainParameter.enddate,
                                    GetStockData.ROE_index)
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
        main_imge = GetStockData.All_imge(RecordMainParameter.startdate,
                                    RecordMainParameter.enddate,
                                    GetStockData.OCF_index)
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
        main_imge = GetStockData.All_imge(RecordMainParameter.startdate,
                                    RecordMainParameter.enddate,
                                    GetStockData.ICF_index)
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
        main_imge = GetStockData.All_imge(RecordMainParameter.startdate,
                                    RecordMainParameter.enddate,
                                    GetStockData.FreeCF_index)
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
        main_imge = GetStockData.All_imge(RecordMainParameter.startdate,
                                    RecordMainParameter.enddate,
                                    GetStockData.PCF_index)
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
        main_imge = GetStockData.All_imge(RecordMainParameter.startdate,
                                    RecordMainParameter.enddate,
                                    GetStockData.EPS_index)
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
        main_imge = GetStockData.All_imge(RecordMainParameter.startdate,
                                    RecordMainParameter.enddate,
                                    GetStockData.Debt_index)
        data_result = main_imge.get_Chart(RecordMainParameter.number)
        df.draw_RP(data_result,
                RecordMainParameter.number,
                main_imge._report._name,
                main_imge._report._name,
                'Debt Asset Ratio') 
    def ADL(self, RecordMainParameter: RecordMainParameter):
        """騰落指標"""
        if (RecordMainParameter.enddate.day == datetime.today().day):
            print("今天還沒過完無資資訊")
            return
        main_imge = GetStockData.All_imge(RecordMainParameter.startdate,
                                    RecordMainParameter.enddate,
                                    GetStockData.ADL_index)
        data_result = main_imge.get_Chart()
        df.draw_RP(data_result,
                0,
                main_imge._report._name,
                main_imge._report._name,
                'ADL')
    def ADLs(self, RecordMainParameter: RecordMainParameter):
        """騰落比例指標"""
        if (RecordMainParameter.enddate.day == datetime.today().day):
            print("今天還沒過完無資資訊")
            return
        main_imge = GetStockData.All_imge(RecordMainParameter.startdate,
                                    RecordMainParameter.enddate,
                                    GetStockData.ADLs_index)
        data_result = main_imge.get_Chart()
        df.draw_RP(data_result,
                0,
                main_imge._report._name,
                main_imge._report._name,
                'ADL')
    def MonthRevenueGrowth(self, RecordMainParameter: RecordMainParameter):
        if(RecordMainParameter.number == None):
            print('請輸入股票號碼')
            return
        if (RecordMainParameter.enddate.day == datetime.today().day):
            print("今天還沒過完無資資訊")
            return
        main_imge = GetStockData.All_imge(RecordMainParameter.startdate,
                                    RecordMainParameter.enddate,
                                    GetStockData.MR_Growth_index)
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
        main_imge = GetStockData.All_imge(RecordMainParameter.startdate,
                                    RecordMainParameter.enddate,
                                    GetStockData.SR_Growth_index)
        data_result = main_imge.get_Chart(RecordMainParameter.number)
        df.draw_RP(data_result,
                RecordMainParameter.number,
                main_imge._report._name,
                main_imge._report._name,
                'Season Revenue Growth') 