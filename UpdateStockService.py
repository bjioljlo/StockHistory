from datetime import datetime, timedelta
import threading
import pandas as pd
import twstock #抓取台灣股票資料套件
from pandas_datareader import data
import yfinance as yf
from sqlalchemy.ext.declarative import declarative_base
import os
import Tools
import InfomationType as info
from StockInfos import UserInfoDatas
from GetExternalData import TGetExternalData
import Globals

class UpdateStockService():
    def __init__(self) -> None:
        self.threads = []
        self.isUpdating:bool = False  
        
    def UpdateAllStocksHandle(self, MainUserInfoDatas: UserInfoDatas):
        temp_thread = threading.Thread(target=self.__runUpdate, args=[MainUserInfoDatas,])
        temp_thread.setDaemon(True)

        temp_thread.start()
        self.threads.append(temp_thread)
        
    def __runUpdate(self, MainUserInfoDatas: UserInfoDatas):
        print("Update all stocks start!")
        df = pd.DataFrame()
        end_date = datetime.today() - timedelta(days=1)#設定資料起訖日期
        # twstock.__update_codes()
        yf.pdr_override()
        for key,value in twstock.codes.items():
            if not self.isUpdating: 
                print("Update stocks "  + value.code + info.local_type.Taiwan + " be Stop")
                return
            if value.market == "上市" and len(value.code) >= 4 :
                if len(value.code) >= 5 and Tools.check_ETF_stock(value.code) == False:
                    continue            
                #SQL沒資料抓取一整包
                start_date = datetime(2005,1,1)
                end_date = datetime.today()#設定資料起訖日期
                df = data.get_data_yahoo([value.code + info.local_type.Taiwan], start_date, end_date)
                if df.empty:
                    print("yahoo no data:" + str(value.code + info.local_type.Taiwan))
                    continue
                with Globals.MYSQL.server_flask.app_context():
                    df.to_sql(name=value.code + info.local_type.Taiwan,con=Globals.MYSQL.MySql_server.engine,if_exists='replace')
                Globals.READLOAD.load_memery[os.getcwd() +'/' + 'stockInfo'  + '/' + value.code] = df
                print("Update stocks " + value.code + info.local_type.Taiwan + " OK!") 
        
        #存更新日期
        MainUserInfoDatas.UpdateDate = str(datetime.today())[0:10]
        self.__RunUpDate2()
        print("Update all stocks end!")    
        
    def __RunUpdate_sp500(self):
        print("Update all sp500 stocks start!")
        sp500 = Tools.get_SP500_list()
        yf.pdr_override()
        for temp in sp500:
            try:
                self.__deleteStockDayTable(temp)
            except:
                print("SQL No Table:" + str(temp))
                
            #SQL沒資料抓取一整包
            start_date = datetime(2005,1,1)
            end_date = datetime.today()#設定資料起訖日期
            df = data.get_data_yahoo([temp], start_date, end_date,index_col=0)
            if df.empty:
                print("yahoo no data:" + str(temp))
                continue
            with Globals.MYSQL.server_flask.app_context():
                df.to_sql(name=temp,con=Globals.MYSQL.MySql_server.engine)
            print("Update stocks " + temp + " OK!")
        print("Update all stocks end!")
        
    def __RunUpDate2(self):
        print("Update stocks other Info start!")
        end_date = datetime(datetime.today().year,datetime.today().month,datetime.today().day)#設定資料起訖日期
        TGetExternalData().get_stock_AD_index(end_date)#更新騰落
        print("Update stocks other Info end!")    
        
    def __deleteStockDayTable(self, name):
        DynamicBase = declarative_base(class_registry=dict())
        class StockDayInfo(DynamicBase,Globals.MYSQL.MySql_server.Model):
            __tablename__ = ""
            Date = Globals.MYSQL.MySql_server.Column(Globals.MYSQL.MySql_server.DateTime, primary_key=True)
            Open = Globals.MYSQL.MySql_server.Column(Globals.MYSQL.MySql_server.Float)
            High = Globals.MYSQL.MySql_server.Column(Globals.MYSQL.MySql_server.Float)
            Low = Globals.MYSQL.MySql_server.Column(Globals.MYSQL.MySql_server.Float)
            Close = Globals.MYSQL.MySql_server.Column(Globals.MYSQL.MySql_server.Float)
            AdjClose = Globals.MYSQL.MySql_server.Column(Globals.MYSQL.MySql_server.Float)
            Volume = Globals.MYSQL.MySql_server.Column(Globals.MYSQL.MySql_server.Integer)
            def __init__(self,name,Date,Open,High,Low,Close,AdjClose,Volume):
                self.__tablename__ = name
                self.Date = Date
                self.Open = Open
                self.High = High
                self.Low = Low
                self.Close = Close
                self.AdjClose = AdjClose
                self.Volume = Volume
        
        temp_table = StockDayInfo.__table__
        temp_table.name = name
        StockDayInfo.__table__ = temp_table
        StockDayInfo.__table__.drop(Globals.MYSQL.MySql_server.session.bind)      