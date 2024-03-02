from datetime import timedelta, datetime
import pandas as pd
from pandas import DataFrame
from get_stock_history import get_stock_price,stock_data_kind
from StockInfoData import StockInfoData, BaseInfoData, StockInfoCurrentData
from StockInfoDataInHand import IStockInfoDataInHand, StockInfoDataInHandWithWeightedAverage
import tools
import twstock as ts #抓取台灣股票資料套件
from abc import ABC, abstractmethod, abstractproperty

class IStockInfoDatasInBackTest(ABC):
    '''回測資訊'''
    @abstractproperty
    @property
    def BaseInfoData(self)-> BaseInfoData:
        pass
    @abstractproperty
    @property
    def HandleStock(self)-> dict[str, IStockInfoDataInHand]:
        pass
    @abstractmethod
    def SellAllStock(self):
        pass
    @abstractmethod
    def SellStock(self,number:str,amount:int) -> bool:
        pass
    @abstractmethod
    def BuyAllStock(self,data:DataFrame):
        pass
    @abstractmethod
    def BuyStock(self,number:str,amount:int) -> bool:
        pass

class TStockInfoDatasInBackTest(IStockInfoDatasInBackTest):
    '''回測資訊實作'''
    def __init__(self, _baseInfoData:BaseInfoData) -> None:
        super(TStockInfoDatasInBackTest,self).__init__()
        self._BaseInfoData:BaseInfoData = _baseInfoData
        self._HandleStock:dict[str, IStockInfoDataInHand] = {}#手持股票
    def _GetUserStockAsset(self) -> int:
        '''股票資產'''
        Temp_money = 0
        for key,value in self._HandleStock.items():
            Temp = get_stock_price(key,self._BaseInfoData.now_day,stock_data_kind.AdjClose)
            if Temp == None:
                print('no stock price:' + str(key))
                continue
            Temp_money = Temp_money + (Temp * value.Amount)
        return Temp_money  
    def _GetUserAllAsset(self) -> int:
        '''總資產'''
        Temp_money = self._GetUserStockAsset()
        return Temp_money + self._BaseInfoData.now_money  
    @property
    def BaseInfoData(self) -> BaseInfoData:
        if self._BaseInfoData == None:
            raise
        return self._BaseInfoData
    @property
    def HandleStock(self)-> dict[str, IStockInfoDataInHand]:
        if self._HandleStock == None:
            raise
        return self._HandleStock
    @abstractmethod
    def SellStock(self,number:str,amount:int) -> bool:
        '''賣某張股票'''
        pass
    @abstractmethod
    def BuyStock(self,number:str,amount:int) -> bool:
        '''買股票'''
        pass
    def SellAllStock(self):
        '''賣出所有股票'''
        for key,value in list(self._HandleStock.items()):
            self.SellStock(key,value.Amount)
    def BuyAllStock(self,data:DataFrame):
        '''買入所有股票'''
        while len(data) > 0:
            for index,row in data.iterrows():
                if self.BuyStock(index,1000) == False:
                    data = data.drop(index=index)

class StockInfoDatasInBackTestPriceByToday(TStockInfoDatasInBackTest):
    '''回測資訊(當天價格)'''
    def __init__(self, _baseInfoData: BaseInfoData) -> None:
        super().__init__(_baseInfoData)
        self._TempResultDraw:DataFrame = DataFrame(columns=['date','資產比例'])
        self._TempResultAll:DataFrame = DataFrame(columns=['date','股票資產','剩餘現金','總資產'])
        self._TempTradeInfo:DataFrame = DataFrame(columns=['date','號碼','數量','均價'])        
    def SellStock(self,number:str,amount:int) -> bool:
        '''賣某張股票'''
        if self._HandleStock.__contains__(number) == False:
            print('手上無'+ number +'股票')
            return False    
        elif self._HandleStock[number].Amount < amount:
            print('股票'+ number +'數量不足:' + amount)
            return False
        else:
            stock_price = get_stock_price(number,self._BaseInfoData.now_day,stock_data_kind.AdjClose)
            self._BaseInfoData.now_money = self._BaseInfoData.now_money + tools.Total_with_Handling_fee_and_Tax(stock_price,amount,False)
            if self._HandleStock[number].MinusAmount(amount) == False:
                self._HandleStock.pop(number,None)
            return True
    def BuyStock(self,number:str,amount:int) -> bool:
        '''買股票'''
        stock_price = get_stock_price(number,self._BaseInfoData.now_day,stock_data_kind.AdjClose)
        if stock_price == None:
            print(str(number) + ' no use stock')
            return False
        elif tools.Total_with_Handling_fee_and_Tax(stock_price,amount) > self._BaseInfoData.now_money:
            print('錢不夠：')
            return False
        else:
            m_stock = ts.codes[str(number)]
            m_info = StockInfoData(m_stock.code,m_stock.name,m_stock.type,m_stock.start,m_stock.market,m_stock.group)
            if self._HandleStock.__contains__(number) == False:
                self._HandleStock[number] = StockInfoDataInHandWithWeightedAverage(StockInfoCurrentData(m_info,amount,stock_price))
            else:
                self._HandleStock[number].AddAmount(amount,stock_price)
            self._BaseInfoData.now_money = self._BaseInfoData.now_money - tools.Total_with_Handling_fee_and_Tax(stock_price,amount)
            return True
    def RunFinish(self):
        '''完成結果'''
        self._TempResultAll['date'] = pd.to_datetime(self._TempResultAll['date'])
        self._TempResultDraw['date'] = pd.to_datetime(self._TempResultDraw['date'])
        self._TempTradeInfo['date'] = pd.to_datetime(self._TempTradeInfo['date'])
        if self._TempResultAll.index.name != 'date':
            self._TempResultAll = self._TempResultAll.set_index('date')
            self._TempResultDraw = self._TempResultDraw.set_index('date')
            self._TempTradeInfo = self._TempTradeInfo.set_index('date')
    def AddOneDay(self):
        '''過一天'''
        if self._BaseInfoData.now_day >= self._BaseInfoData.end_day:
            if self._TempResultAll.index.name != 'date':
                self._TempResultAll = self._TempResultAll.set_index('date')
                self._TempResultDraw = self._TempResultDraw.set_index('date')
                self._TempTradeInfo = self._TempTradeInfo.set_index('date')
            return False
        else:
            self._BaseInfoData.now_day = self._BaseInfoData.now_day + timedelta(days=1)#加一天
            return True
    def RecordUserInfo(self):
        '''紀錄回測資產紀錄'''
        self._TempResultDraw = pd.concat([self._TempResultDraw, DataFrame({'date':[self._BaseInfoData.now_day],
                                                                '資產比例':[self._GetUserAllAsset()/self._BaseInfoData.start_money]})], 
                                                                ignore_index = True)
        self._TempResultAll = pd.concat([self._TempResultAll,DataFrame({'date':[self._BaseInfoData.now_day],
                                                            '股票資產':[self._GetUserStockAsset()],
                                                            '剩餘現金':[self._BaseInfoData.now_money],
                                                            '總資產':[self._GetUserAllAsset()]})],
                                                            ignore_index=True)    
    def RecodTradeInfo(self):
        '''紀錄交易紀錄'''
        temp_numbers = ''
        temp_amount = ''
        temp_price = ''
        for key,value in self._HandleStock.items():
            temp_amount = temp_amount + str(value.Amount) + '/' 
            temp_price = temp_price + str(value.Price)+ '/' 
            temp_numbers = temp_numbers + str(key)+ '/' 
        self._TempTradeInfo = pd.concat([self._TempTradeInfo,DataFrame({'date':[self._BaseInfoData.now_day],
                                                                        '號碼':[temp_numbers],
                                                                        '數量':[temp_amount],
                                                                        '均價':[temp_price]})],
                                                                        ignore_index=True)
        
    