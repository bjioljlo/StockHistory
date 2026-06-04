"""
Financial Statement Provider
Handles quarterly financial statement data operations

Part of TGetExternalData refactoring
"""
import os
import re
from io import StringIO
from datetime import datetime
import pandas as pd
import logging

from src.Common import InfomationType as info
from pydb_core.field_mapping import FieldMapping
from pydb_core.sql_service import SqlService
from pydb_core.mongo_service import MongoService
from pydb_core.read_load_system import ReadLoadSystem
from pydb_core.cache_service import HybridCacheService
from src.Common import Tools
from src.ExternalService.providers.crawlers.base_crawler import BaseFinancialCrawler
from src.ExternalService.providers.crawlers.bs_crawler import BsCrawler
from src.ExternalService.providers.crawlers.cpl_crawler import CplCrawler
from src.ExternalService.providers.crawlers.scf_crawler import ScfCrawler
from src.ExternalService.providers.crawlers.pla_crawler import PlaCrawler


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
        # 初始化各報表類型專用爬蟲
        self._crawlers = {
            info.FS_type.BS: BsCrawler(),
            info.FS_type.CPL: CplCrawler(),
            info.FS_type.SCF: ScfCrawler(),
            info.FS_type.PLA: PlaCrawler(),
        }

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
            # 只在有有效數值資料時才寫入 Redis，避免空白資料被快取後永不爬蟲更新
            if self._has_valid_financial_data(processed_data):
                self._cache_service.set(cache_key, processed_data, ttl=86400)
                return processed_data
            else:
                self._logger.warning("SQL returned empty/nan data for %s %d Q%d, skipping cache and trying crawler", type.name, start.year, season)
                # 不 return，繼續嘗試爬蟲下載

        # 3. Get from local file
        file_data = self._get_financial_statement_from_file(file_path, start, season, type)
        if not file_data.empty:
            processed_data = self._process_financial_statement_data(file_data, start, season, type)
            if self._has_valid_financial_data(processed_data):
                self._save_financial_statement_to_db(processed_data, type)
                self._cache_service.set(cache_key, processed_data, ttl=86400)
                return processed_data
            else:
                self._logger.warning("File data is empty/nan for %s %d Q%d, skipping cache and trying crawler", type.name, start.year, season)

        # 4. Download from external source using dedicated crawler
        crawler_df = self._financial_statement_download(start.year, season, type)
        if crawler_df.empty:
            self._logger.error(
                "Failed to download %s statement for %d Q%d",
                type.name, start.year, season
            )
            return pd.DataFrame()

        processed_data = self._process_financial_statement_data(crawler_df, start, season, type)
        self._save_financial_statement_to_db(processed_data, type)
        self._cache_service.set(cache_key, processed_data, ttl=86400)

        return processed_data

    def _has_valid_financial_data(self, data: pd.DataFrame) -> bool:
        """檢查 DataFrame 中是否包含有效的數值資料（非全部 NaN/空白）。

        Args:
            data: 財務報表 DataFrame

        Returns:
            True 如果有任何有效的數值資料，False 如果全部為 NaN 或空白
        """
        if data is None or data.empty:
            return False

        # 排除非數值欄位（symbol, company_name, statement_type 等）
        numeric_cols = data.select_dtypes(include=['number']).columns
        if numeric_cols.empty:
            return False

        # 檢查是否有任何非 NaN 的數值
        for col in numeric_cols:
            if data[col].notna().any():
                return True

        return False

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

    def _normalize_column_name(self, column_name: str) -> str:
        raw_name = str(column_name).strip()
        raw_name = raw_name.replace('　', ' ').replace('％', '%').replace('／', '/')
        raw_name = re.sub(r'\s+', ' ', raw_name).strip()

        alias_map = {
            '毛利率/': '毛利率(%)',
            '營業利益率/': '營業利益率(%)',
            '稅前純益率/': '稅前純益率(%)',
            '稅後純益率/': '稅後純益率(%)',
            '稅後 純益率/': '稅後純益率(%)',
            '股東權益總額': '權益總額',
            '稅前淨利': '稅前純益',
            '營業活動現金流量': '營業活動之淨現金流入（流出）',
            '投資活動現金流量': '投資活動之淨現金流入（流出）',
            '籌資活動現金流量': '籌資活動之淨現金流入（流出）',
        }

        if raw_name in alias_map:
            return alias_map[raw_name]

        if FieldMapping.get_sql_column(raw_name) is not None:
            return raw_name

        normalized = re.sub(r'\s*\([^)]*\)', '', raw_name).strip()
        normalized = re.sub(r'\s*（[^）]*）', '', normalized).strip()
        normalized = normalized.rstrip('/').strip()
        return normalized

    def _load_reference_csv_columns(self, year: int, season: int, fs_type: info.FS_type) -> list[str]:
        reference_file = os.path.join(self._file_path, "seasonInfo", f"{year}-season{season}-{fs_type.value}.csv")
        if not os.path.exists(reference_file):
            return []

        try:
            reference_df = pd.read_csv(reference_file, nrows=0)
            return list(reference_df.columns)
        except Exception:
            return []

    def _filter_data_by_reference_columns(
        self,
        data: pd.DataFrame,
        year: int,
        season: int,
        fs_type: info.FS_type,
    ) -> pd.DataFrame:
        reference_columns = self._load_reference_csv_columns(year, season, fs_type)
        if not reference_columns:
            return data

        common_name_map = {
            '公司代號': 'symbol',
            '公司名稱': 'company_name',
            '會計年度': 'fiscal_year',
            '季度': 'fiscal_season'
        }

        keep_columns = []
        for ref_col in reference_columns:
            if ref_col in data.columns:
                target_column = ref_col
            elif ref_col in common_name_map and common_name_map[ref_col] in data.columns:
                target_column = common_name_map[ref_col]
            else:
                mapped_column = FieldMapping.get_sql_column(ref_col, fs_type.name)
                target_column = mapped_column if mapped_column and mapped_column in data.columns else None

            if target_column and target_column not in keep_columns:
                keep_columns.append(target_column)

        for extra in ['symbol', 'company_name', 'report_year', 'report_season', 'report_type']:
            if extra in data.columns and extra not in keep_columns:
                keep_columns.append(extra)

        if not keep_columns:
            return data

        return data.loc[:, keep_columns]

    def _process_financial_statement_data(self, data: pd.DataFrame, start: datetime, season: int, type: info.FS_type) -> pd.DataFrame:
        """Process and clean financial statement data"""
        if data.empty:
            return data

        # 加入報表年度與季度欄位
        data['report_year'] = start.year
        data['report_season'] = season
        data['report_type'] = type.name

        # Normalize column names by removing unit annotations, slashes, and variant labels.
        normalized_columns = {}
        for col in data.columns:
            if isinstance(col, str):
                normalized_name = self._normalize_column_name(col)
                normalized_columns[col] = normalized_name
        if normalized_columns:
            data = data.rename(columns=normalized_columns)

        # 財務報表欄位對應
        common_column_mapping = {
            '公司代號': 'symbol',
            '公司名稱': 'company_name',
            '會計年度': 'fiscal_year',
            '季度': 'fiscal_season'
        }

        # 不同財報類型的額外欄位對應
        type_specific_mapping = {}
        if type.name in FieldMapping.ALL_MAPPINGS:
            type_specific_mapping = FieldMapping.get_all_mappings(type.name)

        # 合併欄位對應
        column_mapping = {**common_column_mapping, **type_specific_mapping}

        # 重新命名欄位
        for old_name, new_name in column_mapping.items():
            if old_name in data.columns:
                data = data.rename(columns={old_name: new_name})

        data = self._filter_data_by_reference_columns(data, start.year, season, type)

        # 轉換數值欄位
        numeric_columns = [col for col in data.columns if col not in ['symbol', 'company_name', 'report_type']]
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

    def _get_crawler(self, fs_type: info.FS_type) -> BaseFinancialCrawler:
        """Get the appropriate crawler for the given financial statement type.

        Args:
            fs_type: Financial statement type

        Returns:
            Crawler instance for the specified report type
        """
        return self._crawlers[fs_type]

    def _financial_statement_download(
        self, year: int, season: int, fs_type: info.FS_type
    ) -> pd.DataFrame:
        """Download financial statement using the appropriate dedicated crawler.

        Args:
            year: Western calendar year
            season: Quarter number (1-4)
            fs_type: Financial statement type

        Returns:
            DataFrame with parsed data, or empty DataFrame on failure
        """
        crawler = self._get_crawler(fs_type)
        result = crawler.download(year, season)

        if not result.success:
            self._logger.error(
                "Failed to download %s statement for %d Q%d",
                fs_type.name, year, season
            )
            return pd.DataFrame()

        # Save to local file
        file_name = f"{year}-season{season}-{fs_type.value}"
        file_path = os.path.join(self._file_path, "seasonInfo", f"{file_name}.csv")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        result.df.to_csv(file_path, index=False, encoding='utf-8-sig')

        self._logger.info(
            "Downloaded %s statement: %d Q%d (%d rows)",
            fs_type.name, year, season, len(result.df)
        )
        return result.df

    def _financial_statement(self, year: int, season: int, type: info.FS_type) -> None:
        """Download financial statement data from external source (deprecated).

        .. deprecated::
            Use _financial_statement_download() instead, which delegates
            to dedicated crawler classes per report type.
        """
        crawler_data = self._financial_statement_download(year, season, type)
        if crawler_data.empty:
            self._logger.error("Legacy _financial_statement failed for %s %d Q%d", type.name, year, season)
            raise RuntimeError(f"Failed to download {type.name} for {year} Q{season}")
        self._logger.info("Legacy _financial_statement completed via crawler: %d rows", len(crawler_data))
