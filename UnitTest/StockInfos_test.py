import unittest
from unittest.mock import patch, MagicMock

from src.StockInfos import PickInfoDatas


class PickInfoDatas_test(unittest.TestCase):
    def setUp(self) -> None:
        # Mock twstock.codes to avoid external dependency
        self.patcher = patch('src.StockInfos.ts.codes')
        mock_codes = self.patcher.start()

        # Create mock stock objects
        mock_stock_2356 = MagicMock()
        mock_stock_2356.code = "2356"
        mock_stock_2356.name = "Test Stock 2356"
        mock_stock_2356.type = "股票"
        mock_stock_2356.start = "2020/01/01"
        mock_stock_2356.market = "上市"
        mock_stock_2356.group = "電子"

        mock_stock_2327 = MagicMock()
        mock_stock_2327.code = "2327"
        mock_stock_2327.name = "Test Stock 2327"
        mock_stock_2327.type = "股票"
        mock_stock_2327.start = "2020/01/01"
        mock_stock_2327.market = "上市"
        mock_stock_2327.group = "電子"

        mock_stock_2317 = MagicMock()
        mock_stock_2317.code = "2317"
        mock_stock_2317.name = "Test Stock 2317"
        mock_stock_2317.type = "股票"
        mock_stock_2317.start = "2020/01/01"
        mock_stock_2317.market = "上市"
        mock_stock_2317.group = "電子"

        mock_stock_2330 = MagicMock()
        mock_stock_2330.code = "2330"
        mock_stock_2330.name = "Test Stock 2330"
        mock_stock_2330.type = "股票"
        mock_stock_2330.start = "2020/01/01"
        mock_stock_2330.market = "上市"
        mock_stock_2330.group = "電子"

        # Configure mock_codes to behave like a dictionary
        mock_codes.__contains__ = MagicMock(side_effect=lambda key: key in ["2356", "2327", "2317", "2330"])
        mock_codes.__getitem__ = MagicMock(side_effect=lambda key: {
            "2356": mock_stock_2356,
            "2327": mock_stock_2327,
            "2317": mock_stock_2317,
            "2330": mock_stock_2330
        }[key])

        self.test_StockInfoDatas = PickInfoDatas()
        self.test_StockInfoDatas.AddStockInfo("2356")
        self.test_StockInfoDatas.AddStockInfo("2327")
        self.test_StockInfoDatas.AddStockInfo("2317")

    def tearDown(self) -> None:
        self.patcher.stop()

    @patch('src.StockInfos.ts.codes')
    def test_AddStockInfo(self, mock_codes):
        # Set up mock for the additional stock
        mock_stock_2330 = MagicMock()
        mock_stock_2330.code = "2330"
        mock_stock_2330.name = "Test Stock 2330"
        mock_stock_2330.type = "股票"
        mock_stock_2330.start = "2020/01/01"
        mock_stock_2330.market = "上市"
        mock_stock_2330.group = "電子"

        mock_codes.__contains__ = MagicMock(return_value=True)
        mock_codes.__getitem__ = MagicMock(return_value=mock_stock_2330)

        Add_Data = "2330"
        self.test_StockInfoDatas.AddStockInfo(Add_Data)
        Result = self.test_StockInfoDatas.StockList
        self.assertIn(Add_Data, Result)

    def test_DeletStockInfo(self):
        Del_Data = "2317"
        self.test_StockInfoDatas.DeletStockInfo(Del_Data)
        Result = self.test_StockInfoDatas.StockList
        self.assertNotIn(Del_Data, Result)

    def test_GetStockInfo(self):
        Result = self.test_StockInfoDatas.GetStockInfo("2327")
        Result_conferme = self.test_StockInfoDatas.StockList
        self.assertEqual(Result, Result_conferme["2327"])

    def test_CleanData(self):
        Clean_Data = {}
        self.test_StockInfoDatas.CleanData()
        Result = self.test_StockInfoDatas.StockList
        self.assertCountEqual(Result, Clean_Data)
