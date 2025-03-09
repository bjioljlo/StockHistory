import os
import threading
from datetime import datetime, timedelta

import twstock  # 抓取台灣股票資料套件
import yfinance as yf
from sqlalchemy.ext.declarative import declarative_base

import Globals
import InfomationType as info
import Tools
from GetExternalDataService import ExternalDataFactory, IGetExternalData
from StockInfos import UserInfoDatas


class UpdateStockService:
    def __init__(self) -> None:
        self.threads = []
        self.isUpdating: bool = False
        self._getExternalData: IGetExternalData = ExternalDataFactory.Get_instance()

    def UpdateAllStocksHandle(self, MainUserInfoDatas: UserInfoDatas):
        temp_thread = threading.Thread(
            target=self.__runUpdate,
            args=[
                MainUserInfoDatas,
            ],
        )
        temp_thread.setDaemon(True)
        temp_thread.start()
        self.threads.append(temp_thread)
        # temp_thread.join()
        # temp_thread_drawdown = threading.Thread(target=self.__RunUpDate2, args=["",])
        # temp_thread_drawdown.setDaemon(True)
        # temp_thread_drawdown.start()
        # self.threads.append(temp_thread_drawdown)

    def __runUpdate(self, MainUserInfoDatas: UserInfoDatas):
        print("Update all stocks start!")
        end_date = datetime.today() - timedelta(days=1)  # 設定資料起訖日期
        for key, value in twstock.codes.items():
            if not self.isUpdating:
                print(
                    "Update stocks " + value.code + info.local_type.Taiwan + " be Stop"
                )
                return
            if value.market == "上市" and len(value.code) >= 4:
                if len(value.code) >= 5 and Tools.check_ETF_stock(value.code) is False:
                    continue
                # SQL沒資料抓取一整包
                start_date = datetime(2005, 1, 1)
                end_date = datetime.today()  # 設定資料起訖日期
                df_result = yf.download(
                    [value.code + info.local_type.Taiwan],
                    start=start_date,
                    end=end_date,
                )

                if df_result.empty:
                    print("yahoo no data:" + str(value.code + info.local_type.Taiwan))
                    continue

                df_result = Tools.TidyTicketData(df_result, value.code + ".TW")

                with Globals.MYSQL.server_flask.app_context():
                    df_result.to_sql(
                        name=value.code + info.local_type.Taiwan,
                        con=Globals.MYSQL.MySql_server.engine,
                        if_exists="replace",
                    )
                Globals.READLOAD.load_memery[
                    os.getcwd() + "/" + "stockInfo" + "/" + value.code
                ] = df_result
                Globals.MONGO.saveTable(
                    str(value.code) + info.local_type.Taiwan, df_result
                )
                print("Update stocks " + value.code + info.local_type.Taiwan + " OK!")

        # 存更新日期
        MainUserInfoDatas.UpdateDate = str(datetime.today())[0:10]
        self.__RunUpDate2()
        print("Update all stocks end!")

    def __RunUpdate_sp500(self):
        # TODO : 可以加入每日更新行列
        print("Update all sp500 stocks start!")
        sp500 = Tools.get_SP500_list()
        for temp in sp500:
            try:
                self.__deleteStockDayTable(temp)
            except Exception:
                print("SQL No Table:" + str(temp) + " " + Exception)

            # SQL沒資料抓取一整包
            start_date = datetime(2005, 1, 1)
            end_date = datetime.today()  # 設定資料起訖日期
            df_result = yf.download([temp], start_date, end_date)

            if df_result.empty:
                print("yahoo no data:" + str(temp))
                continue

            df_result = self.__TidyTicketData(df_result, temp)
            with Globals.MYSQL.server_flask.app_context():
                df_result.to_sql(name=temp, con=Globals.MYSQL.MySql_server.engine)
            print("Update stocks " + temp + " OK!")
        print("Update all stocks end!")

    def __RunUpDate2(self):
        print("Update stocks other Info start!")
        end_date = datetime(
            datetime.today().year, datetime.today().month, datetime.today().day
        )  # 設定資料起訖日期
        self._getExternalData.get_stock_AD_index(end_date)  # 更新騰落
        print("Update stocks other Info end!")

    def __deleteStockDayTable(self, name):
        DynamicBase = declarative_base(class_registry=dict())

        class StockDayInfo(DynamicBase, Globals.MYSQL.MySql_server.Model):
            __tablename__ = ""
            Date = Globals.MYSQL.MySql_server.Column(
                Globals.MYSQL.MySql_server.DateTime, primary_key=True
            )
            Open = Globals.MYSQL.MySql_server.Column(Globals.MYSQL.MySql_server.Float)
            High = Globals.MYSQL.MySql_server.Column(Globals.MYSQL.MySql_server.Float)
            Low = Globals.MYSQL.MySql_server.Column(Globals.MYSQL.MySql_server.Float)
            Close = Globals.MYSQL.MySql_server.Column(Globals.MYSQL.MySql_server.Float)
            AdjClose = Globals.MYSQL.MySql_server.Column(
                Globals.MYSQL.MySql_server.Float
            )
            Volume = Globals.MYSQL.MySql_server.Column(
                Globals.MYSQL.MySql_server.Integer
            )

            def __init__(self, name, Date, Open, High, Low, Close, AdjClose, Volume):
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
