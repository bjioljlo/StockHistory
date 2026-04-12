#!/usr/bin/env python3
"""
欄位映射工具
將 InfomationType.py 中的中文欄位名稱映射到 SQL 表格的英文欄位名稱
"""

from enum import Enum
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


class FieldMapping:
    """欄位映射類別"""

    # CPL (綜合損益彙總表) 欄位映射
    CPL_MAPPING = {
        "本期綜合損益總額（稅後）": "consolidated_net_income",
        "基本每股盈餘（元）": "consolidated_eps"
    }

    # BS (資產負債彙總表) 欄位映射
    BS_MAPPING = {
        "資產總額": "total_assets",
        "負債總額": "total_liabilities",
        "股本": "capital",
        "權益總額": "equity",
        "每股參考淨值": "book_value_per_share"
    }

    # PLA (營益分析彙總表) 欄位映射
    PLA_MAPPING = {
        "營業收入": "revenue",
        "毛利率(%)": "gross_margin",
        "營業利益率(%)": "operating_margin",
        "稅前純益率(%)": "pre_tax_margin",
        "稅後純益率(%)": "net_margin"
    }

    # SCF (現金流量表) 欄位映射
    SCF_MAPPING = {
        "營業活動之淨現金流入（流出）": "operating_cash_flow",
        "投資活動之淨現金流入（流出）": "investing_cash_flow",
        "籌資活動之淨現金流入（流出）": "financing_cash_flow"
    }

    # Month (月報表) 欄位映射
    MONTH_MAPPING = {
        "當月營收": "revenue_current_month"
    }

    # Day (日指標) 欄位映射
    DAY_MAPPING = {
        "本益比": "pe_ratio",
        "股價淨值比": "pb_ratio",
        "殖利率(%)": "dividend_yield"
    }

    # 綜合映射字典
    ALL_MAPPINGS = {
        'CPL': CPL_MAPPING,
        'BS': BS_MAPPING,
        'PLA': PLA_MAPPING,
        'SCF': SCF_MAPPING,
        'Month': MONTH_MAPPING,
        'Day': DAY_MAPPING
    }

    @classmethod
    def get_sql_column(cls, chinese_name: str, report_type: str = None) -> Optional[str]:
        """
        根據中文欄位名稱獲取對應的 SQL 欄位名稱

        Args:
            chinese_name: 中文欄位名稱
            report_type: 報表類型 (可選)

        Returns:
            str: 對應的 SQL 欄位名稱，如果找不到則返回 None
        """
        if report_type and report_type in cls.ALL_MAPPINGS:
            mapping = cls.ALL_MAPPINGS[report_type]
            return mapping.get(chinese_name)

        # 如果沒有指定報表類型或在指定類型中找不到，則在所有映射中查找
        for mapping in cls.ALL_MAPPINGS.values():
            if chinese_name in mapping:
                return mapping[chinese_name]

        return None

    @classmethod
    def get_chinese_name(cls, sql_column: str, report_type: str = None) -> Optional[str]:
        """
        根據 SQL 欄位名稱獲取對應的中文欄位名稱

        Args:
            sql_column: SQL 欄位名稱
            report_type: 報表類型 (可選)

        Returns:
            str: 對應的中文欄位名稱，如果找不到則返回 None
        """
        if report_type and report_type in cls.ALL_MAPPINGS:
            mapping = cls.ALL_MAPPINGS[report_type]
            for chinese_name, sql_name in mapping.items():
                if sql_name == sql_column:
                    return chinese_name

        # 如果沒有指定報表類型或在指定類型中找不到，則在所有映射中查找
        for mapping in cls.ALL_MAPPINGS.values():
            for chinese_name, sql_name in mapping.items():
                if sql_name == sql_column:
                    return chinese_name

        return None

    @classmethod
    def get_all_mappings(cls, report_type: str = None) -> Dict[str, str]:
        """
        獲取所有欄位映射

        Args:
            report_type: 報表類型 (可選)

        Returns:
            Dict: 欄位映射字典
        """
        if report_type and report_type in cls.ALL_MAPPINGS:
            return cls.ALL_MAPPINGS[report_type]
        else:
            return cls.ALL_MAPPINGS

    @classmethod
    def apply_mapping_to_dataframe(cls, df, report_type: str = None) -> 'pd.DataFrame':
        """
        將欄位映射應用到 DataFrame

        Args:
            df: 要處理的 DataFrame
            report_type: 報表類型

        Returns:
            pd.DataFrame: 應用映射後的 DataFrame
        """
        import pandas as pd

        if not isinstance(df, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")

        df_mapped = df.copy()
        mapping = cls.get_all_mappings(report_type)

        # 建立重命名字典
        rename_dict = {}
        for chinese_name, sql_name in mapping.items():
            if chinese_name in df_mapped.columns:
                rename_dict[chinese_name] = sql_name

        # 應用重命名
        if rename_dict:
            df_mapped = df_mapped.rename(columns=rename_dict)

        return df_mapped

    @classmethod
    def validate_mapping(cls, chinese_name: str, sql_column: str, report_type: str = None) -> bool:
        """
        驗證欄位映射是否正確

        Args:
            chinese_name: 中文欄位名稱
            sql_column: SQL 欄位名稱
            report_type: 報表類型

        Returns:
            bool: 映射是否正確
        """
        actual_sql = cls.get_sql_column(chinese_name, report_type)
        return actual_sql == sql_column

    @classmethod
    def get_supported_columns(cls, report_type: str = None) -> List[str]:
        """
        獲取支援的欄位列表

        Args:
            report_type: 報表類型

        Returns:
            List: 支援的欄位列表
        """
        mapping = cls.get_all_mappings(report_type)
        return list(mapping.keys())


def get_field_mapping_info() -> Dict[str, Dict[str, str]]:
    """
    獲取完整的欄位映射資訊

    Returns:
        Dict: 完整的欄位映射資訊
    """
    return {
        'CPL': FieldMapping.CPL_MAPPING,
        'BS': FieldMapping.BS_MAPPING,
        'PLA': FieldMapping.PLA_MAPPING,
        'SCF': FieldMapping.SCF_MAPPING,
        'Month': FieldMapping.MONTH_MAPPING,
        'Day': FieldMapping.DAY_MAPPING
    }


def print_mapping_summary():
    """列印映射摘要"""
    print("=== 欄位映射摘要 ===")
    print()

    for report_type, mapping in FieldMapping.ALL_MAPPINGS.items():
        print(f"{report_type} 報表 ({len(mapping)} 個欄位):")
        for chinese_name, sql_name in mapping.items():
            print(f"  {chinese_name} → {sql_name}")
        print()


if __name__ == "__main__":
    # 測試欄位映射功能
    print_mapping_summary()

    # 測試單個映射
    print("=== 單個映射測試 ===")
    test_cases = [
        ("本期綜合損益總額（稅後）", "CPL"),
        ("資產總額", "BS"),
        ("營業收入", "PLA"),
        ("本益比", "Day"),
        ("當月營收", "Month")
    ]

    for chinese_name, report_type in test_cases:
        sql_name = FieldMapping.get_sql_column(chinese_name, report_type)
        print(f"{chinese_name} ({report_type}) → {sql_name}")

    print()

    # 測試反向映射
    print("=== 反向映射測試 ===")
    sql_test_cases = [
        "consolidated_net_income",
        "total_assets",
        "revenue",
        "pe_ratio",
        "revenue_current_month"
    ]

    for sql_name in sql_test_cases:
        chinese_name = FieldMapping.get_chinese_name(sql_name)
        print(f"{sql_name} → {chinese_name}")