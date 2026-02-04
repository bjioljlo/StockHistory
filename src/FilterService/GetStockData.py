import sys
from datetime import datetime

import pandas as pd
from pandas import DataFrame

from src.Common import InfomationType as info
from src.Common import Tools
from src.Common.InfomationType import stock_data_kind
from src.ExternalService.ExternalDataFactory import ExternalDataFactory
from src.ExternalService.IGetExternalData import IGetExternalData

from .StockHistory import (
    OriginalStock,
    OriginalStockByYahoo,
    RangeDate_Stock,
    RecordHigh_Stock,
    SMA_Stock,
    StockFilter,
    StockFilterInfo,
    StockPriceBetterMA,
    StockRecordHigh,
    StockAvgVolMultiple,
)
from .StockReportHistory import (
    ADL_Indicator,
    ADL_Report,
    ADLs_Indicator,
    Day_Report,
    Debt_Indicator,
    FreeCF_Indicator,
    Indicator,
    Month_Report,
    MR_Growth_Indicator,
    OCFPerShare_Indicator,
    OM_Growth_Indicator,
    Original_Indicator,
    PCF_Indicator,
    PEG_Indicator,
    ROE_Indicator,
    Season_Report,
    SR_Growth_Indicator,
    TReport,
)


class All_Stock_Filters_fuc:
    """增加篩選器在這邊加
    所有要輸入TStock類就可以加進來
    所有的篩選方法集合體(外部只會用到這裡)
    """

    @property
    def Data(self):
        return self._data

    @Data.setter
    def Data(self, data: pd.DataFrame):
        self._data = data

    def __init__(self, Date: datetime, Data: pd.DataFrame, original_stock: OriginalStock) -> None:
        self.Data = Data
        self._date = Date
        self.original_stock = original_stock

    def get_Filter(self, Name: str, Max: int, Min: int, Type: info.Price_type):
        print("get_price_rang: start")
        if Max < Min or Max < 0 or Min < 0:
            print("price range number wrong!" + "Max:" + Max + " min:" + Min)
            return self._date
        aFilter = StockFilter(
            self.original_stock, Name, Max, Min, self.Data, self._date, Type
        )
        temp = aFilter.get_ALL()
        print("get_price_rang: end")
        return temp

    def get_FilterInfo(self, groupName: str):
        print("get_GroupInfo: start")
        if (groupName is None) or (groupName == ""):
            print("GroupInfo Name wrong!" + " Input:" + groupName)
            return self._date
        aFilter = StockFilterInfo(
            self.original_stock, self.Data, self._date, groupName
        )
        temp = aFilter.get_ALL()
        print("get_price_rang: end")
        return temp

    def get_Filter_SMA(
        self, Name: str, Max: int, Min: int, avgMA: int, Type: info.Price_type
    ):
        aSMA = SMA_Stock(self.original_stock, avgMA, Type)
        aFilter = StockFilter(aSMA, Name, Max, Min, self.Data, self._date, aSMA._type)
        temp = aFilter.get_ALL()
        return temp

    def get_Filter_RecordHigh(
        self, flashDay: int, recordDays: int, atype: info.Price_type
    ):
        print("get_RecordHigh: start")
        aRH = StockRecordHigh(
            RecordHigh_Stock(self.original_stock), self._date, flashDay, recordDays, self.Data, atype
        )
        temp = aRH.get_ALL()
        print("get_RecordHigh: end")
        return temp

    def get_Filter_BetterMA(self, avgMA: int, Type: info.Price_type):
        aSMA = SMA_Stock(self.original_stock, avgMA, Type)
        aBetterMA = StockPriceBetterMA(aSMA, self.Data, self._date)
        temp = aBetterMA.get_ALL()
        return temp

    def get_Filter_AvgVol_Multiple(self, multiple: int, avg_days: int):
        print("get_Filter_AvgVol_Multiple: start")
        aSMA = SMA_Stock(self.original_stock, avg_days, info.Price_type.Volume)
        aVolFilter = StockAvgVolMultiple(aSMA, self.Data, self._date, multiple)
        temp = aVolFilter.get_ALL()
        print("get_Filter_AvgVol_Multiple: end")
        return temp


class ReportServices:
    def __init__(self, external_data_factory:ExternalDataFactory):
        self.GetExternal = external_data_factory.Get_instance()
        self.original_stock = OriginalStockByYahoo(externalDataFactory=external_data_factory)

        # Reports
        self.CPL_RP = Season_Report(info.FS_type.CPL.value, 3, self.GetExternal, info.FS_type.CPL)
        self.BS_RP = Season_Report(info.FS_type.BS.value, 3, self.GetExternal, info.FS_type.BS)
        self.PLA_RP = Season_Report(info.FS_type.PLA.value, 3, self.GetExternal, info.FS_type.PLA)
        self.SCF_RP = Season_Report(info.FS_type.SCF.value, 3, self.GetExternal, info.FS_type.SCF)
        self.Month_RP = Month_Report("month_RP", 1, self.GetExternal)
        self.Yield_RP = Day_Report("yield_RP", 1, self.GetExternal)
        self.ADL_RP = ADL_Report("aDL_RP", 1, self.GetExternal)

        # Indicators
        self.ROE_index = ROE_Indicator("ROE", self.CPL_RP, self.BS_RP)
        self.FreeCF_index = FreeCF_Indicator("FreeCF", self.SCF_RP)
        self.Debt_index = Debt_Indicator("Debt", self.BS_RP)
        self.OM_Growth_index = OM_Growth_Indicator("OM_Growth", self.PLA_RP)
        self.MR_Growth_index = MR_Growth_Indicator("MR_Growth", self.Month_RP)
        self.SR_Growth_index = SR_Growth_Indicator("SR_Growth", self.PLA_RP)
        self.PEG_index = PEG_Indicator("PEG", self.OM_Growth_index, self.Yield_RP)
        self.PER_index = Original_Indicator("PER", self.Yield_RP, info.Day_type.PER)
        self.PBR_index = Original_Indicator("PBR", self.Yield_RP, info.Day_type.PBR)
        self.Yield_index = Original_Indicator("Yield", self.Yield_RP, info.Day_type.Yield)
        self.EPS_index = Original_Indicator("EPS", self.CPL_RP, info.CPL_type.EPS)
        self.Month_index = Original_Indicator("Month", self.Month_RP, info.Month_type.MR)
        self.OCF_index = Original_Indicator("OCF", self.SCF_RP, info.SCF_type.OCF)
        self.ICF_index = Original_Indicator("ICF", self.SCF_RP, info.SCF_type.ICF)
        self.OM_index = Original_Indicator("OM", self.PLA_RP, info.PLA_type.type_2)
        self.OCFPerShare_index = OCFPerShare_Indicator("OCFPerShare", self.SCF_RP, self.BS_RP)
        self.PCF_index = PCF_Indicator(
            "P/CF", self.OCFPerShare_index, self.original_stock, self.GetExternal
        )
        self.ADL_index = ADL_Indicator("ADL", self.ADL_RP)
        self.ADLs_index = ADLs_Indicator("ADLs", self.ADL_RP)
        self.RangeDate_Stock = RangeDate_Stock(self.original_stock)


# 新增功能的虛擬類別
class VirtualReportFunc:
    def __init__(self, Report: TReport) -> None:
        self._Report = Report
        self._name = Report._name


# 自動找最近資料功能
class ReportAutoTrace(TReport):
    def __init__(self, name: str, Report: Indicator, Unit: int) -> None:
        super().__init__(name, Unit)
        self._Report = Report
        self._Unit = Unit

    def get_ALL_Report(self, date):
        return self.get_AutoTrace(date)

    def get_AutoTrace(self, date):
        print("{} / {} is Start!".format(self._name, sys._getframe().f_code.co_name))
        Timer = 0
        Temp = self._Report.get_ALL_Report(date)
        while Temp.empty:
            date = self._Report.Next_date(date)
            Temp = self._Report.get_ALL_Report(date)
            if Timer == 4:
                raise NotImplementedError(
                    "ReportAutoTrace error!"
                    + str(type(self._Report))
                    + "its too many times!"
                )
            Timer = Timer + 1
        print("{} / {} is End!".format(self._name, sys._getframe().f_code.co_name))
        return Temp


# 數值篩選功能
class ReportFilter(TReport):
    def __init__(
        self, name: str, Report: Indicator, Unit: int, big: float, small: float
    ) -> None:
        super().__init__(name, Unit)
        self._big = big
        self._small = small
        self._Report = Report
        self._Unit = Unit

    def get_ALL_Report(self, date):
        return self.get_Filter(date, self._big, self._small)

    def get_Filter(self, date, big, small):
        print("{} / {} is Start!".format(self._name, sys._getframe().f_code.co_name))
        Temp = self._Report.get_ALL_Report(date)
        if big == small == 0:
            print("Range number wrong!")
            return Temp
        if big < 0 or small < 0 or big < small:
            print("Range number wrong!")
            return Temp
        if Temp.empty:
            return pd.DataFrame()
        mask1 = Temp[self._Report._name] > small
        mask2 = Temp[self._Report._name] <= big
        Temp = Temp[(mask1 & mask2)]
        print("{} / {} is End!".format(self._name, sys._getframe().f_code.co_name))
        return Temp


# 增高篩選功能
class ReportUp(TReport):
    def __init__(self, name: str, upNum: int, Report: Indicator, Unit: int) -> None:
        super().__init__(name, Unit)
        self._upNum = upNum
        self._Report = Report
        self._Unit = Unit
        self._name = self._Report._name + "_" + self._name

    def get_ALL_Report(self, date):
        return self.get_up(date, self._upNum)

    def get_up(self, date, upNum):
        print("{} / {} is Start!".format(self._name, sys._getframe().f_code.co_name))
        if type(self._Report) is ReportAutoTrace:
            raise NotImplementedError("ReportType error!" + str(type(self._Report)))
        data = {}
        table_result = pd.DataFrame()
        need_num = upNum + 2  # 需要多一個數據點進行比較
        while need_num > 0:
            temp_data = self._Report.get_ALL_Report(date)
            if temp_data.empty:
                return pd.DataFrame()
            data["%d-%d-1" % (date.year, date.month)] = temp_data
            date = self._Report.Next_date(date)
            need_num = need_num - 1
        
        # 處理數據合併
        if not data:
            return pd.DataFrame()
        
        # 檢查第一個數據框的結構
        first_data = next(iter(data.values()))
        if isinstance(first_data, pd.Series):
            # 如果是 Series，直接使用
            result = pd.DataFrame({k: result for k, result in data.items()}).transpose()
        elif isinstance(first_data, pd.DataFrame):
            # 如果是 DataFrame，需要選擇正確的列
            if self._Report._name in first_data.columns:
                # 使用報告名稱作為列名
                result = pd.DataFrame(
                    {k: result[self._Report._name] for k, result in data.items()}
                ).transpose()
            else:
                # 如果沒有報告名稱列，使用第一列
                result = pd.DataFrame(
                    {k: result.iloc[:, 0] for k, result in data.items()}
                ).transpose()
        else:
            return pd.DataFrame()
        
        result.index = pd.to_datetime(result.index)
        result = result.sort_index()
        
        # 確保數據類型正確
        result = result.apply(pd.to_numeric, errors='coerce')
        
        # 檢查是否有足夠的數據進行比較
        if len(result) < upNum + 1:
            print(f"數據不足，需要 {upNum + 1} 個時間點，但只有 {len(result)} 個")
            return pd.DataFrame()
        
        # 進行比較操作
        try:
            # 確保 result 數據類型一致，避免比較時出現類型錯誤
            result = result.apply(pd.to_numeric, errors='coerce')
            
            # 移除包含 NaN 的列
            result = result.dropna(axis=1, how='any')
            
            if result.empty:
                print("數據清理後無有效數據")
                return pd.DataFrame()
            
            comparison_result = result > result.shift()
            method2 = comparison_result.iloc[-upNum:].sum()
            
            # 確保 method2 中的所有值都是數值類型，避免類型比較錯誤
            method2 = pd.to_numeric(method2, errors='coerce')
            
            # 過濾掉 NaN 值
            method2 = method2.dropna()
            
            # 只保留大於等於 upNum 的值
            method2 = method2[method2 >= upNum]
            
            if not method2.empty:
                method2 = pd.DataFrame(method2)
                table_result[self._name] = method2
            else:
                print(f"沒有符合條件的數據 (需要連續 {upNum} 次增長)")
        except Exception as e:
            print(f"比較操作失敗: {e}")
            return pd.DataFrame()
        
        print("{} / {} is End!".format(self._name, sys._getframe().f_code.co_name))
        return table_result


# 平滑數據
class ReportSmooth(TReport):
    def __init__(self, name: str, avgNum: int, Report: Indicator, Unit: int) -> None:
        super().__init__(name, Unit)
        self.avgNum = avgNum
        self._Report = Report
        self._Unit = Unit
        self._name = self._Report._name + "_" + self._name

    def get_ALL_Report(self, date):
        return self.get_Smooth(date, self.avgNum)

    def get_Smooth(self, date, avgNum):
        print("{} / {} is Start!".format(self._name, sys._getframe().f_code.co_name))
        if type(self._Report) is ReportAutoTrace:
            raise NotImplementedError("ReportType error!" + str(type(self.Report)))
        
        # 確保 avgNum 是整數
        avgNum = int(avgNum)
        
        data = {}
        table_result = pd.DataFrame()
        need_num = avgNum + 1
        while need_num > 0:
            temp_data = self._Report.get_ALL_Report(date)
            if temp_data.empty:
                return pd.DataFrame()
            data["%d-%d-1" % (date.year, date.month)] = temp_data
            date = self._Report.Next_date(date)
            need_num = need_num - 1
        
        # 處理數據合併
        if not data:
            return pd.DataFrame()
        
        # 檢查第一個數據框的結構
        first_data = next(iter(data.values()))
        if isinstance(first_data, pd.Series):
            # 如果是 Series，直接使用
            result = pd.DataFrame({k: result for k, result in data.items()}).transpose()
        elif isinstance(first_data, pd.DataFrame):
            # 如果是 DataFrame，需要選擇正確的列
            if self._Report._name in first_data.columns:
                # 使用報告名稱作為列名
                result = pd.DataFrame(
                    {k: result[self._Report._name] for k, result in data.items()}
                ).transpose()
            else:
                # 如果沒有報告名稱列，使用第一列
                result = pd.DataFrame(
                    {k: result.iloc[:, 0] for k, result in data.items()}
                ).transpose()
        else:
            return pd.DataFrame()
        
        result.index = pd.to_datetime(result.index)
        result = result.sort_index()
        method2 = result.rolling(avgNum, min_periods=avgNum).mean()
        method2 = method2.loc[method2.index[-1]]
        
        # 確保 method2 中的所有值都是數值類型，避免類型比較錯誤
        method2 = pd.to_numeric(method2, errors='coerce')
        
        # 過濾掉 NaN 值
        method2 = method2.dropna()
        
        if not method2.empty:
            table_result[self._name] = method2
        else:
            print(f"平滑計算後沒有有效的數據")
        print("{} / {} is End!".format(self._name, sys._getframe().f_code.co_name))
        return table_result


class All_fuc:
    """增加篩選器在這邊加
    所有要輸入Indicator類就可以加進來
    所有的篩選方法集合體(外部只會用到這裡)
    """

    def __init__(self, date: datetime, Report: Indicator) -> None:
        self._date = date
        self._report = Report

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, date: datetime):
        self._date = date

    @property
    def report(self):
        return self._report

    @report.setter
    def report(self, report: Indicator):
        self._report = report

    def get_Filter(self, big, small):
        aFilter = ReportFilter("filter", self._report, self._report._Unit, big, small)
        temp = aFilter.get_ALL_Report(self._date)
        return temp

    def get_Smooth_Up_Auto(self, avgNum, upNum):
        aSmooth = ReportSmooth("smooth", avgNum, self._report, self._report._Unit)
        aUp = ReportUp("up", upNum, aSmooth, aSmooth._Report._Unit)
        aAuto = ReportAutoTrace("auto", aUp, aUp._Report._Unit)
        temp = aAuto.get_ALL_Report(self._date)
        return temp

    def get_Filter_Auto(self, big, small):
        aFilter = ReportFilter("filter", self._report, self._report._Unit, big, small)
        aAuto = ReportAutoTrace("auto", aFilter, aFilter._Unit)
        temp = aAuto.get_ALL_Report(self._date)
        return temp

    def get_Up_Auto(self, upNum: int):
        aUp = ReportUp("up", upNum, self._report, self._report._Unit)
        aAuto = ReportAutoTrace("auto", aUp, aUp._Report._Unit)
        temp = aAuto.get_ALL_Report(self._date)
        return temp


class All_imge:
    """取得各種數值圖表
    所有要輸入Indicator類就可以加進來
    """

    def __init__(self, start: datetime, end: datetime, report: Indicator, external_service:IGetExternalData) -> None:
        self._start = start
        self._end = end
        self._report = report
        self._main_GetExternalData = external_service

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    @start.setter
    def start(self, start: datetime):
        self._start = start

    @end.setter
    def end(self, end: datetime):
        self._end = end

    @property
    def report(self):
        return self._report

    @report.setter
    def report(self, report: Indicator):
        self._report = report

    def get_Chart(self, number: int = None):
        if number is None:
            if (self._report._name != "ADL") and (self._report._name != "ADLs"):
                raise
        
        results_list = []
        stock_history_index = self._main_GetExternalData.get_stock_history("2330").index
        start = self._start
        end = self._end
        
        while start <= end:
            if end not in stock_history_index:
                end = self._report.Next_date(end)
                continue
            
            if (self._report._name == "ADL") or (self._report._name == "ADLs"):
                temp = self._report.get_ALL_Report(end)
            else:
                temp = self._report.get_ReportByNumber(end, number)
            
            if temp.empty:
                end = self._report.Next_date(end)
                continue
            
            temp.insert(0, "Date", end)
            results_list.append(temp)
            end = self._report.Next_date(end)
            
        if not results_list:
            data_result = pd.DataFrame(columns=["Date", self._report._name])
        else:
            data_result = pd.concat(results_list, ignore_index=True)

        data_result.set_index("Date", inplace=True)
        return data_result


def get_stock_MA(number: str, date: datetime, MA_day: int, original_stock: OriginalStockByYahoo):  # 取得某股票某天的均線
    original_stock.number = number
    Temp_MA = SMA_Stock(
        original_stock, MA_day, info.Price_type.Close
    ).get_ALL()[date]
    return Temp_MA


def get_stock_price(
    number: str, date: datetime, kind: stock_data_kind, original_stock: OriginalStockByYahoo
):  # 取得某股票某天的價格
    original_stock.number = number
    if kind == stock_data_kind.Volume:
        stock_sma = SMA_Stock(original_stock)
        stock_sma.AvgDay = 5
        stock_sma.PriceType = info.Price_type.Volume
        Temp = stock_sma.get_PriceByDate(date)
    else:
        Temp = original_stock.get_PriceByDateAndType(date, kind)
    return Temp


# 取得月營收逐步升高的篩選
def get_monthRP_up(
    services: ReportServices, time: datetime, avgNum: int, upNum: int
):  # time = 取得資料的時間 avgNum = 平滑曲線月份 upNum = 連續成長月份
    print("get_monthRP_up: start:" + str(time))
    Result = All_fuc(time, services.Month_index).get_Smooth_Up_Auto(avgNum, upNum)
    print("get_monthRP_up: end")
    return Result


# 取得本益比篩選 #股價/每股盈餘(EPS)
def get_PER_range(
    services: ReportServices, time: datetime, PER_start, PER_end
):  # time = 取得資料的時間 PER_start = PER最小值 PER_end PER最大值
    print("get_PER_range: start")
    Result = All_fuc(time, services.PER_index).get_Filter_Auto(PER_start, PER_end)
    print("get_PER_range: end")
    return Result


# 取得本益成長比(PEG)篩選
def get_PEG_range(
    services: ReportServices, time: datetime, PEG_start, PEG_end
):  # time = 取得資料的時間 PEG_start = PEG最小值 PEG_end PEG最大值
    print("get_PEG_range: start")
    Result = All_fuc(time, services.PEG_index).get_Filter_Auto(PEG_start, PEG_end)
    print("get_PEG_range: end")
    return Result


# 取得平均日成交金額篩選
def get_AVG_value(
    time: datetime, volume: int, days: int, data: DataFrame, original_stock: OriginalStockByYahoo
):  # time = 取得資料的時間 volume = 平均成交金額 days = 平均天數
    print("get_AVG_value: start")
    result = All_Stock_Filters_fuc(time, data, original_stock).get_Filter_SMA(
        "volume", 99999999999, volume, days, info.Price_type.Volume
    )
    print("get_AVG_value: end")
    return result


# 取得股價淨值比篩選  #股價/每股淨值 = PBR
def get_PBR_range(
    services: ReportServices, time: datetime, PBR_start: float, PBR_end: float, data=pd.DataFrame()
):  # time = 取得資料的時間 PBR_start = PBR最小值 PBR_end PBR最大值
    print("get_PBR_rang: start")
    Result = All_fuc(time, services.PBR_index).get_Filter_Auto(PBR_start, PBR_end)
    print("get_PBR_rang: end")
    return Result


# 取得股東權益報酬率 #ROE(股東權益報酬率) = 稅後淨利/股東權益
def get_ROE_range(
    services: ReportServices, time: datetime, ROE_start, ROE_end, data=pd.DataFrame()
):  # time = 取得資料的時間 ROE_start = ROE最小值 ROE_end ROE最大值
    print("get_ROE_rang: start")
    Result = All_fuc(time, services.ROE_index).get_Filter_Auto(ROE_start, ROE_end)
    print("get_ROE_rang: end")
    return Result


# 取得股價篩選
def get_price_range(
    time: datetime, high: int, low: int, data: DataFrame, original_stock: OriginalStockByYahoo
):  # time = 取得資料的時間 high = 最高價 low = 最低價
    print("get_price_rang: start")
    if high == low == 0:
        return data
    if high < low or high < 0 or low < 0:
        print("price range number wrong!")
        return data
    Temp = All_Stock_Filters_fuc(time, data, original_stock).get_Filter(
        "price", high, low, info.Price_type.Close
    )
    print("get_price_rang: end")
    return Temp


# 取得創新高篩選
def get_RecordHigh_range(
    time: datetime, Day: int, RecordHighDay: int, data: DataFrame, original_stock: OriginalStockByYahoo
):  # time = 取得資料的時間 Day = 往前找多少天的創新高 RecordHighDay = 找創新高的區間
    print("get_RecordHigh: start")
    result = All_Stock_Filters_fuc(time, data, original_stock).get_Filter_RecordHigh(
        Day, RecordHighDay, info.Price_type.High
    )
    print("get_RecordHigh: end")
    return result


def AvgStockPrice(date, original_stock: OriginalStockByYahoo, vData=pd.DataFrame()):
    """平均vData股價"""
    All_price = 0  #
    Count = 0
    Result_avg_price = 0
    if vData.empty:
        return 0, 0
    for value in range(0, len(vData)):
        Nnumber = str(vData.iloc[value].name)
        Temp_stock_price = get_stock_price(
            Nnumber, Tools.DateTime2String(date), stock_data_kind.Close, original_stock
        )
        if Temp_stock_price is not None:
            All_price = All_price + Temp_stock_price
            Count = Count + 1
    if All_price == 0 or Count == 0:
        return 0, 0
    Result_avg_price = All_price / Count
    return Result_avg_price, Count
