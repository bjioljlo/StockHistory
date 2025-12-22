from abc import ABC, abstractmethod
from datetime import datetime

import pandas as pd

from src.Common import InfomationType as info


class IGetExternalData(ABC):
    @abstractmethod
    def get_allstock_financial_statement(self, start: datetime, type: info.FS_type):
        """#爬某季所有股票歷史財報"""
        pass

    @abstractmethod
    def get_allstock_monthly_report(self, start: datetime):
        """爬某月所有股票月營收"""
        pass

    @abstractmethod
    def get_allstock_yield(self, start: datetime):
        """#爬某天所有股票殖利率"""
        pass

    @abstractmethod
    def get_stock_history(
        self, number: str, start=datetime.strptime("2005-1-1", "%Y-%m-%d")
    ) -> pd.DataFrame:
        """#爬某個股票的歷史紀錄"""
        pass

    @abstractmethod
    def get_stock_AD_index(self, date: datetime, getNew=False):
        """#取得上漲和下跌家數"""
        pass

    @abstractmethod
    def get_full_ad_index(self) -> pd.DataFrame:
        """#取得完整的上漲和下跌家數歷史資料"""
        pass