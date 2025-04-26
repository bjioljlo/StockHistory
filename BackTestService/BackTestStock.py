from datetime import datetime

import pandas as pd

import InfomationType as info
import Tools
from BackTestService.BackTestFilterData import (
    BacktestFilterDataFactory,
    BacktestFilterDataType,
)
from BackTestService.BackTestInfoData import BackTestInfoDataPriceByToday
from BackTestService.BackTestInOutStrategy import (
    PERandPBR_BackTestInOutStrategy,
    Regular_backTestInOutStrategy,
    TBacktestInOutStrategy,
)
from BackTestService.FilterAndSignalStrategy import (
    BacktestFilterFactory,
    BacktestFilterType,
    BacktestSignalFactory,
    BacktestSignalType,
    Regular_quotatestFilter,
    TBacktestSignal,
)
from FilterService import All_Stock_Filters_fuc, GetStockData, OriginalStockByYahoo
from FilterService.StockReportHistory import (
    Day_Report,
    Month_Report,
    OM_Growth_Indicator,
    Original_Indicator,
    PEG_Indicator,
    ROE_Indicator,
    Season_Report,
    SeasonReportFactory,
)
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
        userInfo = BackTestInfoDataPriceByToday(
            BaseInfoData(
                mainParament.money_start, mainParament.date_start, mainParament.date_end
            ),
            OriginalStockByYahoo(),
        )
        external_data = ExternalDataFactory.Get_instance(ExternalDataTypeEnum.Normal)
        stocksUsedForExecution = external_data.get_stock_history(
            mainParament.buy_number, mainParament.date_start
        )
        index_ROE = ROE_Indicator(
            "ROE",
            SeasonReportFactory(info.FS_type.CPL, external_data),
            SeasonReportFactory(info.FS_type.BS, external_data),
        )
        backTestFilterData = BacktestFilterDataFactory(
            BacktestFilterDataType.KD,
            self.BuyStrockFun,
            BacktestFilterFactory(BacktestFilterType.KD, [index_ROE]),
            BacktestSignalFactory(BacktestSignalType.KD, OriginalStockByYahoo()),
            mainParament.date_start,
            mainParament.date_end,
        )
        KDInOutStrategy = TBacktestInOutStrategy(
            userInfo, backTestFilterData, OriginalStockByYahoo()
        )
        startTime = datetime.now()
        buy_month = mainParament.date_start
        for index, row in stocksUsedForExecution.iterrows():
            if not userInfo.GoToNextWorkDay(index):
                break
            KDInOutStrategy.Run()
            KDInOutStrategy.Out()
            if userInfo.BaseInfoData.now_day >= buy_month:
                KDInOutStrategy.In()
                buy_month = Tools.changeDateMonth(buy_month, 3)
            KDInOutStrategy.Record()
        # 最後總結算
        KDInOutStrategy.Finish()
        userInfo.RunFinish()
        Temp_alldata = Tools.MixDataFrames(
            {"draw": userInfo._TempResultDraw.Data, "pick": KDInOutStrategy.ResultPick},
            "date",
        )
        Temp_alldata = Tools.MixDataFrames(
            {"all": Temp_alldata, "userinfo": userInfo._TempResultAll.Data}, "date"
        )
        Temp_alldata.to_csv("backtestAll.csv")
        print("回測時間:", datetime.now() - startTime)
        return userInfo._TempResultDraw.Data

    def backtest_PEG_pick(self, mainParament: RecordBackTestParameter):
        """
        PEG選股外加月營收增高
        https://www.finlab.tw/finlab-tw-stock-peg-strategy/#PEG_ding_yi
        """
        userInfo = BackTestInfoDataPriceByToday(
            BaseInfoData(
                mainParament.money_start,
                mainParament.date_start,
                mainParament.date_end,
            ),
            OriginalStockByYahoo(),
        )
        external_data = ExternalDataFactory.Get_instance(ExternalDataTypeEnum.Normal)
        stocksUsedForExecution = external_data.get_stock_history(
            mainParament.buy_number, mainParament.date_start
        )
        index_PEG = PEG_Indicator(
            "PEG",
            OM_Growth_Indicator(
                "OM_Growth",
                Season_Report(
                    info.FS_type.PLA.value, 3, external_data, info.FS_type.PLA
                ),
            ),
            Day_Report("yield_RP", 1, external_data),
        )
        index_MonthUp = Original_Indicator(
            "Month", Month_Report("month_RP", 1, external_data), info.Month_type.MR
        )
        backTestFilterData = BacktestFilterDataFactory(
            BacktestFilterDataType.PEG,
            self.BuyStrockFun,
            BacktestFilterFactory(BacktestFilterType.PEG, [index_PEG, index_MonthUp]),
            BacktestSignalFactory(BacktestSignalType.PEG, OriginalStockByYahoo()),
            mainParament.date_start,
            mainParament.date_end,
        )
        PEGInOutStrategy = TBacktestInOutStrategy(
            userInfo, backTestFilterData, OriginalStockByYahoo()
        )
        buy_month = mainParament.date_start
        startTime = datetime.now()
        for index, row in stocksUsedForExecution.iterrows():
            if not userInfo.GoToNextWorkDay(index):
                break
            PEGInOutStrategy.Run()
            # 出場訊號篩選
            PEGInOutStrategy.Out()
            # 開始篩選
            # 入場訊號篩選
            if userInfo.BaseInfoData.now_day.day >= mainParament.buy_day:
                if (
                    userInfo.BaseInfoData.now_day.month != buy_month.month
                    or userInfo.BaseInfoData.now_day.year != buy_month.year
                ):
                    PEGInOutStrategy.In()
                    buy_month = userInfo.BaseInfoData.now_day
            # 更新資訊
            PEGInOutStrategy.Record()
        # 最後總結算
        PEGInOutStrategy.Finish()
        userInfo.RunFinish()
        Temp_alldata = Tools.MixDataFrames(
            {
                "draw": userInfo._TempResultDraw.Data,
                "pick": PEGInOutStrategy.ResultPick,
            },
            "date",
        )
        Temp_alldata = Tools.MixDataFrames(
            {"all": Temp_alldata, "userinfo": userInfo._TempResultAll.Data}, "date"
        )
        Temp_alldata.to_csv("backtestAll.csv")
        print("回測時間:", datetime.now() - startTime)
        return userInfo._TempResultDraw.Data

    def backtest_Regular_quota(self, mainParament: RecordBackTestParameter):
        """
        定期定額
        """
        userInfo = BackTestInfoDataPriceByToday(
            BaseInfoData(0, mainParament.date_start, mainParament.date_end),
            OriginalStockByYahoo(),
        )
        buy_month = mainParament.date_start
        external_data = ExternalDataFactory.Get_instance(ExternalDataTypeEnum.Normal)
        All_data = external_data.get_stock_history(
            mainParament.buy_number, mainParament.date_start
        )
        backTestFilterData = BacktestFilterDataFactory(
            BacktestFilterDataType.RegularQuota,
            self.BuyStrockFun,
            Regular_quotatestFilter(mainParament.buy_number),
            TBacktestSignal(),
            mainParament.date_start,
            mainParament.date_end,
        )
        RegularInOutStrategy = Regular_backTestInOutStrategy(
            userInfo, backTestFilterData, OriginalStockByYahoo()
        )
        startTime = datetime.now()
        for index, row in All_data.iterrows():
            if not userInfo.GoToNextWorkDay(index):
                break
            # 開始篩選--------------------------------------
            # 定期定額不用篩選--------------------------------------
            # 入場訊號篩選--------------------------------------
            if (
                userInfo.BaseInfoData.now_day.month != buy_month.month
                and userInfo.BaseInfoData.now_day.day >= mainParament.buy_day
            ):
                RegularInOutStrategy.Run()
                userInfo.BaseInfoData.now_money = (
                    userInfo.BaseInfoData.now_money + mainParament.money_start
                )
                userInfo.BaseInfoData.start_money = (
                    userInfo.BaseInfoData.start_money + mainParament.money_start
                )
                RegularInOutStrategy.In()
                buy_month = userInfo.BaseInfoData.now_day
                # 更新資訊--------------------------------------
                RegularInOutStrategy.Record()
        # 最後總結算----------------------------
        RegularInOutStrategy.Finish()
        userInfo.RunFinish()
        Temp_alldata = Tools.MixDataFrames(
            {
                "draw": userInfo._TempResultDraw.Data,
                "pick": RegularInOutStrategy.ResultPick,
            },
            "date",
        )
        Temp_alldata = Tools.MixDataFrames(
            {"all": Temp_alldata, "userinfo": userInfo._TempResultAll.Data}, "date"
        )
        Temp_alldata.to_csv("backtestAll.csv")
        print("回測時間:", datetime.now() - startTime)
        return userInfo._TempResultDraw.Data

    def backtest_Record_high(self, mainParament: RecordBackTestParameter):
        """
        創新高
        https://www.finlab.tw/break-new-high-roe-stock/
        """
        Temp_reset = 0  # 休息日剩餘天數
        userInfo = BackTestInfoDataPriceByToday(
            BaseInfoData(
                mainParament.money_start, mainParament.date_start, mainParament.date_end
            ),
            OriginalStockByYahoo(),
        )
        external_data = ExternalDataFactory.Get_instance(ExternalDataTypeEnum.Normal)
        All_data = external_data.get_stock_history(
            mainParament.buy_number, mainParament.date_start
        )

        index_ROE = ROE_Indicator(
            "ROE",
            SeasonReportFactory(info.FS_type.CPL, external_data),
            SeasonReportFactory(info.FS_type.BS, external_data),
        )

        index_PBR = Original_Indicator(
            "PBR", Day_Report("yield_RP", 1, external_data), info.Day_type.PBR
        )

        backTestFilterData = BacktestFilterDataFactory(
            BacktestFilterDataType.RecordHigh,
            self.BuyStrockFun,
            BacktestFilterFactory(
                BacktestFilterType.RecordHigh, [index_ROE, index_PBR]
            ),
            BacktestSignalFactory(
                BacktestSignalType.RecordHigh, OriginalStockByYahoo()
            ),
            mainParament.date_start,
            mainParament.date_end,
        )

        RecordHighInOutStrategy = TBacktestInOutStrategy(
            userInfo, backTestFilterData, OriginalStockByYahoo()
        )
        startTime = datetime.now()
        for index, row in All_data.iterrows():
            if not userInfo.GoToNextWorkDay(index):
                break
            RecordHighInOutStrategy.Run()
            # 出場訊號篩選--------------------------------------
            RecordHighInOutStrategy.Out()
            # 開始篩選--------------------------------------
            # 入場訊號篩選--------------------------------------
            if Temp_reset <= 0:
                RecordHighInOutStrategy.In()
                Temp_reset = mainParament.change_days
            else:
                Temp_reset = Temp_reset - 1
            # 更新資訊--------------------------------------
            RecordHighInOutStrategy.Record()
        # 最後總結算
        RecordHighInOutStrategy.Finish()
        userInfo.RunFinish()
        Temp_alldata = Tools.MixDataFrames(
            {
                "draw": userInfo._TempResultDraw.Data,
                "pick": RecordHighInOutStrategy.ResultPick,
            },
            "date",
        )
        Temp_alldata = Tools.MixDataFrames(
            {"all": Temp_alldata, "userinfo": userInfo._TempResultAll.Data}, "date"
        )
        Temp_alldata.to_csv("backtestAll.csv")
        print("回測時間:", datetime.now() - startTime)
        return userInfo._TempResultDraw.Data

    def backtest_PERandPBR_Fast(self, mainParament: RecordBackTestParameter):
        """
        14年14倍
        https://www.finlab.tw/%E6%AF%94%E7%AD%96%E7%95%A5%E7%8B%97%E9%82%84%E8%A6%81%E5%AE%89%E5%85%A8%E7%9A%84%E9%81%B8%E8%82%A1%E7%AD%96%E7%95%A5%EF%BC%81/
        """
        Temp_reset = 0  # 休息日剩餘天數
        Temp_changeDays = 0  # 換股剩餘天數

        userInfo = BackTestInfoDataPriceByToday(
            BaseInfoData(
                mainParament.money_start, mainParament.date_start, mainParament.date_end
            ),
            OriginalStockByYahoo(),
        )
        external_data = ExternalDataFactory.Get_instance(ExternalDataTypeEnum.Normal)
        All_data = external_data.get_stock_history(
            mainParament.buy_number, mainParament.date_start
        )

        index_PER = Original_Indicator(  # 本益比
            "PER", Day_Report("yield_RP", 1, external_data), info.Day_type.PER
        )

        index_PBR = Original_Indicator(  # 股價淨值比
            "PBR", Day_Report("yield_RP", 1, external_data), info.Day_type.PBR
        )

        backTestFilterData = BacktestFilterDataFactory(
            BacktestFilterDataType.PERandPBR,
            self.BuyStrockFun,
            BacktestFilterFactory(BacktestFilterType.PERandPBR, [index_PER, index_PBR]),
            BacktestSignalFactory(BacktestSignalType.PERandPBR, OriginalStockByYahoo()),
            mainParament.date_start,
            mainParament.date_end,
        )

        PERandPBRInOutStrategy = PERandPBR_BackTestInOutStrategy(
            userInfo, backTestFilterData, OriginalStockByYahoo()
        )

        startTime = datetime.now()
        for index, row in All_data.iterrows():
            if not userInfo.GoToNextWorkDay(index):
                break
            # 休息日直接跳過
            if Temp_reset > 0 and len(userInfo.HandleStock) == 0:
                print(
                    str(userInfo.BaseInfoData.now_day)
                    + " is reset time:第"
                    + str(Temp_reset)
                    + "天"
                )
                Temp_reset = Temp_reset - 1
            else:
                # 開始篩選
                PERandPBRInOutStrategy.Run()
                # 出場訊號篩選
                if (
                    len(PERandPBRInOutStrategy.FilterData.ShouldBuyStocks())
                    < 100
                    and len(userInfo.HandleStock) > 0
                ):
                    PERandPBRInOutStrategy.Out()
                    Temp_reset = 120
                # 出場訊號篩選
                if Temp_changeDays <= 0 and len(userInfo.HandleStock) > 0:
                    PERandPBRInOutStrategy.Out()
                # 入場訊號篩選
                if (
                    len(PERandPBRInOutStrategy.FilterData.ShouldBuyStocks())
                    >= 100
                    and Temp_reset == 0
                    and len(userInfo.HandleStock) == 0
                ):
                    PERandPBRInOutStrategy.In()
                    Temp_changeDays = 120
            PERandPBRInOutStrategy.Record()
            Temp_changeDays = Temp_changeDays - 1
        # 最後總結算
        PERandPBRInOutStrategy.Finish()
        userInfo.RunFinish()
        Temp_alldata = Tools.MixDataFrames(
            {
                "draw": userInfo._TempResultDraw.Data,
                "pick": PERandPBRInOutStrategy.ResultPick,
            },
            "date",
        )
        Temp_alldata = Tools.MixDataFrames(
            {"all": Temp_alldata, "userinfo": userInfo._TempResultAll.Data}, "date"
        )
        Temp_alldata.to_csv("backtestAll.csv")
        print("回測時間:", datetime.now() - startTime)
        return userInfo._TempResultDraw.Data

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
