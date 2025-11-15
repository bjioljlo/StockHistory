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
        self._main_user_info_data: UserInfoDatas = UserInfoDatas(
            "stock_info_list.npy", "Update_date.npy"
        )
        self._main_user_info_data._Show_all_stock_info()
        self._schedule_service = schedule
        self._draw_figur_service = draw_figur_service
        self._external_data_service = external_data_service
        self._report_services = report_services

    @property
    def main_user_info_data(self):
        return self._main_user_info_data

    def _create_and_draw_chart(
        self,
        record_parameter: RecordMainParameter,
        report_index,
        chart_title: str,
        stock_number_required: bool = True,
        draw: bool = True,
    ):
        if stock_number_required and record_parameter.number is None:
            print("請輸入股票號碼")
            return None
        
        if record_parameter.enddate.day == datetime.today().day:
            print("今天還沒過完無資資訊")
            return None

        main_imge = All_imge(
            record_parameter.startdate,
            record_parameter.enddate,
            report_index,
            self._external_data_service,
        )

        if stock_number_required:
            data_result = main_imge.get_Chart(record_parameter.number)
            stock_number_for_draw = record_parameter.number
        else:
            data_result = main_imge.get_Chart()
            stock_number_for_draw = 0

        if draw and data_result is not None:
            self._draw_figur_service.draw_RP(
                data_result,
                stock_number_for_draw,
                main_imge._report._name,
                main_imge._report._name,
                chart_title,
            )
        
        return data_result

    def month_rp(self, record_main_parameter: RecordMainParameter):
        """某股票月營收曲線"""
        if record_main_parameter.number is None:
            print("請輸入股票號碼")
            return
        if record_main_parameter.enddate.month == datetime.today().month:
            print("本月還沒過完無資資訊")
            return
        if (
            record_main_parameter.enddate.month
            == Tools.changeDateMonth(datetime.today(), -1).month
            and datetime.today().day < 15
        ):
            print("還沒15號沒有上個月的資料")
            return
        
        self._create_and_draw_chart(
            record_main_parameter,
            self._report_services.Month_index,
            "Monthly Revenue(UNIT-->NTD:1000,000)",
        )

    def dividend_yield(self, record_main_parameter: RecordMainParameter):
        """某股票殖利率曲線"""
        self._create_and_draw_chart(
            record_main_parameter,
            self._report_services.Yield_index,
            "Dividend yield",
        )

    def operating_margin(self, record_main_parameter: RecordMainParameter):
        """某股票營業利益率曲線"""
        self._create_and_draw_chart(
            record_main_parameter,
            self._report_services.OM_index,
            "Operating Margin Ratio",
        )

    def operating_margin_ratio(self, record_main_parameter: RecordMainParameter):
        """#某股票營業利益成長率曲線"""
        self._create_and_draw_chart(
            record_main_parameter,
            self._report_services.OM_Growth_index,
            "Operating Margin Growth Up (season by season)(%)",
        )

    def roe_ratio(self, record_main_parameter: RecordMainParameter):
        """#某股票ROE曲線"""
        self._create_and_draw_chart(
            record_main_parameter,
            self._report_services.ROE_index,
            "Return On Equity Ratio(ROE)",
        )

    def ocf(self, record_main_parameter: RecordMainParameter):
        """某股票營業現金流"""
        self._create_and_draw_chart(
            record_main_parameter,
            self._report_services.OCF_index,
            "Operating cash flow",
        )

    def icf(self, record_main_parameter: RecordMainParameter):
        """某股票投資現金流"""
        self._create_and_draw_chart(
            record_main_parameter,
            self._report_services.ICF_index,
            "Investment cash flow",
        )

    def free_scf(self, record_main_parameter: RecordMainParameter):
        """某股票自由現金流"""
        self._create_and_draw_chart(
            record_main_parameter,
            self._report_services.FreeCF_index,
            "Free cash flow",
        )

    def pcf(self, record_main_parameter: RecordMainParameter):
        """某股票股價現金流量比"""
        self._create_and_draw_chart(
            record_main_parameter,
            self._report_services.PCF_index,
            "Price to Cash Flow Ratio(P/CF)",
        )

    def eps(self, record_main_parameter: RecordMainParameter):
        """某股票eps"""
        self._create_and_draw_chart(
            record_main_parameter,
            self._report_services.EPS_index,
            "Earnings Per Share(EPS)",
        )

    def debt_ratio(self, record_main_parameter: RecordMainParameter):
        """某股票資產負債比率"""
        self._create_and_draw_chart(
            record_main_parameter,
            self._report_services.Debt_index,
            "Debt Asset Ratio",
        )

    def adl(self, record_main_parameter: RecordMainParameter):
        """騰落指標"""
        return self._create_and_draw_chart(
            record_main_parameter,
            self._report_services.ADL_index,
            "",
            stock_number_required=False,
            draw=False,
        )

    def adls(self, record_main_parameter: RecordMainParameter):
        """騰落比例指標"""
        self._create_and_draw_chart(
            record_main_parameter,
            self._report_services.ADLs_index,
            "ADLs",
            stock_number_required=False,
        )

    def month_revenue_growth(self, record_main_parameter: RecordMainParameter):
        """月營收成長率"""
        self._create_and_draw_chart(
            record_main_parameter,
            self._report_services.MR_Growth_index,
            "Month Revenue Growth",
        )

    def season_revenue_growth(self, record_main_parameter: RecordMainParameter):
        """季營收成長率"""
        self._create_and_draw_chart(
            record_main_parameter,
            self._report_services.SR_Growth_index,
            "Season Revenue Growth",
        )

    def RunSchedule(self, progress_callback=None):
        self._schedule_service.RunUpdateInfoNow(self.main_user_info_data, progress_callback)
        
    def RunUpdateInfoNow_sp500(self, progress_callback=None):
        self._schedule_service.RunUpdateInfoNow_sp500(self.main_user_info_data, progress_callback)

    def RunSyncToMongo(self, progress_callback=None):
        self._schedule_service.RunSyncToMongo(progress_callback)

    def RunOtherSchedule(self, progress_callback=None):
        self._schedule_service.RunUpdateADLNow(progress_callback)

    def StopThreadSchedule(self):
        self._schedule_service.StopThreadSchedule()
