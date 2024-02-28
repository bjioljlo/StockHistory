import os #讀取路徑套件
import twstock as ts #抓取台灣股票資料套件  
import numpy as np
from datetime import datetime
from abc import ABC, abstractmethod
from StockInfoData import StockInfoData

class IStockInfoDatas(ABC):
    '''存檔資訊'''
    @abstractmethod
    def AddStockInfo(number:str):
        '''新增股票'''
        pass
    @abstractmethod
    def DeletStockInfo(self, number:str):
        '''刪除股票'''
        pass
    @abstractmethod
    def GetStockInfo(self, number:str) -> StockInfoData:
        '''取得某隻股票資訊'''
        pass
    @abstractmethod
    def CleanData(self):
        '''清空資料'''
        pass

class TStockInfoDatas(IStockInfoDatas):
    '''存檔資訊實作'''
    def __init__(self) -> None:
        super(TStockInfoDatas,self).__init__()
        self._Stock_list:dict = {}

    def _Show_all_stock_info(self):
        '''顯示所有追蹤股票'''
        if len(self._Stock_list) == 0:
            print('No stock List in there!')
            return
        for m_stock_info in self._Stock_list:
            print(str(m_stock_info) + " : " + self._Stock_list[m_stock_info].name)

    def AddStockInfo(self, number:str):
        '''新增股票'''
        if self._Stock_list.__contains__(number):
            print("此股票已經在清單中")
            return False
        if ts.codes.__contains__(number) == False:
            print("無此檔股票")
            return False
        m_stock = ts.codes[number]
        m_info = StockInfoData(m_stock.code,m_stock.name,m_stock.type,m_stock.start,m_stock.market,m_stock.group)
        self._Stock_list[number]  = m_info
        return True
    def DeletStockInfo(self, number:str):
        '''刪除股票'''
        if self._Stock_list.__contains__(number) == False:
            print("此股票已經不在清單中")
            return False
        del self._Stock_list[number]
        return True
    def GetStockInfo(self, number:str) -> StockInfoData:
        '''取得某隻股票資訊'''
        if self._Stock_list.__contains__(number):
            return self._Stock_list[number]
        else:
            print("no this stock infomation")
            return None
    def CleanData(self):
        self._Stock_list = {}

class PickInfoDatas(TStockInfoDatas):
    '''篩選股票資料'''
    def __init__(self) -> None:
        super().__init__()

class UserInfoDatas(TStockInfoDatas):
    '''使用者股票資料'''
    def __init__(self, Save_name: str, Update_date_name: str) -> None:
        super().__init__()
        self._FilePath:str = os.getcwd()#取得目錄路徑
        self._Save_name:str = Save_name
        self._Update_date_name:str = Update_date_name
        self._Update_date:str = self._Load_Update_date()
        self._Stock_list:dict = self._Load_stock_info()

    @property
    def StockList(self):
        if self._Stock_list == None:
            raise
        return self._Stock_list
    @property
    def UpdateDate(self):
        if self._Update_date == None:
            raise
        return self._Update_date
    @UpdateDate.setter
    def UpdateDate(self, _updateDat:str):
        self._Update_date = _updateDat
        self._Save_Update_date()

    def _Save_Update_date(self):
        '''存檔更新日期'''
        np.save(self._Update_date_name, self._Update_date)
    def _Load_Update_date(self):
        '''讀取更新日期'''
        if os.path.isfile(self._FilePath + '/' + self._Update_date_name):
            m_Update_date = np.load(self._Update_date_name).item()
            print("上次存檔時間:" + str(m_Update_date))
        else:
            m_Update_date = str(datetime.today())
            print('沒存檔時間:'+ str(m_Update_date))
        return m_Update_date
    def _Save_stock_info(self):
        '''存檔追蹤股票'''
        np.save(self._Save_name,self._Stock_list)
    def _Load_stock_info(self) -> dict:
        '''讀取追蹤股票'''
        if os.path.isfile(self._FilePath + '/' + self._Save_name):
            m_stock_list = np.load(self._Save_name,None,True).item()
        else:
            self._Save_stock_info()
        return m_stock_list

    def AddStockInfo(self, number:str):
        Result = super().AddStockInfo(number)
        if Result:
            self._Save_stock_info() 
        return Result
    def DeletStockInfo(self, number: str):
        Result = super().DeletStockInfo(number)
        if Result:
           self._Save_stock_info() 
        return Result
    def CleanData(self):
        super().CleanData()
        self._Save_stock_info()
