from datetime import datetime

import Common.Tools as Tools
from DrawFigur import DrawFigur
from FilterService.GetStockData import ReportServices, All_imge
from Model.Model import TModel
from Common.Parameter import RecordMainParameter
from ScheduleService import ScheduleService
from StockInfos import UserInfoDatas

from ExternalService.IGetExternalData import IGetExternalData


class Model_main(TModel):
    def __init__(self, schedule: ScheduleService, draw_figur_service: DrawFigur, 
                    external_data_service: IGetExternalData, report_services: ReportServices) -> None:
        super().__init__()
        self._MainUserInfoData: UserInfoDatas = UserInfoDatas(
            "stock_info_list.npy", "Update_date.npy"
        )
        self._MainUserInfoData._Show_all_stock_info()
        self._schedule_service = schedule
        self._draw_figur_service = draw_figur_service
        self._external_data_service = external_data_service
        self._report_services = report_services

    @property
    def MainUserInfoData(self):
        if self._MainUserInfoData is None:
            raise
        return self._MainUserInfoData

    def monthRP(self, RecordMainParameter: RecordMainParameter):
        """某股票月營收曲線"""
        if RecordMainParameter.number is None:
            print("請輸入股票號碼")
            return
        if RecordMainParameter.enddate.day == datetime.today().day:
            print("今天還沒過完無資資訊")
            return
        if RecordMainParameter.enddate.month == datetime.today().month:
            print("本月還沒過完無資資訊")
            return
        if (
            RecordMainParameter.enddate.month
            == Tools.changeDateMonth(datetime.today(), -1).month
            and datetime.today().day < 15
        ):
            print("還沒15號沒有上個月的資料")
            return
        main_imge = All_imge(
            RecordMainParameter.startdate,
            RecordMainParameter.enddate,
            self._report_services.Month_index,
            self._external_data_service
        )
        data_result = main_imge.get_Chart(RecordMainParameter.number)
        self._draw_figur_service.draw_RP(
            data_result,
            RecordMainParameter.number,
            main_imge._report._name,
            main_imge._report._name,
            "Monthly Revenue(UNIT-->NTD:1000,000)",
        )

    def Dividend_yield(self, RecordMainParameter: RecordMainParameter):
        """某股票殖利率曲線"""
        if RecordMainParameter.number is None:
            print("請輸入股票號碼")
            return
        if RecordMainParameter.enddate.day == datetime.today().day:
            print("今天還沒過完無資資訊")
            return
        main_imge = All_imge(
            RecordMainParameter.startdate,
            RecordMainParameter.enddate,
            self._report_services.Yield_index,
            self._external_data_service
        )
        data_result = main_imge.get_Chart(RecordMainParameter.number)
        self._draw_figur_service.draw_RP(
            data_result,
            RecordMainParameter.number,
            main_imge._report._name,
            main_imge._report._name,
            "Dividend yield",
        )

    def Operating_Margin(self, RecordMainParameter: RecordMainParameter):
        """某股票營業利益率曲線"""
        if RecordMainParameter.number is None:
            print("請輸入股票號碼")
            return
        if RecordMainParameter.enddate.day == datetime.today().day:
            print("今天還沒過完無資資訊")
            return
        main_imge = All_imge(
            RecordMainParameter.startdate,
            RecordMainParameter.enddate,
            self._report_services.OM_index,
            self._external_data_service
        )
        data_result = main_imge.get_Chart(RecordMainParameter.number)
        self._draw_figur_service.draw_RP(
            data_result,
            RecordMainParameter.number,
            main_imge._report._name,
            main_imge._report._name,
            "Operating Margin Ratio",
        )

    def Operating_Margin_Ratio(self, RecordMainParameter: RecordMainParameter):
        """#某股票營業利益成長率曲線"""
        if RecordMainParameter.number is None:
            print("請輸入股票號碼")
            return
        if RecordMainParameter.enddate.day == datetime.today().day:
            print("今天還沒過完無資資訊")
            return
        main_imge = All_imge(
            RecordMainParameter.startdate,
            RecordMainParameter.enddate,
            self._report_services.OM_Growth_index,
            self._external_data_service
        )
        # 取得營業利益率成長率資料(與去年同季相比)
        data_result_up = main_imge.get_Chart(RecordMainParameter.number)
        self._draw_figur_service.draw_RP(
            data_result_up,
            RecordMainParameter.number,
            main_imge._report._name,
            main_imge._report._name,
            "Operating Margin Growth Up (season by season)(%)",
        )

    def ROE_Ratio(self, RecordMainParameter: RecordMainParameter):
        """#某股票ROE曲線"""
        if RecordMainParameter.number is None:
            print("請輸入股票號碼")
            return
        if RecordMainParameter.enddate.day == datetime.today().day:
            print("今天還沒過完無資資訊")
            return
        # 取得ROE資料
        main_imge = All_imge(
            RecordMainParameter.startdate,
            RecordMainParameter.enddate,
            self._report_services.ROE_index,
            self._external_data_service
        )
        data_result_up = main_imge.get_Chart(RecordMainParameter.number)
        self._draw_figur_service.draw_RP(
            data_result_up,
            RecordMainParameter.number,
            main_imge._report._name,
            main_imge._report._name,
            "Return On Equity Ratio(ROE)",
        )

    def OCF(self, RecordMainParameter: RecordMainParameter):
        """某股票營業現金流"""
        if RecordMainParameter.number is None:
            print("請輸入股票號碼")
            return
        if RecordMainParameter.enddate.day == datetime.today().day:
            print("今天還沒過完無資資訊")
            return
        main_imge = All_imge(
            RecordMainParameter.startdate,
            RecordMainParameter.enddate,
            self._report_services.OCF_index,
            self._external_data_service
        )
        data_result = main_imge.get_Chart(RecordMainParameter.number)
        self._draw_figur_service.draw_RP(
            data_result,
            RecordMainParameter.number,
            main_imge._report._name,
            main_imge._report._name,
            "Operating cash flow",
        )

    def ICF(self, RecordMainParameter: RecordMainParameter):
        """某股票投資現金流"""
        if RecordMainParameter.number is None:
            print("請輸入股票號碼")
            return
        if RecordMainParameter.enddate.day == datetime.today().day:
            print("今天還沒過完無資資訊")
            return
        main_imge = All_imge(
            RecordMainParameter.startdate,
            RecordMainParameter.enddate,
            self._report_services.ICF_index,
            self._external_data_service
        )
        data_result = main_imge.get_Chart(RecordMainParameter.number)
        self._draw_figur_service.draw_RP(
            data_result,
            RecordMainParameter.number,
            main_imge._report._name,
            main_imge._report._name,
            "Investment cash flow",
        )

    def FreeSCF(self, RecordMainParameter: RecordMainParameter):
        """某股票自由現金流"""
        if RecordMainParameter.number is None:
            print("請輸入股票號碼")
            return
        if RecordMainParameter.enddate.day == datetime.today().day:
            print("今天還沒過完無資資訊")
            return
        main_imge = All_imge(
            RecordMainParameter.startdate,
            RecordMainParameter.enddate,
            self._report_services.FreeCF_index,
            self._external_data_service
        )
        data_result = main_imge.get_Chart(RecordMainParameter.number)
        self._draw_figur_service.draw_RP(
            data_result,
            RecordMainParameter.number,
            main_imge._report._name,
            main_imge._report._name,
            "Free cash flow",
        )

    def PCF(self, RecordMainParameter: RecordMainParameter):
        """某股票股價現金流量比"""
        if RecordMainParameter.number is None:
            print("請輸入股票號碼")
            return
        if RecordMainParameter.enddate.day == datetime.today().day:
            print("今天還沒過完無資資訊")
            return
        main_imge = All_imge(
            RecordMainParameter.startdate,
            RecordMainParameter.enddate,
            self._report_services.PCF_index,
            self._external_data_service
        )
        data_result = main_imge.get_Chart(RecordMainParameter.number)
        self._draw_figur_service.draw_RP(
            data_result,
            RecordMainParameter.number,
            main_imge._report._name,
            main_imge._report._name,
            "Price to Cash Flow Ratio(P/CF)",
        )

    def EPS(self, RecordMainParameter: RecordMainParameter):
        """某股票eps"""
        if RecordMainParameter.number is None:
            print("請輸入股票號碼")
            return
        if RecordMainParameter.enddate.day == datetime.today().day:
            print("今天還沒過完無資資訊")
            return
        main_imge = All_imge(
            RecordMainParameter.startdate,
            RecordMainParameter.enddate,
            self._report_services.EPS_index,
            self._external_data_service
        )
        data_result = main_imge.get_Chart(RecordMainParameter.number)
        self._draw_figur_service.draw_RP(
            data_result,
            RecordMainParameter.number,
            main_imge._report._name,
            main_imge._report._name,
            "Earnings Per Share(EPS)",
        )

    def DebtRatio(self, RecordMainParameter: RecordMainParameter):
        """某股票資產負債比率"""
        if RecordMainParameter.number is None:
            print("請輸入股票號碼")
            return
        if RecordMainParameter.enddate.day == datetime.today().day:
            print("今天還沒過完無資資訊")
            return
        main_imge = All_imge(
            RecordMainParameter.startdate,
            RecordMainParameter.enddate,
            self._report_services.Debt_index,
            self._external_data_service
        )
        data_result = main_imge.get_Chart(RecordMainParameter.number)
        self._draw_figur_service.draw_RP(
            data_result,
            RecordMainParameter.number,
            main_imge._report._name,
            main_imge._report._name,
            "Debt Asset Ratio",
        )

    def ADL(self, RecordMainParameter: RecordMainParameter):
        """騰落指標"""
        if RecordMainParameter.enddate.day == datetime.today().day:
            print("今天還沒過完無資資訊")
            return
        main_imge = All_imge(
            RecordMainParameter.startdate,
            RecordMainParameter.enddate,
            self._report_services.ADL_index,
            self._external_data_service
        )
        data_result = main_imge.get_Chart()
        return data_result

    def ADLs(self, RecordMainParameter: RecordMainParameter):
        """騰落比例指標"""
        if RecordMainParameter.enddate.day == datetime.today().day:
            print("今天還沒過完無資資訊")
            return
        main_imge = All_imge(
            RecordMainParameter.startdate,
            RecordMainParameter.enddate,
            self._report_services.ADLs_index,
            self._external_data_service
        )
        data_result = main_imge.get_Chart()
        self._draw_figur_service.draw_RP(
            data_result, 0, main_imge._report._name, main_imge._report._name, "ADLs"
        )

    def MonthRevenueGrowth(self, RecordMainParameter: RecordMainParameter):
        if RecordMainParameter.number is None:
            print("請輸入股票號碼")
            return
        if RecordMainParameter.enddate.day == datetime.today().day:
            print("今天還沒過完無資資訊")
            return
        main_imge = All_imge(
            RecordMainParameter.startdate,
            RecordMainParameter.enddate,
            self._report_services.MR_Growth_index,
            self._external_data_service
        )
        data_result = main_imge.get_Chart(RecordMainParameter.number)
        self._draw_figur_service.draw_RP(
            data_result,
            RecordMainParameter.number,
            main_imge._report._name,
            main_imge._report._name,
            "Month Revenue Growth",
        )

    def SeasonRevenueGrowth(self, RecordMainParameter: RecordMainParameter):
        if RecordMainParameter.number is None:
            print("請輸入股票號碼")
            return
        if RecordMainParameter.enddate.day == datetime.today().day:
            print("今天還沒過完無資資訊")
            return
        main_imge = All_imge(
            RecordMainParameter.startdate,
            RecordMainParameter.enddate,
            self._report_services.SR_Growth_index,
            self._external_data_service
        )
        data_result = main_imge.get_Chart(RecordMainParameter.number)
        self._draw_figur_service.draw_RP(
            data_result,
            RecordMainParameter.number,
            main_imge._report._name,
            main_imge._report._name,
            "Season Revenue Growth",
        )

    def RunSchedule(self):
        self._schedule_service.RunUpdateInfoNow(self.MainUserInfoData)

    def RunOtherSchedule(self):
        self._schedule_service.RunOtherInfoNow()

    def StopThreadSchedule(self):
        self._schedule_service.StopThreadSchedule()