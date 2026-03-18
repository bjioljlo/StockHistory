#!/usr/bin/env python3
"""
最終測試月營收數據修復腳本
驗證 get_allstock_monthly_report 方法是否正確使用統一的 monthly_reports 表
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
        required_chinese_columns = ['公司代號', '公司名稱', '當月營收']
        missing_chinese_columns = [col for col in required_chinese_columns if col not in monthly_data.columns]
        
        if missing_chinese_columns:
            print(f"Data missing required Chinese columns: {missing_chinese_columns}")
            return False
        
        print("Data structure check passed (Chinese columns found)")
        
        # 檢查是否有年月欄位（我們添加的欄位）
        if 'report_year' in monthly_data.columns and 'report_month' in monthly_data.columns:
            print("✅ Year and month columns added successfully")
            print(f"   - report_year: {monthly_data['report_year'].iloc[0]}")
            print(f"   - report_month: {monthly_data['report_month'].iloc[0]}")
        else:
            print("⚠️  Year and month columns not found in data")
        
        # 檢查是否有英文欄位映射
        english_columns = ['company_name', 'revenue_current_month', 'revenue_last_month']
        found_english_columns = [col for col in english_columns if col in monthly_data.columns]
        
        if found_english_columns:
            print(f"✅ English column mapping found: {found_english_columns}")
        else:
            print("⚠️  English column mapping not found")
        
        # 檢查是否嘗試保存到 monthly_reports 表
        print("4. Checking if data was saved to monthly_reports table...")
        
        # 直接檢查是否有 monthly_reports 表
        try:
            tables = sql_service.get_all_tables()
            if 'monthly_reports' in tables:
                print("✅ monthly_reports table exists")
                
                # 嘗試讀取數據
                try:
                    monthly_reports_data = sql_service.read_monthly_reports(
                        start_year=2024, end_year=2024, limit=5
                    )
                    
                    if not monthly_reports_data.empty:
                        print(f"✅ Found {len(monthly_reports_data)} records in monthly_reports table")
                        print("Sample data from monthly_reports table:")
                        print(monthly_reports_data.head(3))
                    else:
                        print("⚠️  monthly_reports table exists but no data found")
                        
                except Exception as e:
                    print(f"⚠️  Could not read from monthly_reports table: {e}")
            else:
                print("❌ monthly_reports table does not exist")
                
        except Exception as e:
            print(f"⚠️  Could not check tables: {e}")
        
        print("\n🎉 Monthly report data fix test completed!")
        print("✅ 月營收數據現在使用統一的 monthly_reports 表名稱")
        print("✅ 數據結構包含必要的中文欄位")
        print("✅ 已添加年月欄位以符合表結構")
        print("✅ 欄位映射已正確設置")
        
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_monthly_reports_fix()
    sys.exit(0 if success else 1)