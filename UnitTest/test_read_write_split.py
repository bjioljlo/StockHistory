"""
讀寫分離服務單元測試

測試 ReadWriteSplitService 類別的各項功能
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.Common.ReadWriteSplitService import (
    ReadWriteSplitService,
    ReadWriteSplitAnalyzer,
    create_read_write_split_service,
    analyze_read_write_split_feasibility
)


class TestReadWriteSplitService(unittest.TestCase):

    def setUp(self):
        """測試前準備"""
        self.config = {
            'read_write_split': {
                'write_master': {
                    'type': 'mysql',
                    'host': 'mysql-master',
                    'port': 3306,
                    'database': 'stock_data',
                    'username': 'user',
                    'password': 'pass',
                    'pool_size': 5,
                    'max_overflow': 10
                },
                'read_replicas': [
                    {
                        'type': 'mysql',
                        'host': 'mysql-replica-1',
                        'port': 3306,
                        'database': 'stock_data',
                        'username': 'user',
                        'password': 'pass',
                        'pool_size': 10,
                        'max_overflow': 20
                    },
                    {
                        'type': 'mysql',
                        'host': 'mysql-replica-2',
                        'port': 3306,
                        'database': 'stock_data',
                        'username': 'user',
                        'password': 'pass',
                        'pool_size': 10,
                        'max_overflow': 20
                    }
                ]
            }
        }

    @patch('src.Common.ReadWriteSplitService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.ReadWriteSplitService.create_engine')
    def test_initialization_with_replicas(self, mock_engine, mock_open, mock_yaml):
        """測試有讀取副本的初始化"""
        mock_yaml.return_value = self.config

        # 模擬引擎創建
        mock_write_engine = Mock()
        mock_read_engine1 = Mock()
        mock_read_engine2 = Mock()
        mock_engine.side_effect = [mock_write_engine, mock_read_engine1, mock_read_engine2]

        service = ReadWriteSplitService('config.yml')

        self.assertIsNotNone(service.write_engine)
        self.assertEqual(len(service.read_engines), 2)
        self.assertEqual(mock_engine.call_count, 3)  # 1 write + 2 read

    @patch('src.Common.ReadWriteSplitService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.ReadWriteSplitService.create_engine')
    def test_initialization_without_replicas(self, mock_engine, mock_open, mock_yaml):
        """測試沒有讀取副本的初始化"""
        config_no_replicas = {
            'read_write_split': {
                'write_master': self.config['read_write_split']['write_master'],
                'read_replicas': []
            }
        }
        mock_yaml.return_value = config_no_replicas

        mock_write_engine = Mock()
        mock_engine.return_value = mock_write_engine

        service = ReadWriteSplitService('config.yml')

        self.assertIsNotNone(service.write_engine)
        self.assertEqual(len(service.read_engines), 0)

    @patch('src.Common.ReadWriteSplitService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.ReadWriteSplitService.create_engine')
    def test_get_write_engine_healthy(self, mock_engine, mock_open, mock_yaml):
        """測試獲取健康的寫入引擎"""
        mock_yaml.return_value = self.config
        mock_write_engine = Mock()
        mock_engine.return_value = mock_write_engine

        service = ReadWriteSplitService('config.yml')

        # Mock 健康檢查通過
        mock_conn = Mock()
        mock_write_engine.connect.return_value = mock_conn
        mock_conn.execute.return_value.fetchone.return_value = (1,)

        engine = service.get_write_engine()
        self.assertEqual(engine, mock_write_engine)

    @patch('src.Common.ReadWriteSplitService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.ReadWriteSplitService.create_engine')
    def test_get_write_engine_unhealthy(self, mock_engine, mock_open, mock_yaml):
        """測試寫入引擎健康檢查失敗"""
        mock_yaml.return_value = self.config
        mock_write_engine = Mock()
        mock_engine.return_value = mock_write_engine

        service = ReadWriteSplitService('config.yml')

        # Mock 健康檢查失敗
        mock_write_engine.connect.side_effect = Exception("Connection failed")

        engine = service.get_write_engine()
        self.assertIsNone(engine)

    @patch('src.Common.ReadWriteSplitService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.ReadWriteSplitService.create_engine')
    def test_get_read_engine_with_replicas(self, mock_engine, mock_open, mock_yaml):
        """測試有副本時的讀取引擎獲取"""
        mock_yaml.return_value = self.config

        mock_write_engine = Mock()
        mock_read_engine1 = Mock()
        mock_read_engine2 = Mock()
        mock_engine.side_effect = [mock_write_engine, mock_read_engine1, mock_read_engine2]

        service = ReadWriteSplitService('config.yml')

        # Mock 健康檢查
        for engine in [mock_read_engine1, mock_read_engine2]:
            mock_conn = Mock()
            engine.connect.return_value = mock_conn
            mock_conn.execute.return_value.fetchone.return_value = (1,)

        # 測試負載均衡
        engine1 = service.get_read_engine()
        engine2 = service.get_read_engine()

        # 應該輪流返回不同的引擎
        self.assertIn(engine1, [mock_read_engine1, mock_read_engine2])
        self.assertIn(engine2, [mock_read_engine1, mock_read_engine2])

    @patch('src.Common.ReadWriteSplitService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.ReadWriteSplitService.create_engine')
    def test_get_read_engine_without_replicas(self, mock_engine, mock_open, mock_yaml):
        """測試沒有副本時的讀取引擎獲取"""
        config_no_replicas = {
            'read_write_split': {
                'write_master': self.config['read_write_split']['write_master'],
                'read_replicas': []
            }
        }
        mock_yaml.return_value = config_no_replicas

        mock_write_engine = Mock()
        mock_engine.return_value = mock_write_engine

        service = ReadWriteSplitService('config.yml')

        # Mock 寫入引擎健康
        mock_conn = Mock()
        mock_write_engine.connect.return_value = mock_conn
        mock_conn.execute.return_value.fetchone.return_value = (1,)

        engine = service.get_read_engine()
        self.assertEqual(engine, mock_write_engine)  # 應該返回寫入引擎

    @patch('src.Common.ReadWriteSplitService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.ReadWriteSplitService.create_engine')
    def test_execute_write(self, mock_engine, mock_open, mock_yaml):
        """測試寫入操作執行"""
        mock_yaml.return_value = self.config
        mock_write_engine = Mock()
        mock_engine.return_value = mock_write_engine

        service = ReadWriteSplitService('config.yml')

        # Mock 寫入引擎和健康檢查
        mock_conn = Mock()
        mock_write_engine.connect.return_value = mock_conn
        mock_conn.execute.return_value = Mock(rowcount=1)

        result = service.execute_write("INSERT INTO test VALUES (?)", [123])

        mock_conn.execute.assert_called_with("INSERT INTO test VALUES (?)", [123])
        mock_conn.commit.assert_called_once()

    @patch('src.Common.ReadWriteSplitService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.ReadWriteSplitService.create_engine')
    def test_execute_read(self, mock_engine, mock_open, mock_yaml):
        """測試讀取操作執行"""
        mock_yaml.return_value = self.config

        mock_write_engine = Mock()
        mock_read_engine = Mock()
        mock_engine.side_effect = [mock_write_engine, mock_read_engine]

        service = ReadWriteSplitService('config.yml')

        # Mock 讀取引擎健康檢查
        mock_conn = Mock()
        mock_read_engine.connect.return_value = mock_conn
        mock_conn.execute.return_value.fetchall.return_value = [(1, 'test'), (2, 'data')]

        results = service.execute_read("SELECT * FROM test")

        mock_conn.execute.assert_called_with("SELECT * FROM test", None)
        self.assertEqual(results, [(1, 'test'), (2, 'data')])

    @patch('src.Common.ReadWriteSplitService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.ReadWriteSplitService.create_engine')
    def test_get_cluster_status(self, mock_engine, mock_open, mock_yaml):
        """測試叢集狀態獲取"""
        mock_yaml.return_value = self.config

        mock_write_engine = Mock()
        mock_read_engine1 = Mock()
        mock_read_engine2 = Mock()
        mock_engine.side_effect = [mock_write_engine, mock_read_engine1, mock_read_engine2]

        service = ReadWriteSplitService('config.yml')

        status = service.get_cluster_status()

        self.assertIn('write_master', status)
        self.assertIn('read_replicas', status)
        self.assertEqual(len(status['read_replicas']), 2)

        # 檢查副本編號
        self.assertEqual(status['read_replicas'][0]['id'], 1)
        self.assertEqual(status['read_replicas'][1]['id'], 2)

    @patch('src.Common.ReadWriteSplitService.yaml.safe_load')
    @patch('builtins.open')
    def test_analyze_read_write_split_benefits(self, mock_open, mock_yaml):
        """測試讀寫分離效益分析"""
        mock_yaml.return_value = self.config

        service = ReadWriteSplitService('config.yml')

        analysis = service.analyze_read_write_split_benefits()

        self.assertIn('current_setup', analysis)
        self.assertIn('performance_benefits', analysis)
        self.assertIn('scalability_improvements', analysis)
        self.assertIn('high_availability_features', analysis)
        self.assertIn('recommendations', analysis)

        # 檢查當前設定
        setup = analysis['current_setup']
        self.assertTrue(setup['has_write_master'])
        self.assertEqual(setup['read_replicas_count'], 2)
        self.assertTrue(setup['read_write_split_enabled'])

    @patch('src.Common.ReadWriteSplitService.yaml.safe_load')
    @patch('builtins.open')
    def test_simulate_read_write_split(self, mock_open, mock_yaml):
        """測試讀寫分離模擬"""
        mock_yaml.return_value = self.config

        service = ReadWriteSplitService('config.yml')

        simulation = service.simulate_read_write_split(read_percentage=0.8)

        self.assertIn('assumptions', simulation)
        self.assertIn('current_single_db', simulation)
        self.assertIn('with_read_write_split', simulation)
        self.assertIn('estimated_improvements', simulation)

        # 檢查假設
        assumptions = simulation['assumptions']
        self.assertEqual(assumptions['total_operations'], 1000)
        self.assertEqual(assumptions['read_percentage'], 0.8)

        # 檢查改善估計
        improvements = simulation['estimated_improvements']
        self.assertIn('read_latency_reduction', improvements)
        self.assertIn('write_latency_stability', improvements)
        self.assertIn('overall_throughput_increase', improvements)

    @patch('src.Common.ReadWriteSplitService.yaml.safe_load')
    @patch('builtins.open')
    def test_generate_read_write_split_config(self, mock_open, mock_yaml):
        """測試讀寫分離配置生成"""
        mock_yaml.return_value = self.config

        service = ReadWriteSplitService('config.yml')

        config_template = service.generate_read_write_split_config()

        self.assertIn('read_write_split', config_template)
        rw_config = config_template['read_write_split']

        self.assertIn('write_master', rw_config)
        self.assertIn('read_replicas', rw_config)
        self.assertIn('load_balancing', rw_config)
        self.assertIn('monitoring', rw_config)

        # 檢查副本數量
        replicas = rw_config['read_replicas']
        self.assertEqual(len(replicas), 2)

    @patch('src.Common.ReadWriteSplitService.yaml.safe_load')
    @patch('builtins.open')
    def test_create_migration_plan(self, mock_open, mock_yaml):
        """測試遷移計劃創建"""
        mock_yaml.return_value = self.config

        service = ReadWriteSplitService('config.yml')

        plan = service.create_migration_plan()

        self.assertIn('phase_1_assessment', plan)
        self.assertIn('phase_2_setup', plan)
        self.assertIn('phase_3_migration', plan)
        self.assertIn('phase_4_optimization', plan)
        self.assertIn('risks_and_mitigations', plan)

        # 檢查階段持續時間
        self.assertEqual(plan['phase_1_assessment']['duration'], '1-2週')
        self.assertEqual(plan['phase_2_setup']['duration'], '1週')
        self.assertEqual(plan['phase_3_migration']['duration'], '3-5天')

    def test_build_connection_uri_mysql(self):
        """測試 MySQL 連線 URI 建構"""
        service = ReadWriteSplitService.__new__(ReadWriteSplitService)  # 不調用 __init__

        config = {
            'type': 'mysql',
            'host': 'localhost',
            'port': 3306,
            'database': 'test',
            'username': 'user',
            'password': 'pass'
        }

        uri = service._build_connection_uri(config)
        expected = "mysql+pymysql://user:pass@localhost:3306/test"
        self.assertEqual(uri, expected)

    def test_build_connection_uri_postgresql(self):
        """測試 PostgreSQL 連線 URI 建構"""
        service = ReadWriteSplitService.__new__(ReadWriteSplitService)

        config = {
            'type': 'postgresql',
            'host': 'localhost',
            'port': 5432,
            'database': 'test',
            'username': 'user',
            'password': 'pass'
        }

        uri = service._build_connection_uri(config)
        expected = "postgresql://user:pass@localhost:5432/test"
        self.assertEqual(uri, expected)

    def test_build_connection_uri_invalid_type(self):
        """測試無效資料庫類型的 URI 建構"""
        service = ReadWriteSplitService.__new__(ReadWriteSplitService)

        config = {
            'type': 'invalid',
            'host': 'localhost',
            'port': 3306,
            'database': 'test'
        }

        with self.assertRaises(ValueError):
            service._build_connection_uri(config)


class TestReadWriteSplitAnalyzer(unittest.TestCase):

    def setUp(self):
        """測試前準備"""
        self.config = {
            'database': {
                'mysql': {
                    'host': 'localhost',
                    'port': 3306
                }
            }
        }

    @patch('src.Common.ReadWriteSplitService.yaml.safe_load')
    @patch('builtins.open')
    def test_analyze_workload_pattern(self, mock_open, mock_yaml):
        """測試工作負載模式分析"""
        mock_yaml.return_value = self.config

        analyzer = ReadWriteSplitAnalyzer('config.yml')

        analysis = analyzer.analyze_workload_pattern()

        self.assertIn('estimated_read_write_ratio', analysis)
        self.assertIn('peak_hours_pattern', analysis)
        self.assertIn('query_types', analysis)
        self.assertIn('recommendations', analysis)

        # 檢查讀寫比例估計
        ratio = analysis['estimated_read_write_ratio']
        self.assertIn('read_operations', ratio)
        self.assertIn('write_operations', ratio)

        # 檢查建議
        recommendations = analysis['recommendations']
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)

    @patch('src.Common.ReadWriteSplitService.yaml.safe_load')
    @patch('builtins.open')
    def test_calculate_optimal_replica_count(self, mock_open, mock_yaml):
        """測試最佳副本數量計算"""
        mock_yaml.return_value = self.config

        analyzer = ReadWriteSplitAnalyzer('config.yml')

        load = {
            'read_qps': 500,
            'write_qps': 50
        }

        result = analyzer.calculate_optimal_replica_count(load)

        self.assertIn('input_load', result)
        self.assertIn('calculations', result)
        self.assertIn('recommendations', result)

        # 檢查計算結果
        calc = result['calculations']
        self.assertIn('read_replicas_needed', calc)
        self.assertIn('write_instances_needed', calc)

        # 檢查建議
        rec = result['recommendations']
        self.assertIn('read_replicas', rec)
        self.assertIn('write_instances', rec)
        self.assertIn('total_instances', rec)


class TestUtilityFunctions(unittest.TestCase):

    @patch('src.Common.ReadWriteSplitService.yaml.safe_load')
    @patch('builtins.open')
    @patch('src.Common.ReadWriteSplitService.create_engine')
    def test_create_read_write_split_service(self, mock_engine, mock_open, mock_yaml):
        """測試服務創建工具函數"""
        mock_yaml.return_value = {}

        service = create_read_write_split_service('config.yml')

        self.assertIsInstance(service, ReadWriteSplitService)

    @patch('src.Common.ReadWriteSplitService.ReadWriteSplitAnalyzer')
    @patch('src.Common.ReadWriteSplitService.ReadWriteSplitService')
    @patch('src.Common.ReadWriteSplitService.yaml.safe_load')
    @patch('builtins.open')
    def test_analyze_read_write_split_feasibility(self, mock_open, mock_yaml, mock_service, mock_analyzer):
        """測試可行性分析工具函數"""
        mock_yaml.return_value = {}

        # Mock 服務和分析器
        mock_service_instance = Mock()
        mock_service_instance.get_cluster_status.return_value = {'write_master': {'healthy': True}, 'read_replicas': []}
        mock_service_instance.analyze_read_write_split_benefits.return_value = {'current_setup': {'read_replicas_count': 0}}
        mock_service_instance.simulate_read_write_split.return_value = {'simulation': 'data'}
        mock_service_instance.create_migration_plan.return_value = {'plan': 'data'}

        mock_analyzer_instance = Mock()
        mock_analyzer_instance.analyze_workload_pattern.return_value = {'workload': 'analysis'}

        mock_service.return_value = mock_service_instance
        mock_analyzer.return_value = mock_analyzer_instance

        result = analyze_read_write_split_feasibility('config.yml')

        self.assertIn('workload_analysis', result)
        self.assertIn('cluster_status', result)
        self.assertIn('benefits_analysis', result)
        self.assertIn('simulation_results', result)
        self.assertIn('migration_plan', result)
        self.assertIn('feasibility_score', result)
        self.assertIn('implementation_complexity', result)
        self.assertIn('estimated_roi', result)


if __name__ == '__main__':
    unittest.main()
