import unittest
from datetime import datetime

from BackTestService.BackTestInfoData import BackTestInfoDataPriceByToday
from FilterService.StockHistory import OriginalStockTest
from StockInfoData import BaseInfoData


class BackTestInfoDataPriceByToday_test(unittest.TestCase):
    def setUp(self) -> None:
        self._BaseInfoData = BaseInfoData(
            5000000,
            datetime.strptime("2020-03-06", "%Y-%m-%d"),
            datetime.strptime("2021-03-04", "%Y-%m-%d"),
        )
        self._OriginalStockTest = OriginalStockTest()
        self.BackTestInfoDataPriceByToday_test = BackTestInfoDataPriceByToday(
            self._BaseInfoData, self._OriginalStockTest
        )

    def setDown(self):
        pass

    def test_BuyStock(self):
        self.BackTestInfoDataPriceByToday_test.BuyStock("2330", 1000)
        Result = self.BackTestInfoDataPriceByToday_test.HandleStock["2330"]
        self.assertEqual(Result.Amount, 1000)
        self.assertEqual(Result.Price, 303.793091)

    def test_SellStock(self):
        self.BackTestInfoDataPriceByToday_test.BuyStock("2330", 2000)
        _oldAmount = self.BackTestInfoDataPriceByToday_test.HandleStock["2330"].Amount
        if self.BackTestInfoDataPriceByToday_test.SellStock("2330", 1000):
            Result = self.BackTestInfoDataPriceByToday_test.HandleStock["2330"]
            self.assertEqual(Result.Amount, _oldAmount - 1000)
            self.assertEqual(Result.Price, 303.793091)

    def test_RecordUserInfo(self):
        self.BackTestInfoDataPriceByToday_test.BuyStock("2330", 1000)
        self.BackTestInfoDataPriceByToday_test.RecordUserInfo()
        self.BackTestInfoDataPriceByToday_test.RunFinish()
        self.assertEqual(
            self.BackTestInfoDataPriceByToday_test._TempTradeInfo.Data["號碼"][
                datetime.strptime("2020-03-06", "%Y-%m-%d")
            ],
            "2330",
        )
        self.assertAlmostEqual(
            self.BackTestInfoDataPriceByToday_test._TempResultAll.Data["股票資產"][
                datetime.strptime("2020-03-06", "%Y-%m-%d")
            ]
            / 1000,
            303.793091,
        )
