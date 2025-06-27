import sys
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from pandas import DataFrame

import Common.Tools as Tools
from FilterService import OriginalStock
from Common.InfomationType import stock_data_kind
from Common.StockInfoData import BaseInfoData

from .BackTestRecord import BackTestRecord_indexWithDate, IBackTestRecord
from .StockInfoDataInHand import IStockInfoDataInHand, StockInfoDataInHandFactory


class IBackTestInfoData(ABC):
    """回測資訊"""

    @property
    @abstractmethod
    def BaseInfoData(self) -> BaseInfoData:
        raise NotImplementedError(
            "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name)
        )

    @property
    @abstractmethod
    def HandleStock(self) -> dict[str, IStockInfoDataInHand]:
        raise NotImplementedError(
            "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name)
        )

    @property
    @abstractmethod
    def UserStockAsset(self) -> int:
        raise NotImplementedError(
            "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name)
        )

    @property
    @abstractmethod
    def UserAllAsset(self) -> int:
        raise NotImplementedError(
            "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name)
        )

    @abstractmethod
    def SellAllStock(self):
        raise NotImplementedError(
            "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name)
        )

    @abstractmethod
    def SellStock(self, number: str, amount: int) -> bool:
        raise NotImplementedError(
            "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name)
        )

    @abstractmethod
    def BuyAllStock(self, data: DataFrame) -> bool:
        raise NotImplementedError(
            "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name)
        )

    @abstractmethod
    def BuyStock(self, number: str, amount: int) -> bool:
        raise NotImplementedError(
            "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name)
        )

    @abstractmethod
    def GoToNextWorkDay(self, _dateNow: datetime) -> bool:
        raise NotImplementedError(
            "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name)
        )

    @abstractmethod
    def RunFinish(self):
        raise NotImplementedError(
            "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name)
        )

    @abstractmethod
    def RecordUserInfo(self):
        raise NotImplementedError(
            "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name)
        )


class TBackTestInfoData(IBackTestInfoData):
    """回測資訊實作"""

    def __init__(
        self, _baseInfoData: BaseInfoData, _getStockPrice: OriginalStock
    ) -> None:
        super(TBackTestInfoData, self).__init__()
        self._BaseInfoData: BaseInfoData = _baseInfoData
        self._HandleStock: dict[str, IStockInfoDataInHand] = {}  # 手持股票
        self._GetStockPrice: OriginalStock = _getStockPrice
        self._TempResultDraw: IBackTestRecord = BackTestRecord_indexWithDate(
            ["date", "資產比例"], "backtest_data"
        )
        self._TempResultAll: IBackTestRecord = BackTestRecord_indexWithDate(
            ["date", "股票資產", "剩餘現金", "總資產"], "backtest_asset"
        )
        self._TempTradeInfo: IBackTestRecord = BackTestRecord_indexWithDate(
            ["date", "號碼", "數量", "均價"], "backtest_trade"
        )

    def _GetUserStockAsset(self) -> int:
        """股票資產"""
        Temp_money = 0
        for key, value in self._HandleStock.items():
            self._GetStockPrice.number = key
            Temp = self._GetStockPrice.get_PriceByDateAndType(
                self._BaseInfoData.now_day, stock_data_kind.Close
            )
            if Temp is None:
                print("no stock price:" + str(key))
                continue
            Temp_money = Temp_money + (Temp * value.Amount)
        return Temp_money

    def _GetUserAllAsset(self) -> int:
        """總資產"""
        Temp_money = self._GetUserStockAsset()
        return Temp_money + self._BaseInfoData.now_money

    @property
    def BaseInfoData(self) -> BaseInfoData:
        if self._BaseInfoData is None:
            raise
        return self._BaseInfoData

    @property
    def HandleStock(self) -> dict[str, IStockInfoDataInHand]:
        if self._HandleStock is None:
            raise
        return self._HandleStock

    @property
    def UserStockAsset(self) -> int:
        return self._GetUserStockAsset()

    @property
    def UserAllAsset(self) -> int:
        return self._GetUserAllAsset()

    def SellAllStock(self):
        """賣出所有股票"""
        for key, value in list(self._HandleStock.items()):
            self.SellStock(key, value.Amount)

    def BuyAllStock(self, data: DataFrame) -> bool:
        """買入所有股票"""
        result = False
        while len(data) > 0:
            for index, row in data.iterrows():
                if not self.BuyStock(index, 1000):
                    data = data.drop(index=index)
                else:
                    result = True
        return result

    def GoToNextWorkDay(self, _dateNow: datetime) -> bool:
        if (self._BaseInfoData.now_day <= _dateNow) and (
            self._BaseInfoData.end_day >= _dateNow
        ):
            self._BaseInfoData.now_day = _dateNow
            return True
        else:
            print("輸入日期錯誤")
            return False

    def RunFinish(self):
        self._TempResultDraw.RunFinish()
        self._TempResultAll.RunFinish()
        self._TempTradeInfo.RunFinish()

    def RecordUserInfo(self):
        self._TempResultDraw.RunRecord(
            [
                self._BaseInfoData.now_day,
                self._GetUserAllAsset() / self._BaseInfoData.start_money,
            ]
        )
        self._TempResultAll.RunRecord(
            [
                self._BaseInfoData.now_day,
                self._GetUserStockAsset(),
                self._BaseInfoData.now_money,
                self._GetUserAllAsset(),
            ]
        )
        for key, value in self._HandleStock.items():
            self._TempTradeInfo.RunRecord(
                [self._BaseInfoData.now_day, key, value.Amount, value.Price]
            )


class BackTestInfoDataPriceByToday(TBackTestInfoData):
    """回測資訊(當天價格)"""

    def SellStock(self, number: str, amount: int) -> bool:
        """賣某張股票"""
        if not self._HandleStock.__contains__(number):
            print("手上無" + number + "股票")
            return False
        elif self._HandleStock[number].Amount < amount:
            print("股票" + number + "數量不足:" + amount)
            return False
        else:
            self._GetStockPrice.number = number
            stock_price = self._GetStockPrice.get_PriceByDateAndType(
                self._BaseInfoData.now_day, stock_data_kind.Close
            )
            self._BaseInfoData.now_money = (
                self._BaseInfoData.now_money
                + Tools.Total_with_Handling_fee_and_Tax(stock_price, amount, False)
            )
            if not self._HandleStock[number].MinusAmount(amount):
                self._HandleStock.pop(number, None)
            return True

    def BuyStock(self, number: str, amount: int) -> bool:
        """買股票"""
        self._GetStockPrice.number = number
        stock_price = self._GetStockPrice.get_PriceByDateAndType(
            self._BaseInfoData.now_day, stock_data_kind.Close
        )
        if stock_price is None:
            print(str(number) + " no use stock")
            return False
        elif (
            Tools.Total_with_Handling_fee_and_Tax(stock_price, amount)
            > self._BaseInfoData.now_money
        ):
            print("錢不夠買：" + str(number) + " " + str(amount) + "股")
            return False
        else:
            if not self._HandleStock.__contains__(number):
                self._HandleStock[number] = StockInfoDataInHandFactory(number)
            self._HandleStock[number].AddAmount(amount, stock_price)
            self._BaseInfoData.now_money = (
                self._BaseInfoData.now_money
                - Tools.Total_with_Handling_fee_and_Tax(stock_price, amount)
            )
            return True

    def AddOneDay(self):
        """過一天"""
        if self._BaseInfoData.now_day >= self._BaseInfoData.end_day:
            return False
        else:
            self._BaseInfoData.now_day = self._BaseInfoData.now_day + timedelta(
                days=1
            )  # 加一天
            return True
