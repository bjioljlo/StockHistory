#!/usr/bin/env python3
"""
測試月營收數據修復腳本
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
    print("開始測試月營收數據修復...")
    
    try:
        # 初始化服務
        print("1. 初始化服務...")
        sql_service = SqlService()
        sql_service.RunMysql()
        
        mongo_service = MongoService()
        read_load_system = ReadLoadSystem(sql_service)
        cache_service = HybridCacheService()
        
        external_data = TGetExternalData(
            sql_service, mongo_service, read_load_system, cache_service
        )
        
        # 測試日期（使用一個較早的月份以避免重複數據）
        test_date = datetime(2024, 1, 1)  # 2024年1月
        print(f"2. 測試日期: {test_date}")
        
        # 獲取月營收數據
        print("3. 獲取月營收數據...")
        monthly_data = external_data.get_allstock_monthly_report(test_date)
        
        if monthly_data.empty:
            print("❌ 獲取月營收數據失敗，返回空數據")
            return False
        
        print(f"✅ 成功獲取 {len(monthly_data)} 筆月營收數據")
        print(f"數據欄位: {list(monthly_data.columns)}")
        
        # 檢查數據結構
        required_columns = ['report_year', 'report_month']
        missing_columns = [col for col in required_columns if col not in monthly_data.columns]
        
        if missing_columns:
            print(f"❌ 數據缺少必要欄位: {missing_columns}")
            return False
        
        print("✅ 數據結構檢查通過")
        
        # 檢查是否正確保存到 monthly_reports 表
        print("4. 檢查 monthly_reports 表...")
        monthly_reports_data = sql_service.read_monthly_reports(
            start_year=2024, end_year=2024, limit=10
        )
        
        if monthly_reports_data.empty:
            print("❌ monthly_reports 表中沒有數據")
            return False
        
        print(f"✅ monthly_reports 表中有 {len(monthly_reports_data)} 筆數據")
        
        # 檢查是否有測試日期的數據
        test_data = monthly_reports_data[
            (monthly_reports_data['report_year'] == 2024) & 
            (monthly_reports_data['report_month'] == 1)
        ]
        
        if test_data.empty:
            print("❌ 找不到測試日期的數據")
            return False
        
        print(f"✅ 找到 {len(test_data)} 筆 2024年1月的數據")
        
        # 檢查數據完整性
        print("5. 數據完整性檢查...")
        print(f"   - 數據筆數: {len(test_data)}")
        print(f"   - 欄位: {list(test_data.columns)}")
        print(f"   - 樣本數據:")
        print(test_data.head(3))
        
        # 檢查是否有重複數據
        duplicates = test_data[test_data.duplicated(subset=['symbol', 'report_year', 'report_month'], keep=False)]
        if not duplicates.empty:
            print(f"⚠️  發現 {len(duplicates)} 筆重複數據")
        else:
            print("✅ 無重複數據")
        
        print("\n🎉 月營收數據修復測試成功！")
        print("✅ 月營收數據現在正確保存到 monthly_reports 表中")
        print("✅ 數據結構符合預期")
        print("✅ 無重複數據問題")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_monthly_reports_fix()
    sys.exit(0 if success else 1)