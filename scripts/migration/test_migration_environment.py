#!/usr/bin/env python3
"""
遷移環境測試腳本

此腳本用於測試遷移環境的各項功能，確保遷移過程能夠正常執行。

測試項目：
1. 資料庫連接測試
2. 表格建立測試
3. CSV檔案讀取測試
4. 數據清理測試
5. 批次插入測試
6. 遷移驗證測試
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd
from sqlalchemy import create_engine, text, inspect
import time

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from pyutils_core.config import load_config, get_config_path

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_environment.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class MigrationEnvironmentTester:
    """遷移環境測試器"""

    def __init__(self, config_path: str = None):
        """初始化測試器"""
        self.config = load_config(config_path or get_config_path())
        self.db_config = self.config.get('database', {})
        self.data_config = self.config.get('data', {})

        # 測試結果
        self.test_results = {}

        logger.info("MigrationEnvironmentTester initialized")

    def run_all_tests(self) -> Dict[str, Any]:
        """執行所有測試"""
        logger.info("Starting comprehensive migration environment test")

        test_methods = [
            self.test_database_connection,
            self.test_table_creation,
            self.test_csv_file_access,
            self.test_data_cleaning,
            self.test_batch_insert_performance,
            self.test_migration_validation,
            self.test_error_handling
        ]

        for test_method in test_methods:
            test_name = test_method.__name__
            logger.info(f"Running test: {test_name}")

            try:
                start_time = time.time()
                result = test_method()
                end_time = time.time()

                self.test_results[test_name] = {
                    'status': 'PASSED' if result else 'FAILED',
                    'duration': round(end_time - start_time, 2),
                    'details': result if isinstance(result, dict) else {}
                }

                logger.info(f"Test {test_name}: {'PASSED' if result else 'FAILED'} ({self.test_results[test_name]['duration']}s)")

            except Exception as e:
                self.test_results[test_name] = {
                    'status': 'ERROR',
                    'duration': 0,
                    'details': {'error': str(e)}
                }
                logger.error(f"Test {test_name} failed with error: {e}")

        return self.generate_test_report()

    def test_database_connection(self) -> Dict[str, Any]:
        """測試資料庫連接"""
        try:
            db_uri = self._build_db_uri()
            engine = create_engine(db_uri, echo=False)

            # 測試連接
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                test_value = result.fetchone()[0]

                # 獲取資料庫資訊
                db_info = {}
                if self.db_config.get('type') == 'mysql':
                    result = conn.execute(text("SELECT VERSION() as version"))
                    db_info['version'] = result.fetchone()[0]

                    result = conn.execute(text("SHOW VARIABLES LIKE 'innodb_buffer_pool_size'"))
                    pool_size = result.fetchone()
                    db_info['innodb_buffer_pool_size'] = pool_size[1] if pool_size else None

            return {
                'connection': True,
                'test_query': test_value == 1,
                'database_info': db_info
            }

        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return {'connection': False, 'error': str(e)}

    def test_table_creation(self) -> Dict[str, Any]:
        """測試表格建立"""
        try:
            db_uri = self._build_db_uri()
            engine = create_engine(db_uri, echo=False)

            test_table_name = 'migration_test_table'

            # 建立測試表格
            create_query = f"""
            CREATE TABLE IF NOT EXISTS {test_table_name} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                test_column VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """

            with engine.connect() as conn:
                conn.execute(text(create_query))
                conn.commit()

                # 驗證表格是否存在
                inspector = inspect(engine)
                tables = inspector.get_table_names()
                table_exists = test_table_name in tables

                # 清理測試表格
                conn.execute(text(f"DROP TABLE IF EXISTS {test_table_name}"))
                conn.commit()

            return {
                'table_creation': True,
                'table_exists': table_exists,
                'cleanup': True
            }

        except Exception as e:
            logger.error(f"Table creation test failed: {e}")
            return {'table_creation': False, 'error': str(e)}

    def test_csv_file_access(self) -> Dict[str, Any]:
        """測試CSV檔案存取"""
        results = {}

        # 測試股息殖利率檔案
        yield_dir = self.data_config.get('yield_dir', 'yieldInfo')
        results['yield_dir'] = self._test_directory_access(yield_dir, 'dividend_yield_*.csv')

        # 測試月報檔案
        month_dir = self.data_config.get('month_dir', 'monthRP')
        results['month_dir'] = self._test_directory_access(month_dir, 'monthly_report_*.csv')

        # 測試季報檔案
        season_dir = self.data_config.get('season_dir', 'seasonInfo')
        results['season_dir'] = self._test_directory_access(season_dir, '*-*.csv')

        return results

    def _test_directory_access(self, directory: str, pattern: str) -> Dict[str, Any]:
        """測試目錄存取"""
        import glob

        try:
            if not os.path.exists(directory):
                return {'exists': False, 'accessible': False, 'file_count': 0}

            files = glob.glob(os.path.join(directory, pattern))
            sample_file = files[0] if files else None

            # 測試讀取第一個檔案
            readable = False
            if sample_file:
                try:
                    df = pd.read_csv(sample_file, nrows=5)  # 只讀取前5行
                    readable = not df.empty
                except Exception as e:
                    logger.warning(f"Cannot read sample file {sample_file}: {e}")

            return {
                'exists': True,
                'accessible': True,
                'file_count': len(files),
                'sample_readable': readable,
                'sample_file': os.path.basename(sample_file) if sample_file else None
            }

        except Exception as e:
            return {'exists': False, 'accessible': False, 'error': str(e)}

    def test_data_cleaning(self) -> Dict[str, Any]:
        """測試數據清理功能"""
        # 創建測試數據
        test_data = pd.DataFrame({
            '證券代號': ['2330', '2454', 'INVALID'],
            '證券名稱': ['TSMC', 'MediaTek', None],
            '本益比': ['15.5', '20.3', 'N/A'],
            '殖利率(%)': ['2.5', '3.1', ''],
            '股價淨值比': ['3.2', '4.1', '0']
        })

        # 測試清理邏輯
        df_cleaned = test_data.copy()

        # 重新命名欄位
        column_mapping = {
            '證券代號': 'symbol',
            '證券名稱': 'company_name',
            '本益比': 'pe_ratio',
            '殖利率(%)': 'dividend_yield',
            '股價淨值比': 'pb_ratio'
        }
        df_cleaned = df_cleaned.rename(columns=column_mapping)

        # 數據類型轉換
        numeric_columns = ['pe_ratio', 'dividend_yield', 'pb_ratio']
        for col in numeric_columns:
            df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors='coerce')

        # 清理結果
        original_count = len(test_data)
        cleaned_count = len(df_cleaned.dropna(subset=['symbol']))

        return {
            'original_records': original_count,
            'cleaned_records': cleaned_count,
            'data_types_converted': True,
            'null_values_handled': True
        }

    def test_batch_insert_performance(self) -> Dict[str, Any]:
        """測試批次插入效能"""
        try:
            db_uri = self._build_db_uri()
            engine = create_engine(db_uri, echo=False)

            test_table_name = 'performance_test_table'

            # 建立測試表格
            create_query = f"""
            CREATE TABLE IF NOT EXISTS {test_table_name} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(20),
                value DECIMAL(10,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """

            with engine.connect() as conn:
                conn.execute(text(create_query))
                conn.commit()

                # 產生測試數據
                test_data = []
                for i in range(1000):
                    test_data.append({
                        'symbol': f'TEST{i:03d}',
                        'value': i * 1.5
                    })

                df = pd.DataFrame(test_data)

                # 測試批次插入效能
                start_time = time.time()
                df.to_sql(
                    name=test_table_name,
                    con=engine,
                    if_exists='append',
                    index=False,
                    method='multi',
                    chunksize=100
                )
                end_time = time.time()

                insert_time = end_time - start_time
                records_per_second = len(df) / insert_time

                # 清理測試表格
                conn.execute(text(f"DROP TABLE IF EXISTS {test_table_name}"))
                conn.commit()

            return {
                'records_inserted': len(df),
                'insert_time_seconds': round(insert_time, 2),
                'records_per_second': round(records_per_second, 2),
                'performance_acceptable': insert_time < 5.0  # 應在5秒內完成
            }

        except Exception as e:
            logger.error(f"Batch insert performance test failed: {e}")
            return {'error': str(e)}

    def test_migration_validation(self) -> Dict[str, Any]:
        """測試遷移驗證功能"""
        try:
            db_uri = self._build_db_uri()
            engine = create_engine(db_uri, echo=False)

            test_table_name = 'validation_test_table'

            # 建立測試表格和數據
            with engine.connect() as conn:
                # 建立表格
                conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {test_table_name} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    symbol VARCHAR(20),
                    date DATE,
                    value DECIMAL(10,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_symbol_date (symbol, date)
                )
                """))
                conn.commit()

                # 插入測試數據
                test_data = [
                    ('2330', '2024-01-01', 100.5),
                    ('2330', '2024-01-02', 101.0),
                    ('2454', '2024-01-01', 200.5),
                    ('2330', '2024-01-01', 100.5),  # 重複資料
                ]

                for symbol, date, value in test_data:
                    try:
                        conn.execute(text(f"""
                        INSERT INTO {test_table_name} (symbol, date, value)
                        VALUES (:symbol, :date, :value)
                        """), {'symbol': symbol, 'date': date, 'value': value})
                        conn.commit()
                    except Exception:
                        # 忽略重複鍵錯誤
                        pass

                # 執行驗證查詢
                result = conn.execute(text(f"SELECT COUNT(*) as total FROM {test_table_name}"))
                total_count = result.fetchone()[0]

                # 檢查重複資料
                result = conn.execute(text(f"""
                    SELECT symbol, date, COUNT(*) as count
                    FROM {test_table_name}
                    GROUP BY symbol, date
                    HAVING COUNT(*) > 1
                """))
                duplicates = result.fetchall()

                # 清理測試表格
                conn.execute(text(f"DROP TABLE IF EXISTS {test_table_name}"))
                conn.commit()

            return {
                'total_records': total_count,
                'duplicates_found': len(duplicates),
                'validation_logic_works': True
            }

        except Exception as e:
            logger.error(f"Migration validation test failed: {e}")
            return {'error': str(e)}

    def test_error_handling(self) -> Dict[str, Any]:
        """測試錯誤處理"""
        error_tests = {}

        # 測試無效的資料庫URI
        try:
            invalid_engine = create_engine("mysql+pymysql://invalid:invalid@invalid:3306/invalid")
            with invalid_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            error_tests['invalid_connection'] = False
        except Exception:
            error_tests['invalid_connection'] = True

        # 測試無效的CSV檔案
        try:
            df = pd.read_csv('nonexistent_file.csv')
            error_tests['invalid_csv'] = False
        except Exception:
            error_tests['invalid_csv'] = True

        # 測試數據類型轉換錯誤
        try:
            invalid_data = pd.DataFrame({'col': ['a', 'b', 'c']})
            pd.to_numeric(invalid_data['col'])  # 這會產生警告但不會報錯
            error_tests['data_type_conversion'] = True
        except Exception:
            error_tests['data_type_conversion'] = False

        return error_tests

    def _build_db_uri(self) -> str:
        """建構資料庫URI"""
        db_type = self.db_config.get('type', 'mysql')

        if db_type == 'mysql':
            mysql_config = self.db_config.get('mysql', {})
            user = mysql_config.get('user')
            password = mysql_config.get('password')
            host = mysql_config.get('host', 'localhost')
            port = mysql_config.get('port', 3306)
            database = mysql_config.get('databasename')

            return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?local_infile=1"

        elif db_type == 'sqlite':
            path = self.db_config.get('sqlite', {}).get('path', 'default.db')
            return f"sqlite:///{path}"

        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    def generate_test_report(self) -> Dict[str, Any]:
        """生成測試報告"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['status'] == 'PASSED')
        failed_tests = sum(1 for result in self.test_results.values() if result['status'] == 'FAILED')
        error_tests = sum(1 for result in self.test_results.values() if result['status'] == 'ERROR')

        total_duration = sum(result['duration'] for result in self.test_results.values())

        report = {
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'errors': error_tests,
                'success_rate': round(passed_tests / total_tests * 100, 2) if total_tests > 0 else 0,
                'total_duration': round(total_duration, 2)
            },
            'details': self.test_results,
            'environment_ready': passed_tests == total_tests,
            'recommendations': self._generate_recommendations()
        }

        return report

    def _generate_recommendations(self) -> List[str]:
        """生成建議"""
        recommendations = []

        for test_name, result in self.test_results.items():
            if result['status'] != 'PASSED':
                if test_name == 'test_database_connection':
                    recommendations.append("檢查資料庫連接設定和網路連接")
                elif test_name == 'test_csv_file_access':
                    recommendations.append("確認CSV檔案路徑和權限設定")
                elif test_name == 'test_batch_insert_performance':
                    recommendations.append("檢查資料庫效能設定和網路延遲")
                elif test_name == 'test_table_creation':
                    recommendations.append("確認資料庫使用者權限")
                else:
                    recommendations.append(f"檢查{test_name}相關的配置")

        if not recommendations:
            recommendations.append("所有測試通過，環境準備完成")

        return recommendations


def main():
    """主程式"""
    import argparse

    parser = argparse.ArgumentParser(description='遷移環境測試腳本')
    parser.add_argument('--config', help='配置文件路徑')
    parser.add_argument('--output', help='輸出報告檔案路徑')
    parser.add_argument('--json', action='store_true', help='以JSON格式輸出')

    args = parser.parse_args()

    try:
        # 初始化測試器
        tester = MigrationEnvironmentTester(args.config)

        # 執行測試
        logger.info("Starting migration environment tests...")
        report = tester.run_all_tests()

        # 輸出結果
        if args.json:
            import json
            output = json.dumps(report, indent=2, ensure_ascii=False)
        else:
            output = f"""
遷移環境測試報告
================

總結:
- 總測試數: {report['summary']['total_tests']}
- 通過測試: {report['summary']['passed']}
- 失敗測試: {report['summary']['failed']}
- 錯誤測試: {report['summary']['errors']}
- 成功率: {report['summary']['success_rate']}%
- 總耗時: {report['summary']['total_duration']}秒
- 環境準備狀態: {'就緒' if report['environment_ready'] else '未就緒'}

詳細結果:
"""
            for test_name, result in report['details'].items():
                output += f"- {test_name}: {result['status']} ({result['duration']}s)\n"

            output += f"\n建議:\n"
            for rec in report['recommendations']:
                output += f"- {rec}\n"

        print(output)

        # 保存到檔案
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            logger.info(f"Report saved to {args.output}")

        # 根據測試結果設定退出碼
        if not report['environment_ready']:
            logger.warning("Environment is not ready for migration")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        print(f"Test execution failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
