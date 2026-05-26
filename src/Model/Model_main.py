from datetime import datetime

from src.Common import Tools
from src.DrawFigur import DrawFigur
from src.FilterService.StockReportHistory import Season_Report, SeasonReportFactory, MonthReportFactory, DayReportFactory, DividendYieldReportFactory, ADLReportFactory
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
                 dividend_yield_report_factory: DividendYieldReportFactory,
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
        self._dividend_yield_report_factory = dividend_yield_report_factory
        self._adl_report_factory = adl_report_factory

        # 初始化報表索引到配置的映射
        self._init_report_config_map()

    @property
    def main_user_info_data(self):
        return self._main_user_info_data

    def _validate_record_parameter(self, record_parameter: RecordMainParameter, stock_number_required: bool = True) -> bool:
        """驗證 RecordMainParameter 的共用邏輯

        Args:
            record_parameter: 要驗證的參數
            stock_number_required: 是否需要股票號碼

        Returns:
            True 如果驗證通過，False 如果驗證失敗
        """
        if record_parameter is None:
            print("錯誤：參數對象為空")
            return False

        if stock_number_required and record_parameter.number is None:
            print("請輸入股票號碼")
            return False

        if record_parameter.enddate is None:
            print("錯誤：結束日期未設定")
            return False

        if record_parameter.startdate is None:
            print("錯誤：開始日期未設定")
            return False

        return True

    def _init_report_config_map(self):
        """初始化報表索引到配置的映射

        每個報表配置包含：
        - report_factory: 報表工廠物件
        - fs_type: 財務表類型（可選）
        - show_column: 繪圖欄位索引（預設 0）
        - skip_date_check: 是否跳過今日檢查（如月營收）
        """
        self._report_config_map = {
            self._month_report_factory.Month_index: {
                'factory': self._month_report_factory,
                'show_column': 3,
                'skip_date_check': True,
            },
            self._month_report_factory.MR_Growth_index: {
                'factory': self._month_report_factory,
                'show_column': 5,
                'skip_date_check': True,
            },
            self._dividend_yield_report_factory.Yield_index: {
                'factory': self._dividend_yield_report_factory,
                'show_column': 3,
            },
            self._day_report_factory.PCF_index: {
                'factory': self._day_report_factory,
                'show_column': 0,
            },
            self._season_report_factory.OM_index: {
                'factory': self._season_report_factory,
                'fs_type': info.FS_type.PLA,
                'show_column': 3,
            },
            self._season_report_factory.OM_Growth_index: {
                'factory': self._season_report_factory,
                'show_column': 0,
            },
            self._season_report_factory.ROE_index: {
                'factory': self._season_report_factory,
                'show_column': 0,
            },
            self._season_report_factory.OCF_index: {
                'factory': self._season_report_factory,
                'fs_type': info.FS_type.SCF,
                'show_column': 1,
            },
            self._season_report_factory.ICF_index: {
                'factory': self._season_report_factory,
                'fs_type': info.FS_type.SCF,
                'show_column': 2,
            },
            self._season_report_factory.FreeCF_index: {
                'factory': self._season_report_factory,
                'fs_type': info.FS_type.SCF,
                'show_column': 0,
            },
            self._season_report_factory.EPS_index: {
                'factory': self._season_report_factory,
                'fs_type': info.FS_type.CPL,
                'show_column': 2,
                'skip_date_check': True,
            },
            self._season_report_factory.Debt_index: {
                'factory': self._season_report_factory,
                'show_column': 0,
            },
            self._season_report_factory.SR_Growth_index: {
                'factory': self._season_report_factory,
                'show_column': 0,
            },
            self._adl_report_factory.ADL_index: {
                'factory': self._adl_report_factory,
                'show_column': 0,
            },
            self._adl_report_factory.ADLs_index: {
                'factory': self._adl_report_factory,
                'show_column': 0,
            },
        }

    def _get_report_config(self, report_index):
        """取得指定索引的報表配置

        Args:
            report_index: 報表索引

        Returns:
            報表配置字典，或 None 如果索引不存在
        """
        return self._report_config_map.get(report_index)

    def _validate_date_for_chart(self, record_parameter: RecordMainParameter, report_index) -> bool:
        """檢查圖表特殊日期驗證

        某些報表（如月營收）不需要檢查今日是否過完

        Args:
            record_parameter: 記錄參數
            report_index: 報表索引

        Returns:
            True 如果日期有效，False 如果日期無效
        """
        config = self._get_report_config(report_index)

        # 若配置指定跳過日期檢查或配置不存在，則通過
        if config is None or config.get('skip_date_check', False):
            return True

        # 檢查今日是否過完
        if record_parameter.enddate.day == datetime.today().day:
            print("今天還沒過完無資資訊")
            return False

        return True

    def _create_and_draw_chart(
        self,
        record_parameter: RecordMainParameter,
        report_index,
        chart_title: str,
        stock_number_required: bool = True,
        draw: bool = True,
    ):
        """通用的圖表建立與繪製方法

        Args:
            record_parameter: 記錄參數
            report_index: 報表索引
            chart_title: 圖表標題
            stock_number_required: 是否需要股票號碼
            draw: 是否繪製圖表

        Returns:
            資料 DataFrame，或 None 如果失敗
        """
        # Step 1: 基本驗證
        if not self._validate_record_parameter(record_parameter, stock_number_required):
            return None

        # Step 2: 日期驗證
        if not self._validate_date_for_chart(record_parameter, report_index):
            return None

        # 直接從 ReportFactory 取得數據，不再使用 ChartDataGenerator
        report = None
        showClumn = 0
        is_indicator = False  # 是否為衍生指標（需透過 Indicator 類計算）

        # 根據指標索引取得對應的報表物件
        if report_index == self._month_report_factory.Month_index:
            report = self._month_report_factory
            showClumn = 3
        elif report_index == self._month_report_factory.MR_Growth_index:
            report = self._month_report_factory
            showClumn = 5
        elif report_index == self._dividend_yield_report_factory.Yield_index:
            report = self._dividend_yield_report_factory
            showClumn = 3
        elif report_index == self._day_report_factory.PCF_index:
            report = self._day_report_factory
        elif report_index == self._season_report_factory.OM_index:
            # 營業利益率：從 PLA 報表中取出營業利益率(operating_margin)欄位
            report = self._season_report_factory
            report._FS_type = info.FS_type.PLA
            showClumn = 3  # operating_margin 在 PLA 資料中的欄位索引 (0:company_name, 1:revenue, 2:gross_margin, 3:operating_margin)
        elif report_index == self._season_report_factory.OM_Growth_index:
            # 營業利益成長率：使用 OM_Growth_Indicator 計算
            is_indicator = True
        elif report_index == self._season_report_factory.ROE_index:
            # 歷史ROE：使用 ROE_Indicator 計算
            is_indicator = True
        elif report_index == self._season_report_factory.OCF_index:
            report: Season_Report = self._season_report_factory
            report._FS_type = info.FS_type.SCF
            showClumn = 1
        elif report_index == self._season_report_factory.ICF_index:
            report: Season_Report = self._season_report_factory
            report._FS_type = info.FS_type.SCF
            showClumn = 2
        elif report_index == self._season_report_factory.FreeCF_index:
            report = self._season_report_factory
            report._FS_type = info.FS_type.SCF
        elif report_index == self._season_report_factory.EPS_index:
            report = self._season_report_factory
            report._FS_type = info.FS_type.CPL
            showClumn = 2  # eps 在 CPL 資料中的欄位索引 (0:company_name, 1:net_income, 2:eps)
        elif report_index == self._season_report_factory.Debt_index:
            from src.FilterService.StockReportHistory import Debt_Indicator
            report = self._season_report_factory
            report._FS_type = info.FS_type.BS
            report = Debt_Indicator("Debt Asset Ratio", report)
            showClumn = 0
        elif report_index == self._season_report_factory.SR_Growth_index:
            from src.FilterService.StockReportHistory import SR_Growth_Indicator
            report = self._season_report_factory
            report._FS_type = info.FS_type.PLA
            report = SR_Growth_Indicator("Season Revenue Growth (year by year)(%)", report)
            showClumn = 0
        elif report_index == self._adl_report_factory.ADL_index:
            report = self._adl_report_factory
        elif report_index == self._adl_report_factory.ADLs_index:
            report = self._adl_report_factory

        # 處理衍生指標（ROE、營業利益成長率等）
        if is_indicator and stock_number_required and record_parameter.number is not None:
            data_result = self._get_indicator_data(record_parameter, report_index)
            stock_number_for_draw = record_parameter.number
            if draw and data_result is not None and not data_result.empty:
                column_name = data_result.columns[0] if len(data_result.columns) > 0 else data_result.index.name
                self._draw_figur_service.draw_RP(
                    data_result,
                    stock_number_for_draw,
                    column_name,
                    column_name,
                    chart_title,
                )
            return data_result

        if report is None:
            print(f"錯誤：無法識別的報表索引 {report_index}")
            return None

        # 取得數據
        if stock_number_required and record_parameter.number is not None:
            data_result = report.get_ReportByNumber(
                record_parameter.startdate,
                record_parameter.number,
                record_parameter.enddate
            )
            stock_number_for_draw = record_parameter.number
        else:
            data_result = report.get_ALL_Report(
                record_parameter.startdate,
                record_parameter.enddate
            )
            stock_number_for_draw = 0

        # Step 6: 繪製圖表
        if draw and data_result is not None and not data_result.empty:
            # 取得第一個欄位名稱做為繪圖欄位
            column_name = data_result.columns[showClumn] if len(data_result.columns) > 0 and showClumn < len(data_result.columns) else (
                data_result.columns[0] if len(data_result.columns) > 0 else data_result.index.name
            )
            self._draw_figur_service.draw_RP(
                data_result,
                stock_number_for_draw,
                column_name,
                report._name,
                chart_title,
            )

        return data_result

    def _get_indicator_data(self, record_parameter: RecordMainParameter, report_index):
        """
        使用 Indicator 類計算衍生指標數據
        """
        from src.FilterService.StockReportHistory import OM_Growth_Indicator, ROE_Indicator

        if report_index == self._season_report_factory.OM_Growth_index:
            # 營業利益成長率 = (本季營業利益率 - 去年同期營業利益率) / 去年同期營業利益率 * 100
            indicator = OM_Growth_Indicator("OM_Growth", self._season_report_factory)
            # 設定正確的報表類型為 PLA
            self._season_report_factory._FS_type = info.FS_type.PLA
            return indicator.get_ReportByNumber(
                record_parameter.startdate,
                record_parameter.number,
                end_date=record_parameter.enddate
            )

        elif report_index == self._season_report_factory.ROE_index:
            # ROE = 本期綜合損益總額 / 權益總額 * 100
            cpl_report = Season_Report(
                info.FS_type.CPL.value, 3, self._external_data_service, info.FS_type.CPL
            )
            bs_report = Season_Report(
                info.FS_type.BS.value, 3, self._external_data_service, info.FS_type.BS
            )
            indicator = ROE_Indicator("ROE", cpl_report, bs_report)
            return indicator.get_ReportByNumber(
                record_parameter.startdate,
                record_parameter.number,
                end_date=record_parameter.enddate
            )

        return None

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
            self._dividend_yield_report_factory.Yield_index,
            "Dividend yield",
        )

    def _find_column_by_keywords(self, data_result, keywords_list):
        """根據關鍵字列表在 DataFrame 中查找欄位

        Args:
            data_result: 要搜尋的 DataFrame
            keywords_list: 關鍵字列表，可以是字串或字串元組

        Returns:
            找到的欄位名稱，或 None
        """
        for col in data_result.columns:
            col_lower = str(col).lower().replace(' ', '_').replace('(', '').replace(')', '')
            for keyword in keywords_list if isinstance(keywords_list, (list, tuple)) else [keywords_list]:
                if isinstance(keyword, tuple):
                    keyword_lower = keyword[0].lower().replace(' ', '_').replace('(', '').replace(')', '')
                    if keyword_lower in col_lower or keyword[1] in str(col):
                        return col
                else:
                    if keyword.lower() in col_lower:
                        return col
        return None

    def operating_margin(self, record_main_parameter: RecordMainParameter):
        """某股票營業利益率曲線"""
        if not self._validate_record_parameter(record_main_parameter):
            return

        # 設定為 PLA 類型取得損益表資料
        report = self._season_report_factory
        report._FS_type = info.FS_type.PLA

        # 取得多個季度的 PLA 資料
        data_result = report.get_ReportByNumber(
            record_main_parameter.startdate,
            record_main_parameter.number,
            record_main_parameter.enddate,
        )

        if data_result is None or data_result.empty:
            print("無營業利益率資料")
            return

        # 直接查找營業利益率欄位（已存在於資料中）
        margin_col = self._find_column_by_keywords(
            data_result,
            [('operating_margin', '營業利益率')]
        )

        if margin_col is None:
            print(f"錯誤：PLA 資料缺少營業利益率欄位")
            print(f"可用欄位: {list(data_result.columns)}")
            return

        # 繪製圖表
        self._draw_figur_service.draw_RP(
            data_result,
            record_main_parameter.number,
            margin_col,
            self._season_report_factory._name,
            "Operating Margin Ratio",
        )

    def operating_margin_ratio(self, record_main_parameter: RecordMainParameter):
        """某股票營業利益成長率曲線 (季增率)"""
        if not self._validate_record_parameter(record_main_parameter):
            return

        # 設定為 PLA 類型取得損益表資料
        report = self._season_report_factory
        report._FS_type = info.FS_type.PLA

        # 取得多個季度的 PLA 資料
        data_result = report.get_ReportByNumber(
            record_main_parameter.startdate,
            record_main_parameter.number,
            record_main_parameter.enddate,
        )

        if data_result is None or data_result.empty:
            print("無營業利益成長率資料")
            return

        # 直接查找營業利益率欄位（已存在於資料中）
        margin_col = self._find_column_by_keywords(
            data_result,
            [('operating_margin', '營業利益率')]
        )

        if margin_col is None:
            print(f"錯誤：PLA 資料缺少營業利益率欄位")
            print(f"可用欄位: {list(data_result.columns)}")
            return

        # 計算營業利益率季增率 (本季 - 上季) / 上季
        data_result['operating_margin_growth'] = data_result[margin_col].pct_change() * 100

        # 繪製成長率圖表
        self._draw_figur_service.draw_RP(
            data_result,
            record_main_parameter.number,
            'operating_margin_growth',
            self._season_report_factory._name,
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
        if not self._validate_record_parameter(record_main_parameter):
            return

        report = self._season_report_factory
        report._FS_type = info.FS_type.SCF

        data_result = report.get_ReportByNumber(
            record_main_parameter.startdate,
            record_main_parameter.number,
            record_main_parameter.enddate,
        )

        if data_result is None or data_result.empty:
            print("無自由現金流資料")
            return

        # 查找營業現金流和投資現金流欄位
        operating_cash_flow_col = self._find_column_by_keywords(
            data_result,
            [('operating_cash_flow', '營業活動'), ('cash_flow_from_operations', '營業活動')]
        )
        investing_cash_flow_col = self._find_column_by_keywords(
            data_result,
            [('investing_cash_flow', '投資活動'), ('cash_flow_from_investing', '投資活動')]
        )

        if operating_cash_flow_col is None or investing_cash_flow_col is None:
            print("錯誤：SCF 資料缺少營業現金流或投資現金流欄位")
            print(f"可用欄位: {list(data_result.columns)}")
            return

        data_result["free_cash_flow"] = (
            data_result[operating_cash_flow_col] + data_result[investing_cash_flow_col]
        )

        self._draw_figur_service.draw_RP(
            data_result,
            record_main_parameter.number,
            "free_cash_flow",
            self._season_report_factory._name,
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
        if not self._validate_record_parameter(record_main_parameter, stock_number_required=False):
            return

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
