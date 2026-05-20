"""
單元測試：歷史ROE、營業利益率、營業利益成長率按鈕功能

測試目標：
1. button_getROE → roe_ratio() → 使用 ROE_Indicator 計算 ROE
2. button_getOperating_Margin → operating_margin() → 從 PLA 報表取營業利益率
3. button_Operating_Margin_Ratio → operating_margin_ratio() → 使用 OM_Growth_Indicator 計算成長率
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
import pandas as pd

from src.Common.Parameter import RecordMainParameter
from src.Model.Model_main import Model_main


@pytest.fixture
def mock_services():
    """建立 Mock 服務"""
    schedule = Mock()
    draw_figur = Mock()
    external_data = Mock()
    season_factory = Mock()
    month_factory = Mock()
    day_factory = Mock()
    dividend_yield_factory = Mock()
    adl_factory = Mock()

    # 設定指標索引
    season_factory.OM_index = 10
    season_factory.OM_Growth_index = 11
    season_factory.ROE_index = 12
    season_factory.OCF_index = 13
    season_factory.ICF_index = 14
    season_factory.FreeCF_index = 15
    season_factory.EPS_index = 16
    season_factory.Debt_index = 17
    season_factory.SR_Growth_index = 18

    month_factory.Month_index = 0
    month_factory.MR_Growth_index = 1

    day_factory.PCF_index = 3

    dividend_yield_factory.Yield_index = 2

    adl_factory.ADL_index = 20
    adl_factory.ADLs_index = 21

    return {
        "schedule": schedule,
        "draw_figur": draw_figur,
        "external_data": external_data,
        "season_factory": season_factory,
        "month_factory": month_factory,
        "day_factory": day_factory,
        "dividend_yield_factory": dividend_yield_factory,
        "adl_factory": adl_factory,
    }


@pytest.fixture
def record_param():
    """建立 RecordMainParameter 實例"""
    param = RecordMainParameter()
    param.number = 2330
    param.startdate = datetime(2024, 1, 1)
    param.enddate = datetime(2024, 6, 30)
    return param


def create_model(mock_services):
    """建立 Model_main 實例"""
    return Model_main(
        schedule=mock_services["schedule"],
        draw_figur_service=mock_services["draw_figur"],
        external_data_service=mock_services["external_data"],
        season_report_factory=mock_services["season_factory"],
        month_report_factory=mock_services["month_factory"],
        day_report_factory=mock_services["day_factory"],
        dividend_yield_report_factory=mock_services["dividend_yield_factory"],
        adl_report_factory=mock_services["adl_factory"],
    )


class TestOperatingMarginButton:
    """測試營業利益率按鈕"""

    def test_operating_margin_calls_create_chart_with_correct_index(self, mock_services, record_param):
        """測試 operating_margin 使用正確的 OM_index"""
        model = create_model(mock_services)
        model._create_and_draw_chart = Mock(return_value=pd.DataFrame())

        model.operating_margin(record_param)

        model._create_and_draw_chart.assert_called_once_with(
            record_param,
            mock_services["season_factory"].OM_index,
            "Operating Margin Ratio",
        )


class TestOperatingMarginRatioButton:
    """測試營業利益成長率按鈕"""

    def test_operating_margin_ratio_calls_create_chart_with_correct_index(self, mock_services, record_param):
        """測試 operating_margin_ratio 使用正確的 OM_Growth_index"""
        model = create_model(mock_services)
        model._create_and_draw_chart = Mock(return_value=pd.DataFrame())

        model.operating_margin_ratio(record_param)

        model._create_and_draw_chart.assert_called_once_with(
            record_param,
            mock_services["season_factory"].OM_Growth_index,
            "Operating Margin Growth Up (season by season)(%)",
        )


class TestROEButton:
    """測試歷史ROE按鈕"""

    def test_roe_ratio_calls_create_chart_with_correct_index(self, mock_services, record_param):
        """測試 roe_ratio 使用正確的 ROE_index"""
        model = create_model(mock_services)
        model._create_and_draw_chart = Mock(return_value=pd.DataFrame())

        model.roe_ratio(record_param)

        model._create_and_draw_chart.assert_called_once_with(
            record_param,
            mock_services["season_factory"].ROE_index,
            "Return On Equity Ratio(ROE)",
        )


class TestCreateAndDrawChart:
    """測試 _create_and_draw_chart 方法"""

    def test_om_index_sets_fs_type_to_pla(self, mock_services, record_param):
        """測試 OM_index 時設定 _FS_type = PLA"""
        model = create_model(mock_services)
        mock_season_factory = mock_services["season_factory"]

        # Mock get_ReportByNumber to return valid data
        mock_data = pd.DataFrame(
            {"operating_margin": [25.5, 26.3], "gross_margin": [52.0, 53.0]},
            index=pd.Index(["2330", "2330"], name="symbol")
        )
        mock_season_factory.get_ReportByNumber = Mock(return_value=mock_data)

        model._create_and_draw_chart(
            record_param,
            mock_services["season_factory"].OM_index,
            "Operating Margin Ratio",
        )

        # 確認 _FS_type 被設定為 PLA
        assert mock_season_factory._FS_type.value == "profit-and-loss-analysis-summary"

    def test_om_growth_index_uses_get_indicator_data(self, mock_services, record_param):
        """測試 OM_Growth_index 使用 _get_indicator_data"""
        model = create_model(mock_services)
        model._get_indicator_data = Mock(return_value=pd.DataFrame({"OM_Growth": [15.5]}, index=["2330"]))

        result = model._create_and_draw_chart(
            record_param,
            mock_services["season_factory"].OM_Growth_index,
            "Operating Margin Growth Up (season by season)(%)",
        )

        model._get_indicator_data.assert_called_once_with(
            record_param, mock_services["season_factory"].OM_Growth_index
        )

    def test_roe_index_uses_get_indicator_data(self, mock_services, record_param):
        """測試 ROE_index 使用 _get_indicator_data"""
        model = create_model(mock_services)
        model._get_indicator_data = Mock(return_value=pd.DataFrame({"ROE": [18.5]}, index=["2330"]))

        result = model._create_and_draw_chart(
            record_param,
            mock_services["season_factory"].ROE_index,
            "Return On Equity Ratio(ROE)",
        )

        model._get_indicator_data.assert_called_once_with(
            record_param, mock_services["season_factory"].ROE_index
        )


class TestGetIndicatorData:
    """測試 _get_indicator_data 方法"""

    def test_om_growth_returns_indicator_data(self, mock_services, record_param):
        """測試 OM_Growth_index 返回正確的衍生指標數據"""
        model = create_model(mock_services)

        # Mock OM_Growth_Indicator (imported inside _get_indicator_data function)
        with patch("src.FilterService.StockReportHistory.OM_Growth_Indicator") as mock_indicator_cls:
            mock_indicator = Mock()
            mock_indicator.get_ReportByNumber = Mock(
                return_value=pd.DataFrame({"OM_Growth": [15.5]}, index=["2330"])
            )
            mock_indicator_cls.return_value = mock_indicator

            result = model._get_indicator_data(record_param, mock_services["season_factory"].OM_Growth_index)

            mock_indicator_cls.assert_called_once_with("OM_Growth", mock_services["season_factory"])
            mock_indicator.get_ReportByNumber.assert_called_once_with(
                record_param.startdate, record_param.number, end_date=record_param.enddate
            )
            assert result is not None
            assert "OM_Growth" in result.columns

    def test_roe_returns_indicator_data(self, mock_services, record_param):
        """測試 ROE_index 返回正確的衍生指標數據"""
        model = create_model(mock_services)

        # Mock ROE_Indicator (imported inside _get_indicator_data function)
        with patch("src.FilterService.StockReportHistory.ROE_Indicator") as mock_indicator_cls:
            mock_indicator = Mock()
            mock_indicator.get_ReportByNumber = Mock(
                return_value=pd.DataFrame({"ROE": [18.5]}, index=["2330"])
            )
            mock_indicator_cls.return_value = mock_indicator

            result = model._get_indicator_data(record_param, mock_services["season_factory"].ROE_index)

            # 驗證 ROE_Indicator 被建立
            mock_indicator_cls.assert_called_once()
            args, kwargs = mock_indicator_cls.call_args
            assert args[0] == "ROE"
            assert mock_indicator.get_ReportByNumber.called
            assert result is not None
            assert "ROE" in result.columns

    def test_unknown_index_returns_none(self, mock_services, record_param):
        """測試未知索引返回 None"""
        model = create_model(mock_services)
        result = model._get_indicator_data(record_param, 999)
        assert result is None
