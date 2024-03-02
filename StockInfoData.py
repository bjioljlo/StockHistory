from datetime import datetime

class StockInfoData():
    '''股票資訊結構'''
    def __init__(self,number:str,name:str,type:str,start:str,market:str,group:str):
        self.name:str = name
        self.number:int = int(number)
        self.type:str = type
        self.start:datetime = datetime.strptime(start,"%Y/%m/%d")
        self.market:str = market
        self.group:str = group

class StockInfoCurrentData():
    '''當下股票資訊結構'''
    def __init__(self,stock_info: StockInfoData,amount:int,price:float):
        self.stock_info:StockInfoData = stock_info
        self.amount:int = amount
        self.price:float = price

class BaseInfoData():
    '''基本資料結構''' 
    def __init__(self,start_money:int,start_day:datetime,end_day:datetime):
        self.start_money:int = start_money #起始現金
        self.now_money:int = start_money #剩餘現金
        self.start_day:datetime = start_day #開始日期
        self.now_day:datetime = start_day #現在日期
        self.end_day:datetime = end_day  #結束日期