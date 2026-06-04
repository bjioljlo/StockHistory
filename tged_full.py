import os
import sys
import time
from datetime import datetime
from io import StringIO
from typing import Optional, Union, Dict, Any, Tuple
import logging

import numpy as np
import pandas as pd
import requests

from src.Common import InfomationType as info
from src.ExternalService.IGetExternalData import IGetExternalData
from pydb_core.mongo_service import MongoService
from pydb_core.read_load_system import ReadLoadSystem
from pydb_core.sql_service import SqlService
import src.StockInfos as StockInfos
from src.Common import Tools
from pydb_core.cache_service import HybridCacheService


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
        self._file_paths = {
            'monthRP': "monthRP",
            'stockInfo': "stockInfo", 
            'yield': "yieldInfo",
            'season': "seasonInfo",
            'index': "indexInfo"
        }
        self._file_path = os.getcwd()  # 取得目錄路徑
        self._logger = logging.getLogger(__name__)

    def get_allstock_financial_statement(self, start: datetime, type: info.FS_type) -> pd.DataFrame:
        """
        爬取某季所有股票歷史財報
        
        Args:
            start: 起始日期
            type: 財報類型
            
        Returns:
            財務報表數據 DataFrame
        """
        self._logger.info(f"取得 {type} 的季財報資料: {start}")
        
        if not Tools.Have_DayRP(start):
            return pd.DataFrame()
        season = int(((start.month - 1) / 3) + 1)
        if not Tools.CheckFS_season(start):
            self._logger.warning("Season rp is no data yet!")
            return pd.DataFrame()

        # 建立緩存鍵和文件路徑
        cache_key = f"financial_statement_{start.year}_{season}_{type.value}"
        file = f"{start.year}-season{season}-{type.value}"
        fileName = self._get_file_path('season', file)

        # 嘗試從快取獲取數據
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data

        # 嘗試從 SQL 數據庫讀取
        sql_data = self._get_financial_statement_from_sql(start, season, type)
        if not sql_data.empty:
            return sql_data

        # 從本地文件讀取並處理
        return self._get_financial_statement_from_file(fileName, start, season, type)

    def _get_financial_statement_from_sql(self, start: datetime, season: int, type: info.FS_type) -> pd.DataFrame:
        """從 SQL 數據庫獲取財務報表數據"""
        cache_key = f"financial_statement_{start.year}_{season}_{type.value}"
        Temp_data = pd.DataFrame()
        
        try:
            # 根據不同的報表類型，調用對應的 SQL 讀取方法
            # 直接傳遞 type 枚舉對象，讓 read_quarterly_reports 內部處理轉換
            Temp_data = self._sql_service.read_quarterly_reports(
                symbol=None,
                report_type=type,
                start_year=start.year,
                end_year=start.year,
                limit=10000
            )
            
            if not Temp_data.empty:
                # 過濾出指定季節的數據
                Temp_data = Temp_data[Temp_data['report_season'] == season]
                if not Temp_data.empty:
                    self._logger.info(f"從 SQL 數據庫成功讀取財務報表: {cache_key}")
                    # 確保 symbol 欄位存在且為字串類型
                    if 'symbol' not in Temp_data.columns:
                        Temp_data['symbol'] = Temp_data.index.astype(str)
                    Temp_data['symbol'] = Temp_data['symbol'].astype(str)
                    Temp_data.set_index("symbol", inplace=True)
                    
                    # 保存到快取
                    self._save_to_cache(cache_key, Temp_data)
                    return Temp_data
        except Exception as e:
            self._logger.error(f"從 SQL 數據庫讀取財務報表失敗: {e}")
        
        return pd.DataFrame()

    def _get_financial_statement_from_file(self, fileName: str, start: datetime, season: int, type: info.FS_type) -> pd.DataFrame:
        """從本地文件獲取財務報表數據"""
        cache_key = f"financial_statement_{start.year}_{season}_{type.value}"
        Temp_data = self._read_load_system.load_month_file(fileName, os.path.basename(fileName))

        if Temp_data.empty:
            if os.path.isfile(fileName + ".csv"):
                self._logger.info(f"已經有 {start.month} 月財務報告")
            self._financial_statement(start.year, season, type)
            self._logger.info(f"下載 {start.month} 月財務報告 OK")

            stock = pd.read_csv(fileName + ".csv")
            stock = self._process_financial_statement_data(stock, start, season, type)
            
            # 保存到數據庫
            self._save_financial_statement_to_db(stock, type)
        else:
            stock = Temp_data

        # 保存到快取
        if (not stock.empty and
            hasattr(self, '_cache_service') and
            self._cache_service):
            self._save_to_cache(cache_key, stock)

        return stock

    def _process_financial_statement_data(self, stock: pd.DataFrame, start: datetime, season: int, type: info.FS_type) -> pd.DataFrame:
        """處理財務報表數據"""
        # 整理資料
        stock.rename(columns={"公司代號": "symbol"}, inplace=True)
        stock.set_index("symbol", inplace=True)
        
        # 添加年季和報表類型欄位
        stock['report_year'] = start.year
        stock['report_season'] = season
        stock['report_type'] = type.value
        
        # 根據不同的報表類型，重新命名欄位
        column_mapping = self._get_financial_statement_column_mapping(type)
        stock = stock.rename(columns=column_mapping)
        
        # 數據類型轉換
        numeric_columns = [col for col in stock.columns if col not in ['symbol', 'report_year', 'report_season', 'report_type']]
        for col in numeric_columns:
            if col in stock.columns:
                stock[col] = pd.to_numeric(stock[col], errors='coerce').fillna(0)
        
        # 確保 symbol 欄位存在且為字串類型
        if 'symbol' not in stock.columns:
            stock['symbol'] = stock.index.astype(str)
        stock.set_index("symbol", inplace=True)
        
        return stock

    def _get_financial_statement_column_mapping(self, type: info.FS_type) -> Dict[str, str]:
        """獲取財務報表欄位映射"""
        column_mappings = {
            info.FS_type.PLA: {
                '營業收入': 'revenue',
                '毛利率(%)': 'gross_margin',
                '營業利益率(%)': 'operating_margin',
                '稅前純益率(%)': 'pre_tax_margin',
                '稅後純益率(%)': 'net_margin'
            },
            info.FS_type.BS: {
                '資產總額': 'total_assets',
                '負債總額': 'total_liabilities',
                '權益總額': 'equity',
                '股本': 'capital',
                '每股參考淨值': 'book_value_per_share'
            },
            info.FS_type.CPL: {
                '營業收入': 'revenue',
                '毛利率(%)': 'gross_margin',
                '營業利益率(%)': 'operating_margin',
                '稅前純益率(%)': 'pre_tax_margin',
                '稅後純益率(%)': 'net_margin'
            },
            info.FS_type.SCF: {
                '營業活動之淨現金流入（流出）': 'operating_cash_flow',
                '投資活動之淨現金流入（流出）': 'investing_cash_flow',
                '籌資活動之淨現金流入（流出）': 'financing_cash_flow'
            }
        }
        return column_mappings.get(type, {})

    def _save_financial_statement_to_db(self, stock: pd.DataFrame, type: info.FS_type) -> None:
        """保存財務報表數據到數據庫"""
        try:
            success = self._sql_service.upsert_data('quarterly_reports', stock.reset_index(), 
                                                  ['symbol', 'report_year', 'report_season', 'report_type'])
            if success:
                self._logger.info(f"Successfully saved quarterly report data to quarterly_reports table for {type.value}")
            else:
                self._logger.error(f"Failed to save quarterly report data to quarterly_reports table for {type.value}")
        except Exception as e:
            self._logger.error(f"Error saving quarterly report data: {e}")
            # 回退到 saveTable 方法
            try:
                self._sql_service.saveTable('quarterly_reports', stock)
                self._logger.info(f"Successfully saved quarterly report data using saveTable method for {type.value}")
            except Exception as e2:
                self._logger.error(f"Failed to save quarterly report data using saveTable method: {e2}")

    def get_allstock_monthly_report(self, start: datetime) -> pd.DataFrame:
        """
        爬取某月所有股票月營收
        
        Args:
            start: 起始日期
            
        Returns:
            月營收數據 DataFrame
        """
        self._logger.info(f"取得月營收資料: {start}")
        
        if not Tools.Have_MonthRP(start):
            return pd.DataFrame()

        # 建立緩存鍵和文件路徑
        cache_key = f"monthly_report_{start.year}_{start.month:02d}"
        file = f"monthly_report_{start.year}_{start.month}"
        fileName = self._get_file_path('monthRP', file)

        # 嘗試從快取獲取數據
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data

        # 嘗試從 SQL 數據庫讀取
        sql_data = self._get_monthly_report_from_sql(start)
        if not sql_data.empty:
            return sql_data

        # 從本地文件讀取並處理
        return self._get_monthly_report_from_file(fileName, start)

    def _get_monthly_report_from_sql(self, start: datetime) -> pd.DataFrame:
        """從 SQL 數據庫獲取月營收數據"""
        cache_key = f"monthly_report_{start.year}_{start.month:02d}"
        m_data = pd.DataFrame()
        year = start.year
        
        try:
            m_data = self._sql_service.read_monthly_reports(
                symbol=None,
                start_year=start.year,
                end_year=start.year,
                limit=10000
            )
            
            if not m_data.empty:
                # 過濾出指定月份的數據
                m_data = m_data[(m_data['report_year'] == start.year) & (m_data['report_month'] == start.month)]
                if not m_data.empty:
                    self._logger.info(f"從 SQL 數據庫成功讀取月營收: {cache_key}")
                    # 確保 symbol 欄位存在且為字串類型
                    if 'symbol' not in m_data.columns:
                        m_data['symbol'] = m_data.index.astype(str)
                    m_data['symbol'] = m_data['symbol'].astype(str)
                    m_data.set_index("symbol", inplace=True)
                    
                    # 保存到快取
                    self._save_to_cache(cache_key, m_data)
                    return m_data
        except Exception as e:
            self._logger.error(f"從 SQL 數據庫讀取月營收失敗: {e}")
        
        return pd.DataFrame()

    def _get_monthly_report_from_file(self, fileName: str, start: datetime) -> pd.DataFrame:
        """從本地文件獲取月營收數據"""
        cache_key = f"monthly_report_{start.year}_{start.month:02d}"
        m_data = self._read_load_system.load_month_file(fileName, os.path.basename(fileName))

        if m_data.empty:
            # 下載月營收數據
            m_data = self._download_monthly_report_data(start, fileName)
            if m_data.empty:
                return pd.DataFrame()

            # 處理數據
            m_data = self._process_monthly_report_data(m_data, start)
            
            # 保存到數據庫
            self._save_monthly_report_to_db(m_data)
        else:
            m_data = self._process_monthly_report_data(m_data, start)

        # 保存到快取
        if (not m_data.empty and
            hasattr(self, '_cache_service') and
            self._cache_service):
            self._save_to_cache(cache_key, m_data)

        return m_data

    def _download_monthly_report_data(self, start: datetime, fileName: str) -> pd.DataFrame:
        """下載月營收數據"""
        year = start.year
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

        return pd.read_csv(fileName + ".csv")

    def _process_monthly_report_data(self, m_data: pd.DataFrame, start: datetime) -> pd.DataFrame:
        """處理月營收數據"""
        m_data.drop(m_data.tail(1).index, inplace=True)
        # 整理資料
        m_data.rename(columns={"公司代號": "symbol"}, inplace=True)
        m_data[["symbol"]] = m_data[["symbol"]].astype(str)
        
        # 添加年月欄位
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
        m_data.set_index("symbol", inplace=True)
        
        return m_data

    def _save_monthly_report_to_db(self, m_data: pd.DataFrame) -> None:
        """保存月營收數據到數據庫"""
        try:
            success = self._sql_service.upsert_data('monthly_reports', m_data.reset_index(), 
                                                  ['symbol', 'report_year', 'report_month'])
            if success:
                self._logger.info("Successfully saved monthly report data to monthly_reports table")
            else:
                self._logger.error("Failed to save monthly report data to monthly_reports table")
        except Exception as e:
            self._logger.error(f"Error saving monthly report data: {e}")
            # 回退到 saveTable 方法
            try:
                self._sql_service.saveTable('monthly_reports', m_data)
                self._logger.info("Successfully saved monthly report data using saveTable method")
            except Exception as e2:
                self._logger.error(f"Failed to save monthly report data using saveTable method: {e2}")

    def get_allstock_yield(self, start: datetime) -> pd.DataFrame:
        """
        爬取某天所有股票殖利率
        
        Args:
            start: 起始日期
            
        Returns:
            殖利率數據 DataFrame
        """
        self._logger.info(f"取得殖利率資料: {start}")

        # 建立緩存鍵和文件路徑
        cache_key = f"yield_data_{start.year}_{start.month:02d}_{start.day:02d}"
        file = f"dividend_yield_{start.year}_{start.month}_{start.day}"
        fileName = self._get_file_path('yield', file)

        # 嘗試從快取獲取數據
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data

        # 嘗試從 SQL 數據庫讀取
        sql_data = self._get_yield_from_sql(start)
        if not sql_data.empty:
            return sql_data

        # 從本地文件讀取並處理
        return self._get_yield_from_file(fileName, start)

    def _get_yield_from_sql(self, start: datetime) -> pd.DataFrame:
        """從 SQL 數據庫獲取殖利率數據"""
        cache_key = f"yield_data_{start.year}_{start.month:02d}_{start.day:02d}"
        m_yield = pd.DataFrame()
        
        try:
            m_yield = self._sql_service.read_dividend_yield(
                symbol=None,
                start_date=start.strftime('%Y-%m-%d'),
                end_date=start.strftime('%Y-%m-%d'),
                limit=10000
            )
            
            if not m_yield.empty:
                self._logger.info(f"從 SQL 數據庫成功讀取殖利率: {cache_key}")
                # 確保 symbol 欄位存在且為字串類型
                if 'symbol' not in m_yield.columns:
                    m_yield['symbol'] = m_yield.index.astype(str)
                m_yield['symbol'] = m_yield['symbol'].astype(str)
                m_yield.set_index("symbol", inplace=True)
                
                # 保存到快取
                self._save_to_cache(cache_key, m_yield)
                return m_yield
        except Exception as e:
            self._logger.error(f"從 SQL 數據庫讀取殖利率失敗: {e}")
        
        return pd.DataFrame()

    def _get_yield_from_file(self, fileName: str, start: datetime) -> pd.DataFrame:
        """從本地文件獲取殖利率數據"""
        cache_key = f"yield_data_{start.year}_{start.month:02d}_{start.day:02d}"
        m_yield = self._read_load_system.load_month_file(fileName, os.path.basename(fileName))

        try:
            if m_yield.empty and (
                self.get_stock_history("2330", start)["Volume"][
                    Tools.DateTime2String(start)
                ]
                > 0
            ):
                # 下載殖利率數據
                m_yield = self._download_yield_data(start, fileName)
                if m_yield.empty:
                    return pd.DataFrame()

                # 處理數據
                m_yield = self._process_yield_data(m_yield, start)
                
                # 保存到數據庫
                self._save_yield_to_db(m_yield)
        except Exception as e:
            self._logger.error(f"Error processing yield data from file: {e}")
            return pd.DataFrame()

        # 如果沒有異常，處理數據
        if not m_yield.empty:
            m_yield = self._process_yield_data(m_yield, start)

        # 保存到快取
        if (not m_yield.empty and
            hasattr(self, '_cache_service') and
            self._cache_service):
            self._save_to_cache(cache_key, m_yield)

        return m_yield

    def _download_yield_data(self, start: datetime, fileName: str) -> pd.DataFrame:
        """下載殖利率數據"""
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
            return pd.read_csv(fileName + ".csv", encoding="ANSI")
        except pd.errors.EmptyDataError:
            self._logger.warning(f"no {fileName} csv file")
            return pd.DataFrame()
        except pd.errors.ParserError:
            self._logger.warning(f"get Parser error {fileName} csv file")
            return pd.DataFrame()
        except UnicodeDecodeError:
            self._logger.warning(f"get UnicodeDecode error {fileName} csv file")
            return pd.DataFrame()

    def _process_yield_data(self, m_yield: pd.DataFrame, start: datetime) -> pd.DataFrame:
        """處理殖利率數據"""
        # 整理資料
        m_yield.rename(columns={"證券代號": "symbol"}, inplace=True)
        m_yield[["symbol"]] = m_yield[["symbol"]].astype(str)
        
        # 添加日期欄位
        m_yield['date'] = start.strftime('%Y-%m-%d')
        
        # 重新命名欄位以匹配 dividend_yield 表結構
        column_mapping = {
            '證券代號': 'symbol',
            '證券名稱': 'company_name',
            '殖利率(%)': 'dividend_yield',
            '本益比': 'pe_ratio',
            '股價淨值比': 'pb_ratio'
        }
        m_yield = m_yield.rename(columns=column_mapping)
        
        # 確保所有必要欄位都存在
        required_columns = ['symbol', 'date', 'company_name', 'dividend_yield', 'pe_ratio', 'pb_ratio']
        for col in required_columns:
            if col not in m_yield.columns:
                if col == 'symbol':
                    m_yield['symbol'] = m_yield.index.astype(str)
                elif col == 'date':
                    m_yield['date'] = start.strftime('%Y-%m-%d')
                else:
                    m_yield[col] = 0
        
        # 數據類型轉換
        numeric_columns = ['dividend_yield', 'pe_ratio', 'pb_ratio']
        for col in numeric_columns:
            if col in m_yield.columns:
                m_yield[col] = pd.to_numeric(m_yield[col], errors='coerce').fillna(0)
        
        # 確保 symbol 欄位存在且為字串類型
        if 'symbol' not in m_yield.columns:
            m_yield['symbol'] = m_yield.index.astype(str)
        m_yield.set_index("symbol", inplace=True)
        
        return m_yield

    def _save_yield_to_db(self, m_yield: pd.DataFrame) -> None:
        """保存殖利率數據到數據庫"""
        try:
            success = self._sql_service.upsert_dividend_yield(m_yield.reset_index())
            if success:
                self._logger.info("Successfully saved dividend yield data to dividend_yield table")
            else:
                self._logger.error("Failed to save dividend yield data to dividend_yield table")
        except Exception as e:
            self._logger.error(f"Error saving dividend yield data: {e}")
            # 回退到 saveTable 方法
            try:
                self._sql_service.saveTable('dividend_yield', m_yield)
                self._logger.info("Successfully saved dividend yield data using saveTable method")
            except Exception as e2:
                self._logger.error(f"Failed to save dividend yield data using saveTable method: {e2}")

    def get_allstock_dividend_yield(self) -> pd.DataFrame:
        """
        從數據庫獲取所有股票股息殖利率數據
        
        Returns:
            殖利率數據 DataFrame
        """
        self._logger.info("從數據庫獲取股息殖利率數據")
        try:
            return self._sql_service.read_dividend_yield()
        except Exception as e:
            self._logger.error(f"Error getting dividend yield from database: {e}")
            return pd.DataFrame()

    def get_stock_history(
        self,
        number: str,
        start: Union[str, datetime] = datetime.strptime("2005-1-1", "%Y-%m-%d"),
    ) -> pd.DataFrame:
        """
        爬取某個股票的歷史紀錄，加入快取統計
        
        Args:
            number: 股票代碼
            start: 起始日期
            
        Returns:
            股票歷史數據 DataFrame
        """
        self._logger.info(f"取得股票 {number} 的歷史資料從 {start} 到今天")
        
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
            self._logger.warning(f"ItsCantUseStock: {number}")
            return result
            
        # Only check Taiwan stock codes for Taiwanese stocks
        if (number.replace('.TW', '').isdigit() or number.endswith('.TW')) and not StockInfos.ts.codes.__contains__(number):
            self._logger.warning("無此檔股票")
            return result
            
        if start_time < data_time:
            self._logger.warning("日期請大於西元2005年")
            return result

        # 統一處理stock_id，移除可能的後綴，與數據庫和快取保持一致
        stock_id = str(number).upper().replace('.TW', '').replace('.US', '').replace('.HK', '')
        filename = self._get_file_path('stockInfo', stock_id)

        # 使用混合快取服務獲取數據
        m_history = self._get_stock_history_from_cache(stock_id)
        if m_history is not None and not m_history.empty:
            return self._filter_and_process_history(m_history, start_time)

        # 如果快取中沒有，則從其他來源獲取
        m_history = self._get_stock_history_from_sources(stock_id, filename)
        if m_history.empty:
            self._logger.warning(f"Could not retrieve data for {stock_id} from any source.")
            return pd.DataFrame()

        # 將新獲取的資料存到混合快取中
        if (not m_history.empty and
            hasattr(self, '_cache_service') and
            self._cache_service):
            self._cache_service.set_stock_data(stock_id, m_history)

        return self._filter_and_process_history(m_history, start_time)

    def _get_stock_history_from_cache(self, stock_id: str) -> Optional[pd.DataFrame]:
        """從快取獲取股票歷史數據"""
        if not self._cache_service:
            return None

        try:
            m_history = self._cache_service.get_stock_data(stock_id)
            if m_history is not None and not m_history.empty:
                self._logger.info(f"Data for {stock_id} loaded from hybrid cache.")
                return m_history
        except Exception as e:
            self._logger.error(f"Error getting data from cache for {stock_id}: {e}")
        
        return None

    def _get_stock_history_from_sources(self, stock_id: str, filename: str) -> pd.DataFrame:
        """從各種來源獲取股票歷史數據"""
        m_history = pd.DataFrame()

        # 1. MongoDB (直接從集合讀取)
        self._logger.info(f"Data for {stock_id} not in cache, trying MongoDB.")
        try:
            collection = self._mongo_service.mongodb[stock_id.lower()]
            cursor = collection.find()
            m_history = pd.DataFrame(list(cursor))
            if not m_history.empty:
                self._logger.info(f"Data for {stock_id} loaded from MongoDB.")
                m_history = self._process_mongodb_data(m_history)
                return m_history
        except Exception as e:
            self._logger.error(f"Could not read from MongoDB for {stock_id}. Error: {e}")

        # 2. MySQL
        self._logger.info(f"Data for {stock_id} not in MongoDB, trying MySQL.")
        m_history = self._sql_service.readStockDay(stock_id)
        if not m_history.empty:
            self._logger.info(f"Data for {stock_id} loaded from MySQL, caching to Mongo.")
            self._mongo_service.saveTable(stock_id, m_history)
            return m_history

        # 3. Local File
        self._logger.info(f"Data for {stock_id} not in MySQL, trying Local File.")
        try:
            m_history = pd.read_csv(filename + ".csv", index_col="Date", parse_dates=["Date"])
            if not m_history.empty:
                self._logger.info(f"Data for {stock_id} loaded from Local File, caching to MySQL and Mongo.")
                self._sql_service.saveTable(stock_id, m_history)
                self._mongo_service.saveTable(stock_id, m_history)
                return m_history
        except Exception as e:
            self._logger.error(f"Could not read from local file for {stock_id}. Error: {e}")

        # 4. Yahoo Finance
        self._logger.info(f"Data for {stock_id} not in any cache, fetching from Yahoo Finance.")
        self._sql_service.yfInfo(stock_id)
        time.sleep(1.5)
        m_history = self._sql_service.readStockDay(stock_id)

        if not m_history.empty:
            self._logger.info(f"Data for {stock_id} loaded from Yahoo->MySQL, caching to other systems.")
            self._mongo_service.saveTable(stock_id, m_history)

        return m_history

    def _process_mongodb_data(self, m_history: pd.DataFrame) -> pd.DataFrame:
        """處理 MongoDB 數據"""
        if '_id' in m_history.columns:
            m_history = m_history.drop('_id', axis=1)
        if 'Date' in m_history.columns:
            m_history['Date'] = pd.to_datetime(m_history['Date'], format='%Y-%m-%d')
            m_history = m_history.set_index('Date')
        elif 'index' in m_history.columns:
            m_history['Date'] = pd.to_datetime(m_history['index'], format='%Y-%m-%d')
            m_history = m_history.set_index('Date').drop('index', axis=1)
        return m_history

    def _filter_and_process_history(self, m_history: pd.DataFrame, start_time: datetime) -> pd.DataFrame:
        """過濾和處理歷史數據"""
        # 確保索引是 DatetimeIndex
        if not isinstance(m_history.index, pd.DatetimeIndex):
            m_history.index = pd.to_datetime(m_history.index)

        # 進行日期比較
        mask = m_history.index >= start_time
        result = m_history[mask]
        
        # 填充 Adj Close 的 NaN 值為 0
        if 'Adj Close' in result.columns:
            result['Adj Close'] = result['Adj Close'].fillna(0)
        result = result.dropna(axis=0, how="any")

        return result

    def get_stock_AD_index(self, date: Union[str, datetime], getNew: bool = False) -> pd.DataFrame:
        """
        取得上漲和下跌家數 - 優化版本，整合快取機制
        
        Args:
            date: 日期
            getNew: 是否強制重新計算
            
        Returns:
            騰落指數數據 DataFrame
        """
        self._logger.info(f"取得騰落指數資料: {date}")
        
        if isinstance(date, str):
            date = datetime.strptime(date, "%Y-%m-%d")

        time = date
        while time not in self.get_stock_history("2330").index:
            time = Tools.backWorkDays(time, 1)

        # 建立緩存鍵
        cache_key = f"ad_index_{time.strftime('%Y-%m-%d')}"

        # 1. 嘗試從快取獲取數據
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None and not getNew:
            return cached_data

        # 2. 嘗試從 SQL 數據庫讀取
        sql_data = self._get_ad_index_from_sql(time)
        if not sql_data.empty and not getNew:
            return sql_data

        # 3. 如果快取和數據庫都沒有，或強制重新計算，則計算騰落指數
        self._logger.info(f"No data for {time.strftime('%Y-%m-%d')} in cache or DB. Calculating...")
        time_yesterday = Tools.backWorkDays(time, 1)
        while time_yesterday not in self.get_stock_history("2330", time_yesterday).index:
            time_yesterday = Tools.backWorkDays(time_yesterday, 1)
        str_yesterday = Tools.DateTime2String(time_yesterday)

        # 使用批量查詢來計算騰落指數
        up, down = self._calculate_ad_index_batch(time, time_yesterday, 
                                               Tools.DateTime2String(time), str_yesterday)

        self._logger.info(f"Calculation result for {time.strftime('%Y-%m-%d')}: Up={up}, Down={down}")

        # 建立新的騰落指數結果
        ADindex_result_new = pd.DataFrame(
            {"Date": [time], "上漲": [up], "下跌": [down]}
        ).set_index("Date")

        # 獲取現有的歷史數據（從 SQL）
        existing_data = self._get_existing_ad_index_data()

        # 合併新舊數據，建立完整歷史記錄
        if not existing_data.empty:
            combined_data = pd.concat([existing_data, ADindex_result_new])
            self._logger.info(f"Merged with existing {len(existing_data)} historical records")
        else:
            combined_data = ADindex_result_new
            self._logger.info("No existing historical data found, creating new record")

        # 去重並排序
        combined_data = combined_data[~combined_data.index.duplicated(keep='last')]
        combined_data = combined_data.sort_index()

        # 保存完整歷史數據到 SQL - 使用 upsert_data 方法
        if not combined_data.empty:
            combined_data_reset = combined_data.reset_index()
            success = self._sql_service.upsert_data("ad_index", combined_data_reset, ["Date"])
            
            if success:
                self._logger.info(f"Successfully saved {len(combined_data)} total records to ad_index table using upsert")
            else:
                self._logger.error("Failed to save data to ad_index table")
        else:
            self._logger.warning("No data to save")

        # 使用混合快取服務更新快取
        if self._cache_service:
            try:
                # 更新 Redis 快取（單筆查詢結果）
                self._save_to_cache(cache_key, ADindex_result_new)
                
                # 更新 MongoDB 快取（完整歷史數據）
                self._cache_service.set_stock_data("ad_index", combined_data)
                self._logger.info(f"已將完整 AD_index 歷史數據存到混合快取")
            except Exception as e:
                self._logger.error(f"儲存 AD_index 到快取失敗: {e}")

        return ADindex_result_new

    def _get_ad_index_from_sql(self, time: datetime) -> pd.DataFrame:
        """從 SQL 數據庫獲取騰落指數數據"""
        cache_key = f"ad_index_{time.strftime('%Y-%m-%d')}"
        ad_index_data = pd.DataFrame()
        
        try:
            ad_index_data = self._sql_service.read_ad_index(limit=10000)
            if not ad_index_data.empty:
                self._logger.info(f"Found AD_index historical data in MySQL ({len(ad_index_data)} records).")
                
                # 如果有當天數據，直接返回
                if time in ad_index_data.index:
                    self._logger.info(f"Found AD_index for {time.strftime('%Y-%m-%d')} in MySQL.")
                    # 保存到快取
                    self._save_to_cache(cache_key, ad_index_data.loc[[time]])
                    return ad_index_data.loc[[time]]
        except Exception as e:
            self._logger.error(f"Could not read AD_index from MySQL. Error: {e}")
        
        return pd.DataFrame()

    def _get_existing_ad_index_data(self) -> pd.DataFrame:
        """獲取現有的騰落指數歷史數據"""
        try:
            return self._sql_service.read_ad_index(limit=10000)
        except Exception as e:
            self._logger.error(f"Could not read existing AD_index data. Error: {e}")
            return pd.DataFrame()

    def _calculate_ad_index_batch(self, time: datetime, time_yesterday: datetime, 
                                str_date: str, str_yesterday: str) -> tuple[int, int]:
        """
        使用批量查詢來計算騰落指數，大幅提升性能
        
        Args:
            time: 目標日期
            time_yesterday: 昨日日期
            str_date: 目標日期字串
            str_yesterday: 昨日日期字串
            
        Returns:
            (上漲家數, 下跌家數)
        """
        up = 0
        down = 0
        
        # 獲取所有上市股票代碼
        stock_codes = [
            value.code for value in StockInfos.ts.codes.values()
            if value.market == "上市" and len(value.code) == 4 and value.type == "股票"
            and not Tools.check_no_use_stock(value.code)
        ]
        
        self._logger.info(f"Calculating AD index for {len(stock_codes)} stocks...")
        
        # 批量查詢股票歷史數據
        batch_size = 50  # 每批處理的股票數量
        total_stocks = len(stock_codes)
        processed_stocks = 0
        
        for i in range(0, total_stocks, batch_size):
            batch_codes = stock_codes[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total_stocks - 1) // batch_size + 1
            
            self._logger.info(f"Processing batch {batch_num}/{total_batches} ({i+1}-{min(i+batch_size, total_stocks)}/{total_stocks})")
            
            # 批量獲取股票數據
            batch_results = {}
            for code in batch_codes:
                try:
                    m_history = self.get_stock_history(code, str_yesterday)
                    batch_results[code] = m_history
                except Exception as e:
                    self._logger.debug(f"Failed to get history for {code}: {e}")
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
                except Exception as e:
                    self._logger.debug(f"Failed to calculate AD index for {code}: {e}")
                    continue
            
            processed_stocks += len(batch_codes)
            progress_percent = (processed_stocks / total_stocks) * 100
            self._logger.info(f"Progress: {processed_stocks}/{total_stocks} stocks processed ({progress_percent:.1f}%)")
        
        self._logger.info(f"Calculation completed: Up={up}, Down={down}")
        return up, down

    def get_full_ad_index(self) -> pd.DataFrame:
        """
        取得完整的上漲和下跌家數歷史資料
        
        Returns:
            騰落指數歷史數據 DataFrame
        """
        self._logger.info("取得完整的騰落指數歷史資料")
        try:
            # 使用專門的 read_ad_index 方法讀取騰落指數數據
            ad_index_table = self._sql_service.read_ad_index(limit=10000)
            if not ad_index_table.empty:
                return ad_index_table.sort_index()
        except Exception as e:
            self._logger.error(f"Could not read AD_index from MySQL. Error: {e}")
        return pd.DataFrame()

    def get_allstock_dividend_yield(self) -> pd.DataFrame:
        """
        從數據庫獲取所有股票股息殖利率數據
        
        Returns:
            殖利率數據 DataFrame
        """
        self._logger.info("從數據庫獲取股息殖利率數據")
        try:
            return self._sql_service.read_dividend_yield()
        except Exception as e:
            self._logger.error(f"Error getting dividend yield from database: {e}")
            return pd.DataFrame()

    def _remove_td(self, column: str) -> str:
        """
        移除 HTML 標籤並清理數據
        
        Args:
            column: 包含 HTML 標籤的字串
            
        Returns:
            清理後的字串
        """
        remove_one = column.split("<")
        remove_two = remove_one[0].split(">")
        return remove_two[1].replace(",", "")

    def _translate_dataFrame(self, response: str) -> pd.DataFrame:
        """
        解析財務報表 HTML 響應
        
        Args:
            response: HTML 響應字串
            
        Returns:
            解析後的 DataFrame
        """
        table_array = response.split("<table")
        tr_array = table_array[1].split("<tr")

        data = []
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
                if revenue == "&nbsp;" or revenue == "":
                    continue
                if i > 1:
                    if name == "公司名稱":
                        continue
                    data.append([
                        name, code, revenue, profitRatio, profitMargin,
                        preTaxIncomeMargin, afterTaxIncomeMargin
                    ])
                if i == 1:
                    column.extend(["公司名稱", "公司代號", revenue, profitRatio,
                                 profitMargin, preTaxIncomeMargin, afterTaxIncomeMargin])

        return pd.DataFrame(data=data, columns=column)

    def _translate_dataFrame2(self, response: str, type: info.FS_type, 
                            year: int, season: int = 1) -> pd.DataFrame:
        """
        解析財務報表 HTML 響應（第二種格式）
        
        Args:
            response: HTML 響應字串
            type: 財報類型
            year: 年份
            season: 季度
            
        Returns:
            解析後的 DataFrame
        """
        table_array = response.split("<table")
        tr_array_array = [table_array[i].split("<tr") for i in range(2, 8)]
        
        # 根據年份和報表類型設定欄位位置
        column_pos_array = self._get_column_positions(year, type, season)
        
        data = []
        column = []

        for k, tr_array in enumerate(tr_array_array):
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
                        preTaxIncomeMargin = self._remove_td(td_array[column_pos_array[k][3]])
                        afterTaxIncomeMargin = self._remove_td(td_array[column_pos_array[k][4]])
                    elif type == info.FS_type.SCF:
                        profitMargin2 = self._remove_td(td_array[column_pos_array[k][2]])
                    
                    if i > 1:
                        if name == "公司名稱":
                            continue
                        if type == info.FS_type.CPL:
                            data.append([name, code, revenue, profitRatio])
                        elif type == info.FS_type.SCF:
                            data.append([name, code, revenue, profitRatio, profitMargin2])
                        else:
                            data.append([name, code, revenue, profitRatio, profitMargin,
                                       preTaxIncomeMargin, afterTaxIncomeMargin])
                    if i == 1 and k == 0:
                        column.extend(["公司名稱", "公司代號", revenue, profitRatio])
                        if type == info.FS_type.BS:
                            column.extend([profitMargin, preTaxIncomeMargin, afterTaxIncomeMargin])
                        elif type == info.FS_type.SCF:
                            column.append(profitMargin2)

        return pd.DataFrame(data=data, columns=column)

    def _get_column_positions(self, year: int, type: info.FS_type, season: int) -> np.ndarray:
        """
        根據年份和報表類型獲取欄位位置
        
        Args:
            year: 年份
            type: 財報類型
            season: 季度
            
        Returns:
            欄位位置陣列
        """
        # 基礎欄位位置
        base_positions = np.array([
            [24, 42, 43, 52, 56],
            [5, 8, 9, 18, 22],
            [5, 8, 9, 18, 22],
            [25, 44, 45, 53, 57],
            [16, 34, 35, 44, 48],
            [5, 8, 9, 17, 21]
        ])
        
        # 根據年份調整
        if year <= 114:
            base_positions = np.array([
                [24, 42, 43, 53, 57],
                [5, 8, 9, 19, 23],
                [5, 8, 9, 19, 23],
                [25, 44, 45, 53, 57],
                [16, 34, 35, 45, 49],
                [5, 8, 9, 18, 22]
            ])
        if year == 109:
            if season == 1:
                base_positions = np.array([
                    [24, 42, 43, 52, 56],
                    [5, 8, 9, 18, 22],
                    [5, 8, 9, 18, 22],
                    [25, 44, 45, 53, 57],
                    [16, 34, 35, 44, 48],
                    [5, 8, 9, 17, 21]
                ])
            else:
                base_positions = np.array([
                    [24, 42, 43, 53, 57],
                    [5, 8, 9, 19, 23],
                    [5, 8, 9, 19, 23],
                    [25, 44, 45, 53, 57],
                    [16, 34, 35, 45, 49],
                    [5, 8, 9, 18, 22]
                ])
        if year == 108:
            base_positions = np.array([
                [24, 42, 43, 52, 56],
                [5, 8, 9, 18, 22],
                [5, 8, 9, 18, 22],
                [25, 44, 45, 53, 57],
                [16, 34, 35, 44, 48],
                [5, 8, 9, 17, 21]
            ])
        if year == 107:
            base_positions = np.array([
                [25, 42, 43, 52, 56],
                [5, 8, 9, 18, 22],
                [5, 8, 9, 18, 22],
                [26, 44, 45, 53, 57],
                [14, 32, 33, 42, 46],
                [5, 8, 9, 17, 21]
            ])
        if year == 106:
            base_positions = np.array([
                [23, 40, 41, 50, 54],
                [5, 8, 9, 17, 21],
                [5, 8, 9, 18, 22],
                [23, 41, 42, 50, 54],
                [14, 32, 33, 42, 46],
                [5, 8, 9, 17, 21]
            ])
        if year < 106:
            base_positions = np.array([
                [22, 39, 40, 49, 53],
                [5, 8, 9, 17, 21],
                [5, 8, 9, 18, 22],
                [23, 41, 42, 50, 54],
                [14, 32, 33, 42, 46],
                [5, 8, 9, 17, 21]
            ])
        if year < 103:
            base_positions = np.array([
                [22, 39, 40, 49, 52],
                [5, 8, 9, 17, 20],
                [5, 8, 9, 18, 21],
                [23, 41, 42, 50, 53],
                [14, 32, 33, 42, 45],
                [5, 8, 9, 17, 20]
            ])
        
        # 根據報表類型調整
        if type == info.FS_type.CPL:
            if year < 108:
                base_positions = np.array([[14, 21], [15, 22], [23, 30], [15, 22], [16, 23], [11, 18]])
            elif year < 106:
                base_positions = np.array([[14, 21], [15, 22], [21, 28], [15, 22], [16, 23], [11, 18]])
            elif year < 104:
                base_positions = np.array([[15, 22], [15, 22], [21, 28], [15, 22], [16, 23], [11, 18]])
            else:
                base_positions = np.array([[15, 22], [15, 22], [23, 30], [15, 22], [16, 23], [11, 18]])
        elif type == info.FS_type.SCF:
            base_positions = np.array([[3, 4, 5], [3, 4, 5], [3, 4, 5], [3, 4, 5], [3, 4, 5], [3, 4, 5]])
        
        return base_positions

    def _financial_statement(self, year: int, season: int, type: info.FS_type) -> None:
        """
        下載財務報表數據到本地文件
        
        Args:
            year: 年份
            season: 季度
            type: 財報類型
        """
        myear = year - 1911 if year >= 1000 else year

        # 根據不同的報表類型，選擇對應的URL
        url_mapping = {
            info.FS_type.CPL: "https://mopsov.twse.com.tw/mops/web/ajax_t163sb04",
            info.FS_type.BS: "https://mopsov.twse.com.tw/mops/web/ajax_t163sb05",
            info.FS_type.PLA: "https://mopsov.twse.com.tw/mops/web/ajax_t163sb06",
            info.FS_type.SCF: "https://mopsov.twse.com.tw/mops/web/ajax_t163sb20"
        }
        
        url = url_mapping.get(type)
        if not url:
            self._logger.error("Invalid financial statement type")
            return

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

        if type == info.FS_type.PLA:
            df = self._translate_dataFrame(response.text)
        else:
            df = self._translate_dataFrame2(response.text, type, myear, season)
            
        file = f"{year}-season{season}-{type.value}"
        df.to_csv(
            self._get_file_path('season', file) + ".csv",
            index=False,
        )
        # 偽停頓
        time.sleep(5)

    def _get_file_path(self, file_type: str, file_name: str) -> str:
        """獲取文件完整路徑"""
        return os.path.join(self._file_path, self._file_paths[file_type], file_name)

    def _get_cached_data(self, cache_key: str) -> Optional[pd.DataFrame]:
        """從快取獲取數據"""
        if not self._cache_service:
            return None

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
                self._logger.info(f"L1 緩存命中: {cache_key}")
                return df
            except Exception as e:
                self._logger.error(f"L1 緩存反序列化失敗: {e}")

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
            self._logger.info(f"L2 緩存命中: {cache_key}")
            return mongo_data

        return None

    def _save_to_cache(self, cache_key: str, data: pd.DataFrame) -> None:
        """保存數據到快取"""
        if not self._cache_service or data.empty:
            return

        try:
            # 更新 Redis L1 緩存
            index_list = [str(idx) for idx in data.index] if not data.index.equals(range(len(data))) else None
            cache_data = {
                'data': data.values.tolist(),
                'columns': data.columns.tolist(),
                'index': index_list
            }
            self._cache_service.set_redis_cache(cache_key, cache_data)

            # 更新 MongoDB L2 緩存
            self._cache_service.set_stock_data(cache_key, data)
            self._logger.info(f"已將數據存到混合緩存: {cache_key}")
        except Exception as e:
            self._logger.error(f"儲存數據到緩存失敗: {e}")
