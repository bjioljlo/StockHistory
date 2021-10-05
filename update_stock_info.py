from datetime import datetime,timedelta
from functools import update_wrapper
import re
import threading
import schedule
import time
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import twstock as ts
from pandas_datareader import data
import yfinance as yf
from sqlalchemy.ext.declarative import declarative_base
import tools
import get_stock_history

MySql_server = None
threads = []

def RunSchedule(func,UpdateTime):
    print("RunSchedule at:" + UpdateTime)
    schedule.every().day.at(UpdateTime).do(func)
    if threads.__len__() == 0:
        temp_thread = threading.Thread(target=ScheduleStart)
        temp_thread.start()
        threads.append(temp_thread)
    

def ScheduleStart():
    t = threading.currentThread()
    while getattr(t, "do_run", True):
        schedule.run_pending()
        time.sleep(1)

def RunMysql():
    temp_thread = threading.Thread(target=setMysqlServer)
    temp_thread.start()

def RunScheduleNow():
    RunSchedule(runUpdate,str(datetime.today().hour).zfill(2)+ ":" + str(datetime.today().minute + 1).zfill(2)+ ":01")
    RunSchedule(RunUpdate_sp500,str(datetime.today().hour).zfill(2)+ ":" + str(datetime.today().minute + 1).zfill(2)+ ":05")

    

def setMysqlServer():
    global MySql_server
    server_flask = Flask(__name__)#初始化server
    #設定mysql DB
    server_flask.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    server_flask.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://" + "demo" + ":" + "demo123" + "@" + "122.116.102.141" + ":"+ "3307" +"/"+"demo"
    #連線mysql DB
    MySql_server = SQLAlchemy(server_flask)
    

def runUpdate():
    print("Update all stocks start!")
    df = pd.DataFrame()
    for key,value in ts.codes.items():
        if value.market == "上市" and len(value.code) >= 4 :
            if len(value.code) >= 5 and get_stock_history.check_ETF_stock(value.code) == False:
                continue
            try:
                deleteStockDayTable(str(value.code+".TW"))
            except:
                print("SQL No Table:" + str(value.code+".TW"))
            
            #SQL沒資料抓取一整包
            yf.pdr_override()
            start_date = datetime(2005,1,1)
            end_date = datetime.today()#設定資料起訖日期
            df = data.get_data_yahoo([value.code+".TW"], start_date, end_date,index_col=0)
            if df.empty:
                print("yahoo no data:" + str(value.code+".TW"))
                continue
            df.to_sql(name=value.code+".TW",con=MySql_server.engine)
            print("Update stocks " + value.code+".TW" + " OK!")
    
    #dataframe = pd.read_sql(sql = "2330.TW",con=MySql_server.engine,index_col='Date')
    #print(dataframe)
    print("Update all stocks end!")

def RunUpdate_sp500():
    print("Update all sp500 stocks start!")
    sp500 = tools.get_SP500_list()
    for temp in sp500:
        try:
            deleteStockDayTable(temp)
        except:
            print("SQL No Table:" + str(temp))
            
        #SQL沒資料抓取一整包
        yf.pdr_override()
        start_date = datetime(2005,1,1)
        end_date = datetime.today()#設定資料起訖日期
        df = data.get_data_yahoo([temp], start_date, end_date,index_col=0)
        if df.empty:
            print("yahoo no data:" + str(temp))
            continue
        df.to_sql(name=temp,con=MySql_server.engine)
        print("Update stocks " + temp + " OK!")
    print("Update all stocks end!")

def stopThreadSchedule():
    for thread in threads:
        thread.do_run = False
    print("thread all stop")

def readStockDay(name):
    dataframe = pd.DataFrame()
    try:
        dataframe = pd.read_sql(sql = name,con=MySql_server.engine,index_col='Date')
        return dataframe
    except Exception as e:
        print('SQL Error {}'.format(e.args))
        return dataframe

def deleteStockDayTable(name):
    DynamicBase = declarative_base(class_registry=dict())
    class StockDayInfo(DynamicBase,MySql_server.Model):
        __tablename__ = ""
        Date = MySql_server.Column(MySql_server.DateTime, primary_key=True)
        Open = MySql_server.Column(MySql_server.Float)
        High = MySql_server.Column(MySql_server.Float)
        Low = MySql_server.Column(MySql_server.Float)
        Close = MySql_server.Column(MySql_server.Float)
        AdjClose = MySql_server.Column(MySql_server.Float)
        Volume = MySql_server.Column(MySql_server.Integer)
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
    StockDayInfo.__table__.drop(MySql_server.session.bind)