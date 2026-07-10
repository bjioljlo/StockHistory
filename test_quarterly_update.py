#!/usr/bin/env python3
"""
Quick test script to trigger quarterly report update and see debug logs
"""
import sys
import logging
import os
from datetime import datetime

# 確保正確匯入
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR) if os.path.basename(CURRENT_DIR) == 'src' else CURRENT_DIR
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Setup basic logging to see DEBUG messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from src.Common import Tools
from src.Common.InfomationType import FS_type
from pydb_core.sql_service import SqlService
from pydb_core.mongo_service import MongoService
from pydb_core.read_load_system import ReadLoadSystem
from pydb_core.cache_service import HybridCacheService
from pyutils_core.config import load_config, get_config_path
from src.ExternalService.ExternalDataFactory import ExternalDataFactory

def main():
    """Run quarterly report update"""
    print("=" * 60)
    print("Starting Quarterly Report Update Test")
    print("=" * 60)

    try:
        # Initialize services like main_stock.py does
        config = load_config(get_config_path())

        sql_service = SqlService()
        sql_service.RunMysql()

        mongo_service = MongoService()
        mongo_service.RunMongoDB(config.get('database.mongodb'))

        read_load_system = ReadLoadSystem(sqlservice=sql_service)

        cache_service = HybridCacheService(
            mongo_service=mongo_service,
            sql_service=sql_service,
            config_path=get_config_path(),
            cache_size=100
        )

        external_data_factory = ExternalDataFactory(
            sql_service=sql_service,
            mongo_service=mongo_service,
            read_load_system=read_load_system,
            cache_service=cache_service
        )

        # Get latest season report date
        report_date = Tools.get_latest_season_report_date(datetime.now(), datetime.now())
        print(f"\nUpdating quarterly reports for: {report_date.strftime('%Y-%m-%d')}")

        # Initialize external data factory and get instance
        external_data = external_data_factory.Get_instance()

        # Test PLA (Profit & Loss) first
        print("\n" + "=" * 60)
        print("Testing PLA (Profit & Loss) Report...")
        print("=" * 60)
        pla_data = external_data.get_allstock_financial_statement(report_date, FS_type.PLA)

        if pla_data is not None and not pla_data.empty:
            print(f"\n[OK] PLA: {len(pla_data)} records retrieved")
            print(f"Columns: {list(pla_data.columns)}")
            print(f"First row:\n{pla_data.iloc[0] if len(pla_data) > 0 else 'Empty'}")
        else:
            print(f"\n[WARN] PLA: no data available")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
