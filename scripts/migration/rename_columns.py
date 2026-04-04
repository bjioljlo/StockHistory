#!/usr/bin/env python3
"""
股票季報CSV欄位名稱中文化英文工具

此腳本用於將seasonInfo目錄中所有CSV文件的中文欄位名稱
替換成英文名稱，基於migrate_reports_data.py中的欄位映射規則。

使用方法:
python rename_columns.py
"""

import os
import sys
import logging
import pandas as pd
from typing import Dict, List

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rename_columns.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ColumnRenamer:
    """欄位名稱替換器"""

    def __init__(self):
        """初始化替換器"""
        self.data_dir = 'seasonInfo'
        logger.info("ColumnRenamer initialized")

    def get_column_mapping(self, report_type: str) -> Dict[str, List[str]]:
        """獲取欄位映射 - 基於migrate_reports_data.py中的規則"""
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
            # 合併損益表欄位（只有淨利和每股盈餘）
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

    def get_report_type_from_filename(self, filename: str) -> str:
        """從檔案名判斷報表類型"""
        if 'profit-and-loss-analysis-summary' in filename:
            return 'PLA'
        elif 'balance-sheet' in filename:
            return 'BS'
        elif 'consolidated-profit-and-loss-summary' in filename:
            return 'CPL'
        elif 'statement-of-cash-flows' in filename:
            return 'SCF'
        else:
            logger.warning(f"Unknown report type for file: {filename}")
            return None

    def apply_column_mapping(self, df: pd.DataFrame, mappings: Dict[str, List[str]]) -> pd.DataFrame:
        """應用欄位映射"""
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

        if rename_dict:
            df_mapped = df_mapped.rename(columns=rename_dict)
            logger.info(f"Applied column mappings: {rename_dict}")

        return df_mapped

    def process_file(self, file_path: str) -> bool:
        """處理單個CSV文件"""
        try:
            logger.info(f"Processing file: {file_path}")

            # 讀取CSV文件
            df = pd.read_csv(file_path, encoding='utf-8')
            original_columns = list(df.columns)
            logger.info(f"Original columns: {original_columns}")

            # 判斷報表類型
            report_type = self.get_report_type_from_filename(os.path.basename(file_path))
            if not report_type:
                logger.warning(f"Skipping file {file_path} - unknown report type")
                return False

            # 獲取欄位映射
            mappings = self.get_column_mapping(report_type)

            # 應用欄位映射
            df_mapped = self.apply_column_mapping(df, mappings)

            # 檢查是否有欄位被替換
            new_columns = list(df_mapped.columns)
            if original_columns != new_columns:
                # 寫回文件
                df_mapped.to_csv(file_path, index=False, encoding='utf-8')
                logger.info(f"Updated file {file_path}: {original_columns} -> {new_columns}")
                return True
            else:
                logger.info(f"No changes needed for {file_path}")
                return False

        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            return False

    def process_all_files(self) -> Dict[str, int]:
        """處理所有CSV文件"""
        if not os.path.exists(self.data_dir):
            logger.error(f"Directory does not exist: {self.data_dir}")
            return {'error': 1}

        # 獲取所有CSV文件
        csv_files = []
        for file in os.listdir(self.data_dir):
            if file.endswith('.csv'):
                csv_files.append(os.path.join(self.data_dir, file))

        logger.info(f"Found {len(csv_files)} CSV files to process")

        processed = 0
        updated = 0
        errors = 0

        for file_path in sorted(csv_files):
            try:
                if self.process_file(file_path):
                    updated += 1
                processed += 1
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {str(e)}")
                errors += 1

        result = {
            'files_processed': processed,
            'files_updated': updated,
            'errors': errors,
            'success': errors == 0
        }

        logger.info(f"Processing completed: {result}")
        return result


def main():
    """主程式"""
    try:
        renamer = ColumnRenamer()
        result = renamer.process_all_files()

        print(f"Column renaming completed: {result}")

        if not result['success']:
            print(f"Errors encountered: {result['errors']} errors")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Column renaming failed: {e}")
        print(f"Column renaming failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
