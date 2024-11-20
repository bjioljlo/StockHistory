import unittest
from BackTestService.BackTestFilterData import IBackTestFilterData, KD_pickFilterData
from BackTestService.BackTestStrategy import KD_pickBacktestFilter, KD_pickBacktestSignal
from FilterService.GetStockData import ROE_index
from FilterService.StockHistory import OriginalStockTest
from datetime import datetime

class TKD_pickFilterData_Test(unittest.TestCase):
    def BuyStrockFun(aName: str, aIsBuy: bool):
        pass
    def setUp(self) -> None:
        self._BackTestFilterData:IBackTestFilterData = KD_pickFilterData(self.BuyStrockFun, KD_pickBacktestFilter(ROE_index), 
                                                                        KD_pickBacktestSignal(OriginalStockTest()), datetime.strptime('2020-03-04', '%Y-%m-%d'))
    def setDown(self):
        pass
    def test_Runtest(self):
        self._BackTestFilterData.GoToNextWorkDay()