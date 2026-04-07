#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
StockHistory 股票歷史分析系統
向後相容匯入模組 - 解決import路徑問題

此檔案提供雙重路徑相容，確保舊程式碼可以正常運作
"""

import os
import sys

# 將當前目錄加入Python路徑，確保相對匯入可以正常運作
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 版本資訊
__version__ = '2.0.0'
__author__ = 'StockHistory Team'

# 向後相容匯入別名
# 舊程式碼使用 `from src import X` 時可以正常運作
try:
    # 匯入主要模組供外部使用
    from . import StockInfos
    from . import MongoService
    from . import SqlService
    from . import ReadLoadSystem
    from . import UpdateStockService
    from . import ScheduleService
    from . import DrawFigur
    from . import main_stock

    # 匯入子模組
    from . import Common
    from . import BackTestService
    from . import Controller
    from . import Model
    from . import View
    from . import FilterService
    from . import ExternalService
    from . import UpdateStockService as UpdateStockServiceModule

except ImportError as e:
    import warnings
    warnings.warn(f"部分模組匯入失敗: {e}", ImportWarning)

__all__ = [
    'StockInfos',
    'MongoService',
    'SqlService',
    'ReadLoadSystem',
    'UpdateStockService',
    'ScheduleService',
    'DrawFigur',
    'main_stock',
    'Common',
    'BackTestService',
    'Controller',
    'Model',
    'View',
    'FilterService',
    'ExternalService',
]