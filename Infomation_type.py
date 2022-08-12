from enum import Enum

class FS_type(Enum):
    CPL = 'Consolidated-profit-and-loss-summary'  #'綜合損益彙總表'
    BS = 'Balance-sheet' #'資產負債彙總表'
    PLA = 'Profit-and-loss-analysis-summary'  #'營益分析彙總表'
    SCF = 'Statement-of-Cash-Flows' #現金流量表

CPL_type = Enum('_type','本期綜合損益總額（稅後） 基本每股盈餘（元）')
BS_type = Enum('_type','資產總額 負債總額 股本 權益總額 每股參考淨值')
PLA_type = Enum('_type','營業收入 毛利率(%) 營業利益率(%) 稅前純益率(%) 稅後純益率(%)')
SCF_type = Enum('_type','營業活動之淨現金流入（流出） 投資活動之淨現金流入（流出） 籌資活動之淨現金流入（流出）')
Month_type = Enum('_type','當月營收')
Day_type = Enum('_type','本益比 股價淨值比 殖利率(%)')

class local_type():
    Taiwan = '.TW'
    USA = ''