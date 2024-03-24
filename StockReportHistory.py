import sys
from abc import ABC, abstractmethod
from pandas import DataFrame, Series
import Infomation_type as info
import tools
from StockHistory import OriginalStock
from GetExternalData import TGetExternalData

class IReport(ABC):
    '''指標歷史資料'''
    @abstractmethod
    def get_ALL_Report(self,date) -> DataFrame:
        raise NotImplementedError( "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name))           
class TReport(IReport):
    '''指標歷史資料實作'''
    def __init__(self, name: str , Unit:int) -> None:
        self._name = name
        self._Unit = Unit
        self._main_GetExternalData = TGetExternalData()
    @abstractmethod
    def get_ALL_Report(self,date)-> DataFrame:
        raise NotImplementedError( "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name))  
    def get_ReportByNumber(self,date,number:int) -> Series:
        Temp = self.get_ALL_Report(date)
        try:
            Temp_Result = Temp[Temp.index == number]
            if Temp_Result.empty:
                raise
            return Temp_Result
        except:
            if Temp.empty:
                print(''.join([str(date),'的',self._name,'表沒出']))
            else:
                print(''.join([str(date),'的',str(number),'公司尚未成立']))
            return DataFrame()  
    def get_ReportByType(self,date,_type:info.StrEnum) -> Series:
        Temp = self.get_ALL_Report(date)
        try:
            return Temp[_type.value]
        except:
            print(''.join([str(date),'的',self._name,'表沒出']))
            return DataFrame()
    def get_ReportByTypeAndNumber(self,date,_type:info.StrEnum,number:int):
        Temp = self.get_ReportByType(date,_type)
        try:
            return Temp[number]
        except:
            if Temp.empty == False:
                print(''.join([str(date),'的',str(number),'公司尚未成立']))
            return None
    def Next_date(self,date):
        return tools.changeDateMonth(date,-self._Unit)
class Season_Report(TReport):
    '''以季為單位的指標歷史資料'''
    def __init__(self, _FS_type:info.FS_type, name: str, Unit: int):
        super().__init__(name, Unit)
        self._FS_type = _FS_type
    def get_ALL_Report(self,date)-> DataFrame:
        main_GetExternalData = TGetExternalData()
        return main_GetExternalData.get_allstock_financial_statement(date,self._FS_type)
class Month_Report(TReport):
    '''以月為單位的指標歷史資料'''
    def get_ALL_Report(self, date):
        main_GetExternalData = TGetExternalData()
        return main_GetExternalData.get_allstock_monthly_report(date)
class Day_Report(TReport):
    '''以日為單位的指標歷史資料'''
    def get_ALL_Report(self, date):
        return self._main_GetExternalData.get_allstock_yield(date)
    def Next_date(self,date):
        date = tools.backWorkDays(date,self._Unit)
        while self._main_GetExternalData.get_stock_history('2330', date).empty == True:
            date = tools.backWorkDays(date,self._Unit)   
        return date
class ADL_Report(TReport):
    '''以日為單位的騰落指標歷史資料(AD)'''
    def get_ALL_Report(self, date):
        return self._main_GetExternalData.get_stock_AD_index(date)
    def Next_date(self,date):
        date = tools.backWorkDays(date,self._Unit)
        while self._main_GetExternalData.get_stock_history('2330', date).empty == True:
            date = tools.backWorkDays(date,self._Unit)   
        return date

class Indicator(TReport):
    '''指標處理'''
    def __init__(self, name: str, Unit: int) -> None:
        super().__init__(name, Unit)
class ROE_Indicator(Indicator):
    '''#取得股東權益報酬率'''
    def __init__(self, name: str,CPL_RP:Season_Report,BS_RP:Season_Report) -> None:
        super().__init__(name, CPL_RP._Unit)
        self.CPL = CPL_RP
        self.BS = BS_RP
    def get_ALL_Report(self,date) -> DataFrame:
        table_result = DataFrame()
        table_CPL = self.CPL.get_ReportByType(date,info.CPL_type.type_0)
        table_BS = self.BS.get_ReportByType(date,info.BS_type.type_3)
        if table_BS.empty or table_CPL.empty:
            return DataFrame()
        table_result[self._name] = round((table_CPL/table_BS),4) * 100
        return table_result
class FreeCF_Indicator(Indicator):
    '''#取得自由現金流'''
    def __init__(self, name: str,SCF_RP:Season_Report) -> None:
        super().__init__(name, SCF_RP._Unit)
        self.SCF = SCF_RP
    def get_ALL_Report(self, date) -> DataFrame:
        table_result = DataFrame()
        table_ICF = self.SCF.get_ReportByType(date,info.SCF_type.ICF)
        table_OCF = self.SCF.get_ReportByType(date,info.SCF_type.OCF)
        if table_ICF.empty or table_OCF.empty:
            return DataFrame()
        table_result[self._name] = table_ICF + table_OCF
        return table_result
class Debt_Indicator(Indicator):
    '''#取得資產負債比率'''
    def __init__(self, name: str,BS_RP:Season_Report) -> None:
        super().__init__(name, BS_RP._Unit)
        self.BS = BS_RP
    def get_ALL_Report(self, date) -> DataFrame:
        table_result = DataFrame()
        table_Assets = self.BS.get_ReportByType(date,info.BS_type.type_0)
        table_Debt = self.BS.get_ReportByType(date,info.BS_type.type_1)
        if table_Debt.empty or table_Assets.empty:
            return DataFrame()
        table_result[self._name] = table_Debt / table_Assets
        return table_result       
class MR_Growth_Indicator(Indicator):
    '''#取得月營收成長率'''
    def __init__(self, name: str, monthRP:Month_Report) -> None:
        super().__init__(name, monthRP._Unit)
        self.monthRP = monthRP
    def get_ALL_Report(self, date):
        data_result = DataFrame()
        MR_now = self.monthRP.get_ReportByType(date,info.Month_type.MR)
        MR_old = self.monthRP.get_ReportByType(tools.changeDateMonth(date,-12),info.Month_type.MR)
        if MR_now.empty or MR_old.empty:
            return DataFrame()
        data_result[self._name] = ((MR_now - MR_old)/MR_old) * 100
        return data_result
class SR_Growth_Indicator(Indicator):
    '''#取得季營收成長率'''
    def __init__(self, name: str, PLA_RP:Season_Report) -> None:
        super().__init__(name, PLA_RP._Unit)
        self.PLA_RP = PLA_RP
    def get_ALL_Report(self, date):
        data_result = DataFrame()
        SR_now = self.PLA_RP.get_ReportByType(date,info.PLA_type.type_0)
        SR_old = self.PLA_RP.get_ReportByType(tools.changeDateMonth(date,-12),info.PLA_type.type_0)
        if SR_now.empty or SR_old.empty:
            return DataFrame()
        data_result[self._name] = ((SR_now - SR_old)/SR_old) * 100
        return data_result
class OM_Growth_Indicator(Indicator):
    '''#取得營業利益成長率'''
    def __init__(self, name: str,PLA_RP:Season_Report) -> None:
        super().__init__(name, PLA_RP._Unit)
        self.PLA = PLA_RP
    def get_ALL_Report(self, date) -> DataFrame:
        data_result = DataFrame()
        OM_now = self.PLA.get_ReportByType(date,info.PLA_type.type_2) 
        OM_old = self.PLA.get_ReportByType(tools.changeDateMonth(date,-12),info.PLA_type.type_2)
        if OM_now.empty or OM_old.empty:
            return DataFrame()
        data_result[self._name] = ((OM_now - OM_old)/OM_old) * 100
        return data_result
class PEG_Indicator(Indicator):
    '''#取得本益成長比'''
    def __init__(self, name: str,OM_Growth:OM_Growth_Indicator,Yield_RP:Day_Report) -> None:
        super().__init__(name, OM_Growth._Unit)
        self.Yield = Yield_RP
        self.OM_Growth = OM_Growth
    def get_ALL_Report(self, date) -> DataFrame:
        table_result = DataFrame()
        table_PE = self.Yield.get_ReportByType(date,info.Day_type.PER)
        table_OM_Growth = self.OM_Growth.get_ALL_Report(date)
        if table_OM_Growth.empty or table_PE.empty:
            return DataFrame()
        table_result[self._name] = table_PE / table_OM_Growth[self.OM_Growth._name]
        return table_result
class OCFPerShare_Indicator(Indicator):
    '''#每股營業現金流'''   
    def __init__(self, name: str,SCF_RP:Season_Report,BS_RP:Season_Report) -> None:
        super().__init__(name, SCF_RP._Unit)
        self.SCF_RP = SCF_RP
        self.BS_RP = BS_RP
    def get_ALL_Report(self, date):
        table_result = DataFrame()
        table_OCF = self.SCF_RP.get_ReportByType(date,info.SCF_type.OCF)
        table_BS = self.BS_RP.get_ReportByType(date,info.BS_type.type_2)
        if table_OCF.empty or table_BS.empty:
            return DataFrame()
        table_result[self._name] = table_OCF / table_BS
        return table_result
class PCF_Indicator(Indicator):
    '''#股價現金流量比率'''
    def __init__(self, name: str,OCFPerShare:OCFPerShare_Indicator,StockPrice:OriginalStock) -> None:
        super().__init__(name, 1)
        self.OCFPerShare = OCFPerShare
        self._number = None
        self._StockPrice = StockPrice
    def get_ALL_Report(self, date):
        if self._number == None:
            raise TypeError('please set number! type now:' + self._number)
        table_result = DataFrame()
        table_OCFPerShare = self.OCFPerShare.get_ReportByNumber(date,self._number)
        if table_OCFPerShare.empty:
            return DataFrame()
        self._StockPrice.number = self._number
        stock_price = self._StockPrice.get_PriceByDateAndType(date,info.Price_type.AdjClose)#get_stock_price(self._number,date,stock_data_kind.AdjClose)
        table_result[self._name] = stock_price/table_OCFPerShare
        return table_result
    def get_ReportByNumber(self, date, number: int) -> Series:
        self._number = number
        return super().get_ReportByNumber(date, number)
    def Next_date(self,date):#有用到每日的價格所以用天為單位
        date = tools.backWorkDays(date,self._Unit)
        while (date not in self._main_GetExternalData.get_stock_history('2330',date).index): #get_stock_price(2330,date,stock_data_kind.AdjClose) == None:
            date = tools.backWorkDays(date,self._Unit)  
        return date
    @property
    def number(self):
        return self._number
    @number.setter
    def number(self,number:int):
        self._number = number
class Original_Indicator(Indicator):
    '''直接取得指標歷史資料'''
    def __init__(self, name: str, Report:TReport, type:info.StrEnum) -> None:
        super().__init__(name,Report._Unit)
        self._Report = Report
        self._type = type
    def get_ALL_Report(self, date) -> DataFrame:
        table_result = DataFrame()
        table_temp = self._Report.get_ReportByType(date,self._type)
        if table_temp.empty:
            return DataFrame()
        table_result[self._name] = table_temp
        return table_result
    def Next_date(self, date,):
        return self._Report.Next_date(date)
    @property
    def Report(self):
        return self._Report       
class ADL_Indicator(Indicator):
    '''騰落指標'''   
    def __init__(self, name: str, AD_RP:ADL_Report) -> None:
        super().__init__(name, AD_RP._Unit)
        self._AD_RP = AD_RP
    def get_ALL_Report(self, date):
        data_result = DataFrame()
        ADL_now = self._AD_RP.get_ALL_Report(date)
        if ADL_now.empty :
            return DataFrame()
        data_result[self._name] = (ADL_now['上漲'] - ADL_now['下跌'])
        return data_result
    def Next_date(self, date):
        return self._AD_RP.Next_date(date)
class ADLs_Indicator(Indicator):
    '''騰落比例指標''' 
    def __init__(self, name: str, AD_RP:ADL_Report) -> None:
        super().__init__(name, AD_RP._Unit)
        self._AD_RP = AD_RP
    def get_ALL_Report(self, date):
        data_result = DataFrame()
        ADLs_today = self._AD_RP.get_ALL_Report(date)
        if ADLs_today.empty:
            return DataFrame()
        data_result[self._name] = (ADLs_today['上漲']/(ADLs_today['上漲'] + ADLs_today['下跌'])) - 0.5
        return data_result
    def Next_date(self, date):
        return self._AD_RP.Next_date(date)

