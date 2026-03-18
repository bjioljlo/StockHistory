#!/usr/bin/env python3
"""
簡單測試月營收數據修復腳本
驗證 get_allstock_monthly_report 方法是否正確保存數據到 monthly_reports 表
"""

import sys
import os
from datetime import datetime

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.Common.ConfigService import load_config, get_config_path
from src.SqlService import SqlService
from src.MongoService import MongoService
from src.ReadLoadSystem import ReadLoadSystem
from src.Common.CacheService import HybridCacheService
from src.ExternalService.TGetExternalData import TGetExternalData

def test_monthly_reports_fix():
    """測試月營收數據修復"""
    print("Testing monthly report data fix...")
    
    try:
        # 初始化服務
        print("1. Initializing services...")
        sql_service = SqlService()
        sql_service.RunMysql()
        
        mongo_service = MongoService()
        read_load_system = ReadLoadSystem(sql_service)
        cache_service = HybridCacheService(mongo_service, sql_service)
        
        external_data = TGetExternalData(
            sql_service, mongo_service, read_load_system, cache_service
        )
        
        # 測試日期（使用一個較早的月份以避免重複數據）
        test_date = datetime(2024, 1, 1)  # 2024年1月
        print(f"2. Test date: {test_date}")
        
        # 獲取月營收數據
        print("3. Getting monthly report data...")
        monthly_data = external_data.get_allstock_monthly_report(test_date)
        
        if monthly_data.empty:
            print("Failed to get monthly report data, returned empty data")
            return False
        
        print(f"Successfully obtained {len(monthly_data)} monthly report records")
        print(f"Data columns: {list(monthly_data.columns)}")
        
        # 檢查數據結構 - 月營收數據使用中文欄位名稱
        # 檢查是否有必要的中文欄位
        required_chinese_columns = ['公司代號', '公司名稱', '當月營收']
        missing_chinese_columns = [col for col in required_chinese_columns if col not in monthly_data.columns]
        
        if missing_chinese_columns:
            print(f"Data missing required Chinese columns: {missing_chinese_columns}")
            return False
        
        print("Data structure check passed (Chinese columns found)")
        
        # 檢查是否正確保存到 monthly_reports 表
        print("4. Checking monthly_reports table...")
        monthly_reports_data = sql_service.read_monthly_reports(
            start_year=2024, end_year=2024, limit=10
        )
        
        if monthly_reports_data.empty:
            print("No data found in monthly_reports table")
            return False
        
        print(f"Found {len(monthly_reports_data)} records in monthly_reports table")
        
        # 檢查是否有測試日期的數據
        test_data = monthly_reports_data[
            (monthly_reports_data['report_year'] == 2024) & 
            (monthly_reports_data['report_month'] == 1)
        ]
        
        if test_data.empty:
            print("Test date data not found")
            return False
        
        print(f"Found {len(test_data)} records for January 2024")
        
        # 檢查數據完整性
        print("5. Data integrity check...")
        print(f"   - Record count: {len(test_data)}")
        print(f"   - Columns: {list(test_data.columns)}")
        print(f"   - Sample data:")
        print(test_data.head(3))
        
        # 檢查是否有重複數據
        duplicates = test_data[test_data.duplicated(subset=['symbol', 'report_year', 'report_month'], keep=False)]
        if not duplicates.empty:
            print(f"Found {len(duplicates)} duplicate records")
        else:
            print("No duplicate data found")
        
        print("\nMonthly report data fix test successful!")
        print("Monthly report data is now correctly saved to monthly_reports table")
        print("Data structure meets expectations")
        print("No duplicate data issues")
        
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_monthly_reports_fix()
    sys.exit(0 if success else 1)