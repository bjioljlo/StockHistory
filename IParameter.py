from abc import ABC, abstractmethod
from datetime import datetime

class IParameter(ABC):
    """此頁的輸入結構"""
    @abstractmethod
    def __init__(self) -> None:
        pass

class RecordMainParameter(IParameter):
    def __init__(self) -> None:
        super().__init__()
        self.number:int = None
        self.startdate:datetime = None     
        self.enddate: datetime = None
    
class RecordPickParameter(IParameter):
    def __init__(self) -> None:
        super().__init__()
        self.GPM:float = None
        self.OPR:float = None
        self.RPS:float = None
        self.OMGR :int = None
        self.PBR_high :float = None
        self.PBR_low :float = None
        self.PER_high :float = None
        self.PER_low :float = None
        self.ROE_high :float = None
        self.ROE_low :float = None
        self.yiled_high :float = None
        self.yiled_low :float = None
        self.PEG_high :float = None
        self.PEG_low :float = None
        self.monthRP_UpMpnth :int = None
        self.volum :int = None
        self.price_high :int = None
        self.price_low :int = None
        self.flash_Day :int = None
        self.record_Day :int = None
        self.FCF :int = None
        self.ROE :int = None
        self.EPS :int = None
        self.SRGR :int = None
        self.MRGR :int = None
        self.monthRP_smoothAVG :int = None
        self.EPS_up :int = None
        self.BetterMA :int = None

class RecordBackTestParameter(IParameter):
    def __init__(self) -> None:
        super().__init__()    
        self.check_monthRP_pick:bool = None
        self.check_PER_pick:bool = None
        self.check_volume_pick:bool = None
        self.check_pickOneStock:bool = None
        self.check_price_pick:bool = None
        self.check_PBR_pick:bool = None
        self.check_ROE_pick:bool = None
        self.date_start:datetime = None
        self.date_end:datetime = None
        self.buy_number:str = None
        self.money_start:int = None
        self.change_days:int = None
        self.smoothAVG:int = None
        self.upMonth:int = None
        self.volumeAVG:int = None
        self.volumeDays:int = None
        self.price_high:int = None
        self.price_low:int = None
        self.Pick_amount:int = None
        self.buy_day:int = None
        self.Record_high_day:int = None
        self.PER_start:float = None
        self.PER_end:float = None
        self.PBR_end:float = None
        self.PBR_start:float = None
        self.ROE_end:float = None
        self.ROE_start:float = None
        self.Dividend_yield_high:float = None
        self.Dividend_yield_low:float = None