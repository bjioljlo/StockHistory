"""
系統的存檔資訊
"""

import os  # 讀取路徑套件
from abc import ABC, abstractmethod
from datetime import datetime

import numpy as np
import twstock as ts  # 抓取台灣股票資料套件

from pydb_core.stock_info_data import StockInfoData


class IStockInfoDatas(ABC):
    """存檔資訊"""

    @property
    @abstractmethod
    def StockList(self) -> dict[StockInfoData]:
        pass

    @abstractmethod
    def AddStockInfo(number: str):
        """新增股票"""
        pass

    @abstractmethod
    def DeletStockInfo(self, number: str):
        """刪除股票"""
        pass

    @abstractmethod
    def GetStockInfo(self, number: str) -> StockInfoData:
        """取得某隻股票資訊"""
        pass

    @abstractmethod
    def CleanData(self):
        """清空資料"""
        pass


class TStockInfoDatas(IStockInfoDatas):
    """存檔資訊實作"""

    def __init__(self) -> None:
        super(TStockInfoDatas, self).__init__()
        self._Stock_list: dict[StockInfoData] = {}

    @property
    def StockList(self) -> dict[StockInfoData]:
        if self._Stock_list is None:
            raise
        return self._Stock_list

    def _Show_all_stock_info(self):
        """顯示所有追蹤股票"""
        if len(self._Stock_list) == 0:
            print("No stock List in there!")
            return
        for m_stock_info in self._Stock_list:
            print(str(m_stock_info) + " : " + self._Stock_list[m_stock_info].name)

    def AddStockInfo(self, number: str):
        """新增股票"""
        if self._Stock_list.__contains__(number):
            print("此股票已經在清單中")
            return False
        if not ts.codes.__contains__(number):
            print("無此檔股票")
            return False
        m_stock = ts.codes[number]
        m_info = StockInfoData(
            m_stock.code,
            m_stock.name,
            m_stock.type,
            m_stock.start,
            m_stock.market,
            m_stock.group,
        )
        self._Stock_list[number] = m_info
        return True

    def DeletStockInfo(self, number: str):
        """刪除股票"""
        if not self._Stock_list.__contains__(number):
            print("此股票已經不在清單中")
            return False
        del self._Stock_list[number]
        return True

    def GetStockInfo(self, number: str) -> StockInfoData:
        """取得某隻股票資訊"""
        if self._Stock_list.__contains__(number):
            return self._Stock_list[number]
        else:
            print("no this stock infomation")
            return None

    def CleanData(self):
        self._Stock_list = {}


class PickInfoDatas(TStockInfoDatas):
    """篩選股票資料"""

    def __init__(self) -> None:
        super().__init__()


class UserInfoDatas(TStockInfoDatas):
    """使用者股票資料"""

    def __init__(self, Save_name: str, Update_date_name: str, TW_Update_date_name: str = None, US_Update_date_name: str = None) -> None:
        super().__init__()
        self._FilePath: str = os.getcwd()  # 取得目錄路徑
        self._Save_name: str = Save_name
        self._Update_date_name: str = Update_date_name
        self._TW_Update_date_name: str = TW_Update_date_name or "TW_Update_date.npy"
        self._US_Update_date_name: str = US_Update_date_name or "US_Update_date.npy"
        self._Update_date: str = self._Load_Update_date()
        self._TW_Update_date: str = self._Load_TW_Update_date()
        self._US_Update_date: str = self._Load_US_Update_date()
        self._Stock_list = self._Load_stock_info()

    @property
    def UpdateDate(self):
        if self._Update_date is None:
            raise
        return self._Update_date

    @UpdateDate.setter
    def UpdateDate(self, _updateDat: str):
        self._Update_date = _updateDat
        self._Save_Update_date()

    @property
    def TW_UpdateDate(self):
        if self._TW_Update_date is None:
            raise
        return self._TW_Update_date

    @TW_UpdateDate.setter
    def TW_UpdateDate(self, _updateDat: str):
        self._TW_Update_date = _updateDat
        self._Save_TW_Update_date()

    @property
    def US_UpdateDate(self):
        if self._US_Update_date is None:
            raise
        return self._US_Update_date

    @US_UpdateDate.setter
    def US_UpdateDate(self, _updateDat: str):
        self._US_Update_date = _updateDat
        self._Save_US_Update_date()

    def _Save_Update_date(self):
        """存檔更新日期"""
        np.save(self._Update_date_name, self._Update_date)

    def _Load_Update_date(self):
        """讀取更新日期"""
        if os.path.isfile(self._FilePath + "/" + self._Update_date_name):
            m_Update_date = np.load(self._Update_date_name).item()
            print("上次存檔時間:" + str(m_Update_date))
        else:
            m_Update_date = str(datetime.today())
            print("沒存檔時間:" + str(m_Update_date))
        return m_Update_date

    def _Save_TW_Update_date(self):
        """存檔台灣股票更新日期"""
        np.save(self._TW_Update_date_name, self._TW_Update_date)

    def _Load_TW_Update_date(self):
        """讀取台灣股票更新日期"""
        if os.path.isfile(self._FilePath + "/" + self._TW_Update_date_name):
            m_Update_date = np.load(self._TW_Update_date_name).item()
            print("上次台灣股票存檔時間:" + str(m_Update_date))
        else:
            # 檢查是否有舊的 Update_date.npy 文件，如果有就使用它
            old_file = self._FilePath + "/" + self._Update_date_name.replace("Update_date.npy", "Update_date.npy")
            if os.path.isfile(old_file):
                m_Update_date = np.load(old_file).item()
                print("從舊文件讀取台灣股票存檔時間:" + str(m_Update_date))
            else:
                m_Update_date = str(datetime.today())
                print("沒台灣股票存檔時間:" + str(m_Update_date))
        return m_Update_date

    def _Save_US_Update_date(self):
        """存檔美股更新日期"""
        np.save(self._US_Update_date_name, self._US_Update_date)

    def _Load_US_Update_date(self):
        """讀取美股更新日期"""
        if os.path.isfile(self._FilePath + "/" + self._US_Update_date_name):
            m_Update_date = np.load(self._US_Update_date_name).item()
            print("上次美股存檔時間:" + str(m_Update_date))
        else:
            # 檢查是否有舊的 Update_date.npy 文件，如果有就使用它
            old_file = self._FilePath + "/" + self._Update_date_name.replace("Update_date.npy", "Update_date.npy")
            if os.path.isfile(old_file):
                m_Update_date = np.load(old_file).item()
                print("從舊文件讀取美股存檔時間:" + str(m_Update_date))
            else:
                m_Update_date = str(datetime.today())
                print("沒美股存檔時間:" + str(m_Update_date))
        return m_Update_date

    def _Save_stock_info(self):
        """存檔追蹤股票（只存dict，不存物件）"""
        dict_to_save = {k: v.__dict__ for k, v in self._Stock_list.items()}
        np.save(self._Save_name, dict_to_save)

    def _Load_stock_info(self) -> dict[StockInfoData]:
        """讀取追蹤股票（反序列化時手動轉回StockInfoData）"""
        if os.path.isfile(self._FilePath + "/" + self._Save_name):
            dict_loaded = np.load(self._Save_name, allow_pickle=True).item()
            m_stock_list = {k: StockInfoData(**v) for k, v in dict_loaded.items()}
        else:
            self._Save_stock_info()
            m_stock_list = {}
        return m_stock_list

    def AddStockInfo(self, number: str):
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
