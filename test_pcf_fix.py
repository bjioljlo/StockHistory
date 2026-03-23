#!/usr/bin/env python3
"""
測試 PCF 計算修復的腳本
"""

import sys
import os
from datetime import datetime

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.FilterService.StockReportHistory import OCFPerShare_Indicator
from src.Common import InfomationType as info
import pandas as pd
from pandas import Series, DataFrame

def test_data_alignment_simple():
    """簡單測試數據對齊功能"""
    print("開始測試數據對齊功能...")
    
    try:
        # 創建一個簡單的 Indicator 實例來測試 check_and_convert_to_series
        indicator = OCFPerShare_Indicator("test", None, None)
        
        # 測試案例 1: 兩個 Series 有不同的索引
        print("\n測試案例 1: 兩個 Series 有不同的索引")
        series1 = Series([100, 200, 300], index=['A', 'B', 'C'])
        series2 = Series([10, 20, 30], index=['X', 'Y', 'Z'])
        
        print(f"Series1: {series1}")
        print(f"Series2: {series2}")
        
        result1, result2 = indicator.check_and_convert_to_series(series1, series2)
        print(f"對齊結果1: {result1}")
        print(f"對齊結果2: {result2}")
        
        # 測試案例 2: 一個 Series 和一個單一值
        print("\n測試案例 2: 一個 Series 和一個單一值")
        series3 = Series([100, 200, 300], index=['A', 'B', 'C'])
        series4 = Series([50], index=['A'])
        
        print(f"Series3: {series3}")
        print(f"Series4: {series4}")
        
        result3, result4 = indicator.check_and_convert_to_series(series3, series4)
        print(f"對齊結果3: {result3}")
        print(f"對齊結果4: {result4}")
        
        # 測試案例 3: 兩個 Series 有共同索引
        print("\n測試案例 3: 兩個 Series 有共同索引")
        series5 = Series([100, 200, 300], index=['A', 'B', 'C'])
        series6 = Series([10, 20, 30], index=['A', 'B', 'C'])
        
        print(f"Series5: {series5}")
        print(f"Series6: {series6}")
        
        result5, result6 = indicator.check_and_convert_to_series(series5, series6)
        print(f"對齊結果5: {result5}")
        print(f"對齊結果6: {result6}")
        
        return True
        
    except Exception as e:
        print(f"數據對齊測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pcf_calculation_simple():
    """簡單測試 PCF 計算邏輯"""
    print("\n開始測試 PCF 計算邏輯...")
    
    try:
        # 創建一個簡單的 PCF 指標實例
        from src.FilterService.StockReportHistory import PCF_Indicator
        from src.FilterService.StockHistory import OriginalStock
        
        # 創建模擬的 OCFPerShare 指標
        class MockOCFPerShare:
            def get_ReportByNumber(self, date, number, base_today=None):
                # 返回模擬的每股營業現金流數據
                return Series([50.0], index=[str(number)])
        
        # 創建模擬的股票價格
        class MockStockPrice:
            def get_PriceByDateAndType(self, date, price_type):
                # 返回模擬的股票價格
                return 1000.0
        
        # 創建 PCF 指標
        pcf_indicator = PCF_Indicator(
            "P/CF",
            MockOCFPerShare(),
            MockStockPrice(),
            None
        )
        
        # 設置股票代碼
        pcf_indicator.number = "2330"
        
        # 測試日期
        test_date = datetime(2024, 12, 31)
        
        print(f"測試股票: 2330")
        print(f"測試日期: {test_date}")
        
        # 計算 PCF
        result = pcf_indicator.get_ALL_Report(test_date)
        
        if not result.empty:
            print(f"PCF 計算成功!")
            print(f"結果: {result}")
            if len(result.columns) > 0:
                print(f"PCF 值: {result.iloc[0, 0]}")
        else:
            print("PCF 計算失敗，返回空結果")
            
        return not result.empty
        
    except Exception as e:
        print(f"PCF 計算測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("PCF 計算修復測試")
    print("=" * 60)
    
    # 測試數據對齊
    alignment_success = test_data_alignment_simple()
    
    # 測試 PCF 計算
    pcf_success = test_pcf_calculation_simple()
    
    print("\n" + "=" * 60)
    print("測試結果總結:")
    print(f"數據對齊測試: {'成功' if alignment_success else '失敗'}")
    print(f"PCF 計算測試: {'成功' if pcf_success else '失敗'}")
    
    if alignment_success and pcf_success:
        print("\n所有測試通過！PCF 計算修復成功！")
    else:
        print("\n部分測試失敗，需要進一步檢查")
    
    print("=" * 60)
