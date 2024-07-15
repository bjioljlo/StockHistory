import pymongo
from pymongo import MongoClient, database
import threading
import twstock #抓取台灣股票資料套件
import Tools
import pandas as pd

class MongoService:
    def __init__(self) -> None:
        self.mongoConnect:MongoClient = None
        self.mongodb:database = None
        
    def RunMongoDB(self):
        temp_thread = threading.Thread(target=self._SetMongoServer,args=["Demo"])
        temp_thread.start()
    
    def saveTable(self, _name:str, _df = pd.DataFrame()):
        dataframe = pd.DataFrame()
        if _name.islower() != True:
            _name = _name.lower()
        try:
            df = _df.copy()
            df.reset_index(inplace=True)
            _clo = self.mongodb[_name]
            _clo.drop()
            _clo.insert_many(df.to_dict('records'))
        except Exception as e:
            print('Mongo Error {}'.format(e.args))
            return dataframe
    
    def _SetMongoServer(self, db_name:str):
        print("SetMongoServer")
        _connectStr = "mongodb://localhost:27017/"
        self.mongoConnect = pymongo.MongoClient(_connectStr)
        self.mongodb = self.mongoConnect[db_name]
    
    def _readStockInfo(self):
        for key,value in twstock.codes.items():
            if value.market == "上市" and len(value.code) >= 4 :
                if len(value.code) >= 5 and Tools.check_ETF_stock(value.code) == False:
                    continue
                _saveData:dict = {}
                _saveData["type"] = value[0]
                _saveData["code"] = value[1]
                _saveData["name"] = value[2]
                _saveData["ISIN"] = value[3]
                _saveData["start"] = value[4]
                _saveData["market"] = value[5]
                _saveData["group"] = value[6]
                _saveData["CFI"] = value[7]
                
                _clo = self.mongodb["StockInfo"]
                _clo.insert_one(_saveData)
            