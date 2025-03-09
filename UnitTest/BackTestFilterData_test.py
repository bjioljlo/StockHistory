import unittest
from datetime import datetime, timedelta
import Tools

import InfomationType as info
from BackTestService.BackTestFilterData import (
    BacktestFilterDataFactory,
    BacktestFilterDataType,
)
from BackTestService.FilterAndSignalStrategy import (
    BacktestFilterFactory,
    BacktestFilterType,
    BacktestSignalFactory,
    BacktestSignalType,
)
from FilterService.GetStockData import ROE_Indicator
from FilterService.StockHistory import OriginalStockTest
from FilterService.StockReportHistory import SeasonReportFactory
from GetExternalDataService import ExternalDataFactory, ExternalDataTypeEnum


class TKD_pickFilterData_Test(unittest.TestCase):
    def BuyStrockFun(aName: str, aIsBuy: bool):
        pass

    def setUp(self) -> None:
        self._external_data = ExternalDataFactory.Get_instance(
            ExternalDataTypeEnum.Test
        )
        self.ROE_index_test = ROE_Indicator(
            "ROE",
            SeasonReportFactory(info.FS_type.CPL, self._external_data),
            SeasonReportFactory(info.FS_type.BS, self._external_data),
        )
        self._BackTestFilterData = BacktestFilterDataFactory(
            BacktestFilterDataType.KD,
            self.BuyStrockFun,
            BacktestFilterFactory(BacktestFilterType.KD, self.ROE_index_test),
            BacktestSignalFactory(BacktestSignalType.KD, OriginalStockTest()),
            datetime.strptime("2019-03-04", "%Y-%m-%d"),
            datetime.strptime("2021-08-07", "%Y-%m-%d"),
        )

    def setDown(self):
        pass

    def test_Run_KDtest_buystocks(self):
        temp_date = datetime.strptime("2020-09-16", "%Y-%m-%d")
        for i in range(1000):
            if temp_date not in self._external_data.get_stock_history("2330").index:
                temp_date = Tools.backWorkDays(temp_date, -1)
                continue
            if temp_date > datetime.strptime("2020-11-5", "%Y-%m-%d"):
                break
            self._BackTestFilterData.GoToNextWorkDay(temp_date)
            _buydata = self._BackTestFilterData.ShouldBuyStocks()
            temp_date = Tools.backWorkDays(temp_date, -1)
            if len(_buydata) != 0:
                self.assertEqual(_buydata, {"2330"})
                break

    def test_Run_KDtest_sellstocks(self):
        temp_date = datetime.strptime("2020-09-16", "%Y-%m-%d")
        for i in range(1000):
            if temp_date not in self._external_data.get_stock_history("2330").index:
                temp_date = Tools.backWorkDays(temp_date, -1)
                continue
            if temp_date > datetime.strptime("2020-11-5", "%Y-%m-%d"):
                break
            self._BackTestFilterData.GoToNextWorkDay(temp_date)
            _selldata = self._BackTestFilterData.ShouldSellStocks({"2330": "1"})
            temp_date = Tools.backWorkDays(temp_date, -1)
            if len(_selldata) != 0:
                self.assertEqual(_selldata, {"2330"})
                break
