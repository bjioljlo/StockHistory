"""
股票指標欄位的枚舉
"""
from enum import Enum

class FS_type(Enum):
    CPL = 'consolidated-profit-and-loss-summary'  #'綜合損益彙總表'
    BS = 'balance-sheet' #'資產負債彙總表'
    PLA = 'profit-and-loss-analysis-summary'  #'營益分析彙總表'
    SCF = 'statement-of-cash-flows' #現金流量表
class StrEnum(str, Enum):
    pass
class CPL_type(StrEnum):
    type_0 = '本期綜合損益總額（稅後）'
    EPS = '基本每股盈餘（元）'
class BS_type(StrEnum):
    type_0 = '資產總額'
    type_1 = '負債總額'
    type_2 = '股本'
    type_3 = '權益總額'
    type_4 = '每股參考淨值'
class PLA_type(StrEnum):
    type_0 = '營業收入'
    type_1 = '毛利率(%)'
    type_2 = '營業利益率(%)'
    type_3 = '稅前純益率(%)'
    type_4 = '稅後純益率(%)'
class SCF_type(StrEnum):
    OCF = '營業活動之淨現金流入（流出）'
    ICF = '投資活動之淨現金流入（流出）'
    FCF = '籌資活動之淨現金流入（流出）'
class Month_type(StrEnum):
    MR = '當月營收'
class Day_type(StrEnum):
    PER = '本益比'
    PBR = '股價淨值比'
    Yield = '殖利率(%)'
class Price_type(StrEnum):
    Open = 'Open'
    High = 'High'
    Low = 'Low'
    Close = 'Close'
    AdjClose = 'Adj Close'
    Volume = 'Volume'
class local_type():
    Taiwan = '.tw'
    USA = ''
class stock_data_kind(Enum):
    AdjClose = 'Adj Close'
    Volume = 'Volume'
