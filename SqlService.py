from datetime import datetime
import threading
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from pandas_datareader import data
import yfinance as yf
import Tools


class SqlService:
    def __init__(self) -> None:
        self.server_flask: Flask = Flask(__name__)  # 初始化server
        self.MySql_server: SQLAlchemy = None

    def RunMysql(self):
        temp_thread = threading.Thread(target=self.__SetMysqlServer, args=["demo"])
        temp_thread.start()

    def readStockDay(self, name: str):
        dataframe = pd.DataFrame()
        if not name.islower():
            name = name.lower()
        try:
            with self.server_flask.app_context():
                dataframe = pd.read_sql(
                    sql=name, con=self.MySql_server.engine, index_col="Date"
                )
                return dataframe
        except Exception as e:
            print("SQL Error {}".format(e.args))
            return dataframe

    def readDividendYield(self, name: str):
        dataframe = pd.DataFrame()
        if not name.islower():
            name = name.lower()
        try:
            with self.server_flask.app_context():
                dataframe = pd.read_sql(
                    sql=name, con=self.MySql_server.engine, index_col="code"
                )
                return dataframe
        except Exception as e:
            print("SQL Error {}".format(e.args))
            return dataframe

    def saveTable(self, _name: str, _df=pd.DataFrame()):
        if not _name.islower():
            _name = _name.lower()
        try:
            with self.server_flask.app_context():
                _df.to_sql(
                    name=_name, con=self.MySql_server.engine, if_exists="replace"
                )
                return True
        except Exception as e:
            print("SQL Error {}".format(e.args))
            return False

    def yfInfo(self, name: str):
        if not name.islower():
            name = name.lower()
        start_date = datetime(2005, 1, 1)
        end_date = datetime.today()  # 設定資料起訖日期
        df_result = yf.download([name], start_date, end_date)
        if df_result.empty:
            print("yahoo no data:" + str(name))
        else:
            df_result = Tools.TidyTicketData(df_result, name)
            with self.server_flask.app_context():
                df_result.to_sql(
                    name=name, con=self.MySql_server.engine, if_exists="replace"
                )
                print("Update stocks " + name + " OK!")

    def __SetMysqlServer(self, db_name: str):
        print("SetMysqlServer")
        # 設定mysql DB
        self.server_flask.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        # self.server_flask.config["SQLALCHEMY_DATABASE_URI"] = (
        #     "mysql+pymysql://"
        #     + "demo"
        #     + ":"
        #     + "demo123"
        #     + "@"
        #     + "122.116.102.141"
        #     + ":"
        #     + "3307"
        #     + "/"
        #     + str(db_name)
        # )
        self.server_flask.config["SQLALCHEMY_DATABASE_URI"] = (
            "mysql+pymysql://"
            + "demo"
            + ":"
            + "~Demo123"
            + "@"
            + "127.0.0.1"
            + ":"
            + "3307"
            + "/"
            + str(db_name)
        )
        # 連線mysql DB
        self.MySql_server = SQLAlchemy(self.server_flask)
