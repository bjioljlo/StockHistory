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

from src.Common.ConfigService import load_config, get_config_path

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

        # 批次處理大小
        self.batch_size = self.config.get('migration', {}).get('batch_size', 1000)

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

                # 讀取CSV檔案
                df = pd.read_csv(csv_file, encoding='utf-8')

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
                                 dry_run: bool = False) -> Dict[str, Any]:
        """遷移季報數據"""
        logger.info(f"Starting quarterly reports migration from year {start_year} to {end_year}")

        total_processed = 0
        total_inserted = 0
        errors = []

        # 處理不同類型的季報
        report_types = ['PLA', 'BS', 'CPL', 'SCF']

        for report_type in report_types:
            logger.info(f"Processing {report_type} reports")
            csv_files = self._get_csv_files(self.season_dir, f'season.*{report_type}', start_year, end_year)

            for csv_file in csv_files:
                try:
                    logger.info(f"Processing {csv_file}")

                    df = pd.read_csv(csv_file, encoding='utf-8')
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
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            PARTITION BY RANGE (YEAR(date)) (
                PARTITION p2020 VALUES LESS THAN (2021),
                PARTITION p2021 VALUES LESS THAN (2022),
                PARTITION p2022 VALUES LESS THAN (2023),
                PARTITION p2023 VALUES LESS THAN (2024),
                PARTITION p2024 VALUES LESS THAN (2025),
                PARTITION p2025 VALUES LESS THAN (2026),
                PARTITION p_future VALUES LESS THAN MAXVALUE
            );
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
                notes TEXT COMMENT '備註',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

                UNIQUE KEY unique_symbol_period (symbol, report_year, report_month),
                INDEX idx_symbol (symbol),
                INDEX idx_period (report_year, report_month),
                INDEX idx_symbol_period (symbol, report_year, report_month),
                INDEX idx_revenue_current_month (revenue_current_month),
                INDEX idx_revenue_ytd (revenue_ytd)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            PARTITION BY RANGE (report_year) (
                PARTITION p2020 VALUES LESS THAN (2021),
                PARTITION p2021 VALUES LESS THAN (2022),
                PARTITION p2022 VALUES LESS THAN (2023),
                PARTITION p2023 VALUES LESS THAN (2024),
                PARTITION p2024 VALUES LESS THAN (2025),
                PARTITION p2025 VALUES LESS THAN (2026),
                PARTITION p_future VALUES LESS THAN MAXVALUE
            );
            """,

            # 季報表格
            """
            CREATE TABLE IF NOT EXISTS quarterly_reports (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL COMMENT '股票代號',
                company_name VARCHAR(100) COMMENT '公司名稱',
                report_year INT NOT NULL COMMENT '報表年份',
                report_season INT NOT NULL COMMENT '報表季別(1-4)',
                report_type ENUM('PLA', 'BS', 'CPL', 'SCF') NOT NULL COMMENT '報表類型',
                revenue BIGINT COMMENT '營業收入',
                gross_margin DECIMAL(5,2) COMMENT '毛利率(%)',
                operating_margin DECIMAL(5,2) COMMENT '營業利益率(%)',
                pre_tax_margin DECIMAL(5,2) COMMENT '稅前純益率(%)',
                net_margin DECIMAL(5,2) COMMENT '稅後純益率(%)',
                total_assets BIGINT COMMENT '總資產',
                total_liabilities BIGINT COMMENT '總負債',
                equity BIGINT COMMENT '股東權益',
                operating_cash_flow BIGINT COMMENT '營業現金流量',
                investing_cash_flow BIGINT COMMENT '投資現金流量',
                financing_cash_flow BIGINT COMMENT '融資現金流量',
                raw_data JSON COMMENT '原始數據存儲',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

                UNIQUE KEY unique_symbol_period_type (symbol, report_year, report_season, report_type),
                INDEX idx_symbol (symbol),
                INDEX idx_period (report_year, report_season),
                INDEX idx_type (report_type),
                INDEX idx_symbol_period (symbol, report_year, report_season),
                INDEX idx_revenue (revenue),
                INDEX idx_net_margin (net_margin)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            PARTITION BY RANGE (report_year) (
                PARTITION p2020 VALUES LESS THAN (2021),
                PARTITION p2021 VALUES LESS THAN (2022),
                PARTITION p2022 VALUES LESS THAN (2023),
                PARTITION p2023 VALUES LESS THAN (2024),
                PARTITION p2024 VALUES LESS THAN (2025),
                PARTITION p2025 VALUES LESS THAN (2026),
                PARTITION p_future VALUES LESS THAN MAXVALUE
            );
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
        """批次插入資料"""
        if df.empty:
            return 0

        try:
            # 使用pandas to_sql進行批量插入
            df.to_sql(
                name=table_name,
                con=self.engine,
                if_exists='append',
                index=False,
                method='multi',
                chunksize=self.batch_size
            )
            return len(df)
        except Exception as e:
            logger.error(f"Batch insert failed for {table_name}: {e}")
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
        return df_cleaned[required_columns] if all(col in df_cleaned.columns for col in required_columns) else pd.DataFrame()

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
        return df_cleaned[required_columns] if all(col in df_cleaned.columns for col in required_columns) else pd.DataFrame()

    def _clean_quarterly_report_data(self, df: pd.DataFrame, source_file: str, report_type: str) -> pd.DataFrame:
        """清理季報數據"""
        if df.empty:
            return df

        # 從檔案名提取年季
        filename = os.path.basename(source_file)
        # 格式: 2023-season1-PLA.csv
        parts = filename.replace('.csv', '').split('-')
        year = int(parts[0])
        season = int(parts[1].replace('season', ''))

        df_cleaned = df.copy()
        df_cleaned['report_year'] = year
        df_cleaned['report_season'] = season
        df_cleaned['report_type'] = report_type

        # 重新命名欄位 (根據不同報表類型)
        base_mapping = {
            '公司代號': 'symbol',
            '公司名稱': 'company_name'
        }

        if report_type == 'PLA':
            # 損益表欄位
            pla_mapping = {
                '營業收入': 'revenue',
                '毛利率(%)': 'gross_margin',
                '營業利益率(%)': 'operating_margin',
                '稅前純益率(%)': 'pre_tax_margin',
                '稅後純益率(%)': 'net_margin'
            }
            base_mapping.update(pla_mapping)
        elif report_type == 'BS':
            # 資產負債表欄位
            bs_mapping = {
                '總資產': 'total_assets',
                '總負債': 'total_liabilities',
                '股東權益': 'equity'
            }
            base_mapping.update(bs_mapping)
        elif report_type == 'CPL':
            # 現金流量表欄位
            cpl_mapping = {
                '營業活動之淨現金流入（流出）': 'operating_cash_flow',
                '投資活動之淨現金流入（流出）': 'investing_cash_flow',
                '籌資活動之淨現金流入（流出）': 'financing_cash_flow',
                '期初現金及約當現金': 'beginning_cash',
                '期末現金及約當現金': 'ending_cash',
                '本期淨現金流入（流出）': 'net_cash_flow',
                '資產負債表帳列之現金及約當現金': 'cash_and_equivalents'
            }
            base_mapping.update(cpl_mapping)

        df_cleaned = df_cleaned.rename(columns=base_mapping)

        # 數據類型轉換
        numeric_columns = [col for col in df_cleaned.columns if col not in ['symbol', 'company_name', 'report_type']]
        for col in numeric_columns:
            if col in df_cleaned.columns:
                df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors='coerce')

        df_cleaned = df_cleaned.dropna(subset=['symbol'])
        df_cleaned['symbol'] = df_cleaned['symbol'].astype(str).str.strip()

        # 存儲原始數據作為JSON
        df_cleaned['raw_data'] = df.to_json(orient='records', force_ascii=False)

        required_columns = ['symbol', 'company_name', 'report_year', 'report_season', 'report_type', 'raw_data']
        return df_cleaned[required_columns] if all(col in df_cleaned.columns for col in required_columns) else pd.DataFrame()


def main():
    """主程式"""
    parser = argparse.ArgumentParser(description='股票報告數據遷移工具')
    parser.add_argument('--type', choices=['dividend_yield', 'monthly_reports', 'quarterly_reports'],
                       required=True, help='遷移數據類型')
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

        if args.validate:
            # 驗證模式
            logger.info(f"Validating migration for table: {args.validate}")
            result = migrator.validate_migration(args.validate)
            print(f"Validation result: {result}")
            return

        # 遷移模式
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
            result = migrator.migrate_quarterly_reports(args.start_year, args.end_year, args.dry_run)

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
