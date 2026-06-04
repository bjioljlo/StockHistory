#!/usr/bin/env python3
"""
測試整合後的快取服務是否正常工作
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_cache_integration():
    """測試快取服務在 main_stock.py 中的整合"""
    print("=== 測試快取服務整合 ===")

    try:
        # 模擬 main_stock.py 的初始化過程
        print("1. 載入配置...")
        from pyutils_core.config import load_config, get_config_path
        config = load_config(get_config_path())
        print("[OK] 配置載入成功")

        print("2. 初始化基礎服務...")
        from pydb_core.sql_service import SqlService
        from pydb_core.mongo_service import MongoService
        from pydb_core.read_load_system import ReadLoadSystem

        sql_service = SqlService()
        # 注意：這裡不實際連線資料庫，只測試類別初始化
        print("[OK] SQL 服務初始化成功")

        mongo_service = MongoService()
        # 注意：這裡不實際連線資料庫，只測試類別初始化
        print("[OK] MongoDB 服務初始化成功")

        read_load_system = ReadLoadSystem(sqlservice=sql_service)
        print("[OK] 讀取載入系統初始化成功")

        print("3. 初始化混合快取服務...")
        from pydb_core.cache_service import HybridCacheService

        # 創建快取服務（不實際連線 Redis/MongoDB）
        cache_service = HybridCacheService(
            mongo_service=mongo_service,
            sql_service=sql_service,
            config_path=get_config_path(),
            cache_size=100
        )
        print("[OK] 混合快取服務初始化成功")

        print("4. 初始化外部資料工廠...")
        from src.ExternalService.ExternalDataFactory import ExternalDataFactory

        external_data_factory = ExternalDataFactory(
            sql_service=sql_service,
            mongo_service=mongo_service,
            read_load_system=read_load_system,
            cache_service=cache_service
        )
        print("[OK] 外部資料工廠初始化成功")

        print("5. 測試快取服務注入...")
        # 獲取 TGetExternalData 實例來測試快取服務是否正確注入
        tget_instance = external_data_factory.Get_instance(None)

        if hasattr(tget_instance, '_cache_service') and tget_instance._cache_service is not None:
            print("[OK] 快取服務已正確注入到 TGetExternalData")
        else:
            print("[FAIL] 快取服務未正確注入到 TGetExternalData")
            return False

        print("6. 測試快取服務基本功能...")
        # 測試快取服務的基本方法
        cache_service.record_query("2330")
        cache_service.record_query("2454")

        hot_stocks = cache_service.get_hot_stocks(5)
        if "2330" in hot_stocks or "2454" in hot_stocks:
            print("[OK] 查詢統計功能正常")
        else:
            print("[FAIL] 查詢統計功能異常")
            return False

        stats = cache_service.get_cache_stats()
        if 'query_stats' in stats:
            print("[OK] 快取統計功能正常")
        else:
            print("[FAIL] 快取統計功能異常")
            return False

        print("\n=== 所有整合測試通過！快取服務已正確整合到系統中 ===")
        return True

    except Exception as e:
        print(f"[FAIL] 整合測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_cache_integration()
    print(f"\n測試結果: {'PASS' if success else 'FAIL'}")
    sys.exit(0 if success else 1)
