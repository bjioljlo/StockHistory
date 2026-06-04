#!/usr/bin/env python3
"""
測試新的SqlService優化查詢方法
"""

import sys
import os
import time

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from pydb_core.sql_service import SqlService

def test_new_sql_methods():
    """測試新的優化查詢方法"""
    print("Testing new SqlService optimized query methods")
    print("=" * 50)

    # 初始化SqlService
    sql_service = SqlService()
    sql_service.RunMysql()

    # 等待資料庫連接初始化
    time.sleep(2)

    # 測試1: 讀取股息殖利率數據
    print("\nTest 1: read_dividend_yield method")
    try:
        df_dividend = sql_service.read_dividend_yield(limit=5)
        if not df_dividend.empty:
            print(f"SUCCESS: Retrieved {len(df_dividend)} dividend yield records")
            print("First 5 records:")
            print(df_dividend.head())
        else:
            print("WARNING: Dividend yield table is empty or query failed")
    except Exception as e:
        print(f"ERROR: Dividend yield query failed: {e}")

    # 測試2: 讀取月報數據
    print("\nTest 2: read_monthly_reports method")
    try:
        df_monthly = sql_service.read_monthly_reports(limit=5)
        if not df_monthly.empty:
            print(f"SUCCESS: Retrieved {len(df_monthly)} monthly report records")
            print("First 5 records:")
            print(df_monthly.head())
        else:
            print("WARNING: Monthly reports table is empty or query failed")
    except Exception as e:
        print(f"ERROR: Monthly reports query failed: {e}")

    # 測試3: 讀取季報數據
    print("\nTest 3: read_quarterly_reports method")
    try:
        df_quarterly = sql_service.read_quarterly_reports(limit=5)
        if not df_quarterly.empty:
            print(f"SUCCESS: Retrieved {len(df_quarterly)} quarterly report records")
            print("First 5 records:")
            print(df_quarterly.head())
        else:
            print("WARNING: Quarterly reports table is empty or query failed")
    except Exception as e:
        print(f"ERROR: Quarterly reports query failed: {e}")

    # 測試4: 獲取股息殖利率統計
    print("\nTest 4: get_dividend_yield_stats method")
    try:
        stats = sql_service.get_dividend_yield_stats()
        if stats:
            print("SUCCESS: Dividend yield statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        else:
            print("WARNING: Unable to retrieve statistics")
    except Exception as e:
        print(f"ERROR: Statistics query failed: {e}")

    # 測試5: 測試具體股票查詢
    print("\nTest 5: Specific stock queries")
    if not df_dividend.empty:
        sample_symbol = df_dividend.iloc[0]['symbol']
        print(f"Querying detailed data for stock {sample_symbol}...")

        try:
            # 股息殖利率
            dividend_data = sql_service.read_dividend_yield(symbol=sample_symbol, limit=3)
            print(f"SUCCESS: Stock {sample_symbol} dividend yield data: {len(dividend_data)} records")

            # 月報數據
            monthly_data = sql_service.read_monthly_reports(symbol=sample_symbol, limit=3)
            print(f"SUCCESS: Stock {sample_symbol} monthly data: {len(monthly_data)} records")

            # 季報數據
            quarterly_data = sql_service.read_quarterly_reports(symbol=sample_symbol, limit=3)
            print(f"SUCCESS: Stock {sample_symbol} quarterly data: {len(quarterly_data)} records")

        except Exception as e:
            print(f"ERROR: Specific stock query failed: {e}")

    print("\n" + "=" * 50)
    print("Testing completed!")

if __name__ == "__main__":
    test_new_sql_methods()
