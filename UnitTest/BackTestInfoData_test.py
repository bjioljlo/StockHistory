import unittest
from datetime import datetime
from BackTestService.BackTestInfoData import BackTestInfoDataPriceByToday
from FilterService.StockHistory import OriginalStockTest
from StockInfoData import BaseInfoData
from BackTestService.StockInfoDataInHand import StockInfoDataInHandWithWeightedAverage 

class BackTestInfoDataPriceByToday_test(unittest.TestCase):
    def setUp(self) -> None:
        self._BaseInfoData = BaseInfoData(5000000, datetime.strptime('2020-03-04', '%Y-%m-%d'), datetime.strptime('2024-03-04', '%Y-%m-%d'))
        self._OriginalStockTest = OriginalStockTest()
        self.BackTestInfoDataPriceByToday_test = BackTestInfoDataPriceByToday(self._BaseInfoData, self._OriginalStockTest)
    def setDown(self):
        pass
    def test_BuyStock(self):
        self.BackTestInfoDataPriceByToday_test.BuyStock("2330", 1000)
        Result:StockInfoDataInHandWithWeightedAverage = self.BackTestInfoDataPriceByToday_test.HandleStock["2330"]
        self.assertEqual(Result.Amount, 1000)
        self.assertEqual(Result.Price, 1005)
    def test_SellStock(self):
        self.BackTestInfoDataPriceByToday_test.BuyStock("2330", 2000)
        _oldAmount = self.BackTestInfoDataPriceByToday_test.HandleStock["2330"].Amount
        if self.BackTestInfoDataPriceByToday_test.SellStock("2330", 1000):
            Result:StockInfoDataInHandWithWeightedAverage = self.BackTestInfoDataPriceByToday_test.HandleStock["2330"]
            self.assertEqual(Result.Amount, _oldAmount-1000)
            self.assertEqual(Result.Price, 1005)