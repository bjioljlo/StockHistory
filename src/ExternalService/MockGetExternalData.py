from datetime import datetime
import pandas as pd
from src.Common import InfomationType as info
from src.ExternalService.IGetExternalData import IGetExternalData


class MockGetExternalData(IGetExternalData):
    """
    模擬外部資料服務實作
    用於開發階段讓系統可以順利啟動
    """
    
    def __init__(self, sql_service=None, mongo_service=None, read_load_system=None, cache_service=None):
        self._sql_service = sql_service
        self._mongo_service = mongo_service
        self._read_load_system = read_load_system
        self._cache_service = cache_service

    def get_allstock_financial_statement(self, start: datetime, type: info.FS_type):
        """模擬財報資料"""
        print(f"[Mock] get_allstock_financial_statement called for date: {start}, type: {type}")
        return pd.DataFrame()

    def get_allstock_monthly_report(self, start: datetime):
        """模擬月營收資料"""
        print(f"[Mock] get_allstock_monthly_report called for date: {start}")
        return pd.DataFrame()

    def get_allstock_yield(self, start: datetime):
        """模擬殖利率資料"""
        print(f"[Mock] get_allstock_yield called for date: {start}")
        return pd.DataFrame()

    def get_allstock_dividend_yield(self):
        """模擬股息殖利率資料"""
        print("[Mock] get_allstock_dividend_yield called")
        return pd.DataFrame()

    def get_stock_history(self, number: str, start=datetime.strptime("2005-1-1", "%Y-%m-%d")) -> pd.DataFrame:
        """模擬股票歷史資料"""
        print(f"[Mock] get_stock_history called for stock: {number}")
        return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'])

    def get_stock_AD_index(self, date: datetime, getNew=False):
        """模擬漲跌家數資料"""
        print(f"[Mock] get_stock_AD_index called for date: {date}")
        return {'up_count': 0, 'down_count': 0}

    def get_full_ad_index(self) -> pd.DataFrame:
        """模擬完整漲跌家數歷史資料"""
        print("[Mock] get_full_ad_index called")
        return pd.DataFrame(columns=['up_count', 'down_count'])

    def get_full_adl(self) -> pd.DataFrame:
        """模擬完整騰落指標歷史資料"""
        print("[Mock] get_full_adl called")
        return pd.DataFrame(columns=['ADL'])