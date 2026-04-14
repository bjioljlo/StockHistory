import threading

import pandas as pd
import pymongo
import twstock  # 抓取台灣股票資料套件
from pymongo import MongoClient, database

from src.Common import Tools


class MongoService:
    def __init__(self) -> None:
        self.mongoConnect: MongoClient = None
        self.mongodb: database = None

    def RunMongoDB(self, config):
        db_name = config['databasename']
        temp_thread = threading.Thread(target=self._SetMongoServer, args=[db_name, config])
        temp_thread.start()

    def saveTable(self, _name: str, _df=pd.DataFrame()):
        dataframe = pd.DataFrame()
        if not _name.islower():
            _name = _name.lower()
        try:
            df = _df.copy()

            # 處理日期索引：將 DatetimeIndex 重置並轉換為字符串格式
            if isinstance(df.index, pd.DatetimeIndex):
                df.reset_index(inplace=True)
                # reset_index() 會將 DatetimeIndex 轉換為 'index' 欄位
                # 重新命名為 'Date' 並格式化為字符串
                if 'index' in df.columns:
                    df.rename(columns={'index': 'Date'}, inplace=True)
                    df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
                elif 'Date' in df.columns:
                    df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
            else:
                df.reset_index(inplace=True)

            _clo = self.mongodb[_name]
            _clo.drop()
            _clo.insert_many(df.to_dict("records"))
        except Exception as e:
            print("Mongo Error {}".format(e.args))
            return dataframe

    def _SetMongoServer(self, db_name: str, config):
        print("SetMongoServer")
        _connectStr = f"mongodb://{config['host']}:{config['port']}/"
        self.mongoConnect = pymongo.MongoClient(_connectStr)
        self.mongodb = self.mongoConnect[db_name]

    def _readStockInfo(self):
        for key, value in twstock.codes.items():
            if value.market == "上市" and len(value.code) >= 4:
                if not len(value.code) >= 5 and Tools.is_etf_stock(value.code):
                    continue
                _saveData: dict = {}
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
