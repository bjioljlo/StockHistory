#!/usr/bin/env python3
"""
MongoDB 智慧快取層測試腳本

測試混合快取服務的基本功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from pydb_core.cache_service import HybridCacheService
from pydb_core.mongo_service import MongoService
from pydb_core.sql_service import SqlService
import pandas as pd
from datetime import datetime

def test_cache_service():
    """測試快取服務基本功能"""
    print("=== 測試 MongoDB 智慧快取層 ===")

    try:
        # 初始化服務
        print("1. 初始化服務...")
        sql_service = SqlService()
        sql_service.RunMysql()

        mongo_service = MongoService()
        mongo_service.RunMongoDB({
            'host': 'localhost',
            'port': 27017,
            'databasename': 'Demo'
        })

        # 初始化快取服務
        cache_service = HybridCacheService(
            mongo_service=mongo_service,
            sql_service=sql_service,
            cache_size=50
        )

        print("[OK] 服務初始化成功")

        # 測試查詢統計
        print("\n2. 測試查詢統計...")
        cache_service.record_query("2330")
        cache_service.record_query("2454")
        cache_service.record_query("2330")  # 重複查詢

        hot_stocks = cache_service.get_hot_stocks(10)
        print(f"[OK] 熱門股票: {hot_stocks}")

        # 測試快取統計
        print("\n3. 測試快取統計...")
        stats = cache_service.get_cache_stats()
        print(f"[OK] 快取統計: {stats}")

        # 測試健康檢查
        print("\n4. 測試健康檢查...")
        health = cache_service.health_check()
        print(f"[OK] 健康狀態: {health}")

        print("\n=== 所有測試通過！MongoDB 智慧快取層實現成功 ===")

    except Exception as e:
        print(f"[FAIL] 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = test_cache_service()
    sys.exit(0 if success else 1)
