import unittest
from datetime import datetime, timedelta
from src.Common import Tools

def get_quarter(month):
    return ((month - 1) // 3) + 1

class TestReportDateTools(unittest.TestCase):
    def setUp(self):
        self.today = datetime(2024, 6, 10)

    def test_get_latest_monthly_report_date(self):
        # 6月10日，月營收只能看到4月（6/15前只能查到前兩個月）
        test_date = datetime(2024, 6, 10)
        safe_date = Tools.get_latest_monthly_report_date(test_date, base_today=test_date)
        self.assertEqual(safe_date.year, 2024)
        self.assertEqual(safe_date.month, 4)

        # 6月16日，月營收可看到5月
        test_date2 = datetime(2024, 6, 16)
        safe_date2 = Tools.get_latest_monthly_report_date(test_date2, base_today=test_date2)
        self.assertEqual(safe_date2.year, 2024)
        self.assertEqual(safe_date2.month, 5)

    def test_get_latest_daily_report_date(self):
        # 6月10日（週一），日報只能看到6月7日（週五）
        test_date = datetime(2024, 6, 10)  # 2024/6/8、6/9為週末
        safe_date = Tools.get_latest_daily_report_date(test_date, base_today=test_date)
        self.assertEqual(safe_date, datetime(2024, 6, 7))

        # 6月11日（週二），日報只能看到6月10日（週一）
        test_date2 = datetime(2024, 6, 11)
        safe_date2 = Tools.get_latest_daily_report_date(test_date2, base_today=test_date2)
        self.assertEqual(safe_date2, datetime(2024, 6, 10))

        # 國定假日（如端午節）需依實際資料源設計，這裡僅測週末

    def test_get_latest_season_report_date(self):
        # 5/10，Q1尚未公告，應查去年Q4（2023, Q4）
        test_date = datetime(2024, 5, 10)
        safe_date = Tools.get_latest_season_report_date(test_date, base_today=test_date)
        self.assertEqual((safe_date.year, get_quarter(safe_date.month)), (2023, 4))

        # 5/16，Q1已公告，應查Q1（2024, Q1）
        test_date2 = datetime(2024, 5, 16)
        safe_date2 = Tools.get_latest_season_report_date(test_date2, base_today=test_date2)
        self.assertEqual((safe_date2.year, get_quarter(safe_date2.month)), (2024, 1))

        # 8/30，Q2尚未公告，應查Q1（2024, Q1）
        test_date3 = datetime(2024, 8, 30)
        safe_date3 = Tools.get_latest_season_report_date(test_date3, base_today=test_date3)
        self.assertEqual((safe_date3.year, get_quarter(safe_date3.month)), (2024, 1))

        # 8/31，Q2已公告，應查Q2（2024, Q2）
        test_date4 = datetime(2024, 8, 31)
        safe_date4 = Tools.get_latest_season_report_date(test_date4, base_today=test_date4)
        self.assertEqual((safe_date4.year, get_quarter(safe_date4.month)), (2024, 2))

        # 11/13，Q3尚未公告，應查Q2（2024, Q2）
        test_date5 = datetime(2024, 11, 13)
        safe_date5 = Tools.get_latest_season_report_date(test_date5, base_today=test_date5)
        self.assertEqual((safe_date5.year, get_quarter(safe_date5.month)), (2024, 2))

        # 11/15，Q3已公告，應查Q3（2024, Q3）
        test_date6 = datetime(2024, 11, 15)
        safe_date6 = Tools.get_latest_season_report_date(test_date6, base_today=test_date6)
        self.assertEqual((safe_date6.year, get_quarter(safe_date6.month)), (2024, 3))

        # 3/30，Q4尚未公告，應查Q3（2024, Q3）
        test_date7 = datetime(2025, 3, 30)
        safe_date7 = Tools.get_latest_season_report_date(test_date7, base_today=test_date7)
        self.assertEqual((safe_date7.year, get_quarter(safe_date7.month)), (2024, 3))

        # 3/31，Q4已公告，應查Q4（2024, Q4）
        test_date8 = datetime(2025, 3, 31)
        safe_date8 = Tools.get_latest_season_report_date(test_date8, base_today=test_date8)
        self.assertEqual((safe_date8.year, get_quarter(safe_date8.month)), (2024, 4))

if __name__ == '__main__':
    unittest.main()
