import unittest
from StockInfos import PickInfoDatas
from StockInfoData import StockInfoData
import twstock as ts

class PickInfoDatas_test(unittest.TestCase):
    def setUp(self) -> None:
        self.test_StockInfoDatas = PickInfoDatas()
        self.test_StockInfoDatas.AddStockInfo("2356")
        self.test_StockInfoDatas.AddStockInfo("2327")
        self.test_StockInfoDatas.AddStockInfo("2317")
    def tearDown(self) -> None:
        pass
    def test_AddStockInfo(self):
        Add_Data = "2330"
        self.test_StockInfoDatas.AddStockInfo(Add_Data)
        Result = self.test_StockInfoDatas.Stock_list
        self.assertIn(Add_Data, Result)
    def test_DeletStockInfo(self):
        Del_Data = "2317"
        self.test_StockInfoDatas.DeletStockInfo(Del_Data)
        Result = self.test_StockInfoDatas.Stock_list
        self.assertNotIn(Del_Data, Result)  
    def test_GetStockInfo(self):
        Result = self.test_StockInfoDatas.GetStockInfo("2327")
        Result_conferme = self.test_StockInfoDatas.Stock_list
        self.assertEqual(Result, Result_conferme["2327"])
    def test_CleanData(self):
        Clean_Data = {}
        self.test_StockInfoDatas.CleanData()
        Result = self.test_StockInfoDatas.Stock_list
        self.assertCountEqual(Result, Clean_Data)

if __name__ == '__main__':
    unittest.main()