import unittest
from datetime import datetime

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

    def test_Runtest(self):
        self._BackTestFilterData.GoToNextWorkDay(
            datetime.strptime("2020-03-04", "%Y-%m-%d")
        )
        _buydata = self._BackTestFilterData.ShouldBuyStocks()
        _selldata = self._BackTestFilterData.ShouldSellStocks()
