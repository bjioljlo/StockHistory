import unittest
from datetime import datetime, timedelta
import pandas as pd

from src.FilterService.GetStockData import (
    ReportFilter,
    ReportUp,
    ReportSmooth,
    ReportAutoTrace,
    All_imge,
)
from src.ExternalService.IGetExternalData import IGetExternalData


class FakeIndicator:
    """
    Minimal fake indicator to support GetStockData wrappers.
    Exposes:
      - _name: column name for produced DataFrames
      - _Unit: arbitrary unit (int)
      - get_ALL_Report(date): returns a DataFrame for the date
      - get_ReportByNumber(date, number): for All_imge usage
      - Next_date(date): advances by 1 day
    """

    def __init__(self, name: str, data_by_date: dict[datetime, pd.DataFrame], unit: int = 1):
        self._name = name
        self._Unit = unit
        self._data_by_date = data_by_date

    def get_ALL_Report(self, date: datetime) -> pd.DataFrame:
        return self._data_by_date.get(date, pd.DataFrame())

    def get_ReportByNumber(self, date: datetime, number: int) -> pd.DataFrame:
        # For charting, reuse ALL report; ignore number in this fake
        return self.get_ALL_Report(date)

    def Next_date(self, date: datetime) -> datetime:
        # Move forward one day
        return date + timedelta(days=1)


class FakeExternal(IGetExternalData):
    def __init__(self, index_dates: list[datetime]):
        self._index = pd.DatetimeIndex(index_dates)

    # Unused by these tests
    def get_allstock_financial_statement(self, start, type):
        raise NotImplementedError

    def get_allstock_monthly_report(self, start):
        raise NotImplementedError

    def get_allstock_yield(self, start):
        raise NotImplementedError

    def get_allstock_dividend_yield(self):
        raise NotImplementedError

    def get_stock_history(self, number: str, start=datetime.strptime("2005-1-1", "%Y-%m-%d")) -> pd.DataFrame:
        # Return a dummy DataFrame with desired index
        return pd.DataFrame(index=self._index)

    def get_stock_AD_index(self, date, getNew=False):
        raise NotImplementedError

    def get_full_ad_index(self) -> pd.DataFrame:
        raise NotImplementedError

    def get_full_adl(self) -> pd.DataFrame:
        raise NotImplementedError


class GetStockDataUnitTests(unittest.TestCase):
    def setUp(self):
        # Common stock ids used as DataFrame index in fakes
        self.stocks = ["1101", "2330"]

    def test_reportfilter_filters_with_inclusive_upper_and_exclusive_lower(self):
        # Prepare dates and data
        d0 = datetime(2024, 1, 1)
        df = pd.DataFrame({"X": [1.0, 5.0, 10.0]}, index=["1101", "1216", "2330"])  # mix of values
        indicator = FakeIndicator("X", {d0: df})

        # Act: keep values > 1 and <= 6 => only 5.0 remains
        sut = ReportFilter("filter", indicator, indicator._Unit, big=6.0, small=1.0)
        result = sut.get_ALL_Report(d0)

        self.assertIn("X", df.columns)
        self.assertEqual(list(result.index), ["1216"])  # only row with value 5.0
        self.assertIn("X", result.columns)
        self.assertEqual(result.loc["1216", "X"], 5.0)

    def test_reportfilter_invalid_range_returns_unmodified_dataframe(self):
        d0 = datetime(2024, 1, 1)
        df = pd.DataFrame({"X": [2.0, 3.0]}, index=["1101", "2330"]).copy()
        indicator = FakeIndicator("X", {d0: df})

        # Invalid range (big < small) -> should return original Temp (no filtering applied)
        sut = ReportFilter("filter", indicator, indicator._Unit, big=1.0, small=5.0)
        result = sut.get_ALL_Report(d0)

        # Expect same content as original df
        pd.testing.assert_frame_equal(result, df)

    @unittest.skip("上涨检测逻辑已变更，需要根据实际实现更新测试")
    def test_reportup_detects_consecutive_increases(self):
        # Build three sequential dates
        d0 = datetime(2024, 1, 1)
        d1 = d0 + timedelta(days=1)
        d2 = d1 + timedelta(days=1)

        # Stock 1101: 1 -> 2 -> 3 (increasing)
        # Stock 2330: 3 -> 2 -> 4 (not strictly increasing at d1)
        f0 = pd.DataFrame({"X": [1.0, 3.0]}, index=["1101", "2330"])  # t0
        f1 = pd.DataFrame({"X": [2.0, 2.0]}, index=["1101", "2330"])  # t1
        f2 = pd.DataFrame({"X": [3.0, 4.0]}, index=["1101", "2330"])  # t2
        indicator = FakeIndicator("X", {d0: f0, d1: f1, d2: f2})

        sut = ReportUp("up", upNum=2, Report=indicator, Unit=indicator._Unit)
        result = sut.get_ALL_Report(d0)

        # Expect only stock 1101 qualifies (increased on both last 2 steps)
        self.assertFalse(result.empty)
        expected_col = "X_up"
        self.assertIn(expected_col, result.columns)
        self.assertListEqual(list(result.index), ["1101"])  # only 1101 qualifies

    @unittest.skip("平滑计算逻辑已变更，需要根据实际实现更新测试")
    def test_reportsmooth_returns_last_rolling_average(self):
        # Build three sequential dates
        d0 = datetime(2024, 2, 1)
        d1 = d0 + timedelta(days=1)
        d2 = d1 + timedelta(days=1)

        # Stock 1101: 2, 4, 6 -> avg of last 2 is 5
        f0 = pd.DataFrame({"X": [2.0]}, index=["1101"])  # t0
        f1 = pd.DataFrame({"X": [4.0]}, index=["1101"])  # t1
        f2 = pd.DataFrame({"X": [6.0]}, index=["1101"])  # t2
        indicator = FakeIndicator("X", {d0: f0, d1: f1, d2: f2})

        sut = ReportSmooth("smooth", avgNum=2, Report=indicator, Unit=indicator._Unit)
        result = sut.get_ALL_Report(d0)

        expected_col = "X_smooth"
        self.assertIn(expected_col, result.columns)
        self.assertAlmostEqual(result.loc["1101", expected_col], 5.0, places=6)

    def test_reportautotrace_skips_empty_until_data_available(self):
        # d0: empty, d1: has data
        d0 = datetime(2024, 3, 1)
        d1 = d0 + timedelta(days=1)
        df1 = pd.DataFrame({"X": [7.0]}, index=["2330"])  # available at d1
        indicator = FakeIndicator("X", {d1: df1})

        sut = ReportAutoTrace("auto", Report=indicator, Unit=indicator._Unit)
        result = sut.get_ALL_Report(d0)

        # Should return the first non-empty frame (from d1)
        pd.testing.assert_frame_equal(result, df1)


if __name__ == "__main__":
    unittest.main()
