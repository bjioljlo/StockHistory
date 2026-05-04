"""
Financial Statement Provider
Handles quarterly financial statement data operations

Part of TGetExternalData refactoring
"""
import os
from io import StringIO
from datetime import datetime
import pandas as pd
import logging

from src.Common import InfomationType as info
from src.SqlService import SqlService
from src.MongoService import MongoService
from src.ReadLoadSystem import ReadLoadSystem
from src.Common.CacheService import HybridCacheService
from src.Common import Tools


class FinancialStatementProvider:
    def __init__(self,
                 sql_service: SqlService,
                 mongo_service: MongoService,
                 read_load_system: ReadLoadSystem,
                 cache_service: HybridCacheService):
        self._sql_service = sql_service
        self._mongo_service = mongo_service
        self._read_load_system = read_load_system
        self._cache_service = cache_service
        self._logger = logging.getLogger(__name__)
        self._file_path = os.getcwd()

    def get_allstock_financial_statement(self, start: datetime, type: info.FS_type) -> pd.DataFrame:
        """
        Get all stock financial statements for specific quarter

        Args:
            start: Target date (any date in target quarter)
            type: Financial statement type

        Returns:
            DataFrame with financial statement data
        """
        self._logger.info(f"Getting {type} financial statement data: {start}")

        if not Tools.Have_DayRP(start):
            return pd.DataFrame()

        season = int(((start.month - 1) / 3) + 1)

        if not Tools.CheckFS_season(start):
            self._logger.warning("Season financial statement data not available yet")
            return pd.DataFrame()

        cache_key = f"financial_statement_{start.year}_{season}_{type.value}"
        file_name = f"{start.year}-season{season}-{type.value}"
        file_path = os.path.join(self._file_path, "seasonInfo", file_name)

        # 1. Get from cache first
        cached_data = self._cache_service.get(cache_key)
        if cached_data is not None:
            return cached_data

        # 2. Get from SQL database
        sql_data = self._get_financial_statement_from_sql(start, season, type)
        if not sql_data.empty:
            processed_data = self._process_financial_statement_data(sql_data, start, season, type)
            self._cache_service.set(cache_key, processed_data, ttl=86400)
            return processed_data

        # 3. Get from local file
        file_data = self._get_financial_statement_from_file(file_path, start, season, type)
        if not file_data.empty:
            processed_data = self._process_financial_statement_data(file_data, start, season, type)
            self._save_financial_statement_to_db(processed_data, type)
            self._cache_service.set(cache_key, processed_data, ttl=86400)
            return processed_data

        # 4. Download from external source
        self._financial_statement(start.year, season, type)
        self._logger.info(f"Downloaded {start.month} financial statement OK")

        crawler_data = pd.read_csv(f"{file_path}.csv")
        processed_data = self._process_financial_statement_data(crawler_data, start, season, type)
        self._save_financial_statement_to_db(processed_data, type)
        self._cache_service.set(cache_key, processed_data, ttl=86400)

        return processed_data

    def _get_financial_statement_from_sql(self, start: datetime, season: int, type: info.FS_type) -> pd.DataFrame:
        """Get financial statement data from SQL database"""
        try:
            with self._sql_service.server_flask.app_context():
                table_name = f"quarterly_reports"  # 固定表格名稱，包含所有季度報表資料
                query = f"""
                SELECT *
                FROM {table_name}
                WHERE report_year = :year AND report_season = :season AND report_type = :type
                """

                from sqlalchemy import text
                dataframe = pd.read_sql(
                    sql=text(query),
                    con=self._sql_service.MySql_server.engine,
                    params={
                        'year': start.year,
                        'season': season,
                        'type': type.name
                    },
                    index_col="id"
                )

                return dataframe
        except Exception as e:
            self._logger.error(f"SQL Error when getting {type} financial statement: {e}")
            return pd.DataFrame()

    def _process_financial_statement_data(self, data: pd.DataFrame, start: datetime, season: int, type: info.FS_type) -> pd.DataFrame:
        """Process and clean financial statement data"""
        if data.empty:
            return data

        # 加入報表年度與季度欄位
        data['report_year'] = start.year
        data['report_season'] = season
        data['statement_type'] = type.value

        # 財務報表欄位對應
        common_column_mapping = {
            '公司代號': 'symbol',
            '公司名稱': 'company_name',
            '會計年度': 'fiscal_year',
            '季度': 'fiscal_season'
        }

        # 不同財報類型的額外欄位對應
        type_specific_mapping = {}

        if type == info.FS_type.BS:
            type_specific_mapping = {
                '現金及約當現金': 'cash_and_equivalents',
                '應收帳款': 'accounts_receivable',
                '存貨': 'inventory',
                '流動資產': 'current_assets',
                '固定資產': 'fixed_assets',
                '資產總額': 'total_assets',
                '應付帳款': 'accounts_payable',
                '流動負債': 'current_liabilities',
                '長期負債': 'long_term_liabilities',
                '負債總額': 'total_liabilities',
                '股本': 'capital_stock',
                '保留盈餘': 'retained_earnings',
                '股東權益總額': 'total_equity'
            }
        elif type == info.FS_type.PLA:
            type_specific_mapping = {
                '營業收入': 'operating_revenue',
                '營業成本': 'operating_costs',
                '營業毛利': 'gross_profit',
                '營業費用': 'operating_expenses',
                '營業利益': 'operating_income',
                '營業外收入及支出': 'non_operating_income',
                '稅前淨利': 'income_before_tax',
                '所得稅費用': 'income_tax_expense',
                '稅後淨利': 'net_income',
                '每股盈餘': 'eps'
            }
        elif type == info.FS_type.SCF:
            type_specific_mapping = {
                '營業活動現金流量': 'cash_flow_from_operations',
                '投資活動現金流量': 'cash_flow_from_investing',
                '籌資活動現金流量': 'cash_flow_from_financing',
                '匯率變動影響數': 'exchange_rate_effects',
                '現金及約當現金增加數': 'net_change_in_cash',
                '期末現金及約當現金': 'ending_cash_and_equivalents'
            }

        # 合併欄位對應
        column_mapping = {**common_column_mapping, **type_specific_mapping}

        # 重新命名欄位
        for old_name, new_name in column_mapping.items():
            if old_name in data.columns:
                data = data.rename(columns={old_name: new_name})

        # 轉換數值欄位
        numeric_columns = [col for col in data.columns if col not in ['symbol', 'company_name', 'statement_type']]
        for col in numeric_columns:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')

        # 🔧 修正: 限制數值範圍避免 MySQL 溢位
        # ✅ 同時停用 pandas 科學記號表示法，避免大數字被轉成科學記號造成匯入失敗
        for col in data.columns:
            if pd.api.types.is_numeric_dtype(data[col]):
                data[col] = pd.to_numeric(data[col], errors='coerce')
                data[col] = data[col].clip(lower=-99999999999.99, upper=99999999999.99)

        # ✅ 全域停用 pandas 科學記號輸出
        pd.set_option('display.float_format', lambda x: f"{x:.10f}".rstrip('0').rstrip('.') if '.' in f"{x:.10f}" else f"{x:.10f}")

        return data

    def _get_financial_statement_from_file(self, filename: str, start: datetime, season: int, type: info.FS_type) -> pd.DataFrame:
        """Get financial statement data from local file"""
        try:
            file_path = f"{filename}.csv"
            if not os.path.exists(file_path):
                return pd.DataFrame()

            df = pd.read_csv(file_path)
            self._logger.debug(f"Read {len(df)} {type} records from file")
            return df
        except Exception as e:
            self._logger.error(f"File read error for {type} statement: {e}")
            return pd.DataFrame()

    def _save_financial_statement_to_db(self, data: pd.DataFrame, type: info.FS_type) -> None:
        """Save financial statement data to database"""
        if data.empty:
            return

        try:
            table_name = "quarterly_reports"

            # 取得資料庫表格欄位
            table_columns = [col['name'] for col in self._sql_service.get_table_columns(table_name)]
            # 只保留資料庫表格中存在的欄位
            df_to_insert = data[[col for col in data.columns if col in table_columns]]

            if df_to_insert.empty:
                self._logger.warning(f"No valid columns found in dataframe for table {table_name}")
                return

            self._logger.info(f"Upserting {len(df_to_insert)} {type} records with columns: {list(df_to_insert.columns)}")

            # 使用 upsert 原子性操作
            # 唯一鍵: 股票代號 + 報表年度 + 報表季度
            success = self._sql_service.upsert_data(
                table_name=table_name,
                data_df=df_to_insert,
                key_columns=['symbol', 'report_year', 'report_season']
            )

            if not success:
                self._logger.error(f"Failed to save {type} financial statement to database")

            report_year = int(data.iloc[0]['report_year'])
            report_season = int(data.iloc[0]['report_season'])
            self._logger.info(f"Saved {len(df_to_insert)} {type} financial statement records for {report_year} Q{report_season}")
        except Exception as e:
            self._logger.error(f"Error saving {type} financial statement to database: {e}")

    def _financial_statement(self, year: int, season: int, type: info.FS_type) -> None:
        """Download financial statement data from external source"""
        try:
            # 轉換為民國年
            roc_year = year - 1911 if year > 1990 else year

            # 對應不同財報類型的 URL 路徑
            type_paths = {
                info.FS_type.BALANCE_SHEET: 'bps',
                info.FS_type.INCOME_STATEMENT: 'is',
                info.FS_type.CASH_FLOW: 'cf'
            }

            report_type = type_paths.get(type, 'is')

            # ✅ 2026/04 TWSE 最新公開資訊觀測站網址
            url = f"https://mopsov.twse.com.tw/server-java/t164sb01?step=1&CO_ID=&SYEAR={roc_year}&SSEASON={season}&REPORT_ID={report_type}"

            import requests
            import time

            # 重試機制
            max_retries = 3
            retry_delay = 3

            for attempt in range(max_retries):
                try:
                    r = requests.get(url, headers=Tools.get_random_headers(), timeout=45)
                    r.raise_for_status()
                    break
                except requests.exceptions.RequestException as e:
                    self._logger.warning(f"Download attempt {attempt+1} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                    else:
                        raise

            time.sleep(0.8)

            # 編碼處理
            for encoding in ['big5', 'cp950', 'big5-hkscs', 'utf-8']:
                try:
                    r.encoding = encoding
                    test_text = r.text
                    break
                except LookupError:
                    continue

            # 解析 HTML 表格
            dfs = pd.read_html(StringIO(r.text))

            # 尋找正確的資料表格 (通常是第2個表格)
            if len(dfs) >= 2:
                df = dfs[1]
            else:
                df = dfs[0]

            # 處理多層次欄位名稱
            if hasattr(df.columns, 'levels') and len(df.columns.levels) > 1:
                df.columns = df.columns.get_level_values(-1)

            # 儲存到檔案
            file_name = f"{year}-season{season}-{type.value}"
            file_path = os.path.join(self._file_path, "seasonInfo", f"{file_name}.csv")
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            df.to_csv(file_path, index=False)

            self._logger.info(f"Downloaded {type} financial statement: {year} Q{season}")

        except Exception as e:
            self._logger.error(f"Download error for {type} statement {year} Q{season}: {e}")
            raise
