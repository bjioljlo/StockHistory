from datetime import datetime

import pandas as pd

import Common.InfomationType as info
import Common.Tools as Tools

from BackTestService.BackTestFilterData import (
    BacktestFilterDataFactory,
    BacktestFilterDataType,
)
from BackTestService.BackTestInfoData import BackTestInfoDataPriceByToday
from BackTestService.BackTestInOutStrategy import (
    KD_BackTestInOutStrategy,
    MonthRpUp_backtestInOutStrategy,
    PEG_BackTestInOutStrategy,
    PERandPBR_BackTestInOutStrategy,
    RecordHigh_backtestInOutStrategy,
    Regular_backTestInOutStrategy,
)
from BackTestService.BackTestFilter import (
    BacktestFilterFactory,
    BacktestFilterType,
    Regular_quotatestFilter,
)
from BackTestService.BackTestSignal import (
    BacktestSignalFactory,
    BacktestSignalType,
    TBacktestSignal,
)
from ExternalService.ExternalDataFactory import ExternalDataFactory
from FilterService.StockHistory import OriginalStock
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

from Common.Parameter import RecordBackTestParameter
from Common.StockInfoData import BaseInfoData


class BackTestStock:
    def __init__(self, original_stock: OriginalStock, external_data_factory: ExternalDataFactory) -> None:
        self.bool_check_monthRP_pick: bool = False
        self.bool_check_PER_pick: bool = False
        self.bool_check_volume_pick: bool = False
        self.bool_check_pickOneStock: bool = False
        self.bool_check_price_pick: bool = False
        self.bool_check_PBR_pick: bool = False
        self.bool_check_ROE_pick: bool = False
        self._original_stock = original_stock
        self._external_data_factory = external_data_factory
        

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

    def backtest_KD_pick(self, mainParament: RecordBackTestParameter, folderName: str, callback=None) -> pd.DataFrame:
        """
        KD值選股
        https://www.finlab.tw/%e7%94%a8kd%e5%80%bc%e9%81%b8%e8%82%a1%ef%bc%9a%e9%82%84%e9%9c%80%e6%90%ad%e9%85%8d%e9%80%99%e4%b8%89%e7%a8%ae%e6%8c%87%e6%a8%99/
        """
        userInfo = BackTestInfoDataPriceByToday(
            BaseInfoData(
                mainParament.money_start, mainParament.date_start, mainParament.date_end
            ),
            self._original_stock,
            folderName
        )
        external_data = self._external_data_factory.Get_instance()
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
            BacktestSignalFactory(BacktestSignalType.KD, self._original_stock),
            mainParament.date_start,
            mainParament.date_end,
        )
        KDInOutStrategy = KD_BackTestInOutStrategy(
            userInfo, backTestFilterData, self._original_stock
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
        KDInOutStrategy.Finish(folderName)
        userInfo.RunFinish()
        Temp_alldata = Tools.MixDataFrames(
            {"draw": userInfo._TempResultDraw.Data, "pick": KDInOutStrategy.ResultPick},
            "date",
        )
        Temp_alldata = Tools.MixDataFrames(
            {"all": Temp_alldata, "userinfo": userInfo._TempResultAll.Data}, "date"
        )
        Temp_alldata.to_csv(folderName + "backtestAll.csv")
        print("KD值選股-回測時間:", datetime.now() - startTime)
        return userInfo

    def backtest_PEG_pick(self, mainParament: RecordBackTestParameter, folderName: str, callback=None):
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
            self._original_stock,
            folderName
        )
        external_data = self._external_data_factory.Get_instance()
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
            BacktestSignalFactory(BacktestSignalType.PEG, self._original_stock),
            mainParament.date_start,
            mainParament.date_end,
        )
        PEGInOutStrategy = PEG_BackTestInOutStrategy(
            userInfo, backTestFilterData, self._original_stock
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
        PEGInOutStrategy.Finish(folderName)
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
        Temp_alldata.to_csv(folderName + "backtestAll.csv")
        print("PEG選股外加月營收增高-回測時間:", datetime.now() - startTime)
        return userInfo

    def backtest_Regular_quota(self, mainParament: RecordBackTestParameter, folderName: str, callback=None):
        """
        定期定額
        """
        userInfo = BackTestInfoDataPriceByToday(
            BaseInfoData(0, mainParament.date_start, mainParament.date_end),
            self._original_stock,
            folderName
        )
        buy_month = mainParament.date_start
        external_data = self._external_data_factory.Get_instance()
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
            userInfo, backTestFilterData, self._original_stock
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
        RegularInOutStrategy.Finish(folderName)
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
        Temp_alldata.to_csv(folderName + "backtestAll.csv")
        print("定期定額-回測時間:", datetime.now() - startTime)
        return userInfo

    def backtest_Record_high(self, mainParament: RecordBackTestParameter, folderName: str, callback=None):
        """
        創新高
        https://www.finlab.tw/break-new-high-roe-stock/
        """
        Temp_reset = 0  # 休息日剩餘天數
        userInfo = BackTestInfoDataPriceByToday(
            BaseInfoData(
                mainParament.money_start, mainParament.date_start, mainParament.date_end
            ),
            self._original_stock,
            folderName
        )
        external_data = self._external_data_factory.Get_instance()
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
                BacktestFilterType.RecordHigh, [index_ROE, index_PBR, self._original_stock]
            ),
            BacktestSignalFactory(
                BacktestSignalType.RecordHigh, self._original_stock
            ),
            mainParament.date_start,
            mainParament.date_end,
        )

        RecordHighInOutStrategy = RecordHigh_backtestInOutStrategy(
            userInfo, backTestFilterData, self._original_stock
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
        RecordHighInOutStrategy.Finish(folderName)
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
        Temp_alldata.to_csv(folderName + "backtestAll.csv")
        print("創新高-回測時間:", datetime.now() - startTime)
        return userInfo
    
    def backtest_PERandPBR(self, mainParament: RecordBackTestParameter, folderName: str, callback=None):
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
            self._original_stock,
            folderName
        )
        external_data = self._external_data_factory.Get_instance()
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
            BacktestSignalFactory(BacktestSignalType.PERandPBR, self._original_stock),
            mainParament.date_start,
            mainParament.date_end,
        )
        PERandPBRInOutStrategy = PERandPBR_BackTestInOutStrategy(
            userInfo, backTestFilterData, self._original_stock
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
                if (len(userInfo.HandleStock) > 0                    
                    and len(PERandPBRInOutStrategy.FilterData.ShouldBuyStocks())
                    < 100
                ):
                    PERandPBRInOutStrategy.Out()
                    Temp_reset = 60
                # 出場訊號篩選
                if len(userInfo.HandleStock) > 0 and Temp_changeDays <= 0:
                    PERandPBRInOutStrategy.Out()
                # 入場訊號篩選
                if (len(userInfo.HandleStock) == 0 and
                    len(PERandPBRInOutStrategy.FilterData.ShouldBuyStocks()) >= 100
                ):
                    PERandPBRInOutStrategy.In()
                    Temp_changeDays = 60
            PERandPBRInOutStrategy.Record()
            Temp_changeDays = Temp_changeDays - 1
        # 最後總結算
        PERandPBRInOutStrategy.Finish(folderName)
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
        Temp_alldata.to_csv(folderName + "backtestAll.csv")
        print("14年14倍-回測時間:", datetime.now() - startTime)
        return userInfo

    def backtest_monthRP_Up(self, mainParament: RecordBackTestParameter, folderName: str, callback=None):
        """
        # 月營收增高
        # https://www.finlab.tw/%e4%b8%89%e7%a8%ae%e6%9c%88%e7%87%9f%e6%94%b6%e9%80%b2%e9%9a%8e%e7%9c%8b%e6%b3%95/#ji_ji_xuan_gu_cheng_zhang_fa
        """
        Temp_change = 0  # 換股剩餘天數
        userInfo = BackTestInfoDataPriceByToday(
            BaseInfoData(
                mainParament.money_start, mainParament.date_start, mainParament.date_end
            ),
            self._original_stock,
            folderName
        )
        external_data = self._external_data_factory.Get_instance()
        All_data = external_data.get_stock_history(
            mainParament.buy_number, mainParament.date_start
        )
        index_ROE = ROE_Indicator(
            "ROE",
            SeasonReportFactory(info.FS_type.CPL, external_data),
            SeasonReportFactory(info.FS_type.BS, external_data),
        )
        index_PBR = Original_Indicator(  # 股價淨值比
            "PBR", Day_Report("yield_RP", 1, external_data), info.Day_type.PBR
        )
        index_PER = Original_Indicator(  # 本益比
            "PER", Day_Report("yield_RP", 1, external_data), info.Day_type.PER
        )
        Month_index = Original_Indicator("Month", Month_Report("month_RP", 1, external_data), info.Month_type.MR)
        backTestFilterData = BacktestFilterDataFactory(
            BacktestFilterDataType.MonthRP_Up,
            self.BuyStrockFun,
            BacktestFilterFactory(BacktestFilterType.MonthRP_Up, [Month_index, index_ROE, index_PER, index_PBR]),
            BacktestSignalFactory(BacktestSignalType.MonthRP_Up, self._original_stock),
            mainParament.date_start,
            mainParament.date_end,
        )
        MonthRpUpInOutStrategy = MonthRpUp_backtestInOutStrategy(
            userInfo, backTestFilterData, self._original_stock
        )
        startTime = datetime.now()
        for index, row in All_data.iterrows():
            if not userInfo.GoToNextWorkDay(index):
                break
            # 開始篩選
            MonthRpUpInOutStrategy.Run()
            # 出場訊號篩選
            if Temp_change <= 0 and len(userInfo.HandleStock) > 0:
                MonthRpUpInOutStrategy.Out()
            # 入場訊號篩選
            if (
                Temp_change <= 0
                and len(userInfo.HandleStock) <= 0
                and len(MonthRpUpInOutStrategy.FilterData.ShouldBuyStocks()) > mainParament.Pick_amount
            ):
                MonthRpUpInOutStrategy.In()
            # 更新資訊--------------------------------------
            MonthRpUpInOutStrategy.Record()
            if Temp_change <= 0:
                Temp_change = mainParament.change_days
            else:
                Temp_change = Temp_change - 1
        # 最後總結算----------------------------
        MonthRpUpInOutStrategy.Finish(folderName)
        userInfo.RunFinish()
        Temp_alldata = Tools.MixDataFrames(
            {
                "draw": userInfo._TempResultDraw.Data,
                "pick": MonthRpUpInOutStrategy.ResultPick,
            },
            "date",
        )
        Temp_alldata = Tools.MixDataFrames(
            {"all": Temp_alldata, "userinfo": userInfo._TempResultAll.Data}, "date"
        )
        Temp_alldata.to_csv(folderName + "backtestAll.csv")
        print("月營收增高-回測時間:", datetime.now() - startTime)
        return userInfo
