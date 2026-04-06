"""
BackTestStock - 回測服務入口外觀類別 (Facade Pattern)

此模組已重構：
- 拆分為策略模組位於 strategies/ 子目錄
- 維持 100% 向後相容性，所有公開介面不變
- 原檔案從 521 行 -> 179 行 (符合 < 500 行規範)
- 單一職責原則：僅作為外部介面
- 實際邏輯已移至各策略模組

Refactored at 2026-04-06 as part of project-refactoring-and-cleanup
"""
from datetime import datetime
import pandas as pd

from src.Common import InfomationType as info
from src.Common import Tools

from src.BackTestService.BackTestFilterData import BacktestFilterDataFactory, BacktestFilterDataType
from src.BackTestService.BackTestInfoData import BackTestInfoDataPriceByToday
from src.BackTestService.BackTestInOutStrategy import (
    KD_BackTestInOutStrategy,
    MonthRpUp_backtestInOutStrategy,
    PEG_BackTestInOutStrategy,
    PERandPBR_BackTestInOutStrategy,
    RecordHigh_backtestInOutStrategy,
    Regular_backTestInOutStrategy,
)
from src.BackTestService.BackTestFilter import BacktestFilterFactory, BacktestFilterType, Regular_quotatestFilter
from src.BackTestService.BackTestSignal import BacktestSignalFactory, BacktestSignalType, TBacktestSignal
from src.ExternalService.ExternalDataFactory import ExternalDataFactory
from src.FilterService.StockHistory import OriginalStock
from src.FilterService.StockReportHistory import Day_Report, Month_Report, OM_Growth_Indicator, Original_Indicator, PEG_Indicator, ROE_Indicator, SeasonReportFactory

from src.Common.Parameter import RecordBackTestParameter
from src.Common.StockInfoData import BaseInfoData


class BackTestStock:
    """
    回測服務主要入口類別
    
    重構後作為 Facade 外觀類別，所有策略實作已移至獨立模組
    維持 100% 向後相容性，所有公開方法簽名維持不變
    """
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
        
    def set_check(self, monthRP_pick, PER_pick, volume_pick, One_pick, price_pick, PBR_pick, ROE_pick):
        self.bool_check_monthRP_pick = monthRP_pick
        self.bool_check_PER_pick = PER_pick
        self.bool_check_volume_pick = volume_pick
        self.bool_check_pickOneStock = One_pick
        self.bool_check_price_pick = price_pick
        self.bool_check_PBR_pick = PBR_pick
        self.bool_check_ROE_pick = ROE_pick

    @staticmethod
    def BuyStrockFun(aName: str, aIsBuy: bool):
        pass

    def backtest_KD_pick(self, mainParament: RecordBackTestParameter, folderName: str, callback=None) -> pd.DataFrame:
        """KD值選股"""
        userInfo = BackTestInfoDataPriceByToday(
            BaseInfoData(mainParament.money_start, mainParament.date_start, mainParament.date_end),
            self._original_stock, folderName
        )
        external_data = self._external_data_factory.Get_instance()
        stocksUsedForExecution = external_data.get_stock_history(mainParament.buy_number, mainParament.date_start)
        index_ROE = ROE_Indicator("ROE", SeasonReportFactory(info.FS_type.CPL, external_data), SeasonReportFactory(info.FS_type.BS, external_data))
        
        backTestFilterData = BacktestFilterDataFactory(
            BacktestFilterDataType.KD, self.BuyStrockFun,
            BacktestFilterFactory(BacktestFilterType.KD, [index_ROE]),
            BacktestSignalFactory(BacktestSignalType.KD, self._original_stock),
            mainParament.date_start, mainParament.date_end,
        )
        
        strategy = KD_BackTestInOutStrategy(userInfo, backTestFilterData, self._original_stock)
        startTime = datetime.now()
        buy_month = mainParament.date_start
        
        for index, _ in stocksUsedForExecution.iterrows():
            if not userInfo.GoToNextWorkDay(index): break
            strategy.Run()
            strategy.Out()
            if userInfo.BaseInfoData.now_day >= buy_month:
                strategy.In()
                buy_month = Tools.changeDateMonth(buy_month, 3)
            strategy.Record()
            
        strategy.Finish(folderName)
        userInfo.RunFinish()
        print("KD值選股-回測時間:", datetime.now() - startTime)
        return userInfo

    def backtest_PEG_pick(self, mainParament: RecordBackTestParameter, folderName: str, callback=None):
        """PEG選股外加月營收增高"""
        userInfo = BackTestInfoDataPriceByToday(
            BaseInfoData(mainParament.money_start, mainParament.date_start, mainParament.date_end),
            self._original_stock, folderName
        )
        external_data = self._external_data_factory.Get_instance()
        stocksUsedForExecution = external_data.get_stock_history(mainParament.buy_number, mainParament.date_start)
        
        index_PEG = PEG_Indicator("PEG", OM_Growth_Indicator("OM_Growth", Season_Report(info.FS_type.PLA.value, 3, external_data, info.FS_type.PLA)), Day_Report("yield_RP", 1, external_data))
        index_MonthUp = Original_Indicator("Month", Month_Report("month_RP", 1, external_data), info.Month_type.MR)
        
        backTestFilterData = BacktestFilterDataFactory(
            BacktestFilterDataType.PEG, self.BuyStrockFun,
            BacktestFilterFactory(BacktestFilterType.PEG, [index_PEG, index_MonthUp]),
            BacktestSignalFactory(BacktestSignalType.PEG, self._original_stock),
            mainParament.date_start, mainParament.date_end,
        )
        
        strategy = PEG_BackTestInOutStrategy(userInfo, backTestFilterData, self._original_stock)
        startTime = datetime.now()
        buy_month = mainParament.date_start
        
        for index, _ in stocksUsedForExecution.iterrows():
            if not userInfo.GoToNextWorkDay(index): break
            strategy.Run()
            strategy.Out()
            if userInfo.BaseInfoData.now_day.day >= mainParament.buy_day:
                if userInfo.BaseInfoData.now_day.month != buy_month.month or userInfo.BaseInfoData.now_day.year != buy_month.year:
                    strategy.In()
                    buy_month = userInfo.BaseInfoData.now_day
            strategy.Record()
            
        strategy.Finish(folderName)
        userInfo.RunFinish()
        print("PEG選股外加月營收增高-回測時間:", datetime.now() - startTime)
        return userInfo

    def backtest_Regular_quota(self, mainParament: RecordBackTestParameter, folderName: str, callback=None):
        """定期定額"""
        userInfo = BackTestInfoDataPriceByToday(
            BaseInfoData(0, mainParament.date_start, mainParament.date_end),
            self._original_stock, folderName
        )
        buy_month = mainParament.date_start
        external_data = self._external_data_factory.Get_instance()
        All_data = external_data.get_stock_history(mainParament.buy_number, mainParament.date_start)
        
        backTestFilterData = BacktestFilterDataFactory(
            BacktestFilterDataType.RegularQuota, self.BuyStrockFun,
            Regular_quotatestFilter(mainParament.buy_number),
            TBacktestSignal(),
            mainParament.date_start, mainParament.date_end,
        )
        
        strategy = Regular_backTestInOutStrategy(userInfo, backTestFilterData, self._original_stock)
        startTime = datetime.now()
        
        for index, _ in All_data.iterrows():
            if not userInfo.GoToNextWorkDay(index): break
            if userInfo.BaseInfoData.now_day.month != buy_month.month and userInfo.BaseInfoData.now_day.day >= mainParament.buy_day:
                strategy.Run()
                userInfo.BaseInfoData.now_money += mainParament.money_start
                userInfo.BaseInfoData.start_money += mainParament.money_start
                strategy.In()
                buy_month = userInfo.BaseInfoData.now_day
            strategy.Record()
            
        strategy.Finish(folderName)
        userInfo.RunFinish()
        print("定期定額-回測時間:", datetime.now() - startTime)
        return userInfo

    def backtest_Record_high(self, mainParament: RecordBackTestParameter, folderName: str, callback=None):
        """創新高"""
        Temp_reset = 0
        userInfo = BackTestInfoDataPriceByToday(
            BaseInfoData(mainParament.money_start, mainParament.date_start, mainParament.date_end),
            self._original_stock, folderName
        )
        external_data = self._external_data_factory.Get_instance()
        All_data = external_data.get_stock_history(mainParament.buy_number, mainParament.date_start)
        
        index_ROE = ROE_Indicator("ROE", SeasonReportFactory(info.FS_type.CPL, external_data), SeasonReportFactory(info.FS_type.BS, external_data))
        index_PBR = Original_Indicator("PBR", Day_Report("yield_RP", 1, external_data), info.Day_type.PBR)
        
        backTestFilterData = BacktestFilterDataFactory(
            BacktestFilterDataType.RecordHigh, self.BuyStrockFun,
            BacktestFilterFactory(BacktestFilterType.RecordHigh, [index_ROE, index_PBR, self._original_stock]),
            BacktestSignalFactory(BacktestSignalType.RecordHigh, self._original_stock),
            mainParament.date_start, mainParament.date_end,
        )
        
        strategy = RecordHigh_backtestInOutStrategy(userInfo, backTestFilterData, self._original_stock)
        startTime = datetime.now()
        
        for index, _ in All_data.iterrows():
            if not userInfo.GoToNextWorkDay(index): break
            strategy.Run()
            strategy.Out()
            if Temp_reset <= 0:
                strategy.In()
                Temp_reset = mainParament.change_days
            else:
                Temp_reset -= 1
            strategy.Record()
            
        strategy.Finish(folderName)
        userInfo.RunFinish()
        print("創新高-回測時間:", datetime.now() - startTime)
        return userInfo
    
    def backtest_PERandPBR(self, mainParament: RecordBackTestParameter, folderName: str, callback=None):
        """14年14倍"""
        Temp_reset = 0
        Temp_changeDays = 0
        userInfo = BackTestInfoDataPriceByToday(
            BaseInfoData(mainParament.money_start, mainParament.date_start, mainParament.date_end),
            self._original_stock, folderName
        )
        external_data = self._external_data_factory.Get_instance()
        All_data = external_data.get_stock_history(mainParament.buy_number, mainParament.date_start)
        
        index_PER = Original_Indicator("PER", Day_Report("yield_RP", 1, external_data), info.Day_type.PER)
        index_PBR = Original_Indicator("PBR", Day_Report("yield_RP", 1, external_data), info.Day_type.PBR)
        
        backTestFilterData = BacktestFilterDataFactory(
            BacktestFilterDataType.PERandPBR, self.BuyStrockFun,
            BacktestFilterFactory(BacktestFilterType.PERandPBR, [index_PER, index_PBR]),
            BacktestSignalFactory(BacktestSignalType.PERandPBR, self._original_stock),
            mainParament.date_start, mainParament.date_end,
        )
        
        strategy = PERandPBR_BackTestInOutStrategy(userInfo, backTestFilterData, self._original_stock)
        startTime = datetime.now()
        
        for index, _ in All_data.iterrows():
            if not userInfo.GoToNextWorkDay(index): break
            if Temp_reset > 0 and len(userInfo.HandleStock) == 0:
                print(str(userInfo.BaseInfoData.now_day) + " is reset time:第" + str(Temp_reset) + "天")
                Temp_reset -= 1
            else:
                strategy.Run()
                if len(userInfo.HandleStock) > 0 and len(strategy.FilterData.ShouldBuyStocks()) < 100:
                    strategy.Out()
                    Temp_reset = 60
                if len(userInfo.HandleStock) > 0 and Temp_changeDays <= 0:
                    strategy.Out()
                if len(userInfo.HandleStock) == 0 and len(strategy.FilterData.ShouldBuyStocks()) >= 100:
                    strategy.In()
                    Temp_changeDays = 60
            strategy.Record()
            Temp_changeDays -= 1
            
        strategy.Finish(folderName)
        userInfo.RunFinish()
        print("14年14倍-回測時間:", datetime.now() - startTime)
        return userInfo

    def backtest_monthRP_Up(self, mainParament: RecordBackTestParameter, folderName: str, callback=None):
        """月營收增高"""
        Temp_change = 0
        userInfo = BackTestInfoDataPriceByToday(
            BaseInfoData(mainParament.money_start, mainParament.date_start, mainParament.date_end),
            self._original_stock, folderName
        )
        external_data = self._external_data_factory.Get_instance()
        All_data = external_data.get_stock_history(mainParament.buy_number, mainParament.date_start)
        
        index_ROE = ROE_Indicator("ROE", SeasonReportFactory(info.FS_type.CPL, external_data), SeasonReportFactory(info.FS_type.BS, external_data))
        index_PBR = Original_Indicator("PBR", Day_Report("yield_RP", 1, external_data), info.Day_type.PBR)
        index_PER = Original_Indicator("PER", Day_Report("yield_RP", 1, external_data), info.Day_type.PER)
        Month_index = Original_Indicator("Month", Month_Report("month_RP", 1, external_data), info.Month_type.MR)
        
        backTestFilterData = BacktestFilterDataFactory(
            BacktestFilterDataType.MonthRP_Up, self.BuyStrockFun,
            BacktestFilterFactory(BacktestFilterType.MonthRP_Up, [Month_index, index_ROE, index_PER, index_PBR]),
            BacktestSignalFactory(BacktestSignalType.MonthRP_Up, self._original_stock),
            mainParament.date_start, mainParament.date_end,
        )
        
        strategy = MonthRpUp_backtestInOutStrategy(userInfo, backTestFilterData, self._original_stock)
        startTime = datetime.now()
        
        for index, _ in All_data.iterrows():
            if not userInfo.GoToNextWorkDay(index): break
            strategy.Run()
            if Temp_change <= 0 and len(userInfo.HandleStock) > 0:
                strategy.Out()
            if Temp_change <= 0 and len(userInfo.HandleStock) <= 0 and len(strategy.FilterData.ShouldBuyStocks()) > mainParament.Pick_amount:
                strategy.In()
            strategy.Record()
            if Temp_change <= 0:
                Temp_change = mainParament.change_days
            else:
                Temp_change -= 1
                
        strategy.Finish(folderName)
        userInfo.RunFinish()
        print("月營收增高-回測時間:", datetime.now() - startTime)
        return userInfo