from datetime import timedelta

import pandas as pd

import InfomationType as info
import Tools
from BackTestService.BackTestFilterData import (
    BacktestFilterDataFactory,
    BacktestFilterDataType,
)
from BackTestService.BackTestInfoData import BackTestInfoDataPriceByToday
from BackTestService.FilterAndSignalStrategy import (
    BacktestFilterFactory,
    BacktestFilterType,
    BacktestSignalFactory,
    BacktestSignalType,
)
from FilterService import All_Stock_Filters_fuc, GetStockData, OriginalStockByYahoo
from FilterService.StockReportHistory import ROE_Indicator, SeasonReportFactory
from GetExternalDataService import (
    ExternalDataFactory,
    ExternalDataTypeEnum,
    TGetExternalData,
)
from InfomationType import stock_data_kind
from Parameter import RecordBackTestParameter
from StockInfoData import BaseInfoData


class BackTestStock:
    def __init__(self):
        self.bool_check_monthRP_pick: bool = False
        self.bool_check_PER_pick: bool = False
        self.bool_check_volume_pick: bool = False
        self.bool_check_pickOneStock: bool = False
        self.bool_check_price_pick: bool = False
        self.bool_check_PBR_pick: bool = False
        self.bool_check_ROE_pick: bool = False

    def set_check(
        self,
        monthRP_pick,
        PER_pick,
        volume_pick,
        One_pick,
        price_pick,
        PBR_pick,
        ROE_pick,
    ):
        self.bool_check_monthRP_pick = monthRP_pick
        self.bool_check_PER_pick = PER_pick
        self.bool_check_volume_pick = volume_pick
        self.bool_check_pickOneStock = One_pick
        self.bool_check_price_pick = price_pick
        self.bool_check_PBR_pick = PBR_pick
        self.bool_check_ROE_pick = ROE_pick

    def BuyStrockFun(aName: str, aIsBuy: bool):
        pass

    def backtest_KD_pick(self, mainParament: RecordBackTestParameter) -> pd.DataFrame:
        """
        KD值選股
        https://www.finlab.tw/%e7%94%a8kd%e5%80%bc%e9%81%b8%e8%82%a1%ef%bc%9a%e9%82%84%e9%9c%80%e6%90%ad%e9%85%8d%e9%80%99%e4%b8%89%e7%a8%ae%e6%8c%87%e6%a8%99/
        """
        Temp_result_pick = pd.DataFrame(columns=["date", "選股數量"])
        buy_data = pd.DataFrame(columns=["date", "code"]).set_index("date")
        sell_data = pd.DataFrame(columns=["date", "code"]).set_index("date")
        userInfo = BackTestInfoDataPriceByToday(
            BaseInfoData(
                mainParament.money_start, mainParament.date_start, mainParament.date_end
            ),
            OriginalStockByYahoo(),
        )
        self._external_data = ExternalDataFactory.Get_instance(
            ExternalDataTypeEnum.Normal
        )
        Temp_table = self._external_data.get_stock_history(
            mainParament.buy_number, mainParament.date_start
        )
        add_one_day = userInfo.AddOneDay
        sell_stock = userInfo.SellStock
        buy_all_stock = userInfo.BuyAllStock

        self.ROE_index = ROE_Indicator(
            "ROE",
            SeasonReportFactory(info.FS_type.CPL, self._external_data),
            SeasonReportFactory(info.FS_type.BS, self._external_data),
        )
        self._BackTestFilterData = BacktestFilterDataFactory(
            BacktestFilterDataType.KD,
            self.BuyStrockFun,
            BacktestFilterFactory(BacktestFilterType.KD, self.ROE_index),
            BacktestSignalFactory(BacktestSignalType.KD, OriginalStockByYahoo()),
            mainParament.date_start,
            mainParament.date_end,
        )
        # TODO 要新增日期的管理 IBackTestDateStrategy  外部帶入所有要用的的功能 EX.userInfo filter...等...
        for index, row in Temp_table.iterrows():
            if index < userInfo.BaseInfoData.now_day:
                continue
            while userInfo.BaseInfoData.now_day != index:
                if not add_one_day():
                    break
            has_trade = False 

            self._BackTestFilterData.GoToNextWorkDay(userInfo.BaseInfoData.now_day)

            buy_numbers = self._BackTestFilterData.ShouldBuyStocks()

            sell_numbers = self._BackTestFilterData.ShouldSellStocks(
                userInfo.HandleStock
            )
            # TODO 弄一個出入場管理 IBackTestInOutStrategy 從外部帶入userInfo買賣由userInfo做，但何時做進出訊號由上方時間管理做

            # TODO 出場訊號--------------------------------------
            if len(sell_numbers) > 0:
                Temp_data = userInfo.HandleStock
                for key, value in list(Temp_data.items()):
                    if key in sell_numbers:
                        sell_stock(key, value.Amount)
                        has_trade = True
            # TODO 入場訊號--------------------------------------
            if len(buy_numbers) > 0:
                Temp_buy = pd.DataFrame(columns=["code", "volume"]).set_index("code")
                for number in buy_numbers:
                    volume = GetStockData.get_stock_price(
                        number,
                        Tools.DateTime2String(userInfo.BaseInfoData.now_day),
                        stock_data_kind.Volume,
                    )[userInfo.BaseInfoData.now_day]
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
                buy_all_stock(Temp_buy)
                has_trade = True

            # TODO 更新資訊 分散至各自的功能紀錄嗎?還是做一個功能?
            if has_trade:
                if len(buy_numbers) != 0:
                    buy_numbers_str = ""
                    for buy_number in buy_numbers:
                        buy_numbers_str += buy_number + ","
                    buy_data = pd.concat(
                        [
                            buy_data,
                            pd.DataFrame({"date": [index], "code": [buy_numbers_str]}),
                        ],
                        ignore_index=True,
                    )
                if len(sell_numbers) != 0:
                    sell_numbers_str = ""
                    for sell_number in sell_numbers:
                        sell_numbers_str += sell_number + ","
                    sell_data = pd.concat(
                        [
                            sell_data,
                            pd.DataFrame({"date": [index], "code": [sell_numbers_str]}),
                        ]
                    )
                userInfo.RecordUserInfo()
                Temp_result_pick = pd.concat(
                    [
                        Temp_result_pick,
                        pd.DataFrame(
                            {
                                "date": [userInfo.BaseInfoData.now_day],
                                "選股數量": [len(buy_numbers)],
                            }
                        ),
                    ],
                    ignore_index=True,
                )
        # TODO 更新資訊 最後完結輸出檔案
        if not buy_data.empty:
            buy_data = buy_data.set_index("date")
            buy_data.to_csv("buy.csv")
        if not sell_data.empty:
            sell_data = sell_data.set_index("date")
            sell_data.to_csv("sell.csv")
        # 最後總結算----------------------------
        Temp_result_pick.set_index("date", inplace=True)
        userInfo.RunFinish()
        Temp_alldata = Tools.MixDataFrames(
            {"draw": userInfo._TempResultDraw.Data, "pick": Temp_result_pick}, "date"
        )

        Temp_alldata = Tools.MixDataFrames(
            {"all": Temp_alldata, "userinfo": userInfo._TempResultAll.Data}, "date"
        )

        userInfo._TempResultDraw.Data.to_csv("backtestdata.csv")
        userInfo._TempTradeInfo.Data.to_csv("backtesttrade.csv")

        Temp_alldata.to_csv("backtestAll.csv")
        return userInfo._TempResultDraw.Data

    def backtest_PEG_pick_Fast(self, mainParament: RecordBackTestParameter):
        """PEG選股外加月營收增高 https://www.finlab.tw/finlab-tw-stock-peg-strategy/#PEG_ding_yi"""
        userInfo = BackTestInfoDataPriceByToday(
            BaseInfoData(
                mainParament.money_start, mainParament.date_start, mainParament.date_end
            )
        )
        buy_month = mainParament.date_start
        Temp_result_pick = pd.DataFrame(columns=["date", "選股數量"])
        All_data = TGetExternalData().get_stock_history(
            mainParament.buy_number, mainParament.date_start
        )
        add_one_day = userInfo.AddOneDay
        Record_userInfo = userInfo.RecordUserInfo
        Recod_tradeInfo = userInfo.RecodTradeInfo
        sell_stock = userInfo.SellStock
        buy_all_stock = userInfo.BuyAllStock
        for index, row in All_data.iterrows():
            has_trade = False
            while userInfo.BaseInfoData.now_day != index:
                # 加一天----------------------------
                if not add_one_day():
                    break
            # 出場訊號篩選-----------------------------------
            if len(userInfo.HandleStock) > 0:
                Temp_data = userInfo.HandleStock
                for key, value in list(Temp_data.items()):
                    if GetStockData.get_stock_price(
                        key, userInfo.BaseInfoData.now_day, info.Price_type.Close
                    ) < GetStockData.get_stock_MA(
                        key, userInfo.BaseInfoData.now_day, 20
                    ):
                        sell_stock(key, value.Amount)
                        has_trade = True
            # 開始篩選--------------------------------------
            # 入場訊號篩選--------------------------------------
            Temp_buy = pd.DataFrame()
            if userInfo.BaseInfoData.now_day.day >= mainParament.buy_day:
                if (
                    userInfo.BaseInfoData.now_day.month != buy_month.month
                    or userInfo.BaseInfoData.now_day.year != buy_month.year
                ):

                    Temp_result0 = {}
                    if self.bool_check_monthRP_pick:
                        Temp_result0["month"] = GetStockData.get_monthRP_up(
                            userInfo.BaseInfoData.now_day,
                            mainParament.smoothAVG,
                            mainParament.upMonth,
                        )
                        Temp_result0["PEG"] = GetStockData.get_PEG_range(
                            userInfo.BaseInfoData.now_day, 0.66, 1
                        )
                        Temp_result0["result"] = Tools.MixDataFrames(Temp_result0)
                    Temp_buy = Temp_result0["result"]
                    if not Temp_buy.empty:
                        Temp_buy = Temp_buy.sort_values(by="PEG")
                        Temp_buy = Temp_buy.head(10)
                        buy_all_stock(Temp_buy)
                        has_trade = True
                    buy_month = userInfo.BaseInfoData.now_day
            # 更新資訊--------------------------------------
            if len(userInfo.HandleStock) > 0 or has_trade:
                Record_userInfo()
                Recod_tradeInfo()
                Temp_result_pick = pd.concat(
                    [
                        Temp_result_pick,
                        pd.DataFrame(
                            {
                                "date": [userInfo.BaseInfoData.now_day],
                                "選股數量": [len(Temp_buy)],
                            }
                        ),
                    ],
                    ignore_index=True,
                )
            # 加一天----------------------------
            if not userInfo.AddOneDay():
                break
            else:
                continue
        # 最後總結算----------------------------
        Temp_result_pick.set_index("date", inplace=True)
        userInfo.RunFinish()
        Temp_alldata = Tools.MixDataFrames(
            {"draw": userInfo._TempResultDraw, "pick": Temp_result_pick}, "date"
        )
        Temp_alldata = Tools.MixDataFrames(
            {"all": Temp_alldata, "userinfo": userInfo._TempResultAll}, "date"
        )

        userInfo._TempResultDraw.to_csv("backtestdata.csv")
        userInfo._TempTradeInfo.to_csv("backtesttrade.csv")
        Temp_alldata.to_csv("backtestAll.csv")
        return userInfo._TempResultDraw

    def backtest_Regular_quota_Fast(self, mainParament: RecordBackTestParameter):
        """定期定額"""
        userInfo = BackTestInfoDataPriceByToday(
            BaseInfoData(0, mainParament.date_start, mainParament.date_end)
        )
        buy_month = mainParament.date_start
        Temp_result_pick = pd.DataFrame(columns=["date", "選股數量"])

        All_data = TGetExternalData().get_stock_history(
            mainParament.buy_number, mainParament.date_start
        )
        add_one_day = userInfo.AddOneDay
        Record_userInfo = userInfo.RecordUserInfo
        Recod_tradeInfo = userInfo.RecodTradeInfo
        buy_stock = userInfo.BuyStock
        for index, row in All_data.iterrows():
            while userInfo.BaseInfoData.now_day != index:  # 消掉假日的誤差用的
                # 加一天----------------------------
                if not add_one_day():
                    break
            # 開始篩選--------------------------------------
            # 定期定額不用篩選--------------------------------------
            # 入場訊號篩選--------------------------------------
            if (
                userInfo.BaseInfoData.now_day.month != buy_month.month
                and userInfo.BaseInfoData.now_day.day >= mainParament.buy_day
            ):
                Temp_price = row["Adj Close"]
                userInfo.BaseInfoData.now_money = (
                    userInfo.BaseInfoData.now_money + mainParament.money_start
                )
                userInfo.BaseInfoData.start_money = (
                    userInfo.BaseInfoData.start_money + mainParament.money_start
                )
                Temp_stockNumber = Tools.Count_Stock_Amount(
                    mainParament.money_start, Temp_price
                )
                buy_stock(mainParament.buy_number, Temp_stockNumber)
                buy_month = userInfo.BaseInfoData.now_day
                # 更新資訊--------------------------------------
                Record_userInfo()
                Recod_tradeInfo()
                Temp_result_pick = pd.concat(
                    [
                        Temp_result_pick,
                        pd.DataFrame(
                            {"date": [userInfo.BaseInfoData.now_day], "選股數量": [1]}
                        ),
                    ],
                    ignore_index=True,
                )
            # 加一天----------------------------
            if not add_one_day():
                break

        # 最後總結算----------------------------
        Temp_result_pick.set_index("date", inplace=True)
        userInfo.RunFinish()
        Temp_alldata = Tools.MixDataFrames(
            {"draw": userInfo._TempResultDraw, "pick": Temp_result_pick}, "date"
        )
        Temp_alldata = Tools.MixDataFrames(
            {"all": Temp_alldata, "userinfo": userInfo._TempResultAll}, "date"
        )

        userInfo._TempResultDraw.to_csv("backtestdata.csv")
        userInfo._TempTradeInfo.to_csv("backtesttrade.csv")
        Temp_alldata.to_csv("backtestAll.csv")
        return userInfo._TempResultDraw

    def backtest_Record_high_Fast(self, mainParament: RecordBackTestParameter):
        """#創新高 https://www.finlab.tw/break-new-high-roe-stock/"""
        Temp_reset = 0  # 休息日剩餘天數
        userInfo = BackTestInfoDataPriceByToday(
            BaseInfoData(
                mainParament.money_start, mainParament.date_start, mainParament.date_end
            )
        )
        Temp_result_pick = pd.DataFrame(columns=["date", "選股數量"])
        All_data = TGetExternalData().get_stock_history(
            mainParament.buy_number, mainParament.date_start
        )
        add_one_day = userInfo.AddOneDay
        Record_userInfo = userInfo.RecordUserInfo
        Recod_tradeInfo = userInfo.RecodTradeInfo
        sell_stock = userInfo.SellStock
        buy_all_stock = userInfo.BuyAllStock
        for index, row in All_data.iterrows():
            has_trade = False
            while userInfo.BaseInfoData.now_day != index:
                # 加一天----------------------------
                if not add_one_day():
                    break
            # 出場訊號篩選--------------------------------------
            if len(userInfo.HandleStock) > 0:
                Temp_data = userInfo.HandleStock
                for key, value in list(Temp_data.items()):
                    if GetStockData().get_stock_price(
                        key, userInfo.BaseInfoData.now_day, stock_data_kind.Close
                    ) < GetStockData.get_stock_MA(
                        key, userInfo.BaseInfoData.now_day, 20
                    ):
                        sell_stock(key, value.Amount)
                        has_trade = True
            # 開始篩選--------------------------------------
            Temp_result = pd.DataFrame()
            Temp_result0 = {}
            if Temp_reset <= 0:
                if self.bool_check_ROE_pick:
                    Temp_result0["ROE"] = GetStockData.get_ROE_range(
                        userInfo.BaseInfoData.now_day,
                        mainParament.ROE_end,
                        mainParament.ROE_start,
                    )
                if self.bool_check_ROE_pick:
                    Temp_result0["ROE_last_seson"] = GetStockData.get_ROE_range(
                        userInfo.BaseInfoData.now_day - timedelta(weeks=12), 10000, 1
                    )
                if self.bool_check_PBR_pick:
                    Temp_result0["PBR"] = GetStockData.get_PBR_range(
                        userInfo.BaseInfoData.now_day,
                        mainParament.PBR_end,
                        mainParament.PBR_start,
                    )
                Temp_result = Tools.MixDataFrames(Temp_result0)

            # 入場訊號篩選--------------------------------------
            if Temp_reset <= 0 and len(Temp_result) > 0:
                Temp_buy0 = {"result": Temp_result}
                Temp_buy0["result"]["point"] = (
                    Temp_result["ROE"] / Temp_result["ROE_R"]
                ) / Temp_result["PBR"]
                if self.bool_check_price_pick:
                    Temp_buy0["price"] = All_Stock_Filters_fuc(
                        userInfo.BaseInfoData.now_day, Temp_result
                    ).get_Filter(
                        "price",
                        mainParament.price_high,
                        mainParament.price_low,
                        info.Price_type.Close,
                    )
                    Temp_buy0["result"] = Tools.MixDataFrames(Temp_buy0)
                if self.bool_check_volume_pick:
                    Temp_buy0["volume"] = GetStockData.get_AVG_value(
                        userInfo.BaseInfoData.now_day,
                        mainParament.volumeAVG,
                        mainParament.volumeDays,
                        Temp_result,
                    )
                    Temp_buy0["result"] = Tools.MixDataFrames(Temp_buy0)

                Temp_buy = Tools.MixDataFrames(Temp_buy0)

                Temp_buy = Temp_buy.sort_values(by="point", ascending=False)

                Temp_buy1 = {"result": Temp_buy}
                Temp_buy1["high"] = All_Stock_Filters_fuc(
                    userInfo.BaseInfoData.now_day, Temp_buy
                ).get_Filter_RecordHigh(
                    mainParament.change_days,
                    mainParament.Record_high_day,
                    info.Price_type.High,
                )
                Temp_buy = Tools.MixDataFrames(Temp_buy1)

                if not Temp_buy.empty:
                    Temp_buy = Temp_buy.sort_values(by="point", ascending=False)
                    Temp_buy = Temp_buy.head(3)
                    buy_all_stock(Temp_buy)
                    has_trade = True
            # 更新資訊--------------------------------------
            if Temp_reset <= 0:
                Temp_reset = mainParament.change_days
            if len(userInfo.HandleStock) > 0 or has_trade:
                Record_userInfo()
                Recod_tradeInfo()
                Temp_result_pick = pd.concat(
                    [
                        Temp_result_pick,
                        pd.DataFrame(
                            {
                                "date": [userInfo.BaseInfoData.now_day],
                                "選股數量": [len(Temp_result)],
                            }
                        ),
                    ],
                    ignore_index=True,
                )
            # 加一天----------------------------
            if not add_one_day():
                break
            else:
                Temp_reset = Temp_reset - 1

        # 最後總結算----------------------------
        Temp_result_pick.set_index("date", inplace=True)
        userInfo.RunFinish()
        Temp_alldata = Tools.MixDataFrames(
            {"draw": userInfo._TempResultDraw, "pick": Temp_result_pick}, "date"
        )
        Temp_alldata = Tools.MixDataFrames(
            {"all": Temp_alldata, "userinfo": userInfo._TempResultAll}, "date"
        )
        userInfo._TempResultDraw.to_csv("backtestdata.csv")
        userInfo._TempTradeInfo.to_csv("backtesttrade.csv")
        Temp_alldata.to_csv("backtestAll.csv")
        return userInfo._TempResultDraw

    def backtest_PERandPBR_Fast(self, mainParament: RecordBackTestParameter):
        """
        # 14年14倍
        # https://www.finlab.tw/%E6%AF%94%E7%AD%96%E7%95%A5%E7%8B%97%E9%82%84%E8%A6%81%E5%AE%89%E5%85%A8%E7%9A%84%E9%81%B8%E8%82%A1%E7%AD%96%E7%95%A5%EF%BC%81/
        """
        Temp_reset = 0  # 休息日剩餘天數
        Temp_changeDays = 0  # 換股剩餘天數
        Temp_result_pick = pd.DataFrame(columns=["date", "選股數量"])

        userInfo = BackTestInfoDataPriceByToday(
            BaseInfoData(
                mainParament.money_start, mainParament.date_start, mainParament.date_end
            )
        )

        All_data = TGetExternalData().get_stock_history(
            mainParament.buy_number, mainParament.date_start
        )

        add_one_day = userInfo.AddOneDay
        sell_all_stock = userInfo.SellAllStock
        buy_all_stock = userInfo.BuyAllStock
        for index, row in All_data.iterrows():
            has_trade = False
            while userInfo.BaseInfoData.now_day != index:
                # 加一天----------------------------
                if not add_one_day():
                    break

            # 休息日直接跳過
            if Temp_reset > 0 and len(userInfo.HandleStock) == 0:
                print(
                    str(userInfo.BaseInfoData.now_day)
                    + " is reset time:第"
                    + str(Temp_reset)
                    + "天"
                )
                if not add_one_day():  # 加一天
                    break
                Temp_reset = Temp_reset - 1
                continue

            # 開始篩選--------------------------------------
            Temp_result0 = {}
            Temp_result = pd.DataFrame()
            if self.bool_check_PER_pick:  # PER pick
                Temp_result0["PER"] = GetStockData.get_PER_range(
                    userInfo.BaseInfoData.now_day,
                    mainParament.PER_end,
                    mainParament.PER_start,
                )
            if self.bool_check_PBR_pick:  # PBR pick
                Temp_result0["PBR"] = GetStockData.get_PBR_range(
                    userInfo.BaseInfoData.now_day,
                    mainParament.PBR_end,
                    mainParament.PBR_start,
                )
            Temp_result = Tools.MixDataFrames(Temp_result0)

            # 出場訊號篩選--------------------------------------
            if (
                len(Temp_result) < mainParament.Pick_amount
                and len(userInfo.HandleStock) > 0
            ):
                sell_all_stock()
                Temp_reset = 120
                has_trade = True
            # 出場訊號篩選--------------------------------------
            if Temp_changeDays <= 0 and len(userInfo.HandleStock) > 0:
                sell_all_stock()
                has_trade = True

            # 入場訊號篩選--------------------------------------
            if (
                len(Temp_result) >= mainParament.Pick_amount
                and Temp_reset == 0
                and len(userInfo.HandleStock) == 0
            ):
                Temp_buy0 = {"result": Temp_result}
                if self.bool_check_price_pick:
                    Temp_buy0["price"] = All_Stock_Filters_fuc(
                        userInfo.BaseInfoData.now_day, Temp_result
                    ).get_Filter(
                        "price",
                        mainParament.price_high,
                        mainParament.price_low,
                        info.Price_type.Close,
                    )
                    Temp_buy0["price"] = Temp_buy0["price"].sort_values(
                        by="price", ascending=False
                    )
                if self.bool_check_volume_pick:
                    Temp_buy0["volume"] = GetStockData.get_AVG_value(
                        userInfo.BaseInfoData.now_day,
                        mainParament.volumeAVG,
                        mainParament.volumeDays,
                        Temp_result,
                    )
                    Temp_buy0["volume"] = Temp_buy0["volume"].sort_values(
                        by="volume", ascending=False
                    )
                Temp_buy = Tools.MixDataFrames(Temp_buy0)
                if Temp_buy0.__contains__("price") and not Temp_buy0["price"].empty:
                    Temp_buy = Temp_buy.sort_values(by="price", ascending=False)
                if Temp_buy0.__contains__("volume") and not Temp_buy0["volume"].empty:
                    Temp_buy = Temp_buy.sort_values(by="volume", ascending=False)
                buy_all_stock(Temp_buy)
                Temp_changeDays = mainParament.change_days
                has_trade = True
            # 更新資訊--------------------------------------
            if len(userInfo.HandleStock) > 0 or has_trade:
                userInfo.RecordUserInfo()
                userInfo.RecodTradeInfo()
                Temp_result_pick = pd.concat(
                    [
                        Temp_result_pick,
                        pd.DataFrame(
                            {
                                "date": [userInfo.BaseInfoData.now_day],
                                "選股數量": [len(Temp_result)],
                            }
                        ),
                    ],
                    ignore_index=True,
                )
            # 加一天----------------------------
            if not add_one_day():
                break
            else:
                Temp_changeDays = Temp_changeDays - 1

        # 最後總結算----------------------------
        Temp_result_pick.set_index("date", inplace=True)
        userInfo.RunFinish()
        Temp_alldata = Tools.MixDataFrames(
            {"draw": userInfo._TempResultDraw, "pick": Temp_result_pick}, "date"
        )

        Temp_alldata = Tools.MixDataFrames(
            {"all": Temp_alldata, "userinfo": userInfo._TempResultAll}, "date"
        )

        userInfo._TempResultDraw.to_csv("backtestdata.csv")
        userInfo._TempTradeInfo.to_csv("backtesttrade.csv")
        Temp_alldata.to_csv("backtestAll.csv")
        return userInfo._TempResultDraw

    def backtest_monthRP_Up_Fast(self, mainParament: RecordBackTestParameter):
        """
        # 月營收增高
        # https://www.finlab.tw/%e4%b8%89%e7%a8%ae%e6%9c%88%e7%87%9f%e6%94%b6%e9%80%b2%e9%9a%8e%e7%9c%8b%e6%b3%95/#ji_ji_xuan_gu_cheng_zhang_fa
        """
        Temp_change = 0  # 換股剩餘天數
        userInfo = BackTestInfoDataPriceByToday(
            BaseInfoData(
                mainParament.money_start, mainParament.date_start, mainParament.date_end
            )
        )
        Temp_result_pick = pd.DataFrame(columns=["date", "選股數量"])
        All_data = TGetExternalData().get_stock_history(
            mainParament.buy_number, mainParament.date_start
        )
        add_one_day = userInfo.AddOneDay
        sell_all_stock = userInfo.SellAllStock
        buy_all_stock = userInfo.BuyAllStock
        for index, row in All_data.iterrows():
            has_trade = False
            while userInfo.BaseInfoData.now_day != index:
                # 加一天----------------------------
                if not add_one_day():
                    break
            # 出場訊號篩選--------------------------------------
            if Temp_change <= 0 and len(userInfo.HandleStock) > 0:
                sell_all_stock()
                has_trade = True
            # 開始篩選--------------------------------------
            Temp_result0 = {}
            Temp_result = pd.DataFrame()
            if Temp_change <= 0:
                if self.bool_check_monthRP_pick:  # 月營收升高篩選(月為單位)
                    Temp_result0["month"] = GetStockData.get_monthRP_up(
                        userInfo.BaseInfoData.now_day,
                        mainParament.smoothAVG,
                        mainParament.upMonth,
                    )
                if self.bool_check_ROE_pick:  # ROE
                    Temp_result0["ROE"] = GetStockData.get_ROE_range(
                        userInfo.BaseInfoData.now_day,
                        mainParament.ROE_start,
                        mainParament.ROE_end,
                    )
                if self.bool_check_PBR_pick:  # PBR
                    Temp_result0["PBR"] = GetStockData.get_PBR_range(
                        userInfo.BaseInfoData.now_day,
                        mainParament.PBR_start,
                        mainParament.PBR_end,
                    )
                if self.bool_check_PER_pick:  # PER
                    Temp_result0["PER"] = GetStockData.get_PER_range(
                        userInfo.BaseInfoData.now_day,
                        mainParament.PER_start,
                        mainParament.PER_end,
                    )
                Temp_result = Tools.MixDataFrames(Temp_result0)
            # 入場訊號篩選--------------------------------------
            if (
                Temp_change <= 0
                and len(userInfo.HandleStock) <= 0
                and len(Temp_result) > mainParament.Pick_amount
            ):
                Temp_buy0 = {"result": Temp_result}
                if self.bool_check_price_pick:
                    Temp_buy0["price"] = All_Stock_Filters_fuc(
                        userInfo.BaseInfoData.now_day, Temp_result
                    ).get_Filter(
                        "price",
                        mainParament.price_high,
                        mainParament.price_low,
                        info.Price_type.Close,
                    )
                    Temp_buy0["price"] = Temp_buy0["price"].sort_values(
                        by="price", ascending=False
                    )
                if self.bool_check_volume_pick:
                    Temp_buy0["volume"] = GetStockData.get_AVG_value(
                        userInfo.BaseInfoData.now_day,
                        mainParament.volumeAVG,
                        mainParament.volumeDays,
                        Temp_result,
                    )
                    Temp_buy0["volume"] = Temp_buy0["volume"].sort_values(
                        by="volume", ascending=False
                    )
                Temp_buy = Tools.MixDataFrames(Temp_buy0)
                if Temp_buy0.__contains__("price") and not Temp_buy0["price"].empty:
                    Temp_buy = Temp_buy.sort_values(by="price", ascending=False)
                if Temp_buy0.__contains__("volume") and not Temp_buy0["volume"].empty:
                    Temp_buy = Temp_buy.sort_values(by="volume", ascending=False)
                buy_all_stock(Temp_buy)
                has_trade = True
            # 更新資訊--------------------------------------
            if Temp_change <= 0:
                Temp_change = mainParament.change_days
            if has_trade or len(userInfo.HandleStock) > 0:
                userInfo.RecordUserInfo()
                userInfo.RecodTradeInfo()
                Temp_result_pick = pd.concat(
                    [
                        Temp_result_pick,
                        pd.DataFrame(
                            {
                                "date": [userInfo.BaseInfoData.now_day],
                                "選股數量": [len(Temp_result)],
                            }
                        ),
                    ],
                    ignore_index=True,
                )
            # 加一天----------------------------
            if not add_one_day():
                break
            else:
                Temp_change = Temp_change - 1
        # 最後總結算----------------------------
        Temp_result_pick.set_index("date", inplace=True)
        userInfo.RunFinish()
        Temp_alldata = Tools.MixDataFrames(
            {"draw": userInfo._TempResultDraw, "pick": Temp_result_pick}, "date"
        )

        Temp_alldata = Tools.MixDataFrames(
            {"all": Temp_alldata, "userinfo": userInfo._TempResultAll}, "date"
        )

        userInfo._TempResultDraw.to_csv("backtestdata.csv")
        userInfo._TempTradeInfo.to_csv("backtesttrade.csv")
        Temp_alldata.to_csv("backtestAll.csv")
        return userInfo._TempResultDraw
