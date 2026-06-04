"""
批量取代 StockHistory 內部的 import 路徑與刪除被取代的舊檔案。
執行前先確認 pyproject.toml 已加入所有套件依賴。
"""
import os
import re
import shutil

ROOT = 'D:/Python/StockHistory'

# 檔案分類
# A: 完全被新套件取代 → 更新所有引用後直接刪除
DELETE_FILES = {
    # pyutils-core 完整取代
    'src/Common/ConfigService.py': 'pyutils_core.config',
    'src/Common/Exceptions.py': 'pyutils_core.exceptions',
    'src/Common/NetworkUtils.py': 'pyutils_core.network',
    'src/Common/ServiceContainer.py': 'pyutils_core.container',
    'src/Common/ConcurrentUtils.py': 'pyutils_core.concurrent',
    'src/Common/LoggingService.py': 'pyutils_core.logging',
    'src/Common/PerformanceMonitor.py': 'pyutils_core.performance',
    # pydb-core 完整取代
    'src/MongoService.py': 'pydb_core.mongo_service',
    'src/ReadLoadSystem.py': 'pydb_core.read_load_system',
    'src/Common/CacheService.py': 'pydb_core.cache_service',
    'src/Common/FieldMapping.py': 'pydb_core.field_mapping',
    'src/Common/StockInfoData.py': 'pydb_core.stock_info_data',
    'src/Common/ReadWriteSplitService.py': 'pydb_core.read_write_split',
    'src/Common/QueryOptimizer.py': 'pydb_core.query_optimizer',
    # indicator-core 完整取代
    'src/Common/DateUtils.py': 'indicator_core.date_utils',
    'src/Common/FinancialUtils.py': 'indicator_core.financial_utils',
    'src/Common/StockUtils.py': 'indicator_core.stock_utils',
}

# B: 有獨有邏輯，但內部 import 需要更新
# Tools.py: 有 TidyTicketData，內部 import from .DateUtils, .FinancialUtils, .StockUtils, .DataUtils, .NetworkUtils
# DataUtils.py: 有 TidyTicketData，無外部 import（僅 stdlib + pandas）
# SqlService.py: 有 yfInfo，import 到 src.Common.ConfigService


def update_imports_in_file(filepath):
    """Replace src.Common.XXX imports with new package imports."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # 取代相對 import: from indicator_core.date_utils import → from indicator_core.date_utils import
    content = re.sub(r'from \.DateUtils import', 'from indicator_core.date_utils import', content)
    content = re.sub(r'from \.FinancialUtils import', 'from indicator_core.financial_utils import', content)
    content = re.sub(r'from \.StockUtils import', 'from indicator_core.stock_utils import', content)
    content = re.sub(r'from \.DataUtils import', 'from indicator_core.data_utils import', content)
    content = re.sub(r'from \.NetworkUtils import', 'from indicator_core.network_utils import', content)
    content = re.sub(r'from \.Exceptions import', 'from pyutils_core.exceptions import', content)
    content = re.sub(r'from \.FieldMapping import', 'from pydb_core.field_mapping import', content)
    content = re.sub(r'from \.CacheService import', 'from pydb_core.cache_service import', content)
    content = re.sub(r'from \.ConfigService import', 'from pyutils_core.config import', content)
    content = re.sub(r'from \.ServiceContainer import', 'from pyutils_core.container import', content)
    content = re.sub(r'from \.ConcurrentUtils import', 'from pyutils_core.concurrent import', content)
    content = re.sub(r'from \.LoggingService import', 'from pyutils_core.logging import', content)
    content = re.sub(r'from \.PerformanceMonitor import', 'from pyutils_core.performance import', content)
    content = re.sub(r'from \.StockInfoData import', 'from pydb_core.stock_info_data import', content)
    content = re.sub(r'from \.ReadWriteSplitService import', 'from pydb_core.read_write_split import', content)
    content = re.sub(r'from \.QueryOptimizer import', 'from pydb_core.query_optimizer import', content)

    # 取代絕對 import
    content = re.sub(r'from src\.Common\.ConfigService import', 'from pyutils_core.config import', content)
    content = re.sub(r'from src\.Common\.Exceptions import', 'from pyutils_core.exceptions import', content)
    content = re.sub(r'from src\.Common\.DateUtils import', 'from indicator_core.date_utils import', content)
    content = re.sub(r'from src\.Common\.FinancialUtils import', 'from indicator_core.financial_utils import', content)
    content = re.sub(r'from src\.Common\.StockUtils import', 'from indicator_core.stock_utils import', content)
    content = re.sub(r'from src\.Common\.DataUtils import', 'from indicator_core.data_utils import', content)
    content = re.sub(r'from src\.Common\.NetworkUtils import', 'from indicator_core.network_utils import', content)
    content = re.sub(r'from src\.Common\.FieldMapping import', 'from pydb_core.field_mapping import', content)
    content = re.sub(r'from src\.Common\.CacheService import', 'from pydb_core.cache_service import', content)
    content = re.sub(r'from src\.Common\.ServiceContainer import', 'from pyutils_core.container import', content)
    content = re.sub(r'from src\.Common\.ConcurrentUtils import', 'from pyutils_core.concurrent import', content)
    content = re.sub(r'from src\.Common\.LoggingService import', 'from pyutils_core.logging import', content)
    content = re.sub(r'from src\.Common\.PerformanceMonitor import', 'from pyutils_core.performance import', content)
    content = re.sub(r'from src\.Common\.StockInfoData import', 'from pydb_core.stock_info_data import', content)
    content = re.sub(r'from src\.Common\.ReadWriteSplitService import', 'from pydb_core.read_write_split import', content)
    content = re.sub(r'from src\.Common\.QueryOptimizer import', 'from pydb_core.query_optimizer import', content)

    # SqlService/MongoService/ReadLoadSystem
    content = re.sub(r'from src\.SqlService import', 'from pydb_core.sql_service import', content)
    content = re.sub(r'from src\.MongoService import', 'from pydb_core.mongo_service import', content)
    content = re.sub(r'from src\.ReadLoadSystem import', 'from pydb_core.read_load_system import', content)

    # Tools - from src.Common import Tools
    content = re.sub(r'from src\.Common import Tools', 'from src.Common import Tools', content)
    content = re.sub(r'import src\.Common\.Tools', '', content)  # rare edge case

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def main():
    # Phase 1: Update imports in ALL Python files
    changed = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        if '__pycache__' in dirpath or '.venv' in dirpath or '.git' in dirpath:
            continue
        for f in filenames:
            if not f.endswith('.py'):
                continue
            fp = os.path.join(dirpath, f)
            if update_imports_in_file(fp):
                changed.append(os.path.relpath(fp, ROOT))

    print(f"=== Updated imports in {len(changed)} files ===")
    for f in sorted(changed):
        print(f"  {f}")

    # Phase 2: Delete fully-replaced files
    deleted = []
    for fpath in DELETE_FILES:
        full = os.path.join(ROOT, fpath)
        if os.path.exists(full):
            os.remove(full)
            deleted.append(fpath)

    # Phase 3: Remove __pycache__ dirs left behind
    for dirpath, dirnames, filenames in os.walk(ROOT):
        if dirpath.endswith('__pycache__'):
            shutil.rmtree(dirpath, ignore_errors=True)

    print(f"\n=== Deleted {len(deleted)} files ===")
    for f in sorted(deleted):
        print(f"  {f}")
    print("\n✅ 完成！請執行 `uv sync` 確認所有 import 正確。")


if __name__ == '__main__':
    main()
