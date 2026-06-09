"""
查詢優化服務單元測試

測試 QueryOptimizer 類別的各項功能
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import text
import pandas as pd

from pydb_core.query_optimizer import QueryOptimizer


class TestQueryOptimizer(unittest.TestCase):

    def setUp(self):
        """測試前準備"""
        self.config = {
            'database': {
                'mysql': {
                    'user': 'test',
                    'password': 'test',
                    'host': 'localhost',
                    'port': 3306,
                    'databasename': 'test_db'
                }
            }
        }

    @patch('src.Common.QueryOptimizer.yaml.safe_load')
    @patch('builtins.open')
    def test_initialization(self, mock_open, mock_yaml):
        """測試初始化"""
        mock_yaml.return_value = self.config

        optimizer = QueryOptimizer('config.yml')

        self.assertEqual(optimizer.db_config, self.config['database']['mysql'])

    @patch('pydb_core.query_optimizer.yaml.safe_load')
    @patch('builtins.open')
    @patch('pydb_core.query_optimizer.create_engine')
    def test_analyze_slow_queries(self, mock_engine, mock_open, mock_yaml):
        """測試慢查詢分析"""
        mock_yaml.return_value = self.config

        # 模擬資料庫連線和結果
        mock_conn = Mock()
        mock_engine.return_value.connect.return_value = mock_conn

        # 模擬慢查詢結果
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            ("SELECT * FROM large_table", 100, 5.5, 3.2, 8.1, 550.0, "2024-01-01 10:00:00")
        ]
        mock_conn.execute.return_value = mock_result

        optimizer = QueryOptimizer('config.yml')
        slow_queries = optimizer.analyze_slow_queries()

        self.assertEqual(len(slow_queries), 1)
        query = slow_queries[0]

        self.assertEqual(query['sql_text'], "SELECT * FROM large_table")
        self.assertEqual(query['exec_count'], 100)
        self.assertEqual(query['avg_time_sec'], 5.5)
        self.assertIn('optimization_suggestions', query)

    @patch('pydb_core.query_optimizer.yaml.safe_load')
    @patch('builtins.open')
    def test_analyze_query_pattern(self, mock_open, mock_yaml):
        """測試查詢模式分析"""
        mock_yaml.return_value = self.config

        optimizer = QueryOptimizer('config.yml')

        # 測試 SELECT * 查詢
        suggestions = optimizer._analyze_query_pattern("SELECT * FROM users WHERE id = 1")
        self.assertIn("避免使用 SELECT *", suggestions[0])

        # 測試沒有 WHERE 的查詢
        suggestions = optimizer._analyze_query_pattern("SELECT id FROM users")
        self.assertTrue(any("全表掃描" in s for s in suggestions))

        # 測試 ORDER BY 查詢
        suggestions = optimizer._analyze_query_pattern("SELECT * FROM users ORDER BY name")
        self.assertTrue(any("ORDER BY" in s for s in suggestions))

        # 測試子查詢
        suggestions = optimizer._analyze_query_pattern("SELECT * FROM users WHERE id IN (SELECT user_id FROM orders)")
        self.assertTrue(any("子查詢" in s for s in suggestions))

    @patch('pydb_core.query_optimizer.yaml.safe_load')
    @patch('builtins.open')
    @patch('pydb_core.query_optimizer.create_engine')
    def test_analyze_table_indexes(self, mock_engine, mock_open, mock_yaml):
        """測試資料表索引分析"""
        mock_yaml.return_value = self.config

        # 模擬資料庫連線和結果
        mock_conn = Mock()
        mock_engine.return_value.connect.return_value = mock_conn

        # 模擬索引資訊
        mock_indexes_result = Mock()
        mock_indexes_result.fetchall.return_value = [
            ("PRIMARY", "id", 1, 12345, "NO", "BTREE"),
            ("idx_name", "name", 1, 6789, "YES", "BTREE"),
            ("idx_name", "email", 2, 6789, "YES", "BTREE")
        ]
        mock_conn.execute.side_effect = [mock_indexes_result, Mock(), Mock()]  # 三次調用

        optimizer = QueryOptimizer('config.yml')
        analysis = optimizer.analyze_table_indexes("users")

        self.assertEqual(analysis['table_name'], "users")
        self.assertIn('PRIMARY', analysis['indexes'])
        self.assertIn('idx_name', analysis['indexes'])
        self.assertIn('recommendations', analysis)

    @patch('pydb_core.query_optimizer.yaml.safe_load')
    @patch('builtins.open')
    @patch('pydb_core.query_optimizer.create_engine')
    def test_optimize_query(self, mock_engine, mock_open, mock_yaml):
        """測試查詢優化"""
        mock_yaml.return_value = self.config

        # 模擬資料庫連線
        mock_conn = Mock()
        mock_engine.return_value.connect.return_value = mock_conn

        # 模擬 EXPLAIN 結果
        mock_explain_result = Mock()
        mock_explain_result.fetchall.return_value = [
            {'table': 'users', 'type': 'ALL', 'rows': 10000, 'Extra': 'Using filesort'}
        ]
        mock_conn.execute.return_value = mock_explain_result

        optimizer = QueryOptimizer('config.yml')
        result = optimizer.optimize_query("SELECT * FROM users ORDER BY name")

        self.assertEqual(result['original_query'], "SELECT * FROM users ORDER BY name")
        self.assertIn('explain_result', result)
        self.assertIn('analysis', result)
        self.assertIn('recommendations', result)

        # 檢查分析結果
        analysis = result['analysis']
        self.assertLess(analysis['performance_score'], 100)  # 應該有優化建議

    @patch('pydb_core.query_optimizer.yaml.safe_load')
    @patch('builtins.open')
    @patch('pydb_core.query_optimizer.create_engine')
    def test_get_database_performance_stats(self, mock_engine, mock_open, mock_yaml):
        """測試資料庫效能統計獲取"""
        mock_yaml.return_value = self.config

        # 模擬資料庫連線和結果
        mock_conn = Mock()
        mock_engine.return_value.connect.return_value = mock_conn

        # 模擬各種統計查詢結果
        mock_conn.execute.side_effect = [
            Mock(fetchall=lambda: [('process1',)]),  # SHOW PROCESSLIST
            Mock(fetchone=lambda: ('InnoDB status info',)),  # SHOW ENGINE INNODB STATUS
            Mock(fetchone=lambda: (8, 1000, 200, 800, 50, 25))  # 緩衝池統計
        ]

        optimizer = QueryOptimizer('config.yml')
        stats = optimizer.get_database_performance_stats()

        self.assertIn('active_connections', stats)
        self.assertIn('innodb_status', stats)
        self.assertIn('buffer_pool', stats)

        buffer_pool = stats['buffer_pool']
        self.assertEqual(buffer_pool['pool_size'], 8)
        self.assertEqual(buffer_pool['pages_total'], 1000)

    @patch('pydb_core.query_optimizer.yaml.safe_load')
    @patch('builtins.open')
    def test_generate_optimization_report(self, mock_open, mock_yaml):
        """測試優化報告生成"""
        mock_yaml.return_value = self.config

        optimizer = QueryOptimizer('config.yml')

        # Mock 相關方法
        with patch.object(optimizer, 'get_database_performance_stats', return_value={'test': 'stats'}), \
             patch.object(optimizer, 'analyze_slow_queries', return_value=[{'sql_text': 'SELECT 1'}]):

            report = optimizer.generate_optimization_report()

            self.assertIn('timestamp', report)
            self.assertIn('database_stats', report)
            self.assertIn('slow_queries', report)
            self.assertIn('recommendations', report)

    @patch('pydb_core.query_optimizer.yaml.safe_load')
    @patch('builtins.open')
    def test_create_index_recommendations(self, mock_open, mock_yaml):
        """測試索引建議創建"""
        mock_yaml.return_value = self.config

        optimizer = QueryOptimizer('config.yml')

        # Mock analyze_table_indexes 方法
        mock_analysis = {
            'recommendations': ['建議建立索引 idx_name ON users(name)']
        }

        with patch.object(optimizer, 'analyze_table_indexes', return_value=mock_analysis):
            recommendations = optimizer.create_index_recommendations("users")

            self.assertIsInstance(recommendations, list)
            self.assertEqual(len(recommendations), 1)

    @patch('pydb_core.query_optimizer.yaml.safe_load')
    @patch('builtins.open')
    def test_analyze_explain_result(self, mock_open, mock_yaml):
        """測試 EXPLAIN 結果分析"""
        mock_yaml.return_value = self.config

        optimizer = QueryOptimizer('config.yml')

        explain_result = [
            {'table': 'users', 'type': 'ALL', 'rows': 10000, 'Extra': 'Using filesort'},
            {'table': 'orders', 'type': 'ref', 'rows': 100, 'key': 'idx_user_id'}
        ]

        analysis = optimizer._analyze_explain_result(explain_result)

        self.assertIn('recommendations', analysis)
        self.assertIn('warnings', analysis)
        self.assertIn('performance_score', analysis)

        # 檢查是否有全表掃描的建議
        recommendations = analysis['recommendations']
        self.assertTrue(any('全表掃描' in rec for rec in recommendations))

        # 效能評分應該低於 100
        self.assertLess(analysis['performance_score'], 100)

    @patch('pydb_core.query_optimizer.yaml.safe_load')
    @patch('builtins.open')
    @patch('pydb_core.query_optimizer.create_engine')
    def test_suggest_new_indexes(self, mock_engine, mock_open, mock_yaml):
        """測試新增索引建議"""
        mock_yaml.return_value = self.config

        # 模擬資料庫連線
        mock_conn = Mock()
        mock_engine.return_value.connect.return_value = mock_conn

        # 模擬沒有索引的欄位
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            ("email", "varchar(255)", ""),
            ("phone", "varchar(20)", "")
        ]
        mock_conn.execute.return_value = mock_result

        optimizer = QueryOptimizer('config.yml')
        suggestions = optimizer._suggest_new_indexes("contacts")

        self.assertIsInstance(suggestions, list)
        # 應該包含為 email 和 phone 欄位建立索引的建議
        self.assertTrue(any('email' in s for s in suggestions))
        self.assertTrue(any('phone' in s for s in suggestions))


if __name__ == '__main__':
    unittest.main()
