"""
股票指標欄位的枚舉
"""

from abc import abstractmethod
from enum import Enum


class FS_type(Enum):
    CPL = "consolidated-profit-and-loss-summary"  # '綜合損益彙總表'
    BS = "balance-sheet"  # '資產負債彙總表'
    PLA = "profit-and-loss-analysis-summary"  # '營益分析彙總表'
    SCF = "statement-of-cash-flows"  # 現金流量表


class StrEnum(str, Enum):
    @abstractmethod
    def get_sql_column(self) -> str:
        """獲取對應的 SQL 欄位名稱"""
        pass


class CPL_type(StrEnum):
    type_0 = "本期綜合損益總額（稅後）"
    EPS = "基本每股盈餘（元）"
    
    def get_sql_column(self) -> str:
        """獲取對應的 SQL 欄位名稱"""
        mapping = {
            "本期綜合損益總額（稅後）": "consolidated_net_income",
            "基本每股盈餘（元）": "consolidated_eps"
        }
        return mapping.get(self.value, self.value)


class BS_type(StrEnum):
    type_0 = "資產總額"
    type_1 = "負債總額"
    type_2 = "股本"
    type_3 = "權益總額"
    type_4 = "每股參考淨值"
    
    def get_sql_column(self) -> str:
        """獲取對應的 SQL 欄位名稱"""
        mapping = {
            "資產總額": "total_assets",
            "負債總額": "total_liabilities",
            "股本": "capital",
            "權益總額": "equity",
            "每股參考淨值": "book_value_per_share"
        }
        return mapping.get(self.value, self.value)


class PLA_type(StrEnum):
    type_0 = "營業收入"
    type_1 = "毛利率(%)"
    type_2 = "營業利益率(%)"
    type_3 = "稅前純益率(%)"
    type_4 = "稅後純益率(%)"
    
    def get_sql_column(self) -> str:
        """獲取對應的 SQL 欄位名稱"""
        mapping = {
            "營業收入": "revenue",
            "毛利率(%)": "gross_margin",
            "營業利益率(%)": "operating_margin",
            "稅前純益率(%)": "pre_tax_margin",
            "稅後純益率(%)": "net_margin"
        }
        return mapping.get(self.value, self.value)


class SCF_type(StrEnum):
    OCF = "營業活動之淨現金流入（流出）"
    ICF = "投資活動之淨現金流入（流出）"
    FCF = "籌資活動之淨現金流入（流出）"
    
    def get_sql_column(self) -> str:
        """獲取對應的 SQL 欄位名稱"""
        mapping = {
            "營業活動之淨現金流入（流出）": "operating_cash_flow",
            "投資活動之淨現金流入（流出）": "investing_cash_flow",
            "籌資活動之淨現金流入（流出）": "financing_cash_flow"
        }
        return mapping.get(self.value, self.value)


class Month_type(StrEnum):
    MR = "當月營收"
    
    def get_sql_column(self) -> str:
        """獲取對應的 SQL 欄位名稱"""
        mapping = {
            "當月營收": "revenue_current_month"
        }
        return mapping.get(self.value, self.value)


class Day_type(StrEnum):
    PER = "本益比"
    PBR = "股價淨值比"
    Yield = "殖利率(%)"
    
    def get_sql_column(self) -> str:
        """獲取對應的 SQL 欄位名稱"""
        mapping = {
            "本益比": "pe_ratio",
            "股價淨值比": "pb_ratio",
            "殖利率(%)": "dividend_yield"
        }
        return mapping.get(self.value, self.value)


class Price_type(StrEnum):
    Open = "Open"
    High = "High"
    Low = "Low"
    Close = "Close"
    AdjClose = "Adj Close"
    Volume = "Volume"
    
    def get_sql_column(self) -> str:
        """獲取對應的 SQL 欄位名稱"""
        # Price_type 已經是英文，直接返回
        return self.value


class local_type:
    Taiwan = ".tw"
    USA = ""


class stock_data_kind(Enum):
    Close = "Close"
    AdjClose = "Adj Close"
    Volume = "Volume"
    
    def get_sql_column(self) -> str:
        """獲取對應的 SQL 欄位名稱"""
        # stock_data_kind 已經是英文，直接返回
        return self.value
