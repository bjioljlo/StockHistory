#!/usr/bin/env python3
"""
資料遷移風險評估報告
基於實際資料庫連接評估資料庫遷移的潛在風險和影響
"""

import sys
import os
import pandas as pd
import mysql.connector
from datetime import datetime
from typing import Dict, List, Any
import logging
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """資料庫配置"""
    host: str = "localhost"
    user: str = "demo"
    password: str = "~Demo123"
    database: str = "demo"
    port: int = 3307

class MigrationRiskAssessor:
    """遷移風險評估器"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connection = None
        self.risks = []
        self.impact_assessment = {}

    def connect(self):
        """建立資料庫連接"""
        try:
            self.connection = mysql.connector.connect(
                host=self.config.host,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                port=self.config.port
            )
            logger.info("資料庫連接成功")
            return True
        except Exception as e:
            logger.error(f"資料庫連接失敗: {e}")
            return False

    def perform_comprehensive_risk_assessment(self) -> Dict[str, Any]:
        """執行綜合風險評估"""
        logger.info("=== 開始資料遷移風險評估 ===")

        if not self.connect():
            return {
                'status': 'failed',
                'error': '無法連接到資料庫',
                'recommendations': ['檢查資料庫服務是否正常運行', '驗證連接參數']
            }

        assessment = {
            'status': 'success',
            'database_info': {},
            'risks': [],
            'impact_assessment': {},
            'mitigation_strategies': [],
            'recommendations': []
        }

        try:
            # 獲取資料庫基本資訊
            assessment['database_info'] = self._get_database_info()

            # 評估資料量風險
            data_volume_risks = self._assess_data_volume_risks()
            assessment['risks'].extend(data_volume_risks)

            # 評估資料結構風險
            structure_risks = self._assess_data_structure_risks()
            assessment['risks'].extend(structure_risks)

            # 評估效能風險
            performance_risks = self._assess_performance_risks()
            assessment['risks'].extend(performance_risks)

            # 評估業務連續性風險
            business_risks = self._assess_business_continuity_risks()
            assessment['risks'].extend(business_risks)

            # 評估資料完整性風險
            integrity_risks = self._assess_data_integrity_risks()
            assessment['risks'].extend(integrity_risks)

            # 影響評估
            assessment['impact_assessment'] = self._assess_system_impact()

            # 緩解策略
            assessment['mitigation_strategies'] = self._develop_mitigation_strategies(assessment['risks'])

            # 生成建議
            assessment['recommendations'] = self._generate_recommendations(assessment)

        except Exception as e:
            logger.error(f"評估過程出錯: {e}")
            assessment['status'] = 'error'
            assessment['error'] = str(e)
        finally:
            if self.connection:
                self.connection.close()

        return assessment

    def _get_database_info(self) -> Dict[str, Any]:
        """獲取資料庫基本資訊"""
        cursor = self.connection.cursor()

        try:
            # 獲取表格數量
            cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s", (self.config.database,))
            table_count = cursor.fetchone()[0]

            # 獲取總資料量（估計）
            cursor.execute("SELECT SUM(data_length + index_length) FROM information_schema.tables WHERE table_schema = %s", (self.config.database,))
            total_size = cursor.fetchone()[0] or 0

            # 獲取樣本表格
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s LIMIT 5", (self.config.database,))
            sample_tables = [row[0] for row in cursor.fetchall()]

            return {
                'table_count': table_count,
                'estimated_size_mb': total_size / (1024 * 1024),
                'sample_tables': sample_tables,
                'database_version': self._get_mysql_version()
            }

        finally:
            cursor.close()

    def _get_mysql_version(self) -> str:
        """獲取MySQL版本"""
        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT VERSION()")
            return cursor.fetchone()[0]
        finally:
            cursor.close()

    def _assess_data_volume_risks(self) -> List[Dict[str, Any]]:
        """評估資料量相關風險"""
        risks = []

        cursor = self.connection.cursor()

        try:
            # 檢查總表格數
            cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s", (self.config.database,))
            table_count = cursor.fetchone()[0]

            if table_count > 1000:
                risks.append({
                    'category': 'data_volume',
                    'severity': 'high',
                    'description': f'表格數量過多 ({table_count}個)，遷移時間可能很長',
                    'impact': '增加遷移失敗風險和時間成本'
                })

            # 檢查單個表格大小
            cursor.execute("""
                SELECT table_name, data_length + index_length as size_bytes
                FROM information_schema.tables
                WHERE table_schema = %s
                ORDER BY size_bytes DESC
                LIMIT 5
            """, (self.config.database,))

            large_tables = cursor.fetchall()
            for table_name, size_bytes in large_tables:
                size_mb = size_bytes / (1024 * 1024)
                if size_mb > 100:  # 大於100MB
                    risks.append({
                        'category': 'data_volume',
                        'severity': 'medium',
                        'description': f'大型表格 {table_name}: {size_mb:.1f}MB',
                        'impact': '需要特別處理大型表格'
                    })

        finally:
            cursor.close()

        return risks

    def _assess_data_structure_risks(self) -> List[Dict[str, Any]]:
        """評估資料結構風險"""
        risks = []

        cursor = self.connection.cursor()

        try:
            # 檢查是否有外鍵約束
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.table_constraints
                WHERE constraint_schema = %s AND constraint_type = 'FOREIGN KEY'
            """, (self.config.database,))

            fk_count = cursor.fetchone()[0]
            if fk_count > 0:
                risks.append({
                    'category': 'data_structure',
                    'severity': 'high',
                    'description': f'存在外鍵約束 ({fk_count}個)，需要特殊處理',
                    'impact': '遷移順序和完整性約束'
                })

            # 檢查觸發器
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.triggers
                WHERE trigger_schema = %s
            """, (self.config.database,))

            trigger_count = cursor.fetchone()[0]
            if trigger_count > 0:
                risks.append({
                    'category': 'data_structure',
                    'severity': 'medium',
                    'description': f'存在觸發器 ({trigger_count}個)',
                    'impact': '可能影響資料同步和完整性'
                })

        finally:
            cursor.close()

        return risks

    def _assess_performance_risks(self) -> List[Dict[str, Any]]:
        """評估效能風險"""
        risks = []

        cursor = self.connection.cursor()

        try:
            # 檢查當前索引使用情況
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.statistics
                WHERE table_schema = %s
            """, (self.config.database,))

            index_count = cursor.fetchone()[0]
            if index_count < 10:  # 索引過少
                risks.append({
                    'category': 'performance',
                    'severity': 'low',
                    'description': f'索引數量較少 ({index_count}個)',
                    'impact': '新表格需要額外建立索引'
                })

        finally:
            cursor.close()

        return risks

    def _assess_business_continuity_risks(self) -> List[Dict[str, Any]]:
        """評估業務連續性風險"""
        risks = []

        # 業務連續性風險（基於一般知識）
        risks.extend([
            {
                'category': 'business_continuity',
                'severity': 'high',
                'description': '資料庫遷移期間系統不可用',
                'impact': '業務中斷，無法更新股票資料'
            },
            {
                'category': 'business_continuity',
                'severity': 'medium',
                'description': '遷移失敗需要回滾',
                'impact': '額外的時間成本和風險'
            },
            {
                'category': 'business_continuity',
                'severity': 'medium',
                'description': '資料驗證失敗導致延遲上線',
                'impact': '延長遷移時間線'
            }
        ])

        return risks

    def _assess_data_integrity_risks(self) -> List[Dict[str, Any]]:
        """評估資料完整性風險"""
        risks = []

        cursor = self.connection.cursor()

        try:
            # 檢查是否有空值
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]

            tables_with_nulls = []
            for table in tables[:10]:  # 檢查前10個表格
                try:
                    # 先檢查表格是否有date欄位
                    cursor.execute(f"""
                        SELECT COUNT(*) FROM information_schema.columns
                        WHERE table_schema = %s AND table_name = %s AND column_name = 'date'
                    """, (self.config.database, table))
                    has_date_column = cursor.fetchone()[0] > 0

                    if has_date_column:
                        cursor.execute(f"SELECT COUNT(*) FROM `{table}` WHERE `date` IS NULL")
                        null_dates = cursor.fetchone()[0]
                        if null_dates > 0:
                            tables_with_nulls.append(table)
                except Exception as e:
                    logger.warning(f"檢查表格 {table} 時出錯: {e}")
                    continue

            if tables_with_nulls:
                risks.append({
                    'category': 'data_integrity',
                    'severity': 'medium',
                    'description': f'部分表格存在空值日期: {tables_with_nulls[:3]}',
                    'impact': '需要資料清理和驗證'
                })

        finally:
            cursor.close()

        return risks

    def _assess_system_impact(self) -> Dict[str, Any]:
        """評估系統影響"""
        return {
            'estimated_downtime': '4-8小時',
            'rollback_time': '1-2小時',
            'resource_requirements': {
                'cpu': '中等',
                'memory': '高',
                'disk_space': '當前資料庫大小的2倍'
            },
            'testing_requirements': '完整的功能測試和資料驗證'
        }

    def _develop_mitigation_strategies(self, risks: List[Dict[str, Any]]) -> List[str]:
        """開發緩解策略"""
        strategies = []

        # 通用策略
        strategies.extend([
            '在維護時段執行遷移',
            '建立完整備份',
            '準備回滾計劃',
            '分批遷移以降低風險',
            '建立測試環境進行驗證'
        ])

        # 根據風險類型添加特定策略
        risk_categories = set(risk['category'] for risk in risks)

        if 'data_volume' in risk_categories:
            strategies.extend([
                '對大型表格單獨處理',
                '使用批次處理減少記憶體使用',
                '監控系統資源使用情況'
            ])

        if 'data_structure' in risk_categories:
            strategies.extend([
                '仔細規劃遷移順序',
                '驗證約束完整性',
                '準備約束重建腳本'
            ])

        if 'business_continuity' in risk_categories:
            strategies.extend([
                '安排維護通知',
                '準備備用系統',
                '最小化停機時間'
            ])

        return strategies

    def _generate_recommendations(self, assessment: Dict[str, Any]) -> List[str]:
        """生成建議"""
        recommendations = []

        risks = assessment.get('risks', [])
        high_severity_risks = [r for r in risks if r.get('severity') == 'high']

        if high_severity_risks:
            recommendations.append('⚠️ 發現高風險項目，建議仔細評估後再執行遷移')
        else:
            recommendations.append('✅ 風險評估完成，可以開始規劃遷移')

        recommendations.extend([
            '建議在測試環境完整驗證遷移腳本',
            '準備詳細的遷移執行計劃',
            '安排專人監控遷移過程',
            '建立遷移後的驗證流程'
        ])

        return recommendations

    def print_assessment_report(self, assessment: Dict[str, Any]):
        """列印評估報告"""
        print("\n" + "="*80)
        print("📊 資料遷移風險評估報告")
        print("="*80)

        if assessment['status'] == 'failed':
            print(f"❌ 評估失敗: {assessment.get('error', '未知錯誤')}")
            print("\n建議:")
            for rec in assessment.get('recommendations', []):
                print(f"  • {rec}")
            return

        # 資料庫資訊
        db_info = assessment.get('database_info', {})
        print("🗄️  資料庫資訊:" )   
        print(f"  表格數量: {db_info.get('table_count', 'N/A')}")
        print(f"  預估大小: {db_info.get('estimated_size_mb', 0):.1f} MB")
        print(f"  MySQL版本: {db_info.get('database_version', 'N/A')}")
        print(f"  樣本表格: {db_info.get('sample_tables', [])[:3]}")
        

        # 風險總結
        risks = assessment.get('risks', [])
        print("⚠️  風險總結:")
        high_risks = [r for r in risks if r.get('severity') == 'high']
        medium_risks = [r for r in risks if r.get('severity') == 'medium']
        low_risks = [r for r in risks if r.get('severity') == 'low']

        print(f"  高風險: {len(high_risks)} 項")
        print(f"  中風險: {len(medium_risks)} 項")
        print(f"  低風險: {len(low_risks)} 項")

        # 詳細風險
        if risks:
            print("\n🔍 詳細風險:")
            for i, risk in enumerate(risks, 1):
                severity_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(risk.get('severity'), '⚪')
                print(f"  {i}. {severity_icon} [{risk.get('category', 'unknown')}] {risk.get('description', '')}")
                print(f"     影響: {risk.get('impact', '')}")

        # 影響評估
        impact = assessment.get('impact_assessment', {})
        if impact:
            print("\n📈 影響評估:")
            print(f"  預估停機時間: {impact.get('estimated_downtime', 'N/A')}")
            print(f"  回滾時間: {impact.get('rollback_time', 'N/A')}")

            resources = impact.get('resource_requirements', {})
            if resources:
                print("  資源需求:")
                for resource, level in resources.items():
                    print(f"    {resource}: {level}")

        # 緩解策略
        strategies = assessment.get('mitigation_strategies', [])
        if strategies:
            print("\n🛡️  緩解策略:")
            for i, strategy in enumerate(strategies, 1):
                print(f"  {i}. {strategy}")

        # 建議
        recommendations = assessment.get('recommendations', [])
        if recommendations:
            print("\n💡 建議:")
            for rec in recommendations:
                print(f"  • {rec}")

        print("\n" + "="*80)

def main():
    """主函數"""
    config = DatabaseConfig()

    assessor = MigrationRiskAssessor(config)
    assessment = assessor.perform_comprehensive_risk_assessment()
    assessor.print_assessment_report(assessment)

    # 返回狀態
    if assessment['status'] == 'failed':
        print(f"\n❌ 風險評估失敗")
        return 1
    elif any(r.get('severity') == 'high' for r in assessment.get('risks', [])):
        print(f"\n⚠️  發現高風險項目，建議仔細評估")
        return 2
    else:
        print(f"\n✅ 風險評估完成，可以繼續規劃遷移")
        return 0

if __name__ == "__main__":
    sys.exit(main())
