from StockInfoData import StockInfoData, StockInfoCurrentData
from abc import ABC, abstractmethod
import twstock as ts #抓取台灣股票資料套件

class IStockInfoDataInHand(ABC):
    '''手持股票資訊'''
    @property
    @abstractmethod
    def Price(self) -> float:
        pass
    @property
    @abstractmethod
    def Amount(self) -> int:
        pass
    @abstractmethod
    def AddAmount(self,amount:int,price:float):
        '''買入'''
        pass
    @abstractmethod
    def MinusAmount(self,amount:int) -> bool:
        '''賣出'''
        pass

class TStockInfoDataInHand(IStockInfoDataInHand):
    '''手持股票資訊實作'''
    def __init__(self,stock_info: StockInfoCurrentData):
        self._StockInfoCurData:StockInfoCurrentData = stock_info

    @property
    def Price(self) -> float:
        '''平均價格'''
        if self._StockInfoCurData.price == None:
            raise
        return self._StockInfoCurData.price
    
    @property
    def Amount(self) -> int:
        '''總持有數量'''
        if self._StockInfoCurData.amount == None:
            raise
        return self._StockInfoCurData.amount
    @abstractmethod
    def AddAmount(self,amount:int,price:float):
        pass
        
    def MinusAmount(self,amount:int) -> bool:
        '''賣出'''
        if self._StockInfoCurData.amount > amount:
            self._StockInfoCurData.amount = self._StockInfoCurData.amount - amount
            return True
        elif self._StockInfoCurData.amount < amount:
            print(str(self._StockInfoCurData.stock_info.name) + '數量不足!')
        self._StockInfoCurData.amount = 0
        return False

class StockInfoDataInHandWithWeightedAverage(TStockInfoDataInHand):
    '''手持股票資訊(買入用加權平均)'''
    def AddAmount(self,amount:int,price:float):
        '''買入(會和之前加權平均)'''
        self._StockInfoCurData.price = ((self._StockInfoCurData.price * self._StockInfoCurData.amount) + (price * amount)) / (self._StockInfoCurData.amount + amount)
        self._StockInfoCurData.amount = self._StockInfoCurData.amount + amount

def  StockInfoDataInHandFactory(number:str) -> IStockInfoDataInHand:
    m_stock = ts.codes[str(number)]
    m_info = StockInfoData(m_stock.code,m_stock.name,m_stock.type,m_stock.start,m_stock.market,m_stock.group)
    return StockInfoDataInHandWithWeightedAverage(StockInfoCurrentData(m_info, 0, 0))
