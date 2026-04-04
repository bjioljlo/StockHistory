"""
StockHistory 查詢優化服務

提供慢查詢分析、索引優化建議和查詢效能優化功能。
支援 MySQL 查詢分析和優化建議。
"""

import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import yaml
from sqlalchemy import text, create_engine, inspect
import pymongo
from sqlalchemy.exc import SQLAlchemyError
import re


class QueryOptimizer:
    """查詢優化服務類別"""

    def __init__(self, config_path='config.yml'):
        self.config = self._load_config(config_path)
        self.db_config = self.config.get('database', {}).get('mysql', {})

        # 設定日誌
        logging.basicConfig(
            filename='logs/query_optimizer.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _load_config(self, config_path):
        """載入配置檔案"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"載入配置檔案失敗: {e}")
            return {}

    def _get_mysql_connection(self):
        """獲取MySQL連線"""
        connection_string = (
            f"mysql+pymysql://{self.db_config.get('user', 'root')}:"
            f"{self.db_config.get('password', '')}@"
            f"{self.db_config.get('host', 'localhost')}:"
            f"{self.db_config.get('port', 3306)}/"
            f"{self.db_config.get('databasename', 'demo')}"
        )
        return create_engine(connection_string)

    def analyze_slow_queries(self, days: int = 7) -> List[Dict[str, Any]]:
        """分析慢查詢日誌"""
        try:
            engine = self._get_mysql_connection()

            # 查詢慢查詢日誌（需要啟用MySQL慢查詢日誌）
            query = """
                SELECT
                    sql_text,
                    exec_count,
                    avg_timer_wait/1000000000 as avg_time_sec,
                    min_timer_wait/1000000000 as min_time_sec,
                    max_timer_wait/1000000000 as max_time_sec,
                    sum_timer_wait/1000000000 as total_time_sec,
                    last_seen
                FROM performance_schema.events_statements_summary_by_digest
                WHERE avg_timer_wait > 1000000000  -- 超過1秒
                ORDER BY avg_timer_wait DESC
                LIMIT 50
            """

            with engine.connect() as conn:
                result = conn.execute(text(query))
                slow_queries = []

                for row in result:
                    slow_queries.append({
                        'sql_text': row[0],
                        'exec_count': row[1],
                        'avg_time_sec': row[2],
                        'min_time_sec': row[3],
                        'max_time_sec': row[4],
                        'total_time_sec': row[5],
                        'last_seen': row[6],
                        'optimization_suggestions': self._analyze_query_pattern(row[0])
                    })

                return slow_queries

        except Exception as e:
            self.logger.error(f"分析慢查詢失敗: {e}")
            return []

    def _analyze_query_pattern(self, sql_text: str) -> List[str]:
        """分析查詢模式並提供優化建議"""
        suggestions = []

        if not sql_text:
            return suggestions

        sql_lower = sql_text.lower()

        # 檢查是否使用索引
        if 'where' in sql_lower and not any(keyword in sql_lower for keyword in ['=', '>', '<', 'between', 'in', 'like']):
            suggestions.append("WHERE 條件可能沒有使用索引")

        # 檢查SELECT *
        if 'select *' in sql_lower:
            suggestions.append("避免使用 SELECT *，明確指定需要的欄位")

        # 檢查子查詢
        if 'select' in sql_lower and '(' in sql_lower and 'from' in sql_lower:
            suggestions.append("考慮將子查詢改為JOIN以提升效能")

        # 檢查ORDER BY沒有索引
        if 'order by' in sql_lower:
            suggestions.append("ORDER BY 欄位建議建立索引")

        # 檢查GROUP BY沒有索引
        if 'group by' in sql_lower:
            suggestions.append("GROUP BY 欄位建議建立索引")

        # 檢查全表掃描
        if 'select' in sql_lower and 'where' not in sql_lower and 'limit' not in sql_lower:
            suggestions.append("查詢可能造成全表掃描，建議增加WHERE條件或LIMIT")

        return suggestions

    def analyze_table_indexes(self, table_name: str) -> Dict[str, Any]:
        """分析資料表的索引使用情況"""
        try:
            engine = self._get_mysql_connection()

            with engine.connect() as conn:
                # 獲取索引資訊
                indexes_query = text("""
                    SELECT
                        INDEX_NAME,
                        COLUMN_NAME,
                        SEQ_IN_INDEX,
                        CARDINALITY,
                        NULLABLE,
                        INDEX_TYPE
                    FROM information_schema.STATISTICS
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME = :table_name
                    ORDER BY INDEX_NAME, SEQ_IN_INDEX
                """)

                result = conn.execute(indexes_query, {'table_name': table_name})
                indexes = {}
                for row in result:
                    index_name = row[0]
                    if index_name not in indexes:
                        indexes[index_name] = {
                            'columns': [],
                            'cardinality': row[3],
                            'index_type': row[5]
                        }
                    indexes[index_name]['columns'].append({
                        'name': row[1],
                        'seq': row[2],
                        'nullable': row[4]
                    })

                # 分析索引使用統計
                usage_query = text("""
                    SELECT
                        object_schema,
                        object_name,
                        index_name,
                        count_read,
                        count_write,
                        count_fetch,
                        count_insert,
                        count_update,
                        count_delete
                    FROM performance_schema.table_io_waits_summary_by_index_usage
                    WHERE object_schema = DATABASE()
                      AND object_name = :table_name
                      AND index_name IS NOT NULL
                """)

                result = conn.execute(usage_query, {'table_name': table_name})
                index_usage = {}
                for row in result:
                    index_name = row[2]
                    index_usage[index_name] = {
                        'count_read': row[3] or 0,
                        'count_write': row[4] or 0,
                        'count_fetch': row[5] or 0,
                        'count_insert': row[6] or 0,
                        'count_update': row[7] or 0,
                        'count_delete': row[8] or 0
                    }

                # 生成索引優化建議
                recommendations = self._analyze_index_usage(table_name, indexes, index_usage)

                return {
                    'table_name': table_name,
                    'indexes': indexes,
                    'index_usage': index_usage,
                    'recommendations': recommendations
                }

        except Exception as e:
            self.logger.error(f"分析資料表索引失敗: {e}")
            return {}

    def _analyze_index_usage(self, table_name: str, indexes: Dict, index_usage: Dict) -> List[str]:
        """分析索引使用情況並生成建議"""
        recommendations = []

        # 檢查未使用的索引
        for index_name, usage in index_usage.items():
            total_usage = sum(usage.values())
            if total_usage == 0 and index_name != 'PRIMARY':
                recommendations.append(f"索引 '{index_name}' 可能未被使用，建議檢查是否需要")

        # 檢查寫入頻繁但讀取少的索引
        for index_name, usage in index_usage.items():
            if usage['count_write'] > usage['count_read'] * 10:
                recommendations.append(f"索引 '{index_name}' 寫入頻繁但讀取較少，考慮是否需要")

        # 檢查複合索引順序
        for index_name, index_info in indexes.items():
            if len(index_info['columns']) > 1:
                columns = [col['name'] for col in index_info['columns']]
                # 檢查是否按照選擇性排序（這裡是簡化的檢查）
                recommendations.append(f"複合索引 '{index_name}' ({', '.join(columns)}) 建議檢查欄位順序")

        # 建議新增索引
        recommendations.extend(self._suggest_new_indexes(table_name))

        return recommendations

    def _suggest_new_indexes(self, table_name: str) -> List[str]:
        """根據查詢模式建議新增索引"""
        suggestions = []

        try:
            engine = self._get_mysql_connection()

            with engine.connect() as conn:
                # 檢查是否有沒有索引的WHERE條件欄位
                query = text("""
                    SELECT
                        COLUMN_NAME,
                        DATA_TYPE,
                        COLUMN_KEY
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME = :table_name
                      AND COLUMN_KEY = ''
                      AND DATA_TYPE IN ('varchar', 'char', 'date', 'datetime', 'int', 'bigint')
                """)

                result = conn.execute(query, {'table_name': table_name})
                unindexed_columns = [row[0] for row in result]

                for col in unindexed_columns:
                    # 這是一個簡化的建議，實際應該基於具體的查詢模式
                    suggestions.append(f"考慮為欄位 '{col}' 建立索引（如果該欄位常用於查詢）")

        except Exception as e:
            self.logger.error(f"建議新增索引失敗: {e}")

        return suggestions

    def optimize_query(self, sql_query: str) -> Dict[str, Any]:
        """優化單個查詢"""
        try:
            engine = self._get_mysql_connection()

            with engine.connect() as conn:
                # 使用EXPLAIN分析查詢
                explain_query = f"EXPLAIN {sql_query}"
                result = conn.execute(text(explain_query))

                explain_result = []
                for row in result:
                    explain_result.append(dict(row._mapping))

                # 分析EXPLAIN結果
                analysis = self._analyze_explain_result(explain_result)

                # 生成優化後的查詢
                optimized_query = self._generate_optimized_query(sql_query, explain_result)

                return {
                    'original_query': sql_query,
                    'explain_result': explain_result,
                    'analysis': analysis,
                    'optimized_query': optimized_query,
                    'recommendations': analysis.get('recommendations', [])
                }

        except Exception as e:
            self.logger.error(f"優化查詢失敗: {e}")
            return {
                'original_query': sql_query,
                'error': str(e)
            }

    def _analyze_explain_result(self, explain_result: List[Dict]) -> Dict[str, Any]:
        """分析EXPLAIN結果"""
        analysis = {
            'recommendations': [],
            'warnings': [],
            'performance_score': 100
        }

        for row in explain_result:
            table = row.get('table', '')
            type_ = row.get('type', '')
            possible_keys = row.get('possible_keys', '')
            key = row.get('key', '')
            rows = row.get('rows', 0)
            extra = row.get('Extra', '')

            # 檢查全表掃描
            if type_ in ['ALL', 'index']:
                analysis['recommendations'].append(f"資料表 '{table}' 使用全表掃描，建議建立索引")
                analysis['performance_score'] -= 20

            # 檢查大量資料掃描
            if rows and rows > 10000:
                analysis['warnings'].append(f"資料表 '{table}' 掃描了 {rows} 行資料，考慮增加查詢條件")

            # 檢查是否使用索引
            if not key and possible_keys:
                analysis['recommendations'].append(f"資料表 '{table}' 有可用索引但未使用：{possible_keys}")

            # 檢查檔案排序
            if 'Using filesort' in str(extra):
                analysis['recommendations'].append(f"資料表 '{table}' 使用檔案排序，建議為ORDER BY欄位建立索引")
                analysis['performance_score'] -= 15

            # 檢查臨時表
            if 'Using temporary' in str(extra):
                analysis['recommendations'].append(f"資料表 '{table}' 使用臨時表，建議優化查詢結構")
                analysis['performance_score'] -= 25

        return analysis

    def _generate_optimized_query(self, original_query: str, explain_result: List[Dict]) -> str:
        """生成優化後的查詢（簡化的實現）"""
        # 這是一個簡化的優化建議生成器
        # 實際的查詢優化需要更複雜的邏輯

        optimized_query = original_query

        # 如果使用全表掃描，建議增加LIMIT
        for row in explain_result:
            if row.get('type') == 'ALL' and 'LIMIT' not in original_query.upper():
                if not optimized_query.upper().strip().endswith('LIMIT 100'):
                    optimized_query += " LIMIT 100"

        return optimized_query

    def create_index_recommendations(self, table_name: str) -> List[str]:
        """為資料表生成索引建議"""
        analysis = self.analyze_table_indexes(table_name)
        return analysis.get('recommendations', [])

    def get_database_performance_stats(self) -> Dict[str, Any]:
        """獲取資料庫整體效能統計"""
        try:
            engine = self._get_mysql_connection()

            with engine.connect() as conn:
                # 獲取連線統計
                connection_query = text("SHOW PROCESSLIST")
                connections = conn.execute(connection_query)
                active_connections = len([row for row in connections])

                # 獲取InnoDB統計
                innodb_query = text("SHOW ENGINE INNODB STATUS")
                innodb_result = conn.execute(innodb_query)
                innodb_status = innodb_result.fetchone()

                # 獲取緩衝池統計
                buffer_query = text("""
                    SELECT
                        pool_size,
                        pages_total,
                        pages_free,
                        pages_data,
                        pages_dirty,
                        pages_flushed
                    FROM information_schema.innodb_buffer_pool_stats
                """)
                buffer_result = conn.execute(buffer_query)
                buffer_stats = buffer_result.fetchone()

                return {
                    'active_connections': active_connections,
                    'innodb_status': str(innodb_status[2]) if innodb_status else '',
                    'buffer_pool': {
                        'pool_size': buffer_stats[0] if buffer_stats else 0,
                        'pages_total': buffer_stats[1] if buffer_stats else 0,
                        'pages_free': buffer_stats[2] if buffer_stats else 0,
                        'pages_data': buffer_stats[3] if buffer_stats else 0,
                        'pages_dirty': buffer_stats[4] if buffer_stats else 0,
                        'pages_flushed': buffer_stats[5] if buffer_stats else 0
                    } if buffer_stats else {}
                }

        except Exception as e:
            self.logger.error(f"獲取資料庫效能統計失敗: {e}")
            return {}

    def generate_optimization_report(self) -> Dict[str, Any]:
        """生成完整的優化報告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'database_stats': self.get_database_performance_stats(),
            'slow_queries': self.analyze_slow_queries(),
            'recommendations': []
        }

        # 收集所有建議
        all_recommendations = []

        # 從慢查詢中收集建議
        for query in report['slow_queries']:
            all_recommendations.extend(query.get('optimization_suggestions', []))

        # 去重複建議
        unique_recommendations = list(set(all_recommendations))
        report['recommendations'] = unique_recommendations

        return report
