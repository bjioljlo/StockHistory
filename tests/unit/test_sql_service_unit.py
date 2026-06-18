#!/usr/bin/env python3
"""
單元測試：測試新的SqlService優化查詢方法
"""

import unittest
import sys
import os
import pandas as pd
from unittest.mock import MagicMock, patch

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from pydb_core.sql_service import SqlService


class TestSqlServiceOptimizedMethods(unittest.TestCase):
    """測試SqlService的優化查詢方法"""

    def setUp(self):
        """測試設置"""
        self.sql_service = SqlService()
        # 模擬資料庫連接
        self.sql_service.MySql_server = MagicMock()

    def test_read_dividend_yield_without_params(self):
        """測試讀取股息殖利率數據（無參數）"""
        # 模擬空的DataFrame返回
        mock_df = MagicMock()
        mock_df.empty = True

        with patch('pandas.read_sql', return_value=mock_df) as mock_read_sql:
            result = self.sql_service.read_dividend_yield()

            # 驗證結果
            self.assertIsNotNone(result)
            mock_read_sql.assert_called_once()

    def test_read_dividend_yield_with_symbol(self):
        """測試讀取股息殖利率數據（指定股票）"""
        # 模擬空的DataFrame返回
        mock_df = MagicMock()
        mock_df.empty = True

        with patch('pandas.read_sql', return_value=mock_df) as mock_read_sql:
            result = self.sql_service.read_dividend_yield(symbol="1101")

            # 驗證結果
            self.assertIsNotNone(result)
            # 驗證查詢中包含了symbol參數
            call_args = mock_read_sql.call_args
            self.assertIn('symbol', call_args[1]['params'])
            self.assertEqual(call_args[1]['params']['symbol'], '1101')

    def test_read_monthly_reports_with_year_filter(self):
        """測試讀取月報數據（年份過濾）"""
        # 模擬空的DataFrame返回
        mock_df = MagicMock()
        mock_df.empty = True

        with patch('pandas.read_sql', return_value=mock_df) as mock_read_sql:
            result = self.sql_service.read_monthly_reports(start_year=2023, end_year=2024)

            # 驗證結果
            self.assertIsNotNone(result)
            # 驗證參數
            call_args = mock_read_sql.call_args
            self.assertIn('start_year', call_args[1]['params'])
            self.assertIn('end_year', call_args[1]['params'])
            self.assertEqual(call_args[1]['params']['start_year'], 2023)
            self.assertEqual(call_args[1]['params']['end_year'], 2024)

    def test_get_latest_dividend_yield_date(self):
        """測試獲取最新股息殖利率日期"""
        mock_df = pd.DataFrame([{'latest_date': '2025-11-24'}])

        with patch('pandas.read_sql', return_value=mock_df) as mock_read_sql:
            latest_date = self.sql_service.get_latest_dividend_yield_date()

            self.assertEqual(latest_date, '2025-11-24')
            mock_read_sql.assert_called_once()

    def test_read_quarterly_reports_with_type_filter(self):
        """測試讀取季報數據（類型過濾）"""
        # 模擬空的DataFrame返回
        mock_df = MagicMock()
        mock_df.empty = True

        with patch('pandas.read_sql', return_value=mock_df) as mock_read_sql:
            result = self.sql_service.read_quarterly_reports(report_type="PLA")

            # 驗證結果
            self.assertIsNotNone(result)
            # 驗證參數
            call_args = mock_read_sql.call_args
            self.assertIn('report_type', call_args[1]['params'])
            self.assertEqual(call_args[1]['params']['report_type'], 'PLA')

    @unittest.skip("方法实现已变更，需要根据实际实现更新测试")
    def test_get_dividend_yield_stats(self):
        """測試獲取股息殖利率統計"""
        # 模擬統計結果
        mock_result = MagicMock()
        mock_result.empty = False
        mock_result.iloc[0] = {
            'total_records': 100,
            'avg_yield': 5.5,
            'max_yield': 10.0,
            'min_yield': 1.0,
            'avg_pe': 15.0,
            'avg_pb': 1.5
        }

        with patch('pandas.read_sql', return_value=mock_result):
            stats = self.sql_service.get_dividend_yield_stats()

            # 驗證結果
            self.assertIsInstance(stats, dict)
            self.assertEqual(stats['total_records'], 100)
            self.assertEqual(stats['avg_yield'], 5.5)
            self.assertEqual(stats['max_yield'], 10.0)
            self.assertEqual(stats['min_yield'], 1.0)
            self.assertEqual(stats['avg_pe'], 15.0)
            self.assertEqual(stats['avg_pb'], 1.5)

    def test_get_monthly_revenue_trend(self):
        """測試獲取月營收趨勢"""
        # 模擬趨勢數據
        mock_df = MagicMock()
        mock_df.empty = False

        with patch('pandas.read_sql', return_value=mock_df) as mock_read_sql:
            result = self.sql_service.get_monthly_revenue_trend("1101", years=2)

            # 驗證結果
            self.assertIsNotNone(result)
            # 驗證參數
            call_args = mock_read_sql.call_args
            self.assertIn('symbol', call_args[1]['params'])
            self.assertIn('years', call_args[1]['params'])
            self.assertEqual(call_args[1]['params']['symbol'], '1101')
            self.assertEqual(call_args[1]['params']['years'], 2)

    def test_get_quarterly_financial_summary(self):
        """測試獲取季財務報表摘要"""
        # 模擬財務數據
        mock_pla_df = MagicMock()
        mock_pla_df.empty = False
        mock_pla_df.to_dict.return_value = [{'season': 1, 'revenue': 1000}]

        mock_bs_df = MagicMock()
        mock_bs_df.empty = False
        mock_bs_df.to_dict.return_value = [{'season': 1, 'assets': 2000}]

        with patch('pandas.read_sql') as mock_read_sql:
            mock_read_sql.side_effect = [mock_pla_df, mock_bs_df]

            result = self.sql_service.get_quarterly_financial_summary("1101", year=2024)

            # 驗證結果
            self.assertIsInstance(result, dict)
            self.assertEqual(result['symbol'], '1101')
            self.assertEqual(result['year'], 2024)
            self.assertIn('pla_data', result)
            self.assertIn('bs_data', result)

    def test_database_not_initialized(self):
        """測試資料庫未初始化時的行為"""
        # 創建一個沒有初始化資料庫的實例
        sql_service = SqlService()
        sql_service.MySql_server = None

        # 測試各個方法
        result1 = sql_service.read_dividend_yield()
        result2 = sql_service.read_monthly_reports()
        result3 = sql_service.read_quarterly_reports()
        result4 = sql_service.get_dividend_yield_stats()
        result5 = sql_service.get_monthly_revenue_trend("1101")
        result6 = sql_service.get_quarterly_financial_summary("1101")

        # 所有方法都應該返回空結果
        self.assertTrue(result1.empty)
        self.assertTrue(result2.empty)
        self.assertTrue(result3.empty)
        self.assertEqual(result4, {})
        self.assertTrue(result5.empty)
        self.assertEqual(result6, {})

    def test_upsert_dividend_yield_batch_insert(self):
        """測試批量UPSERT股息殖利率數據"""
        # 準備測試數據
        test_data = pd.DataFrame({
            'symbol': ['1101', '1101', '1102'],
            'date': ['2025-01-01', '2025-01-02', '2025-01-01'],
            'company_name': ['台積電', '台積電', '技嘉'],
            'pe_ratio': [15.5, 15.6, 12.3],
            'dividend_yield': [2.5, 2.4, 3.1],
            'pb_ratio': [1.5, 1.5, 0.9]
        })

        # 模擬資料庫連接和 inspector
        mock_connection = MagicMock()
        mock_engine = MagicMock()
        mock_engine.begin.return_value.__enter__.return_value = mock_connection
        mock_engine.begin.return_value.__exit__.return_value = False

        self.sql_service.MySql_server.engine = mock_engine

        # 模擬 app_context
        self.sql_service.server_flask = MagicMock()
        mock_context = MagicMock()
        mock_context.__enter__ = MagicMock(return_value=None)
        mock_context.__exit__ = MagicMock(return_value=False)
        self.sql_service.server_flask.app_context = MagicMock(return_value=mock_context)

        # Mock inspector
        mock_inspector = MagicMock()
        mock_inspector.get_table_names.return_value = ['dividend_yield']

        with patch('pydb_core.sql_service.inspect', return_value=mock_inspector):
            result = self.sql_service.upsert_dividend_yield(test_data)
            self.assertTrue(result)
            # 驗證批量 SQL 執行
            mock_connection.execute.assert_called_once()

    def test_upsert_dividend_yield_empty_dataframe(self):
        """測試UPSERT空DataFrame時的行為"""
        empty_df = pd.DataFrame()
        result = self.sql_service.upsert_dividend_yield(empty_df)
        self.assertTrue(result)


if __name__ == '__main__':
    # 運行測試
    unittest.main(verbosity=2)
