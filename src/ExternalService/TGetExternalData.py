import os
import sys
import time
from datetime import datetime
from io import StringIO

import numpy as np
import pandas as pd
import requests

from src.Common import InfomationType as info
from src.ExternalService.IGetExternalData import IGetExternalData
from src.MongoService import MongoService
from src.ReadLoadSystem import ReadLoadSystem
from src.SqlService import SqlService
import src.StockInfos as StockInfos
from src.Common import Tools

class TGetExternalData(IGetExternalData):
    """讀取外部資料"""

    def __init__(self,
        sql_service: SqlService,
        mongo_service: MongoService,
        read_load_system: ReadLoadSystem,
        cache_service=None) -> None:
        self._read_load_system = read_load_system
        self._sql_service = sql_service
        self._mongo_service = mongo_service
        self._cache_service = cache_service
        self.fileName_monthRP: str = "monthRP"
        self.fileName_stockInfo = "stockInfo"
        self.fileName_yield = "yieldInfo"
        self.fileName_season = "seasonInfo"
        self.fileName_index = "indexInfo"
        self.filePath = os.getcwd()  # 取得目錄路徑

    def get_allstock_financial_statement(self, start: datetime, type: info.FS_type):
        """#爬某季所有股票歷史財報"""
        print(
            "".join(["{}:取得".format(sys._getframe().f_code.co_name)]),
            str(type),
            "的季財報的資料:",
            str(start),
        )
        if not Tools.Have_DayRP(start):
            return pd.DataFrame()
        season = int(((start.month - 1) / 3) + 1)
        Temp_data = pd.DataFrame()
        if not Tools.CheckFS_season(start):
            print("Season rp is no data yet!")
            return pd.DataFrame()
        file = str(start.year) + "-season" + str(season) + "-" + type.value
        fileName = self.filePath + "/" + self.fileName_season + "/" + file
        Temp_data = self._read_load_system.load_month_file(fileName, file)  # 去資料庫抓資料

        if Temp_data.empty:
            if os.path.isfile(fileName + ".csv"):
                print("已經有" + str(start.month) + "月財務報告")
            self._financial_statement(start.year, season, type)
            print("下載" + str(start.month) + "月財務報告ＯＫ")

            stock = pd.read_csv(fileName + ".csv")
            # 整理一下資料
            stock.rename(columns={"公司代號": "code"}, inplace=True)
            stock.set_index("code", inplace=True)
            if info.FS_type.SCF == type:
                if stock["投資活動之淨現金流入（流出）"].dtype == object:
                    stock["投資活動之淨現金流入（流出）"] = pd.to_numeric(
                        stock["投資活動之淨現金流入（流出）"].str.replace("--", "0")
                    )
                if stock["營業活動之淨現金流入（流出）"].dtype == object:
                    stock["營業活動之淨現金流入（流出）"] = pd.to_numeric(
                        stock["營業活動之淨現金流入（流出）"].str.replace("--", "0")
                    )
                if stock["籌資活動之淨現金流入（流出）"].dtype == object:
                    stock["籌資活動之淨現金流入（流出）"] = pd.to_numeric(
                        stock["籌資活動之淨現金流入（流出）"].str.replace("--", "0")
                    )
            self._sql_service.saveTable(file, stock)
        else:
            stock = Temp_data
        self._read_load_system.Memery[fileName] = stock
        return stock

    def get_allstock_monthly_report(self, start: datetime):
        """爬某月所有股票月營收"""
        print(
            "".join(["{}:取得".format(sys._getframe().f_code.co_name)]),
            "月營收的資料:",
            str(start),
        )
        if not Tools.Have_MonthRP(start):
            return pd.DataFrame()
        m_data = pd.DataFrame()
        year = start.year
        file = "monthly_report_" + str(start.year) + "_" + str(start.month)
        fileName = self.filePath + "/" + self.fileName_monthRP + "/" + file
        m_data = self._read_load_system.load_month_file(fileName, file)  # 去資料庫抓資料

        if m_data.empty:
            if not os.path.isfile(fileName + ".csv"):
                # 假如是西元，轉成民國
                if year > 1990:
                    year -= 1911
                url = (
                    "https://mopsov.twse.com.tw/nas/t21/sii/t21sc03_"
                    + str(year)
                    + "_"
                    + str(start.month)
                    + "_0.html"
                )
                if year <= 98:
                    url = (
                        "https://mopsov.twse.com.tw/nas/t21/sii/t21sc03_"
                        + str(year)
                        + "_"
                        + str(start.month)
                        + ".html"
                    )

                # 下載該年月的網站，並用pandas轉換成 dataframe
                r = requests.get(url, headers=Tools.get_random_Header())
                r.encoding = "big5-hkscs"

                try:
                    dfs = pd.read_html(StringIO(r.text), encoding="big-5")
                except pd.errors.ParserError:
                    return pd.DataFrame()

                df = pd.concat(
                    [df for df in dfs if df.shape[1] <= 11 and df.shape[1] > 5]
                )

                if "levels" in dir(df.columns):
                    df.columns = df.columns.get_level_values(1)
                    df = df.rename(columns={"公司 代號": "公司代號"})
                else:
                    df = df[list(range(0, 10))]
                    column_index = df.index[(df[0] == "公司代號")][0]
                    df.columns = df.iloc[column_index]

                df["當月營收"] = pd.to_numeric(df["當月營收"], "coerce")
                df = df[~df["當月營收"].isnull()]
                df = df[df["公司代號"] != "合計"]

                df.to_csv(fileName + ".csv", index=False)
                # 偽停頓
                time.sleep(1.5)

            m_data = pd.read_csv(fileName + ".csv")
            m_data.drop(m_data.tail(1).index, inplace=True)
            # 整理一下資料
            m_data.rename(columns={"公司代號": "code"}, inplace=True)
            m_data[[ "code"]] = m_data[[ "code"]].astype(int)
            m_data.set_index("code", inplace=True)
            # 存到資料庫
            self._sql_service.saveTable(file, m_data)
        self._read_load_system.Memery[fileName] = m_data
        return m_data

    def get_allstock_yield(self, start: datetime):
        """#爬某天所有股票殖利率"""
        print(
            "".join(["{}:取得".format(sys._getframe().f_code.co_name)]),
            "殖利率的資料:",
            str(start),
        )
        file = (
            "dividend_yield_"
            + str(start.year)
            + "_"
            + str(start.month)
            + "_"
            + str(start.day)
        )
        fileName = self.filePath + "/" + self.fileName_yield + "/" + file
        m_yield = pd.DataFrame()
        # 去資料庫抓資料
        m_yield = self._read_load_system.load_month_file(fileName, file)

        try:
            if m_yield.empty and (
                self.get_stock_history("2330", start)[ "Volume"][ 
                    Tools.DateTime2String(start)
                ]
                > 0
            ):
                if not os.path.isfile(fileName + ".csv"):
                    url = (
                        "https://www.twse.com.tw/exchangeReport/BWIBBU_d?response=csv&date="
                        + str(start.year)
                        + str(start.month).zfill(2)
                        + str(start.day).zfill(2)
                        + "&selectType=ALL"
                    )
                    response = requests.get(url, Tools.get_random_Header())
                    self._read_load_system.save_stock_file(fileName, response, 1, 2)
                    # 偽停頓
                    time.sleep(3)
                try:
                    m_yield = pd.read_csv(fileName + ".csv", encoding="ANSI")
                except pd.errors.EmptyDataError:
                    print("no " + fileName + " csv file ")
                except pd.errors.ParserError:
                    print("get Parser error " + fileName + " csv file")
                except UnicodeDecodeError:
                    print("get UnicodeDecode error " + fileName + " csv file")
                # 整理一下資料
                m_yield.rename(columns={"證券代號": "code"}, inplace=True)
                m_yield.set_index("code", inplace=True)
                # 存到資料庫
                self._sql_service.saveTable(file, m_yield)
        except Exception:
            return pd.DataFrame()
        self._read_load_system.Memery[fileName] = m_yield
        return m_yield

    def get_stock_history(
        self,
        number: str,
        start=datetime.strptime("2005-1-1", "%Y-%m-%d"),
    ) -> pd.DataFrame:
        """#爬某個股票的歷史紀錄，加入快取統計"""
        print(
            "".join(
                [
                    "取得",
                    str(number),
                    "的資料從",
                    str(start),
                    "到今天:{}".format(sys._getframe().f_code.co_name),
                ]
            )
        )

        # 記錄查詢統計
        if self._cache_service:
            self._cache_service.record_query(number)

        # 確保 start_time 是 datetime 類型
        if isinstance(start, str):
            start_time = datetime.strptime(start, "%Y-%m-%d")
        elif isinstance(start, datetime):
            start_time = start
        else:
            start_time = datetime.strptime("2005-1-1", "%Y-%m-%d")

        if type(number) is not str:
            number = str(number)
        data_time = datetime.strptime("2005-1-1", "%Y-%m-%d")
        result = pd.DataFrame()
        if self._sql_service.CantUseStocks.__contains__(str(number) + ".TW"):
            print("ItsCantUseStock:" + str(number))
            return result
        if not StockInfos.ts.codes.__contains__(number):
            print("無此檔股票")
            return result
        if start_time < data_time:
            print("日期請大於西元2005年")
            return result

        file = str(number)
        filename = self.filePath + "/" + self.fileName_stockInfo + "/" + file
        stock_id = str(number)
        if ".TW" not in stock_id:
            stock_id += ".TW"

        # 使用新的混合快取服務 (Redis L1 + MongoDB L2)
        if self._cache_service:
            print(f"Using hybrid cache service for {stock_id}")
            m_history = self._cache_service.get_stock_data(stock_id)

            if m_history is not None and not m_history.empty:
                print(f"Data for {stock_id} loaded from hybrid cache.")
                # 同步到 Memory 快取以保持向後相容
                self._read_load_system.Memery[filename] = m_history
            else:
                print(f"Data for {stock_id} not in hybrid cache, trying other sources.")
                # 如果快取中沒有，則從其他來源獲取
                m_history = self._get_data_from_sources(stock_id, filename)

                # 將新獲取的資料存到混合快取中
                if m_history is not None and not m_history.empty:
                    self._cache_service.set_stock_data(stock_id, m_history)
        else:
            # 回退到原有的快取邏輯 (如果快取服務不可用)
            print(f"Hybrid cache service not available, using legacy cache for {stock_id}")
            m_history = self._get_data_from_sources(stock_id, filename)

        if m_history.empty:
            print(f"Could not retrieve data for {stock_id} from any source.")
            return pd.DataFrame()

        # 確保索引是 DatetimeIndex 並進行日期比較
        if not isinstance(m_history.index, pd.DatetimeIndex):
            m_history.index = pd.to_datetime(m_history.index)

        # 進行日期比較
        mask = m_history.index >= start_time
        result = m_history[mask]
        # 填充 Adj Close 的 NaN 值為 0
        if 'Adj Close' in result.columns:
            result['Adj Close'] = result['Adj Close'].fillna(0)
        result = result.dropna(axis=0, how="any")

        # 在成功獲取資料後，檢查是否需要更新快取
        if not result.empty and self._cache_service:
            # 非同步更新快取（避免阻塞主要讀取流程）
            import threading
            threading.Thread(
                target=self._cache_service.update_mongo_cache,
                daemon=True
            ).start()

        return result

    def _get_data_from_sources(self, stock_id: str, filename: str) -> pd.DataFrame:
        """從各種來源獲取資料的原有邏輯"""
        m_history = pd.DataFrame()

        # 1. Memory
        if filename in self._read_load_system.Memery:
            m_history = self._read_load_system.Memery[filename]

        if not m_history.empty:
            print(f"Data for {stock_id} loaded from Memory.")
            return m_history

        # 2. MongoDB (直接從集合讀取)
        print(f"Data for {stock_id} not in Memory, trying MongoDB.")
        try:
            collection = self._mongo_service.mongodb[stock_id.lower()]
            cursor = collection.find()
            m_history = pd.DataFrame(list(cursor))
            if not m_history.empty:
                print(f"Data for {stock_id} loaded from MongoDB, caching to Memory.")
                if '_id' in m_history.columns:
                    m_history = m_history.drop('_id', axis=1)
                if 'Date' in m_history.columns:
                    m_history['Date'] = pd.to_datetime(m_history['Date'])
                    m_history = m_history.set_index('Date')
                elif 'index' in m_history.columns:
                    m_history['Date'] = pd.to_datetime(m_history['index'])
                    m_history = m_history.set_index('Date').drop('index', axis=1)
                self._read_load_system.Memery[filename] = m_history
                return m_history
        except Exception as e:
            print(f"Could not read from MongoDB. Error: {e}")

        # 3. MySQL
        print(f"Data for {stock_id} not in MongoDB, trying MySQL.")
        m_history = self._sql_service.readStockDay(stock_id)
        if not m_history.empty:
            print(f"Data for {stock_id} loaded from MySQL, caching to Mongo and Memory.")
            self._mongo_service.saveTable(stock_id, m_history)
            self._read_load_system.Memery[filename] = m_history
            return m_history

        # 4. Local File
        print(f"Data for {stock_id} not in MySQL, trying Local File.")
        try:
            m_history = pd.read_csv(filename + ".csv", index_col="Date", parse_dates=["Date"])
            if not m_history.empty:
                print(f"Data for {stock_id} loaded from Local File, caching to MySQL, Mongo, and Memory.")
                self._sql_service.saveTable(stock_id, m_history)
                self._mongo_service.saveTable(stock_id, m_history)
                self._read_load_system.Memery[filename] = m_history
                return m_history
        except Exception:
            pass

        # 5. Yahoo Finance
        print(f"Data for {stock_id} not in any cache, fetching from Yahoo Finance.")
        self._sql_service.yfInfo(stock_id)
        time.sleep(1.5)
        m_history = self._sql_service.readStockDay(stock_id)

        if not m_history.empty:
            print(f"Data for {stock_id} loaded from Yahoo->MySQL, caching to other systems.")
            self._mongo_service.saveTable(stock_id, m_history)
            self._read_load_system.Memery[filename] = m_history

        return m_history

    def get_stock_AD_index(self, date: datetime, getNew=False):
        """#取得上漲和下跌家數"""
        print("get_stock_AD_index")
        if isinstance(date, str):
            date = datetime.strptime(date, "%Y-%m-%d")

        time = date
        while time not in self.get_stock_history("2330").index:
            time = Tools.backWorkDays(time, 1)

        # --- Start of optimization ---
        # 1. Try to read from MySQL database first (AD_index is still a separate table)
        try:
            ad_index_from_sql = self._sql_service.readDividendYield('ad_index')  # AD_index 使用不同的讀取方法
            if not ad_index_from_sql.empty and time in ad_index_from_sql.index:
                print(f"Found AD_index for {time.strftime('%Y-%m-%d')} in MySQL.")
                return ad_index_from_sql.loc[[time]]
        except Exception as e:
            print(f"Could not read AD_index from MySQL, falling back. Error: {e}")
        # --- End of optimization ---

        # 2. Fallback to original logic (cache/CSV)
        str_date = Tools.DateTime2String(time)
        fileName = self.filePath + "/" + self.fileName_index + "/" + "AD_index"
        ADindex_result = self._read_load_system.load_other_file(fileName, "AD_index")

        if ADindex_result.empty and os.path.isfile(fileName + ".csv"):
            ADindex_result = pd.read_csv(
                fileName + ".csv", index_col="Date", parse_dates=["Date"]
            )
            self._read_load_system.Memery[fileName] = ADindex_result

        if not ADindex_result.empty and time in ADindex_result.index:
            print(f"Found AD_index for {time.strftime('%Y-%m-%d')} in local cache.")
            return ADindex_result.loc[[time]]

        # 3. If not in DB or cache, calculate it
        print(f"No data for {time.strftime('%Y-%m-%d')} in DB or cache. Calculating...")
        time_yesterday = Tools.backWorkDays(time, 1)
        while (
            time_yesterday not in self.get_stock_history("2330", time_yesterday).index
        ):
            time_yesterday = Tools.backWorkDays(time_yesterday, 1)
        str_yesterday = Tools.DateTime2String(time_yesterday)

        up = 0
        down = 0
        for key, value in StockInfos.ts.codes.items():
            if value.market == "上市" and len(value.code) == 4 and value.type == "股票":
                if Tools.check_no_use_stock(value.code):
                    continue
                try:
                    m_history = self.get_stock_history(value.code, str_yesterday)
                    price_Close = round(m_history[ "Close"].get(str_date), 2)
                    price_Open = round(m_history[ "Open"].get(str_yesterday), 2)

                    if price_Close is not None and price_Open is not None:
                        if price_Open < price_Close:
                            up += 1
                        elif price_Open > price_Close:
                            down += 1
                except Exception:
                    # print(f"Could not process stock {value.code}")
                    continue

        print(f"Calculation result for {time.strftime('%Y-%m-%d')}: Up={up}, Down={down}")

        ADindex_result_new = pd.DataFrame(
            {"Date": [time], "上漲": [up], "下跌": [down]}
        ).set_index("Date")

        # Combine with existing data and save
        if not ADindex_result.empty:
            ADindex_result = pd.concat([ADindex_result, ADindex_result_new])
        else:
            ADindex_result = ADindex_result_new

        ADindex_result = ADindex_result[~ADindex_result.index.duplicated(keep='last')]
        ADindex_result = ADindex_result.sort_index()

        self._sql_service.saveTable("AD_index", ADindex_result)
        self._read_load_system.Memery[fileName] = ADindex_result

        return ADindex_result.loc[[time]]

    def get_full_ad_index(self) -> pd.DataFrame:
        """#取得完整的上漲和下跌家數歷史資料"""
        print("get_full_ad_index from MySQL")
        try:
            ad_index_table = self._sql_service.readStockDay('AD_index')
            if not ad_index_table.empty:
                return ad_index_table.sort_index()
        except Exception as e:
            print(f"Could not read AD_index from MySQL. Error: {e}")
        return pd.DataFrame()

    def _remove_td(self, column):
        remove_one = column.split("<")
        remove_two = remove_one[0].split(">")
        return remove_two[1].replace(",", "")

    def _translate_dataFrame(self, response):
        table_array = response.split("<table")
        tr_array = table_array[1].split("<tr")

        data = []
        index = []
        column = []
        for i in range(len(tr_array)):
            td_array = tr_array[i].split("<td")
            if len(td_array) > 1:
                code = self._remove_td(td_array[1])
                name = self._remove_td(td_array[2])
                revenue = self._remove_td(td_array[3])
                profitRatio = self._remove_td(td_array[4])
                profitMargin = self._remove_td(td_array[5])
                preTaxIncomeMargin = self._remove_td(td_array[6])
                afterTaxIncomeMargin = self._remove_td(td_array[7])
                if revenue == "&nbsp;":
                    continue
                if revenue == "":
                    continue
                if i > 1:
                    if name == "公司名稱":
                        continue
                    data.append(
                        [
                            name,
                            code,
                            revenue,
                            profitRatio,
                            profitMargin,
                            preTaxIncomeMargin,
                            afterTaxIncomeMargin,
                        ]
                    )
                    # index.append(name)
                if i == 1:
                    column.append("公司名稱")
                    column.append(code)
                    column.append(revenue)
                    column.append(profitRatio)
                    column.append(profitMargin)
                    column.append(preTaxIncomeMargin)
                    column.append(afterTaxIncomeMargin)
        return pd.DataFrame(data=data, columns=column)

    def _translate_dataFrame2(self, response, type, year, season=1):
        table_array = response.split("<table")
        tr_array_array = [
            table_array[2].split("<tr"),
            table_array[3].split("<tr"),
            table_array[4].split("<tr"),
            table_array[5].split("<tr"),
            table_array[6].split("<tr"),
            table_array[7].split("<tr"),
        ]
        column_pos_array = np.array(
            [
                [24, 42, 43, 52, 56],
                [5, 8, 9, 18, 22],
                [5, 8, 9, 18, 22],
                [25, 44, 45, 53, 57],
                [16, 34, 35, 44, 48],
                [5, 8, 9, 17, 21],
            ]
        )
        if year <= 114:
            column_pos_array = np.array(
                [
                    [24, 42, 43, 53, 57],
                    [5, 8, 9, 19, 23],
                    [5, 8, 9, 19, 23],
                    [25, 44, 45, 53, 57],
                    [16, 34, 35, 45, 49],
                    [5, 8, 9, 18, 22],
                ]
            )
        if year == 109:
            if season == 1:
                column_pos_array = np.array(
                    [
                        [24, 42, 43, 52, 56],
                        [5, 8, 9, 18, 22],
                        [5, 8, 9, 18, 22],
                        [25, 44, 45, 53, 57],
                        [16, 34, 35, 44, 48],
                        [5, 8, 9, 17, 21],
                    ]
                )
            else:
                column_pos_array = np.array(
                    [
                        [24, 42, 43, 53, 57],
                        [5, 8, 9, 19, 23],
                        [5, 8, 9, 19, 23],
                        [25, 44, 45, 53, 57],
                        [16, 34, 35, 45, 49],
                        [5, 8, 9, 18, 22],
                    ]
                )
        if year == 108:
            column_pos_array = np.array(
                [
                    [24, 42, 43, 52, 56],
                    [5, 8, 9, 18, 22],
                    [5, 8, 9, 18, 22],
                    [25, 44, 45, 53, 57],
                    [16, 34, 35, 44, 48],
                    [5, 8, 9, 17, 21],
                ]
            )
        if year == 107:
            column_pos_array = np.array(
                [
                    [25, 42, 43, 52, 56],
                    [5, 8, 9, 18, 22],
                    [5, 8, 9, 18, 22],
                    [26, 44, 45, 53, 57],
                    [14, 32, 33, 42, 46],
                    [5, 8, 9, 17, 21],
                ]
            )
        if year == 106:
            column_pos_array = np.array(
                [
                    [23, 40, 41, 50, 54],
                    [5, 8, 9, 17, 21],
                    [5, 8, 9, 18, 22],
                    [23, 41, 42, 50, 54],
                    [14, 32, 33, 42, 46],
                    [5, 8, 9, 17, 21],
                ]
            )
        if year < 106:
            column_pos_array = np.array(
                [
                    [22, 39, 40, 49, 53],
                    [5, 8, 9, 17, 21],
                    [5, 8, 9, 18, 22],
                    [23, 41, 42, 50, 54],
                    [14, 32, 33, 42, 46],
                    [5, 8, 9, 17, 21],
                ]
            )
        if year < 103:
            column_pos_array = np.array(
                [
                    [22, 39, 40, 49, 52],
                    [5, 8, 9, 17, 20],
                    [5, 8, 9, 18, 21],
                    [23, 41, 42, 50, 53],
                    [14, 32, 33, 42, 45],
                    [5, 8, 9, 17, 20],
                ]
            )
        # if (year < 105):
        #     column_pos_array = np.array([[23,40,41,50,54],
        #                             [5,8,9,17,21],
        #                             [5,8,9,18,22],
        #                             [23,41,42,50,54],
        #                             [14,32,33,42,46],
        #                             [5,8,9,17,21]
        #                             ])
        if type == info.FS_type.CPL:
            if year < 108:
                column_pos_array = np.array(
                    [[14, 21], [15, 22], [23, 30], [15, 22], [16, 23], [11, 18]]
                )
            if year < 106:
                column_pos_array = np.array(
                    [[14, 21], [15, 22], [21, 28], [15, 22], [16, 23], [11, 18]]
                )
            if year < 104:
                column_pos_array = np.array(
                    [[15, 22], [15, 22], [21, 28], [15, 22], [16, 23], [11, 18]]
                )
            if year == 108:
                column_pos_array = np.array(
                    [[15, 22], [15, 22], [23, 30], [15, 22], [16, 23], [11, 18]]
                )
            elif year > 108:
                column_pos_array = np.array(
                    [[15, 22], [15, 22], [23, 30], [15, 22], [16, 23], [11, 18]]
                )
        if type == info.FS_type.SCF:
            column_pos_array = np.array(
                [[3, 4, 5], [3, 4, 5], [3, 4, 5], [3, 4, 5], [3, 4, 5], [3, 4, 5]]
            )
        data = []
        index = []
        column = []

        for k in range(len(tr_array_array)):
            tr_array = tr_array_array[k]
            for i in range(len(tr_array)):
                if i == 1:
                    td_array = tr_array[i].split("<th")
                else:
                    td_array = tr_array[i].split("<td")

                if len(td_array) > 1:
                    code = self._remove_td(td_array[1])
                    name = self._remove_td(td_array[2])
                    revenue = self._remove_td(td_array[column_pos_array[k][0]])
                    profitRatio = self._remove_td(td_array[column_pos_array[k][1]])
                    if type == info.FS_type.BS:
                        profitMargin = self._remove_td(td_array[column_pos_array[k][2]])
                        preTaxIncomeMargin = self._remove_td(
                            td_array[column_pos_array[k][3]]
                        )
                        afterTaxIncomeMargin = self._remove_td(
                            td_array[column_pos_array[k][4]]
                        )
                    if type == info.FS_type.SCF:
                        profitMargin2 = self._remove_td(
                            td_array[column_pos_array[k][2]]
                        )
                    if i > 1:
                        if name == "公司名稱":
                            continue
                        if type == info.FS_type.CPL:
                            data.append([name, code, revenue, profitRatio])
                        elif type == info.FS_type.SCF:
                            data.append(
                                [name, code, revenue, profitRatio, profitMargin2]
                            )
                        else:
                            data.append(
                                [
                                    name,
                                    code,
                                    revenue,
                                    profitRatio,
                                    profitMargin,
                                    preTaxIncomeMargin,
                                    afterTaxIncomeMargin,
                                ]
                            )
                        # index.append(name)
                    if i == 1 and k == 0:
                        column.append("公司名稱")
                        column.append("公司代號")
                        column.append(revenue)
                        column.append(profitRatio)
                        if type == info.FS_type.BS:
                            column.append(profitMargin)
                            column.append(preTaxIncomeMargin)
                            column.append(afterTaxIncomeMargin)
                        if type == info.FS_type.SCF:
                            column.append(profitMargin2)

        return pd.DataFrame(data=data, columns=column)

    def _financial_statement(
        self,
        year: int,
        season: int,
        type: info.FS_type,
    ):  # year = 年 season = 季 type = 財報種類
        myear = year
        if year >= 1000:
            myear -= 1911

        if type == info.FS_type.CPL:
            url = "https://mopsov.twse.com.tw/mops/web/ajax_t163sb04"
        elif type == info.FS_type.BS:
            url = "https://mopsov.twse.com.tw/mops/web/ajax_t163sb05"
        elif type == info.FS_type.PLA:
            url = "https://mopsov.twse.com.tw/mops/web/ajax_t163sb06"
        elif type == info.FS_type.SCF:
            url = "https://mopsov.twse.com.tw/mops/web/ajax_t163sb20"
        else:
            print("type does not match")

        # url = 'http://mops.twse.com.tw/mops/web/ajax_t163sb06'
        form_data = {
            "encodeURIComponent": 1,
            "step": 1,
            "firstin": 1,
            "off": 1,
            "TYPEK": "sii",
            "year": myear,
            "season": season,
        }
        response = requests.post(url, form_data, headers=Tools.get_random_Header())
        # response.encoding = 'utf8'

        if type == info.FS_type.PLA:
            df = self._translate_dataFrame(response.text)
        else:
            df = self._translate_dataFrame2(response.text, type, myear, season)
        file = str(year) + "-season" + str(season) + "-" + type.value
        df.to_csv(
            self.filePath + "/" + self.fileName_season + "/" + file + ".csv",
            index=False,
        )
        # 偽停頓
        time.sleep(5)
