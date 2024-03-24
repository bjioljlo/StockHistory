from datetime import datetime
import pandas as pd
from pandas import DataFrame
import tools
import Infomation_type as info
import sys
from StockHistory import OriginalStockByYahoo, RangeDate_Stock, SMA_Stock, RecordHigh_Stock, StockFilter, StockRecordHigh, StockPriceBetterMA
from StockReportHistory import Indicator, ROE_Indicator,FreeCF_Indicator,Debt_Indicator,OM_Growth_Indicator,MR_Growth_Indicator,SR_Growth_Indicator,PEG_Indicator,Original_Indicator,OCFPerShare_Indicator,PCF_Indicator, ADL_Indicator, ADLs_Indicator
from StockReportHistory import TReport, Season_Report, Month_Report, Day_Report, ADL_Report
from Infomation_type import stock_data_kind

OriginalStocStock_2330 = OriginalStockByYahoo(2330)
OriginalStocStock_main = OriginalStockByYahoo()

Stock_RangeDate = RangeDate_Stock(OriginalStocStock_main)
Stock_SMA = SMA_Stock(OriginalStocStock_main)
Stock_RecordHigh = RecordHigh_Stock(OriginalStocStock_main)
            
class All_Stock_Filters_fuc():
    '''增加篩選器在這邊加
        所有要輸入TStock類就可以加進來
        所有的篩選方法集合體(外部只會用到這裡)
    '''
    @property
    def Data(self):
        return self._data
    @Data.setter
    def Data(self,data:pd.DataFrame):
        self._data = data
    def __init__(self,Date:datetime, Data:pd.DataFrame) -> None:
        self.Data = Data
        self._date = Date
    def get_Filter(self, Name:str, Max:int, Min:int, Type:info.Price_type):
        print('get_price_rang: start')
        if Max < Min or Max < 0 or Min < 0:
            print("price range number wrong!" + "Max:" + Max + " min:" + Min)
            return self._date
        aFilter = StockFilter(OriginalStocStock_main,Name,Max,Min,self.Data,self._date,Type)
        temp = aFilter.get_ALL()
        print('get_price_rang: end')
        return temp
    def get_Filter_SMA(self, Name:str, Max:int, Min:int, avgMA:int, Type:info.Price_type):
        aSMA = SMA_Stock(OriginalStocStock_main,avgMA,Type)
        aFilter = StockFilter(aSMA,Name,Max,Min,self.Data,self._date,aSMA._type)
        temp = aFilter.get_ALL()
        return temp
    def get_Filter_RecordHigh(self, flashDay:int, recordDays:int, atype:info.Price_type):
        print('get_RecordHigh: start')
        aRH = StockRecordHigh(Stock_RecordHigh,self._date,flashDay,recordDays,self.Data,atype)
        temp = aRH.get_ALL()
        print('get_RecordHigh: end')
        return temp
    def get_Filter_BetterMA(self, avgMA:int, Type:info.Price_type):
        aSMA = SMA_Stock(OriginalStocStock_main,avgMA,Type)
        aBetterMA = StockPriceBetterMA(aSMA, self.Data, self._date)
        temp = aBetterMA.get_ALL()
        return temp

CPL_RP = Season_Report(info.FS_type.CPL,info.FS_type.CPL.value,3)
BS_RP = Season_Report(info.FS_type.BS,info.FS_type.BS.value,3)
PLA_RP = Season_Report(info.FS_type.PLA,info.FS_type.PLA.value,3)
SCF_RP = Season_Report(info.FS_type.SCF,info.FS_type.SCF.value,3)

Month_RP = Month_Report('month_RP', 1)#月營收
Yield_RP = Day_Report('yield_RP', 1)
ADL_RP = ADL_Report('aDL_RP', 1)

ROE_index = ROE_Indicator('ROE',CPL_RP,BS_RP)
FreeCF_index = FreeCF_Indicator('FreeCF',SCF_RP)
Debt_index = Debt_Indicator('Debt',BS_RP)
OM_Growth_index = OM_Growth_Indicator('OM_Growth',PLA_RP)
MR_Growth_index = MR_Growth_Indicator('MR_Growth',Month_RP)
SR_Growth_index = SR_Growth_Indicator('SR_Growth',PLA_RP)
PEG_index = PEG_Indicator('PEG',OM_Growth_index,Yield_RP)
PER_index = Original_Indicator('PER',Yield_RP,info.Day_type.PER)#取得本益比
PBR_index = Original_Indicator('PBR',Yield_RP,info.Day_type.PBR)#取得股價淨值比
Yield_index = Original_Indicator('Yield',Yield_RP,info.Day_type.Yield)#取得殖利率
EPS_index = Original_Indicator('EPS',CPL_RP,info.CPL_type.EPS)#取得EPS
Month_index = Original_Indicator('Month',Month_RP,info.Month_type.MR)#取得月營收
OCF_index = Original_Indicator('OCF',SCF_RP,info.SCF_type.OCF)#營業活動之淨現金流入
ICF_index = Original_Indicator('ICF',SCF_RP,info.SCF_type.ICF)#投資活動之淨現金流入
OM_index = Original_Indicator('OM',PLA_RP,info.PLA_type.type_2)#營業利益率(%)
OCFPerShare_index = OCFPerShare_Indicator('OCFPerShare',SCF_RP,BS_RP)
PCF_index = PCF_Indicator('P/CF',OCFPerShare_index,OriginalStocStock_main)
ADL_index = ADL_Indicator('ADL',ADL_RP)
ADLs_index = ADLs_Indicator('ADLs',ADL_RP)
#新增功能的虛擬類別
class VirtualReportFunc():
    def __init__(self, Report: TReport) -> None:
        self._Report = Report
        self._name = Report._name
#自動找最近資料功能
class ReportAutoTrace(TReport):
    def __init__(self, name: str, Report:Indicator, Unit: int) -> None:
        super().__init__(name, Unit)
        self._Report = Report
        self._Unit = Unit
    def get_ALL_Report(self, date):
        return self.get_AutoTrace(date)
    def get_AutoTrace(self,date):
        print("{} / {} is Start!".format(self._name,sys._getframe().f_code.co_name))
        Timer = 0
        Temp = self._Report.get_ALL_Report(date)
        while Temp.empty:
            date = self._Report.Next_date(date)
            Temp = self._Report.get_ALL_Report(date)
            if Timer == 4:
                raise NotImplementedError("ReportAutoTrace error!" + str(type(self._Report)))
            Timer = Timer + 1
        print("{} / {} is End!".format(self._name,sys._getframe().f_code.co_name))
        return Temp
#數值篩選功能
class ReportFilter(TReport):
    def __init__(self, name: str, Report:Indicator, Unit: int, big:float, small:float) -> None:
        super().__init__(name, Unit)
        self._big = big
        self._small = small
        self._Report = Report
        self._Unit = Unit
    def get_ALL_Report(self, date):
        return self.get_Filter(date,self._big,self._small)
    def get_Filter(self,date,big,small):
        print("{} / {} is Start!".format(self._name,sys._getframe().f_code.co_name))
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
        print("{} / {} is End!".format(self._name,sys._getframe().f_code.co_name))
        return Temp
#增高篩選功能
class ReportUp(TReport):
    def __init__(self, name: str, upNum:int, Report:Indicator, Unit: int) -> None:
        super().__init__(name, Unit)
        self._upNum = upNum
        self._Report = Report
        self._Unit = Unit
    def get_ALL_Report(self, date):
        return self.get_up(date,self._upNum)
    def get_up(self,date,upNum):
        print("{} / {} is Start!".format(self._name,sys._getframe().f_code.co_name))
        if type(self._Report) == ReportAutoTrace:
            raise NotImplementedError("ReportType error!" + str(type(self._Report)))
        data = {}
        need_num = upNum + 1
        while need_num > 0 :
            temp_data = self._Report.get_ALL_Report(date)
            if temp_data.empty:
                return pd.DataFrame()
            data['%d-%d-1'%(date.year, date.month)] = temp_data
            if self._Report != Yield_RP:
                date = tools.changeDateMonth(date,-self._Report._Unit)
            else:
                date = tools.backWorkDays(date,-self._Report._Unit)
            need_num = need_num - 1
        result = pd.DataFrame({k:result[self._Report._name] for k,result in data.items()}).transpose()
        result.index = pd.to_datetime(result.index)
        result = result.sort_index()
        method2 = (result > result.shift()).iloc[-upNum:].sum()
        method2 = method2[method2 >= upNum]
        method2 = pd.DataFrame(method2)
        print("{} / {} is End!".format(self._name,sys._getframe().f_code.co_name))
        return method2
#平滑數據
class ReportSmooth(TReport):
    def __init__(self, name: str, avgNum:int, Report:Indicator, Unit: int) -> None:
        super().__init__(name, Unit)
        self.avgNum = avgNum
        self._Report = Report
        self._Unit = Unit
    def get_ALL_Report(self, date):
        return self.get_Smooth(date,self.avgNum)
    def get_Smooth(self, date, avgNum):
        print("{} / {} is Start!".format(self._name,sys._getframe().f_code.co_name))
        if type(self._Report) == ReportAutoTrace:
            raise NotImplementedError("ReportType error!" + str(type(self.Report)))
        data = {}
        table_result = pd.DataFrame()
        need_num = avgNum + 1
        while need_num > 0:
            temp_data = self._Report.get_ALL_Report(date)
            if temp_data.empty:
                return pd.DataFrame()
            data['%d-%d-1'%(date.year, date.month)] = temp_data
            if self._Report != Yield_RP:
                date = tools.changeDateMonth(date,-self._Report._Unit)
            else:
                date = tools.backWorkDays(date,-self._Report._Unit)
            need_num = need_num - 1
        result = pd.DataFrame({k:result[self._Report._name] for k,result in data.items()}).transpose()
        result.index = pd.to_datetime(result.index)
        result = result.sort_index()
        method2 = result.rolling(avgNum,min_periods=avgNum).mean()
        method2 = method2.loc[method2.index[-1]]
        table_result[self._name] = method2
        print("{} / {} is End!".format(self._name,sys._getframe().f_code.co_name))
        return table_result

class All_fuc():
    ''' 增加篩選器在這邊加
        所有要輸入Indicator類就可以加進來
        所有的篩選方法集合體(外部只會用到這裡)
    '''
    def __init__(self, date:datetime, Report:Indicator) -> None:
        self._date = date
        self._report = Report
    @property
    def date(self):
        return self._date
    @date.setter
    def date(self, date:datetime):
        self._date = date
    @property
    def report(self):
        return self._report
    @report.setter
    def report(self, report:Indicator):
        self._report = report
    def get_Filter(self,big,small):
        aFilter = ReportFilter('filter',self._report,self._report._Unit,big,small)
        temp = aFilter.get_ALL_Report(self._date)
        return temp
    def get_Smooth_Up_Auto(self,avgNum,upNum):
        aSmooth = ReportSmooth('smooth',avgNum,self._report,self._report._Unit)
        aUp = ReportUp('up',upNum,aSmooth,aSmooth._Report._Unit)
        aAuto = ReportAutoTrace('auto',aUp,aUp._Report._Unit)
        temp = aAuto.get_ALL_Report(self._date)
        return temp
    def get_Filter_Auto(self,big,small):
        aFilter = ReportFilter('filter',self._report,self._report._Unit,big,small)
        aAuto = ReportAutoTrace('auto',aFilter,aFilter._Unit)
        temp = aAuto.get_ALL_Report(self._date)
        return temp
    def get_Up_Auto(self,upNum:int):
        aUp = ReportUp('up',upNum,self._report,self._report._Unit)
        aAuto = ReportAutoTrace('auto',aUp,aUp._Report._Unit)
        temp = aAuto.get_ALL_Report(self._date)
        return temp

class All_imge():
    '''取得各種數值圖表
        所有要輸入Indicator類就可以加進來
    '''
    def __init__(self,start:datetime,end:datetime,report:Indicator) -> None:
        self._start = start
        self._end = end
        self._report = report
    @property
    def start(self):
        return self._start
    @property
    def end(self):
        return self._end
    @start.setter
    def start(self,start:datetime):
        self._start = start
    @end.setter
    def end(self,end:datetime):
        self._end = end
    @property
    def report(self):
        return self._report
    @report.setter
    def report(self,report:Indicator):
        self._report = report
    def get_Chart(self, number:int = None):
        if (number is None):
            if (self._report._name != 'ADL') and (self._report._name != 'ADLs'):
                raise
        data_result = pd.DataFrame(columns = ['Date',self._report._name])
        start = self._start
        end = self._end
        while (start <= end):
            if (self._report._name == 'ADL') or (self._report._name == 'ADLs'):
                temp = self._report.get_ALL_Report(end)
            else:
                temp = self._report.get_ReportByNumber(end,number)
            if temp.empty:
                end = self._report.Next_date(end)
                continue
            temp.insert(0,'Date',end)
            data_result = pd.concat([data_result,temp])
            end = self._report.Next_date(end)
        data_result.set_index('Date',inplace=True)
        return data_result

def get_stock_MA(number:str,date:datetime,MA_day:int):#取得某股票某天的均線
    OriginalStocStock_main.number = number
    Temp_MA = SMA_Stock(OriginalStocStock_main,MA_day,info.Price_type.Close).get_ALL()[date]
    return Temp_MA

def get_stock_price(number:str,date:datetime,kind:stock_data_kind):#取得某股票某天的價格
    OriginalStocStock_main.number = number
    if kind == stock_data_kind.Volume:
        Stock_SMA.AvgDay = 5
        Stock_SMA.PriceType = info.Price_type.Volume
        Temp = Stock_SMA.get_PriceByDate(date)
    else:
        Temp = OriginalStocStock_main.get_PriceByDateAndType(date,kind)
    return Temp

#取得月營收逐步升高的篩選
def get_monthRP_up(time:datetime,avgNum:int,upNum:int):#time = 取得資料的時間 avgNum = 平滑曲線月份 upNum = 連續成長月份
    print('get_monthRP_up: start:'+ str(time) )
    Result = All_fuc(time,Month_index).get_Smooth_Up_Auto(avgNum,upNum)
    print('get_monthRP_up: end' )
    return Result
    
#取得本益比篩選 #股價/每股盈餘(EPS)
def get_PER_range(time:datetime,PER_start,PER_end,data:DataFrame):#time = 取得資料的時間 PER_start = PER最小值 PER_end PER最大值
    print('get_PER_range: start')
    Result = All_fuc(time,PER_index).get_Filter_Auto(PER_start,PER_end)
    print('get_PER_range: end')
    return Result
    
#取得本益成長比(PEG)篩選
def get_PEG_range(time:datetime,PEG_start,PEG_end,data:DataFrame):#time = 取得資料的時間 PEG_start = PEG最小值 PEG_end PEG最大值
    print('get_PEG_range: start')
    Result = All_fuc(time,PEG_index).get_Filter_Auto(PEG_start,PEG_end)
    print('get_PEG_range: end')
    return Result
   
#取得平均日成交金額篩選
def get_AVG_value(time:datetime,volume:int,days:int,data:DataFrame):#time = 取得資料的時間 volume = 平均成交金額 days = 平均天數
    print('get_AVG_value: start')
    result = All_Stock_Filters_fuc(time,data).get_Filter_SMA('volume',99999999999,volume,days,info.Price_type.Volume)
    print('get_AVG_value: end')
    return result
    
#取得股價淨值比篩選  #股價/每股淨值 = PBR 
def get_PBR_range(time:datetime,PBR_start:float,PBR_end:float,data = pd.DataFrame()):#time = 取得資料的時間 PBR_start = PBR最小值 PBR_end PBR最大值
    print('get_PBR_rang: start')
    Result = All_fuc(time,PBR_index).get_Filter_Auto(PBR_start,PBR_end)
    print('get_PBR_rang: end')
    return Result
    
#取得股東權益報酬率 #ROE(股東權益報酬率) = 稅後淨利/股東權益
def get_ROE_range(time:datetime,ROE_start,ROE_end,data = pd.DataFrame()):#time = 取得資料的時間 ROE_start = ROE最小值 ROE_end ROE最大值
    print('get_ROE_rang: start')
    Result = All_fuc(time,ROE_index).get_Filter_Auto(ROE_start,ROE_end)
    print('get_ROE_rang: end')
    return Result
    
#取得股價篩選
def get_price_range(time:datetime,high:int,low:int,data = pd.DataFrame()):#time = 取得資料的時間 high = 最高價 low = 最低價
    print('get_price_rang: start')
    if high == low == 0:
        return data
    if high < low or high < 0 or low < 0:
        print("price range number wrong!")
        return data
    Temp = All_Stock_Filters_fuc(time,data).get_Filter('price',high,low,info.Price_type.Close)
    print('get_price_rang: end')
    return Temp
    
#取得創新高篩選
def get_RecordHigh_range(time:datetime,Day:int,RecordHighDay:int,data = pd.DataFrame()):#time = 取得資料的時間 Day = 往前找多少天的創新高 RecordHighDay = 找創新高的區間
    print('get_RecordHigh: start')
    result = All_Stock_Filters_fuc(time,data).get_Filter_RecordHigh(Day,RecordHighDay,info.Price_type.High)
    print('get_RecordHigh: end')
    return result
    
def AvgStockPrice(date,vData = pd.DataFrame()):
    '''平均vData股價'''
    All_price = 0 #
    Count = 0
    Result_avg_price = 0
    if(vData.empty == True):
        return 0,0
    for value in range(0,len(vData)):
        Nnumber = str(vData.iloc[value].name)
        Temp_stock_price = get_stock_price(Nnumber,tools.DateTime2String(date),
                                                            stock_data_kind.AdjClose)
        if Temp_stock_price != None:
            All_price = All_price + Temp_stock_price
            Count = Count + 1
    if All_price == 0 or Count == 0:
        return 0,0
    Result_avg_price = All_price / Count
    return Result_avg_price, Count
