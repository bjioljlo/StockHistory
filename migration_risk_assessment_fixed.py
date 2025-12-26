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

    def perform_risk_assessment(self) -> Dict[str, Any]:
        """執行風險評估"""
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

            # 評估風險
            assessment['risks'] = self._assess_risks()

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

            # 獲取樣本表格
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s LIMIT 3", (self.config.database,))
            sample_tables = [row[0] for row in cursor.fetchall()]

            return {
                'table_count': table_count,
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

    def _assess_risks(self) -> List[Dict[str, Any]]:
        """評估風險"""
        risks = []

        cursor = self.connection.cursor()

        try:
            # 檢查總表格數
            cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s", (self.config.database,))
            table_count = cursor.fetchone()[0]

            if table_count > 500:
                risks.append({
                    'category': 'data_volume',
                    'severity': 'high',
                    'description': f'表格數量龐大 ({table_count}個)',
                    'impact': '遷移時間長，風險高'
                })

            # 業務連續性風險
            risks.extend([
                {
                    'category': 'business_continuity',
                    'severity': 'high',
                    'description': '遷移期間系統停機',
                    'impact': '無法更新股票資料'
                },
                {
                    'category': 'business_continuity',
                    'severity': 'medium',
                    'description': '遷移失敗需要回滾',
                    'impact': '額外時間成本'
                }
            ])

        finally:
            cursor.close()

        return risks

    def _assess_system_impact(self) -> Dict[str, Any]:
        """評估系統影響"""
        return {
            'estimated_downtime': '2-4小時',
            'rollback_time': '1小時',
            'resource_requirements': {
                'cpu': '低',
                'memory': '中',
                'disk_space': '當前資料庫大小的1.5倍'
            }
        }

    def _develop_mitigation_strategies(self, risks: List[Dict[str, Any]]) -> List[str]:
        """開發緩解策略"""
        strategies = [
            '建立完整資料庫備份',
            '在測試環境驗證遷移腳本',
            '準備回滾計劃',
            '安排維護時段執行',
            '監控遷移過程'
        ]

        # 根據風險類型添加特定策略
        risk_categories = set(risk['category'] for risk in risks)

        if 'data_volume' in risk_categories:
            strategies.append('分批處理大型表格')

        if 'business_continuity' in risk_categories:
            strategies.append('準備備用系統')

        return strategies

    def _generate_recommendations(self, assessment: Dict[str, Any]) -> List[str]:
        """生成建議"""
        recommendations = []

        risks = assessment.get('risks', [])
        high_severity_risks = [r for r in risks if r.get('severity') == 'high']

        if high_severity_risks:
            recommendations.append('⚠️ 發現高風險項目，建議仔細評估')
        else:
            recommendations.append('✅ 風險評估完成，可以開始遷移')

        recommendations.extend([
            '建議先在測試環境完整驗證',
            '準備詳細的遷移執行計劃',
            '安排專人監控遷移過程'
        ])

        return recommendations

    def print_report(self, assessment: Dict[str, Any]):
        """列印評估報告"""
        print("\n" + "="*60)
        print("📊 資料遷移風險評估報告")
        print("="*60)

        if assessment['status'] == 'failed':
            print(f"❌ 評估失敗: {assessment.get('error', '未知錯誤')}")
            return

        # 資料庫資訊
        db_info = assessment.get('database_info', {})
        print(f"\n🗄️  資料庫資訊:")
        print(f"  表格數量: {db_info.get('table_count', 'N/A')}")
        print(f"  MySQL版本: {db_info.get('database_version', 'N/A')}")
        print(f"  樣本表格: {db_info.get('sample_tables', [])[:3]}")

        # 風險總結
        risks = assessment.get('risks', [])
        high_risks = [r for r in risks if r.get('severity') == 'high']
        print(f"\n⚠️  風險總結:")
        print(f"  高風險: {len(high_risks)} 項")
        print(f"  中風險: {len([r for r in risks if r.get('severity') == 'medium'])} 項")

        # 詳細風險
        if risks:
            print("\n🔍 詳細風險:")
            for i, risk in enumerate(risks, 1):
                severity_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(risk.get('severity'), '⚪')
                print(f"  {i}. {severity_icon} {risk.get('description', '')}")

        # 影響評估
        impact = assessment.get('impact_assessment', {})
        print(f"\n📈 影響評估:")
        print(f"  預估停機時間: {impact.get('estimated_downtime', 'N/A')}")

        # 建議
        recommendations = assessment.get('recommendations', [])
        if recommendations:
            print("\n💡 建議:")
            for rec in recommendations:
                print(f"  • {rec}")

        print("\n" + "="*60)

def main():
    """主函數"""
    print("開始運行風險評估腳本")
    config = DatabaseConfig()

    assessor = MigrationRiskAssessor(config)
    assessment = assessor.perform_risk_assessment()
    assessor.print_report(assessment)

    # 返回狀態
    if assessment['status'] == 'failed':
        print("\n❌ 風險評估失敗")
        return 1
    elif any(r.get('severity') == 'high' for r in assessment.get('risks', [])):
        print("\n⚠️  發現高風險項目，建議仔細評估")
        return 2
    else:
        print("\n✅ 風險評估完成，可以繼續規劃遷移")
        return 0

if __name__ == "__main__":
    sys.exit(main())
