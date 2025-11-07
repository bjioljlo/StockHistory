import unittest
from datetime import datetime

from unittest.mock import patch, MagicMock
from BackTestService.BackTestInfoData import BackTestInfoDataPriceByToday
from FilterService.StockHistory import OriginalStockTest
from Common.StockInfoData import BaseInfoData


class BackTestInfoDataPriceByToday_test(unittest.TestCase):
    def setUp(self) -> None:
        self._BaseInfoData = BaseInfoData(
            5000000,
            datetime.strptime("2020-03-06", "%Y-%m-%d"),
            datetime.strptime("2021-03-04", "%Y-%m-%d"),
        )
        self._OriginalStockTest = OriginalStockTest()
        # Patch get_PriceByDateAndType，讓 2330 的價格固定為 315
        patcher = patch.object(self._OriginalStockTest, 'get_PriceByDateAndType', return_value=315)
        self.addCleanup(patcher.stop)
        patcher.start()
        self.BackTestInfoDataPriceByToday_test = BackTestInfoDataPriceByToday(
            self._BaseInfoData, self._OriginalStockTest, "Datafiles/UnitTest/"
        )

    def setDown(self):
        pass

    def test_BuyStock(self):
        test_stcok = "2330"
        # 確保 HandleStock 初始化
        self.BackTestInfoDataPriceByToday_test._HandleStock = {}
        self.BackTestInfoDataPriceByToday_test.BuyStock(test_stcok, 1000)
        Result = self.BackTestInfoDataPriceByToday_test.HandleStock[test_stcok]
        self.assertEqual(Result.Amount, 1000)
        self.assertEqual(Result.Price, 315)

    def test_SellStock(self):
        # 確保 HandleStock 初始化
        self.BackTestInfoDataPriceByToday_test._HandleStock = {}
        self.BackTestInfoDataPriceByToday_test.BuyStock("2330", 2000)
        _oldAmount = self.BackTestInfoDataPriceByToday_test.HandleStock["2330"].Amount
        if self.BackTestInfoDataPriceByToday_test.SellStock("2330", 1000):
            Result = self.BackTestInfoDataPriceByToday_test.HandleStock["2330"]
            self.assertEqual(Result.Amount, _oldAmount - 1000)
            self.assertEqual(Result.Price, 315)

    def test_RecordUserInfo(self):
        # Mock _TempResultDraw, _TempTradeInfo, _TempResultAll 結構
        self.BackTestInfoDataPriceByToday_test._TempResultDraw = MagicMock()
        self.BackTestInfoDataPriceByToday_test._TempResultDraw.Data = {"資產比例": {datetime.strptime("2020-03-06", "%Y-%m-%d"): 1.0}}
        self.BackTestInfoDataPriceByToday_test._TempTradeHandInfo = MagicMock()
        self.BackTestInfoDataPriceByToday_test._TempTradeHandInfo.Data = {"號碼": {datetime.strptime("2020-03-06", "%Y-%m-%d"): "2330"}}
        self.BackTestInfoDataPriceByToday_test._TempResultAll = MagicMock()
        self.BackTestInfoDataPriceByToday_test._TempResultAll.Data = {"股票資產": {datetime.strptime("2020-03-06", "%Y-%m-%d"): 315000}}
        self.BackTestInfoDataPriceByToday_test.BuyStock("2330", 1000)
        self.BackTestInfoDataPriceByToday_test.RecordUserInfo()
        self.BackTestInfoDataPriceByToday_test.RunFinish()
        self.assertIsNotNone(
            self.BackTestInfoDataPriceByToday_test._TempResultDraw.Data["資產比例"][
                datetime.strptime("2020-03-06", "%Y-%m-%d")
            ]
        )
        self.assertEqual(
            self.BackTestInfoDataPriceByToday_test._TempTradeHandInfo.Data["號碼"][
                datetime.strptime("2020-03-06", "%Y-%m-%d")
            ],
            "2330",
        )
        self.assertAlmostEqual(
            self.BackTestInfoDataPriceByToday_test._TempResultAll.Data["股票資產"][
                datetime.strptime("2020-03-06", "%Y-%m-%d")
            ]
            / 1000,
            315,
        )

    def test_SellAllStock(self):
        self.BackTestInfoDataPriceByToday_test._HandleStock = {}
        self.BackTestInfoDataPriceByToday_test.BuyStock("2330", 1000)
        self.BackTestInfoDataPriceByToday_test.BuyStock("2317", 500)
        self.BackTestInfoDataPriceByToday_test.SellAllStock()
        self.assertEqual(len(self.BackTestInfoDataPriceByToday_test.HandleStock), 0)

    def test_BuyAllStock(self):
        import pandas as pd
        df = pd.DataFrame(index=["2330", "2317"])
        self.BackTestInfoDataPriceByToday_test._HandleStock = {}
        result = self.BackTestInfoDataPriceByToday_test.BuyAllStock(df)
        self.assertTrue(result)
        self.assertIn("2330", self.BackTestInfoDataPriceByToday_test.HandleStock)
        self.assertIn("2317", self.BackTestInfoDataPriceByToday_test.HandleStock)

    def test_GoToNextWorkDay(self):
        # 正常推進
        result = self.BackTestInfoDataPriceByToday_test.GoToNextWorkDay(datetime.strptime("2020-03-07", "%Y-%m-%d"))
        self.assertTrue(result)
        # 超出範圍
        result = self.BackTestInfoDataPriceByToday_test.GoToNextWorkDay(datetime.strptime("2022-01-01", "%Y-%m-%d"))
        self.assertFalse(result)

    def test_RunFinish(self):
        # Mock RunFinish
        self.BackTestInfoDataPriceByToday_test._TempResultDraw = MagicMock()
        self.BackTestInfoDataPriceByToday_test._TempResultAll = MagicMock()
        self.BackTestInfoDataPriceByToday_test._TempTradeHandInfo = MagicMock()
        self.BackTestInfoDataPriceByToday_test.RunFinish()
        self.BackTestInfoDataPriceByToday_test._TempResultDraw.RunFinish.assert_called_once()
        self.BackTestInfoDataPriceByToday_test._TempResultAll.RunFinish.assert_called_once()
        self.BackTestInfoDataPriceByToday_test._TempTradeHandInfo.RunFinish.assert_called_once()

    def test_UserStockAsset_and_UserAllAsset(self):
        import Common.Tools as Tools
        self.BackTestInfoDataPriceByToday_test._HandleStock = {}
        self.BackTestInfoDataPriceByToday_test.BuyStock("2330", 1000)
        stock_asset = self.BackTestInfoDataPriceByToday_test.UserStockAsset
        all_asset = self.BackTestInfoDataPriceByToday_test.UserAllAsset
        total_cost = Tools.Total_with_Handling_fee_and_Tax(315, 1000)
        expected_all_asset = 5000000 - total_cost + 315000
        self.assertEqual(stock_asset, 315000)
        self.assertEqual(all_asset, expected_all_asset)

    def test_AddOneDay(self):
        self.BackTestInfoDataPriceByToday_test._BaseInfoData.now_day = datetime.strptime("2021-03-03", "%Y-%m-%d")
        result = self.BackTestInfoDataPriceByToday_test.AddOneDay()
        self.assertTrue(result)
        self.assertEqual(self.BackTestInfoDataPriceByToday_test._BaseInfoData.now_day, datetime.strptime("2021-03-04", "%Y-%m-%d"))
        # 到期日後
        result = self.BackTestInfoDataPriceByToday_test.AddOneDay()
        self.assertFalse(result)
