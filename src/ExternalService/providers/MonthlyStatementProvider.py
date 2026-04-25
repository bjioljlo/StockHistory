"""
Monthly Statement Provider
Handles monthly revenue report operations

Part of TGetExternalData refactoring
"""
from io import StringIO
import os
from datetime import datetime
import pandas as pd
import logging

from src.SqlService import SqlService
from src.MongoService import MongoService
from src.ReadLoadSystem import ReadLoadSystem
from src.Common.CacheService import HybridCacheService
from src.Common import Tools


class MonthlyStatementProvider:
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

    def get_allstock_monthly_statement(self, start: datetime) -> pd.DataFrame:
        """
        Get all stock monthly revenue statement

        Args:
            start: Target month date

        Returns:
            DataFrame with monthly revenue data
        """
        self._logger.info(f"Getting monthly statement data: {start}")

        if not Tools.Have_MonthRP(start):
            return pd.DataFrame()

        cache_key = f"monthly_statement_{start.year}_{start.month}"
        file_name = f"{start.year}-{start.month}"
        file_path = f"{self._file_path}/monthRP/{file_name}"

        # 1. Get from cache first
        cached_data = self._cache_service.get(cache_key)
        if cached_data is not None:
            self._logger.debug(f"Cache HIT for {cache_key}")
            return cached_data

        # 2. Get from SQL database
        sql_data = self._get_monthly_statement_from_sql(start)
        if not sql_data.empty:
            self._logger.debug(f"Loaded from SQL database")
            processed_data = self._process_monthly_statement_data(sql_data, start)
            self._cache_service.set(cache_key, processed_data, ttl=86400)
            return processed_data

        # 3. Get from local file
        file_data = self._get_monthly_statement_from_file(file_path, start)
        if not file_data.empty:
            self._logger.debug(f"Loaded from local file")
            processed_data = self._process_monthly_statement_data(file_data, start)
            self._save_monthly_statement_to_db(processed_data)
            self._cache_service.set(cache_key, processed_data, ttl=86400)
            return processed_data

        # 4. Download from external source
        self._monthly_statement(start.year, start.month)
        self._logger.info(f"Downloaded {start.month} monthly statement OK")

        crawler_data = pd.read_csv(f"{file_path}.csv")
        processed_data = self._process_monthly_statement_data(crawler_data, start)
        self._save_monthly_statement_to_db(processed_data)
        self._cache_service.set(cache_key, processed_data, ttl=86400)

        return processed_data

    def get_allstock_monthly_report(self, start: datetime) -> pd.DataFrame:
        """Legacy method for backward compatibility"""
        return self.get_allstock_monthly_statement(start)

    def _get_monthly_statement_from_sql(self, start: datetime) -> pd.DataFrame:
        """Get monthly statement data from SQL database"""
        try:
            with self._sql_service.server_flask.app_context():
                query = """
                SELECT code, year, month, revenue, revenue_change,
                       cumulative_revenue, cumulative_change
                FROM monthly_revenue
                WHERE year = :year AND month = :month
                """

                from sqlalchemy import text
                dataframe = pd.read_sql(
                    sql=text(query),
                    con=self._sql_service.MySql_server.engine,
                    params={
                        'year': start.year,
                        'month': start.month
                    },
                    index_col="code"
                )

                return dataframe
        except Exception as e:
            self._logger.error(f"SQL Error when getting monthly statement: {e}")
            return pd.DataFrame()

    def _process_monthly_statement_data(self, data: pd.DataFrame, start: datetime) -> pd.DataFrame:
        """Process and clean monthly statement data"""
        if data.empty:
            return data

        # ✅ 完全對齊 migration/migrate_reports_data.py 的欄位定義
        data['report_year'] = start.year
        data['report_month'] = start.month

        # ✅ 使用與migrate_reports_data.py完全相同的欄位對應
        column_mapping = {
            '公司代號': 'symbol',
            '公司名稱': 'company_name',
            '當月營收': 'revenue_current_month',
            '上月營收': 'revenue_last_month',
            '去年當月營收': 'revenue_last_year_same_month',
            '當月累計營收': 'revenue_ytd',
            '去年累計營收': 'revenue_last_year_ytd',
            '備註': 'notes'
        }

        # Rename columns if they exist
        for old_name, new_name in column_mapping.items():
            if old_name in data.columns:
                data = data.rename(columns={old_name: new_name})

        # Convert numeric columns to proper types
        numeric_columns = ['revenue_current_month', 'revenue_last_month', 'revenue_last_year_same_month', 'revenue_ytd', 'revenue_last_year_ytd']
        for col in numeric_columns:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')

        # ✅ 統一設定 index 為 symbol 欄位
        if 'symbol' in data.columns:
            data = data.set_index('symbol', drop=True)

        return data

    def _get_monthly_statement_from_file(self, filename: str, start: datetime) -> pd.DataFrame:
        """Get monthly statement data from local file"""
        try:
            file_path = f"{filename}.csv"
            if not os.path.exists(file_path):
                return pd.DataFrame()

            df = pd.read_csv(file_path)
            self._logger.debug(f"Read {len(df)} records from file")
            return df
        except Exception as e:
            self._logger.error(f"File read error: {e}")
            return pd.DataFrame()

    def _save_monthly_statement_to_db(self, data: pd.DataFrame) -> None:
        """Save monthly statement data to database"""
        if data.empty:
            return

        try:
            # ✅ 正確的儲存方式: 使用upsert_data不會清空整張表格
            # 先刪除同一月份舊資料再新增，或是使用upsert處理重複
            save_data = data.reset_index()
            
            # 先刪除同一月份的舊資料 (只刪該月份，不會清空整張表)
            with self._sql_service.server_flask.app_context():
                delete_query = text("DELETE FROM monthly_reports WHERE report_year = :year AND report_month = :month")
                self._sql_service.MySql_server.engine.execute(
                    delete_query,
                    {'year': save_data['report_year'].iloc[0], 'month': save_data['report_month'].iloc[0]}
                )
                
                # 再新增新資料，使用append不會覆蓋其他月份
                save_data.to_sql(
                    name='monthly_reports',
                    con=self._sql_service.MySql_server.engine,
                    if_exists='append',
                    index=False
                )
            
            self._logger.info(f"Saved {len(data)} monthly revenue records to database (只更新該月份)")
        except Exception as e:
            self._logger.error(f"Error saving monthly statement to database: {e}")

    def _monthly_statement(self, year: int, month: int) -> None:
        """Download monthly statement data from external source"""
        try:
            # Convert to ROC year if needed
            roc_year = year - 1911 if year > 1990 else year

            # ✅ 2026/04 更新: TWSE 最新網域 2026/4/23 起啟用新網站
            # 新主機: mopsov.twse.com.tw，格式恢復舊有命名規則
            url = f"https://mopsov.twse.com.tw/nas/t21/sii/t21sc03_{roc_year}_{month}_0.html"

            # Download page
            import requests
            import time

            # TWSE 伺服器有連線限制，加入延遲與重試機制
            max_retries = 3
            retry_delay = 2

            for attempt in range(max_retries):
                try:
                    r = requests.get(url, headers=Tools.get_random_headers(), timeout=30)
                    r.raise_for_status()
                    break
                except requests.exceptions.RequestException as e:
                    self._logger.warning(f"Download attempt {attempt+1} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                    else:
                        raise

            # 增加延遲避免被伺服器阻擋
            time.sleep(0.5)

            # Correct encoding handling (fix unknown encoding: big-5 error)
            # Use standard encoding names without dash, with fallback options
            for encoding in ['big5', 'cp950', 'big5-hkscs', 'utf-8']:
                try:
                    r.encoding = encoding
                    test_text = r.text
                    break
                except LookupError:
                    continue

            # Parse HTML tables (no need to specify encoding again as text is already decoded)
            dfs = pd.read_html(StringIO(r.text))

            # Find correct table
            df = pd.concat([df for df in dfs if df.shape[1] <= 11 and df.shape[1] > 5])

            if "levels" in dir(df.columns):
                df.columns = df.columns.get_level_values(1)

            # ✅ 2026/04 新網站欄位名稱修正
            # 新網站的公司代號欄位現在有空格
            column_renames = {
                "公司 代號": "公司代號",
                "公司 名稱": "公司名稱",
                "當月 營收": "當月營收",
                "上月比較 增減(%)": "上月比較增減(%)",
                "去年同月 增減(%)": "去年同月增減(%)",
                "累計當月 營收": "累計當月營收",
                "累計 增減(%)": "累計增減(%)"
            }

            df = df.rename(columns=column_renames)

            # Save to file
            file_path = f"{self._file_path}/monthRP/{year}-{month}.csv"
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            df.to_csv(file_path, index=False)

            self._logger.info(f"Downloaded monthly statement: {year}-{month}")

        except Exception as e:
            self._logger.error(f"Download error: {e}")
            raise
