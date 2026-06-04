#!/usr/bin/env python3
"""
股票報告數據遷移工具

此腳本用於將分散的CSV檔案中的股息殖利率、月報、季報數據
遷移到統一的MySQL資料庫表格中。

使用方法:
python migrate_reports_data.py --type dividend_yield --start-date 2024-01-01 --end-date 2024-12-31
python migrate_reports_data.py --type monthly_reports --start-year 2023 --end-year 2024
python migrate_reports_data.py --type quarterly_reports --start-year 2023 --end-year 2024
python migrate_reports_data.py --validate dividend_yield
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd
from sqlalchemy import create_engine, text, inspect
import yaml

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from pyutils_core.config import load_config, get_config_path

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ReportDataMigrator:
    """股票報告數據遷移器"""

    def __init__(self, config_path: str = None):
        """初始化遷移器"""
        self.config = load_config(config_path or get_config_path())
        self.db_config = self.config.get('database', {})
        self.data_config = self.config.get('data', {})

        # 建立資料庫連接
        db_uri = self._build_db_uri()
        self.engine = create_engine(db_uri, echo=False)

        # 批次處理大小 - 季報使用較小的批次以避免記憶體問題
        self.batch_size = self.config.get('migration', {}).get('batch_size', 500)

        # 數據目錄配置
        self.yield_dir = self.data_config.get('yield_dir', 'yieldInfo')
        self.month_dir = self.data_config.get('month_dir', 'monthRP')
        self.season_dir = self.data_config.get('season_dir', 'seasonInfo')

        logger.info("ReportDataMigrator initialized successfully")

    def _build_db_uri(self) -> str:
        """建構資料庫URI"""
        db_type = self.db_config.get('type', 'mysql')

        if db_type == 'mysql':
            mysql_config = self.db_config.get('mysql', {})
            user = mysql_config.get('user')
            password = mysql_config.get('password')
            host = mysql_config.get('host', 'localhost')
            port = mysql_config.get('port', 3306)
            database = mysql_config.get('databasename')

            return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?local_infile=1"

        elif db_type == 'sqlite':
            path = self.db_config.get('sqlite', {}).get('path', 'default.db')
            return f"sqlite:///{path}"

        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    def migrate_dividend_yield(self, start_date: str = None, end_date: str = None,
                              dry_run: bool = False) -> Dict[str, Any]:
        """遷移股息殖利率數據"""
        logger.info(f"Starting dividend yield migration from {start_date} to {end_date}")

        csv_files = self._get_csv_files(self.yield_dir, 'dividend_yield', start_date, end_date)
        logger.info(f"Found {len(csv_files)} dividend yield CSV files")

        total_processed = 0
        total_inserted = 0
        errors = []

        for csv_file in csv_files:
            try:
                logger.info(f"Processing {csv_file}")

                # 讀取CSV檔案，嘗試多種編碼
                df = self._read_csv_with_encoding_detection(csv_file)

                # 數據清理和轉換
                df_cleaned = self._clean_dividend_yield_data(df, csv_file)

                if not df_cleaned.empty:
                    if not dry_run:
                        # 批次插入資料庫
                        inserted = self._batch_insert('dividend_yield', df_cleaned)
                        total_inserted += inserted
                        logger.info(f"Inserted {inserted} records from {csv_file}")
                    else:
                        total_inserted += len(df_cleaned)
                        logger.info(f"Would insert {len(df_cleaned)} records from {csv_file} (dry run)")

                total_processed += 1

            except Exception as e:
                error_msg = f"Error processing {csv_file}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        result = {
            'files_processed': total_processed,
            'records_inserted': total_inserted,
            'errors': errors,
            'success': len(errors) == 0
        }

        logger.info(f"Migration completed: {result}")
        return result

    def migrate_monthly_reports(self, start_year: int = None, end_year: int = None,
                               dry_run: bool = False) -> Dict[str, Any]:
        """遷移月報數據"""
        logger.info(f"Starting monthly reports migration from year {start_year} to {end_year}")

        csv_files = self._get_csv_files(self.month_dir, 'monthly_report', start_year, end_year)
        logger.info(f"Found {len(csv_files)} monthly report CSV files")

        total_processed = 0
        total_inserted = 0
        errors = []

        for csv_file in csv_files:
            try:
                logger.info(f"Processing {csv_file}")

                df = pd.read_csv(csv_file, encoding='utf-8')
                df_cleaned = self._clean_monthly_report_data(df, csv_file)

                if not df_cleaned.empty:
                    if not dry_run:
                        inserted = self._batch_insert('monthly_reports', df_cleaned)
                        total_inserted += inserted
                        logger.info(f"Inserted {inserted} records from {csv_file}")
                    else:
                        total_inserted += len(df_cleaned)
                        logger.info(f"Would insert {len(df_cleaned)} records from {csv_file} (dry run)")

                total_processed += 1

            except Exception as e:
                error_msg = f"Error processing {csv_file}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        result = {
            'files_processed': total_processed,
            'records_inserted': total_inserted,
            'errors': errors,
            'success': len(errors) == 0
        }

        logger.info(f"Migration completed: {result}")
        return result

    def migrate_quarterly_reports(self, start_year: int = None, end_year: int = None,
                                 dry_run: bool = False, quarterly_type: str = None) -> Dict[str, Any]:
        """遷移季報數據"""
        logger.info(f"Starting quarterly reports migration from year {start_year} to {end_year}")
        if quarterly_type:
            logger.info(f"Processing specific quarterly type: {quarterly_type}")
        else:
            logger.info("Processing all quarterly report types: PLA, BS, CPL, SCF")

        total_processed = 0
        total_inserted = 0
        errors = []

        # 根據參數決定處理的報表類型
        if quarterly_type:
            report_types = [quarterly_type]
        else:
            report_types = ['PLA', 'BS', 'CPL', 'SCF']

        # 映射文件類型到實際的文件名模式
        type_mapping = {
            'PLA': 'profit-and-loss-analysis-summary',
            'BS': 'balance-sheet',
            'CPL': 'consolidated-profit-and-loss-summary',
            'SCF': 'statement-of-cash-flows'
        }

        for report_type in report_types:
            logger.info(f"Processing {report_type} reports")
            file_pattern = type_mapping.get(report_type, report_type)
            csv_files = self._get_csv_files(self.season_dir, f'season.*{file_pattern}', start_year, end_year)

            for csv_file in csv_files:
                try:
                    logger.info(f"Processing {csv_file}")

                    # 使用編碼檢測讀取季報文件
                    df = self._read_csv_with_encoding_detection(csv_file)
                    df_cleaned = self._clean_quarterly_report_data(df, csv_file, report_type)

                    if not df_cleaned.empty:
                        if not dry_run:
                            inserted = self._batch_insert('quarterly_reports', df_cleaned)
                            total_inserted += inserted
                            logger.info(f"Inserted {inserted} records from {csv_file}")
                        else:
                            total_inserted += len(df_cleaned)
                            logger.info(f"Would insert {len(df_cleaned)} records from {csv_file} (dry run)")

                    total_processed += 1

                except Exception as e:
                    error_msg = f"Error processing {csv_file}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

        result = {
            'files_processed': total_processed,
            'records_inserted': total_inserted,
            'errors': errors,
            'success': len(errors) == 0
        }

        logger.info(f"Migration completed: {result}")
        return result

    def validate_migration(self, table_name: str) -> Dict[str, Any]:
        """驗證遷移結果"""
        logger.info(f"Validating migration for table: {table_name}")

        try:
            with self.engine.connect() as conn:
                # 檢查資料完整性
                result = conn.execute(text(f"SELECT COUNT(*) as total FROM {table_name}"))
                total_count = result.fetchone()[0]

                # 檢查重複資料
                if table_name == 'dividend_yield':
                    duplicate_query = """
                        SELECT symbol, date, COUNT(*) as count
                        FROM dividend_yield
                        GROUP BY symbol, date
                        HAVING COUNT(*) > 1
                    """
                elif table_name == 'monthly_reports':
                    duplicate_query = """
                        SELECT symbol, report_year, report_month, COUNT(*) as count
                        FROM monthly_reports
                        GROUP BY symbol, report_year, report_month
                        HAVING COUNT(*) > 1
                    """
                elif table_name == 'quarterly_reports':
                    duplicate_query = """
                        SELECT symbol, report_year, report_season, report_type, COUNT(*) as count
                        FROM quarterly_reports
                        GROUP BY symbol, report_year, report_season, report_type
                        HAVING COUNT(*) > 1
                    """
                else:
                    return {'error': f'Unknown table: {table_name}'}

                result = conn.execute(text(duplicate_query))
                duplicates = result.fetchall()

                # 基本統計
                stats_query = f"""
                    SELECT
                        COUNT(DISTINCT symbol) as unique_symbols,
                        MIN(created_at) as earliest_record,
                        MAX(created_at) as latest_record
                    FROM {table_name}
                """
                result = conn.execute(text(stats_query))
                stats = result.fetchone()

                validation_result = {
                    'table_name': table_name,
                    'total_records': total_count,
                    'unique_symbols': stats[0] if stats else 0,
                    'earliest_record': str(stats[1]) if stats and stats[1] else None,
                    'latest_record': str(stats[2]) if stats and stats[2] else None,
                    'duplicates': len(duplicates),
                    'duplicate_details': [{'symbol': d[0], 'period': str(d[1]) if len(d) > 2 else f"{d[1]}-{d[2]}", 'count': d[-1]} for d in duplicates[:10]],  # 只顯示前10個重複
                    'status': 'valid' if len(duplicates) == 0 else 'has_duplicates'
                }

                logger.info(f"Validation result: {validation_result}")
                return validation_result

        except Exception as e:
            error_msg = f"Validation failed: {str(e)}"
            logger.error(error_msg)
            return {'error': error_msg}

    def create_tables_if_not_exists(self):
        """建立必要的資料表格（如果不存在）"""
        logger.info("Creating tables if they don't exist")

        table_creation_queries = [
            # 股息殖利率表格
            """
            CREATE TABLE IF NOT EXISTS dividend_yield (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL COMMENT '股票代號',
                date DATE NOT NULL COMMENT '資料日期',
                company_name VARCHAR(100) COMMENT '公司名稱',
                pe_ratio DECIMAL(10,2) COMMENT '本益比',
                dividend_yield DECIMAL(5,2) COMMENT '殖利率(%)',
                pb_ratio DECIMAL(10,2) COMMENT '股價淨值比',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

                UNIQUE KEY unique_symbol_date (symbol, date),
                INDEX idx_symbol (symbol),
                INDEX idx_date (date),
                INDEX idx_symbol_date (symbol, date),
                INDEX idx_dividend_yield (dividend_yield),
                INDEX idx_pe_ratio (pe_ratio)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,

            # 月報表格
            """
            CREATE TABLE IF NOT EXISTS monthly_reports (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL COMMENT '股票代號',
                company_name VARCHAR(100) COMMENT '公司名稱',
                report_year INT NOT NULL COMMENT '報表年份',
                report_month INT NOT NULL COMMENT '報表月份',
                revenue_current_month BIGINT COMMENT '當月營收',
                revenue_last_month BIGINT COMMENT '上月營收',
                revenue_last_year_same_month BIGINT COMMENT '去年當月營收',
                revenue_ytd BIGINT COMMENT '當月累計營收',
                revenue_last_year_ytd BIGINT COMMENT '去年累計營收',
                revenue_growth_rate DECIMAL(5,2) COMMENT '上月比較增減(%)',
                revenue_last_year_same_month_growth_rate DECIMAL(5,2) COMMENT '去年同月增減(%)',
                notes TEXT COMMENT '備註',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

                UNIQUE KEY unique_symbol_period (symbol, report_year, report_month),
                INDEX idx_symbol (symbol),
                INDEX idx_period (report_year, report_month),
                INDEX idx_symbol_period (symbol, report_year, report_month),
                INDEX idx_revenue_current_month (revenue_current_month),
                INDEX idx_revenue_ytd (revenue_ytd)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,

            # 季報表格 - 更新以支持PLA和CPL的不同欄位
            """
            CREATE TABLE IF NOT EXISTS quarterly_reports (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL COMMENT '股票代號',
                company_name VARCHAR(100) COMMENT '公司名稱',
                report_year INT NOT NULL COMMENT '報表年份',
                report_season INT NOT NULL COMMENT '報表季別(1-4)',
                report_type ENUM('PLA', 'BS', 'CPL', 'SCF') NOT NULL COMMENT '報表類型',

                    revenue BIGINT COMMENT '營業收入',
                    gross_margin DECIMAL(10,2) COMMENT '毛利率(%)',
                    operating_margin DECIMAL(10,2) COMMENT '營業利益率(%)',
                    pre_tax_margin DECIMAL(10,2) COMMENT '稅前純益率(%)',
                    net_margin DECIMAL(10,2) COMMENT '稅後純益率(%)',

                    consolidated_net_income BIGINT COMMENT '合併淨利',
                    consolidated_eps DECIMAL(5,2) COMMENT '每股盈餘',

                    total_assets BIGINT COMMENT '總資產',
                    total_liabilities BIGINT COMMENT '總負債',
                    equity BIGINT COMMENT '股東權益',
                    capital BIGINT COMMENT '股本',
                    book_value_per_share DECIMAL(10,2) COMMENT '每股參考淨值',

                    operating_cash_flow BIGINT COMMENT '營業現金流量',
                    investing_cash_flow BIGINT COMMENT '投資現金流量',
                    financing_cash_flow BIGINT COMMENT '融資現金流量',

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

                    UNIQUE KEY unique_symbol_period_type (symbol, report_year, report_season, report_type),
                    INDEX idx_symbol (symbol),
                    INDEX idx_period (report_year, report_season),
                    INDEX idx_type (report_type),
                    INDEX idx_symbol_period (symbol, report_year, report_season),
                    INDEX idx_revenue (revenue),
                    INDEX idx_net_margin (net_margin),
                    INDEX idx_consolidated_net_income (consolidated_net_income)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """
            ]

        try:
            with self.engine.connect() as conn:
                for query in table_creation_queries:
                    conn.execute(text(query))
                    conn.commit()
                logger.info("Tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise

    def _batch_insert(self, table_name: str, df: pd.DataFrame) -> int:
        """批次插入資料 - 改進版：更好的錯誤處理"""
        if df.empty:
            return 0

        try:
            # 確保所有欄位都存在於資料庫表格中，如果不存在則跳過
            inspector = inspect(self.engine)
            table_columns = [col['name'] for col in inspector.get_columns(table_name)]

            # 只保留資料庫表格中存在的欄位
            df_to_insert = df[[col for col in df.columns if col in table_columns]]

            if df_to_insert.empty:
                logger.warning(f"No valid columns found in dataframe for table {table_name}")
                return 0

            logger.info(f"Inserting {len(df_to_insert)} records with columns: {list(df_to_insert.columns)}")

            # 使用pandas to_sql進行批量插入
            df_to_insert.to_sql(
                name=table_name,
                con=self.engine,
                if_exists='append',
                index=False,
                method='multi',
                chunksize=self.batch_size
            )
            return len(df_to_insert)
        except Exception as e:
            logger.error(f"Batch insert failed for {table_name}: {e}")
            logger.error(f"DataFrame columns: {list(df.columns)}")
            # 嘗試獲取表格結構以提供更多資訊
            try:
                inspector = inspect(self.engine)
                table_columns = [col['name'] for col in inspector.get_columns(table_name)]
                logger.error(f"Table columns: {table_columns}")
            except Exception as inspect_error:
                logger.error(f"Could not inspect table structure: {inspect_error}")
            raise

    def _get_csv_files(self, directory: str, pattern: str, start_filter=None, end_filter=None) -> List[str]:
        """獲取符合條件的CSV檔案列表"""
        import glob

        if not os.path.exists(directory):
            logger.warning(f"Directory does not exist: {directory}")
            return []

        # 使用glob模式匹配檔案
        if 'dividend_yield' in pattern:
            files = glob.glob(os.path.join(directory, 'dividend_yield_*.csv'))
        elif 'monthly_report' in pattern:
            files = glob.glob(os.path.join(directory, 'monthly_report_*.csv'))
        else:
            # 對於season文件，使用更靈活的匹配
            if 'profit-and-loss-analysis-summary' in pattern:
                files = glob.glob(os.path.join(directory, '*profit-and-loss-analysis-summary.csv'))
            elif 'balance-sheet' in pattern:
                files = glob.glob(os.path.join(directory, '*balance-sheet.csv'))
            elif 'consolidated-profit-and-loss-summary' in pattern:
                files = glob.glob(os.path.join(directory, '*consolidated-profit-and-loss-summary.csv'))
            elif 'statement-of-cash-flows' in pattern:
                files = glob.glob(os.path.join(directory, '*statement-of-cash-flows.csv'))
            else:
                files = glob.glob(os.path.join(directory, f'*-{pattern}.csv'))

        logger.info(f"Found {len(files)} files matching pattern '{pattern}' in {directory}")

        # 應用日期/年份過濾
        if start_filter and end_filter:
            filtered_files = []
            for file in files:
                # 從檔案名提取日期資訊並過濾
                if self._file_matches_filter(file, start_filter, end_filter):
                    filtered_files.append(file)
            logger.info(f"After filtering: {len(filtered_files)} files")
            return sorted(filtered_files)

        return sorted(files)

    def _file_matches_filter(self, filepath: str, start_filter, end_filter) -> bool:
        """檢查檔案是否符合日期/年份過濾條件"""
        filename = os.path.basename(filepath)

        try:
            if 'dividend_yield' in filename:
                # dividend_yield_2023_01_01.csv
                parts = filename.replace('dividend_yield_', '').replace('.csv', '').split('_')
                file_date = f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
                return start_filter <= file_date <= end_filter
            elif 'monthly_report' in filename:
                # monthly_report_2023_01.csv
                parts = filename.replace('monthly_report_', '').replace('.csv', '').split('_')
                file_year = int(parts[0])
                return start_filter <= file_year <= end_filter
            else:
                # season files: 2023-season1-PLA.csv
                year_part = filename.split('-')[0]
                file_year = int(year_part)
                return start_filter <= file_year <= end_filter
        except Exception as e:
            logger.warning(f"Error parsing filename {filename}: {e}")
            return False

    def _clean_dividend_yield_data(self, df: pd.DataFrame, source_file: str) -> pd.DataFrame:
        """清理股息殖利率數據"""
        if df.empty:
            return df

        # 從檔案名提取日期
        filename = os.path.basename(source_file)
        date_str = filename.replace('dividend_yield_', '').replace('.csv', '')
        date_parts = date_str.split('_')
        file_date = f"{date_parts[0]}-{date_parts[1].zfill(2)}-{date_parts[2].zfill(2)}"

        # 清理和標準化欄位
        df_cleaned = df.copy()
        df_cleaned['date'] = pd.to_datetime(file_date).date()

        # 重新命名欄位以匹配資料庫
        column_mapping = {
            '證券代號': 'symbol',
            '證券名稱': 'company_name',
            '本益比': 'pe_ratio',
            '殖利率(%)': 'dividend_yield',
            '股價淨值比': 'pb_ratio'
        }

        df_cleaned = df_cleaned.rename(columns=column_mapping)

        # 數據類型轉換
        numeric_columns = ['pe_ratio', 'dividend_yield', 'pb_ratio']
        for col in numeric_columns:
            if col in df_cleaned.columns:
                df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors='coerce')

        # 移除無效數據
        df_cleaned = df_cleaned.dropna(subset=['symbol'])
        df_cleaned['symbol'] = df_cleaned['symbol'].astype(str).str.strip()

        required_columns = ['symbol', 'date', 'company_name', 'pe_ratio', 'dividend_yield', 'pb_ratio']
        # 只選擇實際存在的欄位，避免因為缺失欄位而丟棄整個數據集
        available_columns = [col for col in required_columns if col in df_cleaned.columns]
        if not available_columns:
            logger.warning("No valid columns found, skipping")
            return pd.DataFrame()

        # 確保至少有基本欄位
        base_columns = ['symbol', 'date', 'company_name']
        base_available = [col for col in base_columns if col in df_cleaned.columns]
        if len(base_available) < len(base_columns):
            logger.warning("Missing required base columns, skipping")
            return pd.DataFrame()

        return df_cleaned[available_columns]

    def _clean_monthly_report_data(self, df: pd.DataFrame, source_file: str) -> pd.DataFrame:
        """清理月報數據"""
        if df.empty:
            return df

        # 從檔案名提取年月
        filename = os.path.basename(source_file)
        date_str = filename.replace('monthly_report_', '').replace('.csv', '')
        year, month = map(int, date_str.split('_'))

        df_cleaned = df.copy()
        df_cleaned['report_year'] = year
        df_cleaned['report_month'] = month

        # 重新命名欄位
        column_mapping = {
            '公司代號': 'symbol',
            '公司名稱': 'company_name',
            '當月營收': 'revenue_current_month',
            '上月營收': 'revenue_last_month',
            '去年當月營收': 'revenue_last_year_same_month',
            '當月累計營收': 'revenue_ytd',
            '去年累計營收': 'revenue_last_year_ytd',
            '上月比較增減(%)': 'revenue_growth_rate',
            '去年同月增減(%)': 'revenue_last_year_same_month_growth_rate',
            '備註': 'notes'
        }

        df_cleaned = df_cleaned.rename(columns=column_mapping)

        # 數據類型轉換
        numeric_columns = ['revenue_current_month', 'revenue_last_month',
                          'revenue_last_year_same_month', 'revenue_ytd', 'revenue_last_year_ytd']
        for col in numeric_columns:
            if col in df_cleaned.columns:
                df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors='coerce')

        df_cleaned = df_cleaned.dropna(subset=['symbol'])
        df_cleaned['symbol'] = df_cleaned['symbol'].astype(str).str.strip()

        required_columns = ['symbol', 'company_name', 'report_year', 'report_month',
                          'revenue_current_month', 'revenue_last_month',
                          'revenue_last_year_same_month', 'revenue_ytd',
                          'revenue_last_year_ytd', 'notes']

        # 只選擇實際存在的欄位，避免因為缺失欄位而丟棄整個數據集
        available_columns = [col for col in required_columns if col in df_cleaned.columns]
        if not available_columns:
            logger.warning("No valid columns found, skipping")
            return pd.DataFrame()

        # 確保至少有基本欄位
        base_columns = ['symbol', 'company_name', 'report_year', 'report_month']
        base_available = [col for col in base_columns if col in df_cleaned.columns]
        if len(base_available) < len(base_columns):
            logger.warning("Missing required base columns, skipping")
            return pd.DataFrame()

        return df_cleaned[available_columns]

    def _get_column_mapping(self, report_type: str) -> Dict[str, List[str]]:
        """獲取靈活的欄位映射，支持多個可能的欄位名稱"""
        # 基本欄位映射（所有報表類型都需要）
        base_mappings = {
            'symbol': ['公司代號', '代號', '股票代號', '證券代號', '股票代碼', 'symbol', 'Symbol'],
            'company_name': ['公司名稱', '名稱', '公司', 'company', 'Company', 'company_name']
        }

        # 根據報表類型添加特定欄位映射
        if report_type == 'PLA':
            # 損益表欄位
            pla_mappings = {
                'revenue': ['營業收入', '收入', '營收', 'revenue', 'Revenue', '營業收入淨額'],
                'gross_margin': ['毛利率(%)', '毛利率', 'gross_margin', 'Gross Margin'],
                'operating_margin': ['營業利益率(%)', '營業利益率', 'operating_margin', 'Operating Margin'],
                'pre_tax_margin': ['稅前純益率(%)', '稅前純益率', 'pre_tax_margin', 'Pre-tax Margin'],
                'net_margin': ['稅後純益率(%)', '稅後純益率', 'net_margin', 'Net Margin', '純益率']
            }
            base_mappings.update(pla_mappings)

        elif report_type == 'BS':
            # 資產負債表欄位
            bs_mappings = {
                'total_assets': ['資產總額', '總資產', '資產總計', 'total_assets', 'Total Assets'],
                'total_liabilities': ['負債總額', '總負債', '負債總計', 'total_liabilities', 'Total Liabilities'],
                'equity': ['權益總額', '股東權益', '權益', 'equity', 'Equity', '股東權益總額'],
                'capital': ['股本', 'capital', 'Capital'],
                'book_value_per_share': ['每股參考淨值', '每股淨值', 'book_value_per_share', 'Book Value Per Share']
            }
            base_mappings.update(bs_mappings)

        elif report_type == 'CPL':
            # 合併損益表欄位（和PLA類似）
            cpl_mappings = {
                'net_income': [
                    '本期綜合損益總額（稅後）', '淨利', '淨損益', 'net_income', 'Net Income',
                    'net_margin'  # 將之前錯誤映射的net_margin改為net_income
                ],
                'eps': [
                    '基本每股盈餘（元）', '每股盈餘', 'EPS', 'eps', '基本每股盈餘'
                ]
            }
            base_mappings.update(cpl_mappings)

        elif report_type == 'SCF':
            # 現金流量表欄位
            scf_mappings = {
                'operating_cash_flow': [
                    '營業活動之淨現金流入（流出）',
                    '營業現金流量',
                    'operating_cash_flow',
                    'Operating Cash Flow',
                    '營業活動現金流量'
                ],
                'investing_cash_flow': [
                    '投資活動之淨現金流入（流出）',
                    '投資現金流量',
                    'investing_cash_flow',
                    'Investing Cash Flow',
                    '投資活動現金流量'
                ],
                'financing_cash_flow': [
                    '籌資活動之淨現金流入（流出）',
                    '融資現金流量',
                    'financing_cash_flow',
                    'Financing Cash Flow',
                    '籌資活動現金流量'
                ]
            }
            base_mappings.update(scf_mappings)

        return base_mappings

    def _apply_flexible_column_mapping(self, df: pd.DataFrame, mappings: Dict[str, List[str]]) -> pd.DataFrame:
        """應用靈活的欄位映射"""
        df_mapped = df.copy()
        rename_dict = {}

        # 記錄哪些欄位已經被映射，避免重複映射
        used_columns = set()

        for target_col, possible_names in mappings.items():
            for possible_name in possible_names:
                if possible_name in df_mapped.columns and possible_name not in used_columns:
                    rename_dict[possible_name] = target_col
                    used_columns.add(possible_name)
                    logger.debug(f"Mapped column '{possible_name}' to '{target_col}'")
                    break  # 找到第一個匹配的就停止

        df_mapped = df_mapped.rename(columns=rename_dict)
        return df_mapped

    def _clean_quarterly_report_data(self, df: pd.DataFrame, source_file: str, report_type: str) -> pd.DataFrame:
        """清理季報數據 - 支持不同報表類型的欄位映射"""
        if df.empty:
            logger.warning(f"Empty dataframe for {source_file}, skipping")
            return df

        logger.info(f"Cleaning quarterly report data for {report_type} from {source_file}")
        logger.info(f"Columns: {list(df.columns)}")

        # 從檔案名提取年季
        filename = os.path.basename(source_file)
        # 格式: 2023-season1-PLA.csv
        parts = filename.replace('.csv', '').split('-')
        if len(parts) < 2:
            logger.error(f"Invalid filename format: {filename}")
            return pd.DataFrame()

        try:
            year = int(parts[0])
            season = int(parts[1].replace('season', ''))
        except (ValueError, IndexError) as e:
            logger.error(f"Failed to parse year/season from filename {filename}: {e}")
            return pd.DataFrame()

        df_cleaned = df.copy()

        # 應用靈活的欄位映射（包括symbol和company_name的處理）
        mappings = self._get_column_mapping(report_type)
        df_cleaned = self._apply_flexible_column_mapping(df_cleaned, mappings)

        df_cleaned['report_year'] = year
        df_cleaned['report_season'] = season
        df_cleaned['report_type'] = report_type

        # 根據報表類型進行額外的欄位名稱映射
        if report_type == 'CPL':
            # CPL欄位名稱映射：將標準化的英文欄位映射到資料庫欄位
            column_mapping = {
                'net_income': 'consolidated_net_income',  # CPL的淨利欄位
                'eps': 'consolidated_eps'  # CPL的每股盈餘欄位
            }
            df_cleaned = df_cleaned.rename(columns=column_mapping)
            logger.info(f"Applied CPL column mapping: {column_mapping}")

        # 數據類型轉換 - 只轉換數值欄位
        numeric_columns = []
        for col in df_cleaned.columns:
            if col not in ['symbol', 'company_name', 'report_type']:
                # 嘗試轉換為數值，如果成功則加入數值欄位列表
                try:
                    pd.to_numeric(df_cleaned[col], errors='coerce')
                    numeric_columns.append(col)
                except:
                    pass  # 不是數值欄位，跳過

        for col in numeric_columns:
            df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors='coerce')

        # 清理股票代號
        if 'symbol' in df_cleaned.columns:
            df_cleaned = df_cleaned.dropna(subset=['symbol'])
            df_cleaned['symbol'] = df_cleaned['symbol'].astype(str).str.strip()
            # 移除空字串
            df_cleaned = df_cleaned[df_cleaned['symbol'] != '']
        else:
            logger.warning(f"No symbol column found for {report_type}, skipping")
            return pd.DataFrame()

        # 基本欄位檢查 - 只需要股票代號和年季資訊
        required_base_columns = ['symbol', 'report_year', 'report_season', 'report_type']
        missing_base_columns = [col for col in required_base_columns if col not in df_cleaned.columns]

        if missing_base_columns:
            logger.warning(f"Missing required base columns {missing_base_columns} for {report_type}, skipping")
            return pd.DataFrame()

        # 清理公司名稱（如果存在）
        if 'company_name' in df_cleaned.columns:
            df_cleaned['company_name'] = df_cleaned['company_name'].astype(str).str.strip()

        # 去除重複記錄（基於唯一鍵：symbol, report_year, report_season, report_type）
        initial_count = len(df_cleaned)
        df_cleaned = df_cleaned.drop_duplicates(subset=['symbol', 'report_year', 'report_season', 'report_type'])
        final_count = len(df_cleaned)

        if initial_count > final_count:
            logger.warning(f"Removed {initial_count - final_count} duplicate records from {report_type} data")

        logger.info(f"Successfully cleaned {final_count} records for {report_type}")
        return df_cleaned

    def _read_csv_with_encoding_detection(self, file_path: str) -> pd.DataFrame:
        """使用多種編碼方式讀取CSV文件"""
        encodings_to_try = ['utf-8', 'big5', 'gbk', 'cp950', 'latin1']

        for encoding in encodings_to_try:
            try:
                logger.debug(f"Trying to read {file_path} with encoding: {encoding}")
                df = pd.read_csv(file_path, encoding=encoding)
                logger.info(f"Successfully read {file_path} with encoding: {encoding}")
                return df
            except UnicodeDecodeError:
                logger.debug(f"Failed to read {file_path} with encoding: {encoding}")
                continue
            except Exception as e:
                logger.debug(f"Error reading {file_path} with encoding {encoding}: {e}")
                continue

        # 如果所有編碼都失敗，嘗試不指定編碼
        try:
            logger.warning(f"All encodings failed for {file_path}, trying without encoding specification")
            df = pd.read_csv(file_path)
            return df
        except Exception as e:
            logger.error(f"Failed to read {file_path} with any encoding: {e}")
            raise


def main():
    """主程式"""
    parser = argparse.ArgumentParser(description='股票報告數據遷移工具')
    parser.add_argument('--type', choices=['dividend_yield', 'monthly_reports', 'quarterly_reports'],
                       help='遷移數據類型')
    parser.add_argument('--quarterly-type', choices=['PLA', 'BS', 'CPL', 'SCF'],
                       help='季報類型 (當type=quarterly_reports時使用)')
    parser.add_argument('--start-date', help='開始日期 (YYYY-MM-DD，適用於股息殖利率)')
    parser.add_argument('--end-date', help='結束日期 (YYYY-MM-DD，適用於股息殖利率)')
    parser.add_argument('--start-year', type=int, help='開始年份 (適用於月報和季報)')
    parser.add_argument('--end-year', type=int, help='結束年份 (適用於月報和季報)')
    parser.add_argument('--validate', help='驗證指定表格的遷移結果')
    parser.add_argument('--dry-run', action='store_true', help='僅模擬遷移，不實際插入數據')
    parser.add_argument('--create-tables', action='store_true', help='建立必要的資料表格')
    parser.add_argument('--config', help='配置文件路徑')

    args = parser.parse_args()

    try:
        # 初始化遷移器
        migrator = ReportDataMigrator(args.config)

        if args.create_tables:
            logger.info("Creating database tables...")
            migrator.create_tables_if_not_exists()
            logger.info("Tables created successfully")
            return

        if args.validate:
            # 驗證模式
            logger.info(f"Validating migration for table: {args.validate}")
            result = migrator.validate_migration(args.validate)
            print(f"Validation result: {result}")
            return

        # 遷移模式
        if not args.type:
            parser.error("--type is required for migration operations")

        if args.type == 'dividend_yield':
            if not args.start_date or not args.end_date:
                parser.error("--start-date and --end-date are required for dividend_yield migration")
            result = migrator.migrate_dividend_yield(args.start_date, args.end_date, args.dry_run)

        elif args.type == 'monthly_reports':
            if not args.start_year or not args.end_year:
                parser.error("--start-year and --end-year are required for monthly_reports migration")
            result = migrator.migrate_monthly_reports(args.start_year, args.end_year, args.dry_run)

        elif args.type == 'quarterly_reports':
            if not args.start_year or not args.end_year:
                parser.error("--start-year and --end-year are required for quarterly_reports migration")
            result = migrator.migrate_quarterly_reports(args.start_year, args.end_year, args.dry_run, args.quarterly_type)

        # 輸出結果
        print(f"Migration completed successfully: {result}")

        if not result['success']:
            print(f"Errors encountered: {result['errors']}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        print(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
