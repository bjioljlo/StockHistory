import sys
from abc import ABC, abstractmethod

import pandas as pd

from FilterService.StockHistory import OriginalStock
from BackTestService.BackTestFilterData import IBackTestFilterData
from BackTestService.BackTestInfoData import IBackTestInfoData
from Common.InfomationType import stock_data_kind
import Common.Tools as Tools


class IBackTestInOutStrategy(ABC):

    @property
    @abstractmethod
    def ResultPick(self) -> pd.DataFrame:
        raise NotImplementedError(
            "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name)
        )

    @property
    @abstractmethod
    def FilterData(self) -> IBackTestFilterData:
        raise NotImplementedError(
            "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name)
        )

    @abstractmethod
    def Out(self, data: pd.DataFrame) -> bool:
        raise NotImplementedError(
            "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name)
        )

    @abstractmethod
    def In(self, data: pd.DataFrame):
        raise NotImplementedError(
            "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name)
        )

    @abstractmethod
    def Run(self):
        raise NotImplementedError(
            "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name)
        )

    @abstractmethod
    def Record(self):
        raise NotImplementedError(
            "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name)
        )

    @abstractmethod
    def Finish(self):
        raise NotImplementedError(
            "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name)
        )


class TBacktestInOutStrategy(IBackTestInOutStrategy):
    def __init__(
        self,
        userInfo: IBackTestInfoData,
        backTestFilterData: IBackTestFilterData,
        originalStock: OriginalStock,
    ):
        self._userInfo: IBackTestInfoData = userInfo
        self._backTestFilterData: IBackTestFilterData = backTestFilterData
        self._original_stock: OriginalStock = originalStock
        self._buy_numbers = []
        self._sell_numbers = []
        self._has_trade = False
        self._buy_data = pd.DataFrame(columns=["date", "code"]).set_index("date")
        self._sell_data = pd.DataFrame(columns=["date", "code"]).set_index("date")
        self._result_pick = pd.DataFrame(columns=["date", "選股數量"])

    @property
    def ResultPick(self) -> pd.DataFrame:
        if self._result_pick is None:
            raise
        return self._result_pick

    @property
    def FilterData(self) -> IBackTestFilterData:
        if self._backTestFilterData is None:
            raise
        return self._backTestFilterData

    def Run(self):
        self._has_trade = False
        self._backTestFilterData.GoToNextWorkDay(self._userInfo.BaseInfoData.now_day)
        self._buy_numbers = []
        self._sell_numbers = []

    def Out(self):
        self._sell_numbers = self._backTestFilterData.ShouldSellStocks(
            self._userInfo.HandleStock
        )
        if len(self._sell_numbers) > 0:
            for key, value in list(self._userInfo.HandleStock.items()):
                if (key in self._sell_numbers) and self._userInfo.SellStock(
                    key, value.Amount
                ):
                    self._has_trade = True

    def In(self):
        self._buy_numbers = self._backTestFilterData.ShouldBuyStocks()
        if len(self._buy_numbers) > 0:
            Temp_buy = pd.DataFrame(columns=["code", "volume"]).set_index("code")
            for number in self._buy_numbers:
                self._original_stock.number = number
                volume = self._original_stock.get_PriceByDateAndType(
                    self._userInfo.BaseInfoData.now_day, stock_data_kind.Volume
                )
                Temp_buy = pd.concat(
                    [
                        Temp_buy,
                        pd.DataFrame({"code": [str(number)], "volume": [volume]}),
                    ],
                    ignore_index=True,
                )
            Temp_buy = Temp_buy.sort_values(by="volume", ascending=False).set_index(
                "code"
            )
            if self._userInfo.BuyAllStock(Temp_buy):
                self._has_trade = True

    def Record(self):
        if self._has_trade:
            if len(self._buy_numbers) != 0:
                buy_numbers_str = ""
                for buy_number in self._buy_numbers:
                    buy_numbers_str += buy_number + ","
                self._buy_data = pd.concat(
                    [
                        self._buy_data,
                        pd.DataFrame(
                            {
                                "date": [self._userInfo.BaseInfoData.now_day],
                                "code": [buy_numbers_str],
                            }
                        ),
                    ],
                    ignore_index=True,
                )
            if len(self._sell_numbers) != 0:
                sell_numbers_str = ""
                for sell_number in self._sell_numbers:
                    sell_numbers_str += sell_number + ","
                self._sell_data = pd.concat(
                    [
                        self._sell_data,
                        pd.DataFrame(
                            {
                                "date": [self._userInfo.BaseInfoData.now_day],
                                "code": [sell_numbers_str],
                            }
                        ),
                    ],
                    ignore_index=True,
                )
            self._result_pick = pd.concat(
                [
                    self._result_pick,
                    pd.DataFrame(
                        {
                            "date": [self._userInfo.BaseInfoData.now_day],
                            "選股數量": [len(self._buy_numbers)],
                        }
                    ),
                ],
                ignore_index=True,
            )
            self._userInfo.RecordUserInfo()

    def Finish(self):
        self._result_pick.set_index("date", inplace=True)
        if not self._buy_data.empty:
            buy_data = self._buy_data.set_index("date")
            buy_data.to_csv("buy.csv")
        if not self._sell_data.empty:
            sell_data = self._sell_data.set_index("date")
            sell_data.to_csv("sell.csv")


class PERandPBR_BackTestInOutStrategy(TBacktestInOutStrategy):
    def Run(self):
        super().Run()
        self._backTestFilterData.RuuFilter()
        self._buy_numbers = self._backTestFilterData.ShouldBuyStocks()

    def Out(self):
        if len(self._userInfo.HandleStock) > 0:
            self._sell_numbers = self._userInfo.HandleStock.keys()
            self._userInfo.SellAllStock()
            self._has_trade = True

    def In(self):
        super().In()


class PEG_BackTestInOutStrategy(TBacktestInOutStrategy):
    def __init__(
        self,
        userInfo: IBackTestInfoData,
        backTestFilterData: IBackTestFilterData,
        originalStock: OriginalStock,
    ):
        super().__init__(
            userInfo,
            backTestFilterData,
            originalStock,
        )

    def Run(self):
        self._has_trade = False
        self._backTestFilterData.GoToNextWorkDay(self._userInfo.BaseInfoData.now_day)
        self._buy_numbers = []
        self._sell_numbers = []

    def Out(self):
        self._sell_numbers = self._backTestFilterData.ShouldSellStocks(
            self._userInfo.HandleStock
        )
        if len(self._sell_numbers) > 0:
            for key, value in list(self._userInfo.HandleStock.items()):
                if (key in self._sell_numbers) and self._userInfo.SellStock(
                    key, value.Amount
                ):
                    self._has_trade = True

    def In(self):
        self._backTestFilterData.RuuFilter()
        self._buy_numbers = self._backTestFilterData.ShouldBuyStocks()
        if len(self._buy_numbers) > 0:
            Temp_buy = pd.DataFrame(columns=["code", "volume"]).set_index("code")
            for number in self._buy_numbers:
                self._original_stock.number = number
                volume = self._original_stock.get_PriceByDateAndType(
                    self._userInfo.BaseInfoData.now_day, stock_data_kind.Volume
                )
                Temp_buy = pd.concat(
                    [
                        Temp_buy,
                        pd.DataFrame({"code": [str(number)], "volume": [volume]}),
                    ],
                    ignore_index=True,
                )
            Temp_buy = Temp_buy.sort_values(by="volume", ascending=False).set_index(
                "code"
            )
            if self._userInfo.BuyAllStock(Temp_buy):
                self._has_trade = True

    def Record(self):
        if self._has_trade:
            if len(self._buy_numbers) != 0:
                buy_numbers_str = ""
                for buy_number in self._buy_numbers:
                    buy_numbers_str += buy_number + ","
                self._buy_data = pd.concat(
                    [
                        self._buy_data,
                        pd.DataFrame(
                            {
                                "date": [self._userInfo.BaseInfoData.now_day],
                                "code": [buy_numbers_str],
                            }
                        ),
                    ],
                    ignore_index=True,
                )
            if len(self._sell_numbers) != 0:
                sell_numbers_str = ""
                for sell_number in self._sell_numbers:
                    sell_numbers_str += sell_number + ","
                self._sell_data = pd.concat(
                    [
                        self._sell_data,
                        pd.DataFrame(
                            {
                                "date": [self._userInfo.BaseInfoData.now_day],
                                "code": [sell_numbers_str],
                            }
                        ),
                    ],
                    ignore_index=True,
                )
            self._result_pick = pd.concat(
                [
                    self._result_pick,
                    pd.DataFrame(
                        {
                            "date": [self._userInfo.BaseInfoData.now_day],
                            "選股數量": [len(self._buy_numbers)],
                        }
                    ),
                ],
                ignore_index=True,
            )
            self._userInfo.RecordUserInfo()

    def Finish(self):
        self._result_pick.set_index("date", inplace=True)
        if not self._buy_data.empty:
            buy_data = self._buy_data.set_index("date")
            buy_data.to_csv("buy.csv")
        if not self._sell_data.empty:
            sell_data = self._sell_data.set_index("date")
            sell_data.to_csv("sell.csv")


class KD_BackTestInOutStrategy(TBacktestInOutStrategy):
    def Run(self):
        self._has_trade = False
        self._backTestFilterData.GoToNextWorkDay(self._userInfo.BaseInfoData.now_day)
        self._buy_numbers = []
        self._sell_numbers = []

    def Out(self):
        self._sell_numbers = self._backTestFilterData.ShouldSellStocks(
            self._userInfo.HandleStock
        )
        if len(self._sell_numbers) > 0:
            for key, value in list(self._userInfo.HandleStock.items()):
                if (key in self._sell_numbers) and self._userInfo.SellStock(
                    key, value.Amount
                ):
                    self._has_trade = True

    def In(self):
        self._backTestFilterData.RuuFilter()
        self._buy_numbers = self._backTestFilterData.ShouldBuyStocks()
        if len(self._buy_numbers) > 0:
            Temp_buy = pd.DataFrame(columns=["code", "volume"]).set_index("code")
            for number in self._buy_numbers:
                self._original_stock.number = number
                volume = self._original_stock.get_PriceByDateAndType(
                    self._userInfo.BaseInfoData.now_day, stock_data_kind.Volume
                )
                Temp_buy = pd.concat(
                    [
                        Temp_buy,
                        pd.DataFrame({"code": [str(number)], "volume": [volume]}),
                    ],
                    ignore_index=True,
                )
            Temp_buy = Temp_buy.sort_values(by="volume", ascending=False).set_index(
                "code"
            )
            if self._userInfo.BuyAllStock(Temp_buy):
                self._has_trade = True

    def Record(self):
        if self._has_trade:
            if len(self._buy_numbers) != 0:
                buy_numbers_str = ""
                for buy_number in self._buy_numbers:
                    buy_numbers_str += buy_number + ","
                self._buy_data = pd.concat(
                    [
                        self._buy_data,
                        pd.DataFrame(
                            {
                                "date": [self._userInfo.BaseInfoData.now_day],
                                "code": [buy_numbers_str],
                            }
                        ),
                    ],
                    ignore_index=True,
                )
            if len(self._sell_numbers) != 0:
                sell_numbers_str = ""
                for sell_number in self._sell_numbers:
                    sell_numbers_str += sell_number + ","
                self._sell_data = pd.concat(
                    [
                        self._sell_data,
                        pd.DataFrame(
                            {
                                "date": [self._userInfo.BaseInfoData.now_day],
                                "code": [sell_numbers_str],
                            }
                        ),
                    ],
                    ignore_index=True,
                )
            self._result_pick = pd.concat(
                [
                    self._result_pick,
                    pd.DataFrame(
                        {
                            "date": [self._userInfo.BaseInfoData.now_day],
                            "選股數量": [len(self._buy_numbers)],
                        }
                    ),
                ],
                ignore_index=True,
            )
            self._userInfo.RecordUserInfo()

    def Finish(self):
        self._result_pick.set_index("date", inplace=True)
        if not self._buy_data.empty:
            buy_data = self._buy_data.set_index("date")
            buy_data.to_csv("buy.csv")
        if not self._sell_data.empty:
            sell_data = self._sell_data.set_index("date")
            sell_data.to_csv("sell.csv")


class Regular_backTestInOutStrategy(TBacktestInOutStrategy):
    def In(self):
        self._buy_numbers = self._backTestFilterData.ShouldBuyStocks()
        for number in self._buy_numbers:
            self._original_stock.number = int(number)
            price = self._original_stock.get_PriceByDateAndType(
                self._userInfo.BaseInfoData.now_day, stock_data_kind.Close
            )
            Temp_stockNumber = Tools.Count_Stock_Amount(
                self._userInfo.BaseInfoData.now_money, price
            )
            if self._userInfo.BuyStock(
                str(self._original_stock.number), Temp_stockNumber
            ):
                self._has_trade = True
                
class MonthRpUp_backtestInOutStrategy(TBacktestInOutStrategy):
    def Run(self):
        super().Run()
        self._backTestFilterData.RuuFilter()

class RecordHigh_backtestInOutStrategy(TBacktestInOutStrategy):
    def In(self):
        self._backTestFilterData.RuuFilter()
        super().In()