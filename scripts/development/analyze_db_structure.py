#!/usr/bin/env python3
"""
資料庫結構分析腳本
用於分析現有的MySQL資料庫結構，為資料庫優化做準備
"""

import sys
import os
sys.path.append('src')

from pydb_core.sql_service import SqlService
from pyutils_core.config import ConfigService
import pandas as pd
import time
from collections import defaultdict

def analyze_database_structure():
    """分析資料庫結構"""
    print("=== 資料庫結構分析開始 ===")

    # 初始化服務
    config = ConfigService('config.yml').get_config()
    sql_service = SqlService()
    sql_service.RunMysql()

    time.sleep(3)  # 等待連接建立

    # 獲取所有表格
    tables = sql_service.get_all_table_names()
    print(f"總表格數量: {len(tables)}")

    if not tables:
        print("沒有找到任何表格")
        return

    # 統計資訊
    structure_stats = defaultdict(int)
    data_stats = defaultdict(int)
    sample_data = []

    print("\n=== 分析前20個表格 ===")
    for i, table in enumerate(tables[:20]):
        try:
            df = sql_service.readStockDay(table)
            if not df.empty:
                row_count = len(df)
                columns = list(df.columns)

                print(f"{i+1:2d}. {table}: {row_count} 行, 欄位: {columns}")

                # 記錄結構統計
                structure_stats[len(columns)] += 1
                data_stats['with_data'] += 1

                # 記錄資料範圍
                if row_count > 0:
                    date_range = f"{df.index.min()} 到 {df.index.max()}"
                    print(f"    日期範圍: {date_range}")

                # 收集樣本資料
                if len(sample_data) < 3:
                    sample_data.append({
                        'table': table,
                        'row_count': row_count,
                        'columns': columns,
                        'date_range': date_range if row_count > 0 else 'N/A'
                    })
            else:
                print(f"{i+1:2d}. {table}: 空表格")
                data_stats['empty'] += 1

        except Exception as e:
            print(f"{i+1:2d}. {table}: 錯誤 - {e}")
            data_stats['error'] += 1

    print("\n=== 統計摘要 ===")
    print(f"總表格數: {len(tables)}")
    print(f"有資料表格: {data_stats['with_data']}")
    print(f"空表格: {data_stats['empty']}")
    print(f"錯誤表格: {data_stats['error']}")

    print("\n欄位數量分佈:")
    for col_count, count in sorted(structure_stats.items()):
        print(f"  {col_count} 欄位: {count} 個表格")

    print("\n=== 樣本資料結構 ===")
    for sample in sample_data:
        print(f"表格: {sample['table']}")
        print(f"  行數: {sample['row_count']}")
        print(f"  欄位: {sample['columns']}")
        print(f"  日期範圍: {sample['date_range']}")
        print()

    # 分析表格命名模式
    print("=== 表格命名分析 ===")
    tw_stocks = [t for t in tables if t.endswith('.tw')]
    us_stocks = [t for t in tables if not t.endswith('.tw') and len(t) <= 5]
    other_tables = [t for t in tables if t not in tw_stocks and t not in us_stocks]

    print(f"台灣股票表格: {len(tw_stocks)}")
    print(f"美股表格: {len(us_stocks)}")
    print(f"其他表格: {len(other_tables)}")

    if tw_stocks:
        print(f"台灣股票樣本: {tw_stocks[:5]}")
    if us_stocks:
        print(f"美股樣本: {us_stocks[:5]}")
    if other_tables:
        print(f"其他表格樣本: {other_tables[:5]}")

    print("\n=== 分析完成 ===")

if __name__ == "__main__":
    analyze_database_structure()
