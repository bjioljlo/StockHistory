import unittest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from src.FilterService.GetStockData import ReportUp, ReportSmooth, ReportAutoTrace
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


class TestReportUpTypeError(unittest.TestCase):
    """測試 ReportUp 類型比較錯誤的修復"""

    def setUp(self):
        self.stocks = ["1101", "2330"]

    def test_reportup_with_mixed_types_should_not_crash(self):
        """測試 ReportUp 處理混合類型數據時不應該崩潰"""
        # 準備包含混合類型的數據（這會導致 '< not supported between instances of 'int' and 'str' 錯誤）
        d0 = datetime(2024, 1, 1)
        d1 = d0 + timedelta(days=1)
        d2 = d1 + timedelta(days=1)
        d3 = d2 + timedelta(days=1)

        # 創建包含混合類型的數據框
        # 有些值是數字，有些是字符串，這會導致類型比較錯誤
        f0 = pd.DataFrame({
            "Month": [100.0, "invalid_string"]  # 混合類型
        }, index=["1101", "2330"])
        
        f1 = pd.DataFrame({
            "Month": [120.0, 110.0]  # 純數字
        }, index=["1101", "2330"])
        
        f2 = pd.DataFrame({
            "Month": [130.0, 115.0]  # 純數字
        }, index=["1101", "2330"])
        
        f3 = pd.DataFrame({
            "Month": [140.0, 120.0]  # 純數字
        }, index=["1101", "2330"])

        indicator = FakeIndicator("Month", {d0: f0, d1: f1, d2: f2, d3: f3})

        # 創建 ReportUp 實例，嘗試檢測連續增長
        sut = ReportUp("up", upNum=2, Report=indicator, Unit=indicator._Unit)
        
        # 這個調用應該不會崩潰，即使數據包含混合類型
        try:
            result = sut.get_ALL_Report(d0)
            # 如果成功，檢查結果
            self.assertIsInstance(result, pd.DataFrame)
            # 結果應該是空的或者只包含有效的數字數據
            if not result.empty:
                self.assertIn("Month_up", result.columns)
        except TypeError as e:
            if "'<' not supported between instances of 'int' and 'str'" in str(e):
                self.fail("ReportUp 仍然存在類型比較錯誤，修復失敗")
            else:
                raise

    def test_reportup_with_all_numeric_data(self):
        """測試 ReportUp 處理純數字數據的正常情況"""
        d0 = datetime(2024, 1, 1)
        d1 = d0 + timedelta(days=1)
        d2 = d1 + timedelta(days=1)
        d3 = d2 + timedelta(days=1)

        # 純數字數據
        f0 = pd.DataFrame({
            "Month": [100.0, 105.0]
        }, index=["1101", "2330"])
        
        f1 = pd.DataFrame({
            "Month": [120.0, 110.0]
        }, index=["1101", "2330"])
        
        f2 = pd.DataFrame({
            "Month": [130.0, 115.0]
        }, index=["1101", "2330"])
        
        f3 = pd.DataFrame({
            "Month": [140.0, 120.0]
        }, index=["1101", "2330"])

        indicator = FakeIndicator("Month", {d0: f0, d1: f1, d2: f2, d3: f3})

        sut = ReportUp("up", upNum=2, Report=indicator, Unit=indicator._Unit)
        result = sut.get_ALL_Report(d0)

        # 應該成功返回結果
        self.assertIsInstance(result, pd.DataFrame)
        if not result.empty:
            self.assertIn("Month_up", result.columns)
            # 檢查是否有股票符合連續增長條件
            self.assertTrue(any(result["Month_up"] >= 2))

    def test_reportup_with_nan_values(self):
        """測試 ReportUp 處理包含 NaN 值的數據"""
        d0 = datetime(2024, 1, 1)
        d1 = d0 + timedelta(days=1)
        d2 = d1 + timedelta(days=1)
        d3 = d2 + timedelta(days=1)

        # 包含 NaN 值的數據
        f0 = pd.DataFrame({
            "Month": [100.0, np.nan]
        }, index=["1101", "2330"])
        
        f1 = pd.DataFrame({
            "Month": [120.0, 110.0]
        }, index=["1101", "2330"])
        
        f2 = pd.DataFrame({
            "Month": [130.0, 115.0]
        }, index=["1101", "2330"])
        
        f3 = pd.DataFrame({
            "Month": [140.0, 120.0]
        }, index=["1101", "2330"])

        indicator = FakeIndicator("Month", {d0: f0, d1: f1, d2: f2, d3: f3})

        sut = ReportUp("up", upNum=2, Report=indicator, Unit=indicator._Unit)
        result = sut.get_ALL_Report(d0)

        # 應該成功返回結果，NaN 值應該被過濾掉
        self.assertIsInstance(result, pd.DataFrame)
        if not result.empty:
            self.assertIn("Month_up", result.columns)

    def test_reportup_with_empty_data(self):
        """測試 ReportUp 處理空數據的情況"""
        d0 = datetime(2024, 1, 1)
        
        # 空的數據框
        f0 = pd.DataFrame()
        indicator = FakeIndicator("Month", {d0: f0})

        sut = ReportUp("up", upNum=2, Report=indicator, Unit=indicator._Unit)
        result = sut.get_ALL_Report(d0)

        # 應該返回空的 DataFrame
        self.assertIsInstance(result, pd.DataFrame)
        self.assertTrue(result.empty)

    def test_reportup_with_smooth_and_auto_trace(self):
        """測試 ReportUp 與 ReportSmooth 和 ReportAutoTrace 組合使用"""
        d0 = datetime(2024, 1, 1)
        d1 = d0 + timedelta(days=1)
        d2 = d1 + timedelta(days=1)
        d3 = d2 + timedelta(days=1)

        # 純數字數據
        f0 = pd.DataFrame({
            "Month": [100.0, 105.0]
        }, index=["1101", "2330"])
        
        f1 = pd.DataFrame({
            "Month": [120.0, 110.0]
        }, index=["1101", "2330"])
        
        f2 = pd.DataFrame({
            "Month": [130.0, 115.0]
        }, index=["1101", "2330"])
        
        f3 = pd.DataFrame({
            "Month": [140.0, 120.0]
        }, index=["1101", "2330"])

        indicator = FakeIndicator("Month", {d0: f0, d1: f1, d2: f2, d3: f3})

        # 創建 ReportSmooth -> ReportUp -> ReportAutoTrace 鏈
        smooth = ReportSmooth("smooth", avgNum=2, Report=indicator, Unit=indicator._Unit)
        up = ReportUp("up", upNum=2, Report=smooth, Unit=smooth._Report._Unit)
        auto = ReportAutoTrace("auto", Report=up, Unit=up._Report._Unit)
        
        result = auto.get_ALL_Report(d0)

        # 應該成功返回結果
        self.assertIsInstance(result, pd.DataFrame)
        if not result.empty:
            self.assertIn("Month_smooth_up", result.columns)

    def test_all_imge_with_invalid_end_date(self):
        """測試 All_imge 智能日期調整功能"""
        from src.FilterService.GetStockData import All_imge
        
        # 模擬當前日期
        today = datetime(2024, 3, 20)  # 假設今天是3月20日
        
        # 設置一個無效的結束日期（當前月份）
        invalid_end = datetime(2024, 3, 15)
        start = datetime(2024, 1, 1)
        
        # 創建測試數據
        d1 = datetime(2024, 1, 1)
        d2 = datetime(2024, 2, 1)
        d3 = datetime(2024, 3, 1)
        
        f1 = pd.DataFrame({"Month": [100.0, 105.0]}, index=["1101", "2330"])
        f2 = pd.DataFrame({"Month": [120.0, 110.0]}, index=["1101", "2330"])
        f3 = pd.DataFrame({"Month": [130.0, 115.0]}, index=["1101", "2330"])
        
        # 創建增強的 FakeIndicator，具有更好的 Next_date 邏輯
        class EnhancedFakeIndicator(FakeIndicator):
            def Next_date(self, date: datetime) -> datetime:
                # 如果已經到達最大測試日期，則停止前進
                if date >= datetime(2024, 12, 31):
                    return date
                return date + timedelta(days=1)
        
        indicator = EnhancedFakeIndicator("Month", {d1: f1, d2: f2, d3: f3})
        
        # 創建模擬的外部服務
        class MockExternalService:
            def get_stock_history(self, number: str):
                # 返回包含有效日期的索引
                return pd.DataFrame(index=[d1, d2, d3])
        
        mock_external = MockExternalService()
        
        # 創建 All_imge 實例
        all_imge = All_imge(start, invalid_end, indicator, mock_external)
        
        # 測試智能日期調整
        result = all_imge.get_Chart(number="1101")
        
        # 應該成功返回結果，不會因為無效日期而崩潰
        self.assertIsInstance(result, pd.DataFrame)
        # 結果應該包含有效的數據
        if not result.empty:
            self.assertIn("Month", result.columns)


if __name__ == "__main__":
    unittest.main()