"""Compatibility shim: expose pydb_core.query_optimizer as src.Common.QueryOptimizer

這個模組為舊有測試與代碼提供相容層，將已安裝的
`pydb_core.query_optimizer` 模組導出為 `src.Common.QueryOptimizer`。
"""
import sys
from importlib import import_module


# Import the real implementation from the installed package
_mod = import_module("pydb_core.query_optimizer")

# Re-export commonly patched names so tests that patch
# 'src.Common.QueryOptimizer.yaml' or 'src.Common.QueryOptimizer.create_engine'
# will operate on the same module object.
QueryOptimizer = getattr(_mod, "QueryOptimizer")
yaml = getattr(_mod, "yaml", None)
create_engine = getattr(_mod, "create_engine", None)
text = getattr(_mod, "text", None)
inspect = getattr(_mod, "inspect", None)

# Make the import system return the real module object when importing
# src.Common.QueryOptimizer so that patch(...) resolving to that name
# will modify the actual implementation module.
sys.modules.setdefault("src.Common.QueryOptimizer", _mod)

__all__ = ["QueryOptimizer", "yaml", "create_engine", "text", "inspect"]
