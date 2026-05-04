from datetime import datetime

from src.Common import Tools
from src.DrawFigur import DrawFigur
from src.FilterService.StockReportHistory import Season_Report, SeasonReportFactory, MonthReportFactory, DayReportFactory, ADLReportFactory
from src.Model.Model import TModel
from src.Common.Parameter import RecordMainParameter
from src.ScheduleService import ScheduleService
from src.StockInfos import UserInfoDatas
from src.Common import InfomationType as info

from src.ExternalService.IGetExternalData import IGetExternalData


class Model_main(TModel):
    def __init__(self, schedule: ScheduleService, draw_figur_service: DrawFigur,
                 external_data_service: IGetExternalData,
                 season_report_factory: SeasonReportFactory,
                 month_report_factory: MonthReportFactory,
                 day_report_factory: DayReportFactory,
                 adl_report_factory: ADLReportFactory) -> None:
        super().__init__()
        self._main_user_info_data: UserInfoDatas = UserInfoDatas(
            "stock_info_list.npy", "Update_date.npy", "TW_Update_date.npy", "US_Update_date.npy"
        )
        self._main_user_info_data._Show_all_stock_info()
        self._schedule_service = schedule
        self._draw_figur_service = draw_figur_service
        self._external_data_service = external_data_service
        self._season_report_factory = season_report_factory
        self._month_report_factory = month_report_factory
        self._day_report_factory = day_report_factory
        self._adl_report_factory = adl_report_factory

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
        # 驗證參數
        if record_parameter is None:
            print("錯誤：參數對象為空")
            return None

        if stock_number_required and record_parameter.number is None:
            print("請輸入股票號碼")
            return None

        if record_parameter.enddate is None:
            print("錯誤：結束日期未設定")
            return None

        if record_parameter.startdate is None:
            print("錯誤：開始日期未設定")
            return None

        # 月營收的日期驗證已經在各自方法 (month_rp, month_revenue_growth) 中做過了
        # 這邊只需要針對其他報表類型做日期檢查
        if report_index != self._month_report_factory.Month_index and \
           report_index != self._month_report_factory.MR_Growth_index and \
           record_parameter.enddate.day == datetime.today().day:
            print("今天還沒過完無資資訊")
            return None

        # 直接從 ReportFactory 取得數據，不再使用 ChartDataGenerator
        report = None
        showClumn = 0

        # 根據指標索引取得對應的報表物件
        if report_index == self._month_report_factory.Month_index:
            report = self._month_report_factory
            showClumn = 3
        elif report_index == self._month_report_factory.MR_Growth_index:
            report = self._month_report_factory
            showClumn = 5  # ✅ 直接使用SQL中已存在的月營收成長率欄位，不需要現場計算
        elif report_index == self._day_report_factory.Yield_index:
            report = self._day_report_factory
        elif report_index == self._day_report_factory.PCF_index:
            report = self._day_report_factory
        elif report_index == self._season_report_factory.OM_index:
            report = self._season_report_factory
        elif report_index == self._season_report_factory.OM_Growth_index:
            report = self._season_report_factory
        elif report_index == self._season_report_factory.ROE_index:
            report = self._season_report_factory
        elif report_index == self._season_report_factory.OCF_index:
            report: Season_Report = self._season_report_factory
            report._FS_type = info.FS_type.SCF
            showClumn = 16
        elif report_index == self._season_report_factory.ICF_index:
            report: Season_Report = self._season_report_factory
            report._FS_type = info.FS_type.SCF
            showClumn = 17
        elif report_index == self._season_report_factory.FreeCF_index:
            report = self._season_report_factory
        elif report_index == self._season_report_factory.EPS_index:
            report = self._season_report_factory
        elif report_index == self._season_report_factory.Debt_index:
            report = self._season_report_factory
        elif report_index == self._season_report_factory.SR_Growth_index:
            report = self._season_report_factory
        elif report_index == self._adl_report_factory.ADL_index:
            report = self._adl_report_factory
        elif report_index == self._adl_report_factory.ADLs_index:
            report = self._adl_report_factory

        if report is None:
            print(f"錯誤：無法識別的報表索引 {report_index}")
            return None

        # 取得數據
        if stock_number_required and record_parameter.number is not None:
            data_result = report.get_ReportByNumber(record_parameter.startdate, record_parameter.number, record_parameter.enddate)
            stock_number_for_draw = record_parameter.number
        else:
            data_result = report.get_ALL_Report(record_parameter.startdate, record_parameter.enddate)
            stock_number_for_draw = 0

        # 繪製圖表
        if draw and data_result is not None and not data_result.empty:
            # 取得第一個欄位名稱做為繪圖欄位
            column_name = data_result.columns[showClumn] if len(data_result.columns) > 0 else data_result.index.name
            self._draw_figur_service.draw_RP(
                data_result,
                stock_number_for_draw,
                column_name,
                report._name,
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
            self._month_report_factory.Month_index,
            "Monthly Revenue(UNIT-->NTD:1000,000)",
        )

    def dividend_yield(self, record_main_parameter: RecordMainParameter):
        """某股票殖利率曲線"""
        self._create_and_draw_chart(
            record_main_parameter,
            self._day_report_factory.Yield_index,
            "Dividend yield",
        )

    def operating_margin(self, record_main_parameter: RecordMainParameter):
        """某股票營業利益率曲線"""
        self._create_and_draw_chart(
            record_main_parameter,
            self._season_report_factory.OM_index,
            "Operating Margin Ratio",
        )

    def operating_margin_ratio(self, record_main_parameter: RecordMainParameter):
        """#某股票營業利益成長率曲線"""
        self._create_and_draw_chart(
            record_main_parameter,
            self._season_report_factory.OM_Growth_index,
            "Operating Margin Growth Up (season by season)(%)",
        )

    def roe_ratio(self, record_main_parameter: RecordMainParameter):
        """#某股票ROE曲線"""
        self._create_and_draw_chart(
            record_main_parameter,
            self._season_report_factory.ROE_index,
            "Return On Equity Ratio(ROE)",
        )

    def ocf(self, record_main_parameter: RecordMainParameter):
        """某股票營業現金流"""
        self._create_and_draw_chart(
            record_main_parameter,
            self._season_report_factory.OCF_index,
            "Operating cash flow",
        )

    def icf(self, record_main_parameter: RecordMainParameter):
        """某股票投資現金流"""
        self._create_and_draw_chart(
            record_main_parameter,
            self._season_report_factory.ICF_index,
            "Investment cash flow",
        )

    def free_scf(self, record_main_parameter: RecordMainParameter):
        """某股票自由現金流"""
        self._create_and_draw_chart(
            record_main_parameter,
            self._season_report_factory.FreeCF_index,
            "Free cash flow",
        )

    def pcf(self, record_main_parameter: RecordMainParameter):
        """某股票股價現金流量比"""
        self._create_and_draw_chart(
            record_main_parameter,
            self._day_report_factory.PCF_index,
            "Price to Cash Flow Ratio(P/CF)",
        )

    def eps(self, record_main_parameter: RecordMainParameter):
        """某股票eps"""
        self._create_and_draw_chart(
            record_main_parameter,
            self._season_report_factory.EPS_index,
            "Earnings Per Share(EPS)",
        )

    def debt_ratio(self, record_main_parameter: RecordMainParameter):
        """某股票資產負債比率"""
        self._create_and_draw_chart(
            record_main_parameter,
            self._season_report_factory.Debt_index,
            "Debt Asset Ratio",
        )

    def adl(self, record_main_parameter: RecordMainParameter):
        """騰落指標"""
        from src.FilterService.StockReportHistory import ADL_Indicator

        # Create ADL Indicator which calculates the actual cumulative ADL (not just raw Ad_index)
        adl_indicator = ADL_Indicator("ADL", self._adl_report_factory)

        # Calculate full ADL history
        if adl_indicator._adl_data is None:
            adl_indicator._calculate_adl()

        # Return full date range between startdate and enddate (not just single day)
        if adl_indicator._adl_data.empty:
            return adl_indicator._adl_data

        # Filter data for the requested date range
        data_result = adl_indicator._adl_data[
            (adl_indicator._adl_data.index >= record_main_parameter.startdate) &
            (adl_indicator._adl_data.index <= record_main_parameter.enddate)
        ].copy()

        return data_result

    def adls(self, record_main_parameter: RecordMainParameter):
        """騰落比例指標"""
        self._create_and_draw_chart(
            record_main_parameter,
            self._adl_report_factory.ADLs_index,
            "ADLs",
            stock_number_required=False,
        )

    def month_revenue_growth(self, record_main_parameter: RecordMainParameter):
        """月營收成長率"""
        self._create_and_draw_chart(
            record_main_parameter,
            self._month_report_factory.MR_Growth_index,
            "Month Revenue Growth",
        )

    def season_revenue_growth(self, record_main_parameter: RecordMainParameter):
        """季營收成長率"""
        self._create_and_draw_chart(
            record_main_parameter,
            self._season_report_factory.SR_Growth_index,
            "Season Revenue Growth",
        )

    def RunSchedule(self, progress_callback=None):
        self._schedule_service.RunUpdateInfoNow(self.main_user_info_data, progress_callback)

    def RunUpdateInfoNow_sp500(self, progress_callback=None):
        self._schedule_service.RunUpdateInfoNow_sp500(self.main_user_info_data, progress_callback)

    def RunSyncToMongo(self, progress_callback=None):
        self._schedule_service.RunSyncToMongo(progress_callback)

    def RunOtherSchedule(self, progress_callback=None):
        self._schedule_service.RunOtherSchedule(progress_callback)

    def StopThreadSchedule(self):
        self._schedule_service.StopThreadSchedule()
