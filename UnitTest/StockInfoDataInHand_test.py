import unittest
from StockInfoData import StockInfoCurrentData, StockInfoData
from BackTestService.StockInfoDataInHand import StockInfoDataInHandWithWeightedAverage


class StockInfoDataInHand_test(unittest.TestCase):
    def setUp(self) -> None:
        self.StockInfoData_test = StockInfoData(
            "2330", "台積電", "ABC", "1990/01/02", "上市", "電子"
        )
        self.StockInfoCurrentData_test = StockInfoCurrentData(
            self.StockInfoData_test, 1000, 100
        )
        self.StockInfoDataInHandWithWeightedAverage_test = (
            StockInfoDataInHandWithWeightedAverage(self.StockInfoCurrentData_test)
        )

    def tearDown(self) -> None:
        pass

    def test_MinusAmount(self):
        if self.StockInfoDataInHandWithWeightedAverage_test.MinusAmount(500):
            Result_Amount = self.StockInfoDataInHandWithWeightedAverage_test.Amount
            self.assertEqual(Result_Amount, 500)

    def test_AddAmount(self):
        self.StockInfoDataInHandWithWeightedAverage_test.AddAmount(1000, 300)
        Result_Amount = self.StockInfoDataInHandWithWeightedAverage_test.Amount
        Result_Price = self.StockInfoDataInHandWithWeightedAverage_test.Price
        self.assertEqual(Result_Amount, 2000)
        self.assertEqual(Result_Price, 200)
