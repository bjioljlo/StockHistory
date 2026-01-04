#!/usr/bin/env python3
"""
簡單的 MongoDB 智慧快取層測試

只測試類別匯入和基本方法，不依賴實際資料庫連線
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_basic_import():
    """測試基本匯入和類別結構"""
    print("=== 測試 MongoDB 智慧快取層基本功能 ===")

    try:
        # 測試類別匯入
        print("1. 測試類別匯入...")
        from src.Common.CacheService import HybridCacheService, CacheService
        print("[OK] 類別匯入成功")

        # 測試別名
        print("\n2. 測試類別別名...")
        assert CacheService == HybridCacheService
        print("[OK] 別名設定正確")

        # 測試方法存在性
        print("\n3. 測試方法存在性...")
        methods = [
            'record_query',
            'get_hot_stocks',
            'get_stock_data',
            'set_stock_data',
            'get_cache_stats',
            'health_check',
            'update_mongo_cache',
            'cleanup_cold_mongo_cache'
        ]

        for method in methods:
            assert hasattr(HybridCacheService, method), f"缺少方法: {method}"
            print(f"[OK] 方法 {method} 存在")

        print("\n4. 測試全域函數...")
        from src.Common.CacheService import get_cache_service
        assert callable(get_cache_service)
        print("[OK] 全域函數 get_cache_service 存在")

        print("\n=== 所有基本測試通過！MongoDB 智慧快取層結構正確 ===")
        return True

    except Exception as e:
        print(f"[FAIL] 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_import()
    print(f"\n測試結果: {'PASS' if success else 'FAIL'}")
    sys.exit(0 if success else 1)
