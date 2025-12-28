#!/usr/bin/env python3
"""
測試備份、恢復和歸檔服務的基本功能
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加src目錄到路徑
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_backup_service():
    """測試BackupService"""
    print("測試 BackupService...")
    try:
        from Common.BackupService import BackupService

        # 使用臨時配置檔案進行測試
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("""
mysql:
  user: test
  password: test
  database: test
  host: localhost
  port: 3306
mongodb:
  database: test
  host: localhost
  port: 27017
redis:
  host: localhost
  port: 6379
backup:
  retention_days: 7
""")
            config_file = f.name

        service = BackupService(config_file)
        print(f"✓ BackupService 初始化成功")
        print(f"  備份目錄: {service.backup_dir}")
        print(f"  配置載入成功")

        # 清理臨時檔案
        os.unlink(config_file)
        return True

    except Exception as e:
        print(f"✗ BackupService 測試失敗: {e}")
        return False

def test_restore_service():
    """測試RestoreService"""
    print("測試 RestoreService...")
    try:
        from Common.RestoreService import RestoreService

        # 使用臨時配置檔案進行測試
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("""
mysql:
  user: test
  password: test
  database: test
  host: localhost
  port: 3306
mongodb:
  database: test
  host: localhost
  port: 27017
redis:
  host: localhost
  port: 6379
""")
            config_file = f.name

        service = RestoreService(config_file)
        print(f"✓ RestoreService 初始化成功")
        print(f"  備份目錄: {service.backup_dir}")

        # 測試列出備份檔案（應該是空的）
        backups = service.find_backup_files()
        print(f"  找到的備份檔案: {backups}")

        # 清理臨時檔案
        os.unlink(config_file)
        return True

    except Exception as e:
        print(f"✗ RestoreService 測試失敗: {e}")
        return False

def test_archival_service():
    """測試ArchivalService"""
    print("測試 ArchivalService...")
    try:
        from Common.ArchivalService import ArchivalService

        # 使用臨時配置檔案進行測試
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("""
mysql:
  user: test
  password: test
  database: test
  host: localhost
  port: 3306
mongodb:
  database: test
  host: localhost
  port: 27017
redis:
  host: localhost
  port: 6379
""")
            config_file = f.name

        service = ArchivalService(config_file)
        print(f"✓ ArchivalService 初始化成功")
        print(f"  歸檔目錄: {service.archive_dir}")

        # 測試獲取統計資訊（應該是空的）
        stats = service.get_archival_stats()
        print(f"  歸檔統計: {stats['total_files']} 檔案, {stats['total_size_mb']:.2f} MB")

        # 清理臨時檔案
        os.unlink(config_file)
        return True

    except Exception as e:
        print(f"✗ ArchivalService 測試失敗: {e}")
        return False

def test_config_validation():
    """測試配置檔案驗證"""
    print("測試配置檔案...")
    try:
        import yaml

        # 檢查config.yml是否存在並可載入
        config_file = 'config.yml'
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            print("✓ config.yml 載入成功")
            print(f"  資料庫類型: {config.get('database', {}).get('type', 'unknown')}")

            # 檢查雲端備份配置
            cloud_backup = config.get('cloud_backup', {})
            if cloud_backup.get('enabled', False):
                print(f"  雲端備份已啟用: {cloud_backup.get('provider', 'unknown')}")
            else:
                print("  雲端備份已停用")

            return True
        else:
            print("✗ config.yml 不存在")
            return False

    except Exception as e:
        print(f"✗ 配置檔案測試失敗: {e}")
        return False

def test_directory_creation():
    """測試目錄創建"""
    print("測試目錄創建...")
    try:
        from pathlib import Path

        # 檢查備份和歸檔目錄
        backup_dir = Path('./backups')
        archive_dir = Path('./archive')
        logs_dir = Path('./logs')

        print("目錄狀態:")
        print(f"  backups: {'存在' if backup_dir.exists() else '不存在'}")
        print(f"  archive: {'存在' if archive_dir.exists() else '不存在'}")
        print(f"  logs: {'存在' if logs_dir.exists() else '不存在'}")

        return True

    except Exception as e:
        print(f"✗ 目錄測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("=" * 50)
    print("StockHistory 備份服務測試")
    print("=" * 50)

    tests = [
        test_config_validation,
        test_directory_creation,
        test_backup_service,
        test_restore_service,
        test_archival_service,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 50)
    print(f"測試結果: {passed}/{total} 通過")

    if passed == total:
        print("🎉 所有測試通過！備份服務已準備就緒。")
        return 0
    else:
        print("⚠️  部分測試失敗，請檢查配置和依賴。")
        return 1

if __name__ == '__main__':
    sys.exit(main())
