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