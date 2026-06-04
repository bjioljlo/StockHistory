"""
修正 Tools import 錯誤 — from src.Common import Tools 應保留為 src.Common.Tools
因為 StockHistory 的 Tools.py 有獨有的 TidyTicketData 函式。
"""
import os

ROOT = 'D:/Python/StockHistory'

# 需要修正的檔案：將 from src.Common import Tools 改回 from src.Common import Tools
count = 0
for dirpath, dirnames, filenames in os.walk(ROOT):
    if '__pycache__' in dirpath or '.venv' in dirpath or '.git' in dirpath:
        continue
    for f in filenames:
        if not f.endswith('.py'):
            continue
        fp = os.path.join(dirpath, f)
        with open(fp, 'r', encoding='utf-8') as fh:
            content = fh.read()

        original = content
        content = content.replace('from src.Common import Tools', 'from src.Common import Tools')

        if content != original:
            with open(fp, 'w', encoding='utf-8') as fh:
                fh.write(content)
            print(f'  Fixed: {os.path.relpath(fp, ROOT)}')
            count += 1

print(f'\nFixed {count} files — Tools imports now point to src.Common.Tools')
