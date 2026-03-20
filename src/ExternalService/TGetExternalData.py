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
from src.Common.CacheService import HybridCacheService


class TGetExternalData(IGetExternalData):
    """讀取外部資料"""

    def __init__(self,
        sql_service: SqlService,
        mongo_service: MongoService,
        read_load_system: ReadLoadSystem,
        cache_service: HybridCacheService) -> None:
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
        if not Tools.CheckFS_season(start):
            print("Season rp is no data yet!")
            return pd.DataFrame()

        # 建立緩存鍵
        cache_key = f"financial_statement_{start.year}_{season}_{type.value}"
        file = str(start.year) + "-season" + str(season) + "-" + type.value
        fileName = self.filePath + "/" + self.fileName_season + "/" + file

        # 使用新的混合緩存服務 (Redis L1 + MongoDB L2)
        if self._cache_service:
            print(f"使用混合緩存服務查詢財務報表: {cache_key}")

            # 1. 嘗試從 Redis L1 緩存獲取
            cached_data = self._cache_service.get_redis_cache(cache_key)
            if cached_data:
                try:
                    df = pd.DataFrame(
                        cached_data['data'],
                        columns=cached_data['columns']
                    )
                    if cached_data.get('index'):
                        df.index = cached_data['index']
                    print(f"L1 緩存命中財務報表: {cache_key}")
                    return df
                except Exception as e:
                    print(f"L1 緩存反序列化失敗: {e}")

            # 2. 嘗試從 MongoDB L2 智慧緩存獲取
            mongo_data = self._cache_service.get_mongo_cache(cache_key)
            if mongo_data is not None and not mongo_data.empty:
                # 同步到 Redis L1 緩存
                index_list = [str(idx) for idx in mongo_data.index] if not mongo_data.index.equals(range(len(mongo_data))) else None
                self._cache_service.set_redis_cache(cache_key, {
                    'data': mongo_data.values.tolist(),
                    'columns': mongo_data.columns.tolist(),
                    'index': index_list
                })
                print(f"L2 緩存命中財務報表: {cache_key}")
                return mongo_data

        # 3. 如果緩存中沒有，從原有邏輯獲取數據
        print(f"緩存未命中，從原有邏輯獲取財務報表: {cache_key}")
        Temp_data = pd.DataFrame()

        # 從資料庫或本地文件獲取數據
        Temp_data = self._read_load_system.load_month_file(fileName, file)

        if Temp_data.empty:
            if os.path.isfile(fileName + ".csv"):
                print("已經有" + str(start.month) + "月財務報告")
            self._financial_statement(start.year, season, type)
            print("下載" + str(start.month) + "月財務報告ＯＫ")

            stock = pd.read_csv(fileName + ".csv")
            # 整理一下資料
            stock.rename(columns={"公司代號": "symbol"}, inplace=True)
            stock.set_index("symbol", inplace=True)
            
            # 添加年季和報表類型欄位以符合 quarterly_reports 表結構
            stock['report_year'] = start.year
            stock['report_season'] = season
            stock['report_type'] = type.value
            
            # 根據不同的報表類型，重新命名欄位以匹配 quarterly_reports 表結構
            if type == info.FS_type.PLA:
                # PLA欄位 (損益分析表)
                column_mapping = {
                    '營業收入': 'revenue',
                    '毛利率(%)': 'gross_margin',
                    '營業利益率(%)': 'operating_margin',
                    '稅前純益率(%)': 'pre_tax_margin',
                    '稅後純益率(%)': 'net_margin'
                }
            elif type == info.FS_type.BS:
                # BS欄位 (資產負債表)
                column_mapping = {
                    '資產總額': 'total_assets',
                    '負債總額': 'total_liabilities',
                    '權益總額': 'equity',
                    '股本': 'capital',
                    '每股參考淨值': 'book_value_per_share'
                }
            elif type == info.FS_type.CPL:
                # CPL欄位 (合併損益表)
                column_mapping = {
                    '營業收入': 'revenue',
                    '毛利率(%)': 'gross_margin',
                    '營業利益率(%)': 'operating_margin',
                    '稅前純益率(%)': 'pre_tax_margin',
                    '稅後純益率(%)': 'net_margin'
                }
            elif type == info.FS_type.SCF:
                # SCF欄位 (現金流量表)
                column_mapping = {
                    '營業活動之淨現金流入（流出）': 'operating_cash_flow',
                    '投資活動之淨現金流入（流出）': 'investing_cash_flow',
                    '籌資活動之淨現金流入（流出）': 'financing_cash_flow'
                }
            
            # 應用欄位映射
            stock = stock.rename(columns=column_mapping)
            
            # 數據類型轉換
            numeric_columns = [col for col in stock.columns if col not in ['symbol', 'report_year', 'report_season', 'report_type']]
            for col in numeric_columns:
                if col in stock.columns:
                    stock[col] = pd.to_numeric(stock[col], errors='coerce').fillna(0)
            
            # 確保 symbol 欄位存在且為字串類型
            if 'symbol' not in stock.columns:
                stock['symbol'] = stock.index.astype(str)
            
            # 設定索引為 symbol，但保存時不包含索引
            stock.set_index("symbol", inplace=True)
            
            # 使用 upsert_data 方法保存到 quarterly_reports 表，避免重複數據
            try:
                success = self._sql_service.upsert_data('quarterly_reports', stock.reset_index(), 
                                                      ['symbol', 'report_year', 'report_season', 'report_type'])
                if success:
                    print(f"Successfully saved quarterly report data to quarterly_reports table for {start.year}-season{season}-{type.value}")
                else:
                    print(f"Failed to save quarterly report data to quarterly_reports table for {start.year}-season{season}-{type.value}")
            except Exception as e:
                print(f"Error saving quarterly report data: {e}")
                # 回退到 saveTable 方法
                try:
                    self._sql_service.saveTable('quarterly_reports', stock)
                    print(f"Successfully saved quarterly report data using saveTable method for {start.year}-season{season}-{type.value}")
                except Exception as e2:
                    print(f"Failed to save quarterly report data using saveTable method: {e2}")
        else:
            stock = Temp_data

        # 4. 將新獲取的資料存到混合緩存中
        if (not stock.empty and
            hasattr(self, '_cache_service') and
            self._cache_service):

            # 更新 Redis L1 緩存
            index_list = [str(idx) for idx in stock.index] if not stock.index.equals(range(len(stock))) else None
            cache_data = {
                'data': stock.values.tolist(),
                'columns': stock.columns.tolist(),
                'index': index_list
            }
            self._cache_service.set_redis_cache(cache_key, cache_data)

            # 更新 MongoDB L2 緩存
            try:
                self._cache_service.set_stock_data(cache_key, stock)
                print(f"已將財務報表存到混合緩存: {cache_key}")
            except Exception as e:
                print(f"儲存財務報表到緩存失敗: {e}")

        # Memory 快取已移除，不再更新
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

        # 建立緩存鍵
        cache_key = f"monthly_report_{start.year}_{start.month:02d}"
        file = "monthly_report_" + str(start.year) + "_" + str(start.month)
        fileName = self.filePath + "/" + self.fileName_monthRP + "/" + file

        # 使用新的混合緩存服務 (Redis L1 + MongoDB L2)
        if self._cache_service:
            print(f"使用混合緩存服務查詢月營收: {cache_key}")

            # 1. 嘗試從 Redis L1 緩存獲取
            cached_data = self._cache_service.get_redis_cache(cache_key)
            if cached_data:
                try:
                    df = pd.DataFrame(
                        cached_data['data'],
                        columns=cached_data['columns']
                    )
                    if cached_data.get('index'):
                        df.index = cached_data['index']
                    print(f"L1 緩存命中月營收: {cache_key}")
                    return df
                except Exception as e:
                    print(f"L1 緩存反序列化失敗: {e}")

            # 2. 嘗試從 MongoDB L2 智慧緩存獲取
            mongo_data = self._cache_service.get_mongo_cache(cache_key)
            if mongo_data is not None and not mongo_data.empty:
                # 同步到 Redis L1 緩存
                index_list = [str(idx) for idx in mongo_data.index] if not mongo_data.index.equals(range(len(mongo_data))) else None
                self._cache_service.set_redis_cache(cache_key, {
                    'data': mongo_data.values.tolist(),
                    'columns': mongo_data.columns.tolist(),
                    'index': index_list
                })
                print(f"L2 緩存命中月營收: {cache_key}")
                return mongo_data

        # 3. 如果緩存中沒有，從原有邏輯獲取數據
        print(f"緩存未命中，從原有邏輯獲取月營收: {cache_key}")
        m_data = pd.DataFrame()
        year = start.year

        # 從資料庫或本地文件獲取數據
        m_data = self._read_load_system.load_month_file(fileName, file)

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
            m_data.rename(columns={"公司代號": "symbol"}, inplace=True)
            m_data[["symbol"]] = m_data[[ "symbol"]].astype(str)
            
            # 添加年月欄位以符合 monthly_reports 表結構
            m_data['report_year'] = start.year
            m_data['report_month'] = start.month
            
            # 重新命名欄位以匹配 monthly_reports 表結構
            column_mapping = {
                '公司名稱': 'company_name',
                '當月營收': 'revenue_current_month',
                '上月營收': 'revenue_last_month',
                '去年當月營收': 'revenue_last_year_same_month',
                '當月累計營收': 'revenue_ytd',
                '去年累計營收': 'revenue_last_year_ytd',
                '備註': 'notes'
            }
            m_data = m_data.rename(columns=column_mapping)
            
            # 數據類型轉換
            numeric_columns = ['revenue_current_month', 'revenue_last_month',
                              'revenue_last_year_same_month', 'revenue_ytd', 'revenue_last_year_ytd']
            for col in numeric_columns:
                if col in m_data.columns:
                    m_data[col] = pd.to_numeric(m_data[col], errors='coerce').fillna(0)
            
            # 確保 symbol 欄位存在且為字串類型
            if 'symbol' not in m_data.columns:
                m_data['symbol'] = m_data.index.astype(str)
            
            # 設定索引為 symbol，但保存時不包含索引
            m_data.set_index("symbol", inplace=True)
            
            # 使用 upsert_data 方法保存到 monthly_reports 表，避免重複數據
            try:
                success = self._sql_service.upsert_data('monthly_reports', m_data.reset_index(), 
                                                      ['symbol', 'report_year', 'report_month'])
                if success:
                    print(f"Successfully saved monthly report data to monthly_reports table for {start.year}-{start.month}")
                else:
                    print(f"Failed to save monthly report data to monthly_reports table for {start.year}-{start.month}")
            except Exception as e:
                print(f"Error saving monthly report data: {e}")
                # 回退到 saveTable 方法
                try:
                    self._sql_service.saveTable('monthly_reports', m_data)
                    print(f"Successfully saved monthly report data using saveTable method for {start.year}-{start.month}")
                except Exception as e2:
                    print(f"Failed to save monthly report data using saveTable method: {e2}")

        # 4. 將新獲取的資料存到混合緩存中
        if (not m_data.empty and
            hasattr(self, '_cache_service') and
            self._cache_service):

            # 更新 Redis L1 緩存
            index_list = [str(idx) for idx in m_data.index] if not m_data.index.equals(range(len(m_data))) else None
            cache_data = {
                'data': m_data.values.tolist(),
                'columns': m_data.columns.tolist(),
                'index': index_list
            }
            self._cache_service.set_redis_cache(cache_key, cache_data)

            # 更新 MongoDB L2 緩存
            try:
                self._cache_service.set_stock_data(cache_key, m_data)
                print(f"已將月營收存到混合緩存: {cache_key}")
            except Exception as e:
                print(f"儲存月營收到緩存失敗: {e}")

        # Memory 快取已移除，不再更新
        return m_data

    def get_allstock_yield(self, start: datetime):
        """#爬某天所有股票殖利率"""
        print(
            "".join(["{}:取得".format(sys._getframe().f_code.co_name)]),
            "殖利率的資料:",
            str(start),
        )

        # 建立緩存鍵
        cache_key = f"yield_data_{start.year}_{start.month:02d}_{start.day:02d}"
        file = (
            "dividend_yield_"
            + str(start.year)
            + "_"
            + str(start.month)
            + "_"
            + str(start.day)
        )
        fileName = self.filePath + "/" + self.fileName_yield + "/" + file

        # 使用新的混合緩存服務 (Redis L1 + MongoDB L2)
        if self._cache_service:
            print(f"使用混合緩存服務查詢殖利率: {cache_key}")

            # 1. 嘗試從 Redis L1 緩存獲取
            cached_data = self._cache_service.get_redis_cache(cache_key)
            if cached_data:
                try:
                    df = pd.DataFrame(
                        cached_data['data'],
                        columns=cached_data['columns']
                    )
                    if cached_data.get('index'):
                        df.index = cached_data['index']
                    print(f"L1 緩存命中殖利率: {cache_key}")
                    return df
                except Exception as e:
                    print(f"L1 緩存反序列化失敗: {e}")

            # 2. 嘗試從 MongoDB L2 智慧緩存獲取
            mongo_data = self._cache_service.get_mongo_cache(cache_key)
            if mongo_data is not None and not mongo_data.empty:
                # 同步到 Redis L1 緩存
                index_list = [str(idx) for idx in mongo_data.index] if not mongo_data.index.equals(range(len(mongo_data))) else None
                self._cache_service.set_redis_cache(cache_key, {
                    'data': mongo_data.values.tolist(),
                    'columns': mongo_data.columns.tolist(),
                    'index': index_list
                })
                print(f"L2 緩存命中殖利率: {cache_key}")
                return mongo_data

        # 3. 如果緩存中沒有，從原有邏輯獲取數據
        print(f"緩存未命中，從原有邏輯獲取殖利率: {cache_key}")
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
                m_yield.rename(columns={"證券代號": "symbol"}, inplace=True)
                m_yield[["symbol"]] = m_yield[["symbol"]].astype(str)
                
                # 添加日期欄位以符合 dividend_yield 表結構
                m_yield['date'] = start.strftime('%Y-%m-%d')
                
                # 重新命名欄位以匹配 dividend_yield 表結構
                column_mapping = {
                    '證券名稱': 'company_name',
                    '殖利率(%)': 'dividend_yield',
                    '本益比': 'pe_ratio',
                    '股價淨值比': 'pb_ratio',
                    '財報年/季': 'financial_report'
                }
                m_yield = m_yield.rename(columns=column_mapping)
                
                # 數據類型轉換
                numeric_columns = ['dividend_yield', 'pe_ratio', 'pb_ratio']
                for col in numeric_columns:
                    if col in m_yield.columns:
                        m_yield[col] = pd.to_numeric(m_yield[col], errors='coerce').fillna(0)
                
                # 確保 symbol 欄位存在且為字串類型
                if 'symbol' not in m_yield.columns:
                    m_yield['symbol'] = m_yield.index.astype(str)
                
                # 設定索引為 symbol，但保存時不包含索引
                m_yield.set_index("symbol", inplace=True)
                
                # 使用 upsert_data 方法保存到 dividend_yield 表，避免重複數據
                try:
                    success = self._sql_service.upsert_data('dividend_yield', m_yield.reset_index(), 
                                                          ['symbol', 'date'])
                    if success:
                        print(f"Successfully saved dividend yield data to dividend_yield table for {start.strftime('%Y-%m-%d')}")
                    else:
                        print(f"Failed to save dividend yield data to dividend_yield table for {start.strftime('%Y-%m-%d')}")
                except Exception as e:
                    print(f"Error saving dividend yield data: {e}")
                    # 回退到 saveTable 方法
                    try:
                        self._sql_service.saveTable('dividend_yield', m_yield)
                        print(f"Successfully saved dividend yield data using saveTable method for {start.strftime('%Y-%m-%d')}")
                    except Exception as e2:
                        print(f"Failed to save dividend yield data using saveTable method: {e2}")
        except Exception:
            return pd.DataFrame()

        # 4. 將新獲取的資料存到混合緩存中
        if (not m_yield.empty and
            hasattr(self, '_cache_service') and
            self._cache_service):

            # 更新 Redis L1 緩存
            index_list = [str(idx) for idx in m_yield.index] if not m_yield.index.equals(range(len(m_yield))) else None
            cache_data = {
                'data': m_yield.values.tolist(),
                'columns': m_yield.columns.tolist(),
                'index': index_list
            }
            self._cache_service.set_redis_cache(cache_key, cache_data)

            # 更新 MongoDB L2 緩存
            try:
                self._cache_service.set_stock_data(cache_key, m_yield)
                print(f"已將殖利率存到混合緩存: {cache_key}")
            except Exception as e:
                print(f"儲存殖利率到緩存失敗: {e}")

        # Memory 快取已移除，不再更新
        return m_yield

    def get_allstock_dividend_yield(self):
        """#從數據庫獲取所有股票股息殖利率數據"""
        print("從數據庫獲取股息殖利率數據")
        try:
            return self._sql_service.read_dividend_yield()
        except Exception as e:
            print(f"Error getting dividend yield from database: {e}")
            return pd.DataFrame()

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
        # Only check Taiwan stock codes for Taiwanese stocks
        if (number.replace('.TW', '').isdigit() or number.endswith('.TW')) and not StockInfos.ts.codes.__contains__(number):
            print("無此檔股票")
            return result
        if start_time < data_time:
            print("日期請大於西元2005年")
            return result

        file = str(number)
        filename = self.filePath + "/" + self.fileName_stockInfo + "/" + file
        # 統一處理stock_id，移除可能的後綴，與數據庫和快取保持一致
        stock_id = str(number).upper().replace('.TW', '').replace('.US', '').replace('.HK', '')

        # 使用新的混合快取服務 (Redis L1 + MongoDB L2)
        if self._cache_service:
            print(f"Using hybrid cache service for {stock_id}")
            m_history = self._cache_service.get_stock_data(stock_id)

            if m_history is not None and not m_history.empty:
                print(f"Data for {stock_id} loaded from hybrid cache.")
                # Memory 快取已移除，不再更新
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

        # 在成功獲取資料後，記錄查詢統計（快取更新由排程服務處理）
        if not result.empty and self._cache_service:
            # 記錄查詢統計，讓排程服務決定何時更新快取
            pass  # 查詢統計已在方法開頭記錄

        return result

    def _get_data_from_sources(self, stock_id: str, filename: str) -> pd.DataFrame:
        """從各種來源獲取資料的原有邏輯"""
        m_history = pd.DataFrame()

        # 1. Memory 快取已移除，不再使用

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
                print(f"Data for {stock_id} loaded from MongoDB.")
                if '_id' in m_history.columns:
                    m_history = m_history.drop('_id', axis=1)
                if 'Date' in m_history.columns:
                    m_history['Date'] = pd.to_datetime(m_history['Date'], format='%Y-%m-%d')
                    m_history = m_history.set_index('Date')
                elif 'index' in m_history.columns:
                    m_history['Date'] = pd.to_datetime(m_history['index'], format='%Y-%m-%d')
                    m_history = m_history.set_index('Date').drop('index', axis=1)
                # Memory 快取已移除，不再更新
                return m_history
        except Exception as e:
            print(f"Could not read from MongoDB. Error: {e}")

        # 3. MySQL
        print(f"Data for {stock_id} not in MongoDB, trying MySQL.")
        m_history = self._sql_service.readStockDay(stock_id)
        if not m_history.empty:
            print(f"Data for {stock_id} loaded from MySQL, caching to Mongo.")
            self._mongo_service.saveTable(stock_id, m_history)
            # Memory 快取已移除，不再更新
            return m_history

        # 4. Local File
        print(f"Data for {stock_id} not in MySQL, trying Local File.")
        try:
            m_history = pd.read_csv(filename + ".csv", index_col="Date", parse_dates=["Date"])
            if not m_history.empty:
                print(f"Data for {stock_id} loaded from Local File, caching to MySQL and Mongo.")
                self._sql_service.saveTable(stock_id, m_history)
                self._mongo_service.saveTable(stock_id, m_history)
                # Memory 快取已移除，不再更新
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
            # Memory 快取已移除，不再更新

        return m_history

    def get_stock_AD_index(self, date: datetime, getNew=False):
        """#取得上漲和下跌家數 - 優化版本，整合快取機制"""
        print("get_stock_AD_index")
        if isinstance(date, str):
            date = datetime.strptime(date, "%Y-%m-%d")

        time = date
        while time not in self.get_stock_history("2330").index:
            time = Tools.backWorkDays(time, 1)

        # 1. Try to read from cache first (Redis L1 + MongoDB L2)
        if self._cache_service:
            cache_key = f"ad_index_{time.strftime('%Y-%m-%d')}"
            cached_data = self._cache_service.get_redis_cache(cache_key)
            
            if cached_data:
                try:
                    df = pd.DataFrame(
                        cached_data['data'],
                        columns=cached_data['columns']
                    )
                    if cached_data.get('index'):
                        df.index = cached_data['index']
                    print(f"Found AD_index for {time.strftime('%Y-%m-%d')} in cache.")
                    return df
                except Exception as e:
                    print(f"Cache deserialization failed: {e}")

        # 2. Try to read from MySQL database for historical data
        try:
            ad_index_from_sql = self._sql_service.readDividendYield('ad_index')
            if not ad_index_from_sql.empty:
                print(f"Found AD_index historical data in MySQL ({len(ad_index_from_sql)} records).")
                
                # 如果有當天數據，直接返回
                if time in ad_index_from_sql.index:
                    print(f"Found AD_index for {time.strftime('%Y-%m-%d')} in MySQL.")
                    # 同步到快取
                    if self._cache_service:
                        try:
                            self._cache_service.set_redis_cache(f"ad_index_{time.strftime('%Y-%m-%d')}", {
                                'data': ad_index_from_sql.loc[[time]].values.tolist(),
                                'columns': ad_index_from_sql.columns.tolist(),
                                'index': [str(time)]
                            })
                            print(f"已將 AD_index 從 MySQL 同步到 Redis 快取")
                        except Exception as e:
                            print(f"同步 AD_index 到快取失敗: {e}")
                    return ad_index_from_sql.loc[[time]]
        except Exception as e:
            print(f"Could not read AD_index from MySQL, falling back. Error: {e}")

        # 3. If not in cache or DB, calculate it using optimized batch query
        print(f"No data for {time.strftime('%Y-%m-%d')} in cache or DB. Calculating...")
        time_yesterday = Tools.backWorkDays(time, 1)
        while (
            time_yesterday not in self.get_stock_history("2330", time_yesterday).index
        ):
            time_yesterday = Tools.backWorkDays(time_yesterday, 1)
        str_yesterday = Tools.DateTime2String(time_yesterday)

        # 使用批量查詢來計算騰落指數
        up, down = self._calculate_ad_index_batch(time, time_yesterday, Tools.DateTime2String(time), str_yesterday)

        print(f"Calculation result for {time.strftime('%Y-%m-%d')}: Up={up}, Down={down}")

        ADindex_result_new = pd.DataFrame(
            {"Date": [time], "上漲": [up], "下跌": [down]}
        ).set_index("Date")

        # 獲取現有的歷史數據（從 MySQL）
        try:
            existing_data = self._sql_service.readDividendYield('ad_index')
        except Exception:
            existing_data = pd.DataFrame()

        # 合併新舊數據，建立完整歷史記錄
        if not existing_data.empty:
            # 合併現有數據和新計算的數據
            combined_data = pd.concat([existing_data, ADindex_result_new])
            print(f"Merged with existing {len(existing_data)} historical records")
        else:
            combined_data = ADindex_result_new
            print("No existing historical data found, creating new record")

        # 去重並排序
        combined_data = combined_data[~combined_data.index.duplicated(keep='last')]
        combined_data = combined_data.sort_index()

        # 保存完整歷史數據到 MySQL - 使用 upsert_data 方法
        if not combined_data.empty:
            # 確保索引是 DatetimeIndex
            if not isinstance(combined_data.index, pd.DatetimeIndex):
                combined_data.index = pd.to_datetime(combined_data.index)
            
            # 重置索引，將 Date 變成普通欄位
            combined_data_reset = combined_data.reset_index()
            
            # 使用 upsert_data 方法，指定 Date 為主鍵
            success = self._sql_service.upsert_data("ad_index", combined_data_reset, ["Date"])
            
            if success:
                print(f"Successfully saved {len(combined_data)} total records to ad_index table using upsert")
            else:
                print("Failed to save data to ad_index table")
        else:
            print("No data to save")
        
        # 使用混合快取服務更新快取
        if self._cache_service:
            try:
                # 更新 Redis 快取（單筆查詢結果）
                self._cache_service.set_redis_cache(f"ad_index_{time.strftime('%Y-%m-%d')}", {
                    'data': ADindex_result_new.values.tolist(),
                    'columns': ADindex_result_new.columns.tolist(),
                    'index': [str(time)]
                })
                print(f"已將 AD_index 存到 Redis 快取")
                
                # 更新 MongoDB 快取（完整歷史數據）
                self._cache_service.set_stock_data("ad_index", combined_data)
                print(f"已將完整 AD_index 歷史數據存到 MongoDB 快取")
            except Exception as e:
                print(f"儲存 AD_index 到快取失敗: {e}")

        return ADindex_result_new

    def _calculate_ad_index_batch(self, time: datetime, time_yesterday: datetime, 
                                str_date: str, str_yesterday: str) -> tuple[int, int]:
        """
        使用批量查詢來計算騰落指數，大幅提升性能
        """
        up = 0
        down = 0
        
        # 獲取所有上市股票代碼
        stock_codes = [
            value.code for value in StockInfos.ts.codes.values()
            if value.market == "上市" and len(value.code) == 4 and value.type == "股票"
            and not Tools.check_no_use_stock(value.code)
        ]
        
        print(f"Calculating AD index for {len(stock_codes)} stocks...")
        
        # 批量查詢股票歷史數據
        batch_size = 50  # 每批處理的股票數量
        total_stocks = len(stock_codes)
        processed_stocks = 0
        
        for i in range(0, total_stocks, batch_size):
            batch_codes = stock_codes[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total_stocks - 1) // batch_size + 1
            
            print(f"Processing batch {batch_num}/{total_batches} ({i+1}-{min(i+batch_size, total_stocks)}/{total_stocks})")
            
            # 批量獲取股票數據
            batch_results = {}
            for code in batch_codes:
                try:
                    m_history = self.get_stock_history(code, str_yesterday)
                    batch_results[code] = m_history
                except Exception:
                    continue
            
            # 計算漲跌
            for code, m_history in batch_results.items():
                if m_history.empty:
                    continue
                    
                try:
                    price_Close = round(m_history["Close"].get(str_date), 2)
                    price_Open = round(m_history["Open"].get(str_yesterday), 2)

                    if price_Close is not None and price_Open is not None:
                        if price_Open < price_Close:
                            up += 1
                        elif price_Open > price_Close:
                            down += 1
                except Exception:
                    continue
            
            processed_stocks += len(batch_codes)
            progress_percent = (processed_stocks / total_stocks) * 100
            print(f"Progress: {processed_stocks}/{total_stocks} stocks processed ({progress_percent:.1f}%)")
        
        print(f"Calculation completed: Up={up}, Down={down}")
        return up, down

    def get_full_ad_index(self) -> pd.DataFrame:
        """#取得完整的上漲和下跌家數歷史資料"""
        print("get_full_ad_index from MySQL")
        try:
            # 使用專門的 read_ad_index 方法讀取騰落指數數據
            ad_index_table = self._sql_service.read_ad_index(limit=10000)
            if not ad_index_table.empty:
                return ad_index_table.sort_index()
        except Exception as e:
            print(f"Could not read AD_index from MySQL. Error: {e}")
        return pd.DataFrame()

    def get_allstock_dividend_yield(self):
        """#從數據庫獲取所有股票股息殖利率數據"""
        print("get_allstock_dividend_yield from database")
        try:
            return self._sql_service.read_dividend_yield()
        except Exception as e:
            print(f"Could not read dividend yield data from database. Error: {e}")
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
