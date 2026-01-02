#!/usr/bin/env python3
"""
資料遷移驗證腳本
驗證遷移後的資料完整性和正確性
"""

import sys
import pandas as pd
import mysql.connector
from typing import Dict, List, Any
import logging
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ValidationConfig:
    """驗證配置"""
    host: str = "localhost"
    user: str = "demo"
    password: str = "~Demo123"
    database: str = "demo"
    port: int = 3307

class DataValidator:
    """資料驗證器"""

    def __init__(self, config: ValidationConfig):
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
        except Exception as e:
            logger.error(f"資料庫連接失敗: {e}")
            raise

    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """執行綜合驗證"""
        logger.info("=== 開始綜合資料驗證 ===")

        results = {
            'summary': {},
            'issues': [],
            'recommendations': []
        }

        try:
            self.connect()

            # 基本統計檢查
            results['summary'] = self._check_basic_stats()

            # 資料完整性檢查
            integrity_issues = self._check_data_integrity()
            results['issues'].extend(integrity_issues)

            # 資料一致性檢查
            consistency_issues = self._check_data_consistency()
            results['issues'].extend(consistency_issues)

            # 效能檢查
            performance_issues = self._check_performance()
            results['issues'].extend(performance_issues)

            # 生成建議
            results['recommendations'] = self._generate_recommendations(results['issues'])

        except Exception as e:
            results['issues'].append(f"驗證過程出錯: {e}")
        finally:
            if self.connection:
                self.connection.close()

        return results

    def _check_basic_stats(self) -> Dict[str, Any]:
        """檢查基本統計"""
        logger.info("檢查基本統計...")

        cursor = self.connection.cursor()

        try:
            stats = {}

            # 新表格統計
            cursor.execute("""
                SELECT
                    COUNT(*) as total_rows,
                    COUNT(DISTINCT symbol) as unique_symbols,
                    COUNT(DISTINCT market) as markets,
                    MIN(date) as earliest_date,
                    MAX(date) as latest_date
                FROM stock_daily_prices
            """)

            row = cursor.fetchone()
            stats['new_table'] = {
                'total_rows': row[0],
                'unique_symbols': row[1],
                'markets': row[2],
                'date_range': f"{row[3]} 到 {row[4]}" if row[3] and row[4] else 'N/A'
            }

            # 市場分佈
            cursor.execute("""
                SELECT market, COUNT(*) as count
                FROM stock_daily_prices
                GROUP BY market
                ORDER BY count DESC
            """)

            market_dist = cursor.fetchall()
            stats['market_distribution'] = {row[0]: row[1] for row in market_dist}

            # 樣本資料檢查
            cursor.execute("""
                SELECT symbol, market, COUNT(*) as records,
                       MIN(date) as start_date, MAX(date) as end_date
                FROM stock_daily_prices
                GROUP BY symbol, market
                ORDER BY records DESC
                LIMIT 10
            """)

            top_symbols = cursor.fetchall()
            stats['top_symbols'] = [
                {
                    'symbol': row[0],
                    'market': row[1],
                    'records': row[2],
                    'date_range': f"{row[3]} 到 {row[4]}"
                }
                for row in top_symbols
            ]

            return stats

        finally:
            cursor.close()

    def _check_data_integrity(self) -> List[str]:
        """檢查資料完整性"""
        logger.info("檢查資料完整性...")

        issues = []
        cursor = self.connection.cursor()

        try:
            # 檢查空值
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN open IS NULL THEN 1 ELSE 0 END) as null_open,
                    SUM(CASE WHEN close IS NULL THEN 1 ELSE 0 END) as null_close,
                    SUM(CASE WHEN date IS NULL THEN 1 ELSE 0 END) as null_date,
                    SUM(CASE WHEN symbol IS NULL OR symbol = '' THEN 1 ELSE 0 END) as null_symbol
                FROM stock_daily_prices
            """)

            null_counts = cursor.fetchone()
            if any(null_counts):
                issues.append(f"發現空值: open={null_counts[0]}, close={null_counts[1]}, date={null_counts[2]}, symbol={null_counts[3]}")

            # 檢查重複記錄
            cursor.execute("""
                SELECT COUNT(*) - COUNT(DISTINCT symbol, date) as duplicates
                FROM stock_daily_prices
            """)

            duplicates = cursor.fetchone()[0]
            if duplicates > 0:
                issues.append(f"發現 {duplicates} 個重複記錄 (symbol+date)")

            # 檢查日期有效性
            cursor.execute("""
                SELECT COUNT(*) as invalid_dates
                FROM stock_daily_prices
                WHERE date < '2000-01-01' OR date > CURDATE()
            """)

            invalid_dates = cursor.fetchone()[0]
            if invalid_dates > 0:
                issues.append(f"發現 {invalid_dates} 個無效日期")

            # 檢查價格合理性
            cursor.execute("""
                SELECT COUNT(*) as negative_prices
                FROM stock_daily_prices
                WHERE open < 0 OR high < 0 OR low < 0 OR close < 0
            """)

            negative_prices = cursor.fetchone()[0]
            if negative_prices > 0:
                issues.append(f"發現 {negative_prices} 個負數價格")

        finally:
            cursor.close()

        return issues

    def _check_data_consistency(self) -> List[str]:
        """檢查資料一致性"""
        logger.info("檢查資料一致性...")

        issues = []
        cursor = self.connection.cursor()

        try:
            # 檢查 OHLC 邏輯：確保 open 和 close 在 [low, high] 區間內
            cursor.execute("""
                SELECT COUNT(*) as invalid_ohlc
                FROM stock_daily_prices
                WHERE NOT (low <= open AND open <= high
                      AND low <= close AND close <= high
                      AND low <= high)
            """)

            invalid_ohlc = cursor.fetchone()[0]
            if invalid_ohlc > 0:
                issues.append(f"發現 {invalid_ohlc} 個 OHLC 邏輯錯誤")

            # 檢查成交量合理性
            cursor.execute("""
                SELECT COUNT(*) as zero_volume
                FROM stock_daily_prices
                WHERE volume = 0
            """)

            zero_volume = cursor.fetchone()[0]
            if zero_volume > 1000:  # 允許少量零成交量
                issues.append(f"發現 {zero_volume} 個零成交量記錄")

            # 檢查市場分類一致性
            cursor.execute("""
                SELECT symbol, GROUP_CONCAT(DISTINCT market) as markets
                FROM stock_daily_prices
                GROUP BY symbol
                HAVING COUNT(DISTINCT market) > 1
            """)

            inconsistent_markets = cursor.fetchall()
            if inconsistent_markets:
                issues.append(f"發現 {len(inconsistent_markets)} 個股票屬於多個市場")

        finally:
            cursor.close()

        return issues

    def _check_performance(self) -> List[str]:
        """檢查效能"""
        logger.info("檢查效能...")

        issues = []
        cursor = self.connection.cursor()

        try:
            # 檢查索引使用情況（簡單檢查）
            cursor.execute("SHOW INDEX FROM stock_daily_prices")
            indexes = cursor.fetchall()

            index_names = [idx[2] for idx in indexes]
            # 更新索引檢查：複合主鍵 (symbol, date) 已涵蓋 unique_symbol_date 和 idx_symbol
            required_indexes = ['PRIMARY', 'idx_market', 'idx_date']

            missing_indexes = [idx for idx in required_indexes if idx not in index_names]
            if missing_indexes:
                issues.append(f"缺少索引: {', '.join(missing_indexes)}")

            # 檢查表格大小和分區狀態
            cursor.execute("SELECT COUNT(*) FROM stock_daily_prices")
            total_rows = cursor.fetchone()[0]

            # 檢查是否已經分區
            cursor.execute("""
                SELECT COUNT(*) as partition_count
                FROM INFORMATION_SCHEMA.PARTITIONS
                WHERE TABLE_NAME = 'stock_daily_prices'
                AND TABLE_SCHEMA = %s
                AND PARTITION_NAME IS NOT NULL
            """, (self.config.database,))

            partition_count = cursor.fetchone()[0]

            if partition_count > 0:
                logger.info(f"表格已分區 ({partition_count} 個分區)")
                # 如果已經分區，檢查每個分區的大小（簡單檢查）
                if total_rows > 5000000:  # 如果總行數超過500萬，即使分區也可能需要優化
                    issues.append(f"表格過大 ({total_rows} 行，即使已分區也建議進一步優化)")
            else:
                if total_rows > 1000000:  # 超過100萬行且未分區
                    issues.append(f"表格過大 ({total_rows} 行)，建議考慮分區")

        finally:
            cursor.close()

        return issues

    def _generate_recommendations(self, issues: List[str]) -> List[str]:
        """生成建議"""
        recommendations = []

        if any('空值' in issue for issue in issues):
            recommendations.append("建議清理或填補空值資料")

        if any('重複' in issue for issue in issues):
            recommendations.append("建議清理重複記錄")

        if any('OHLC' in issue for issue in issues):
            recommendations.append("建議檢查和修正OHLC資料邏輯")

        if any('索引' in issue for issue in issues):
            recommendations.append("建議添加必要的資料庫索引")

        if any('分區' in issue for issue in issues):
            recommendations.append("建議實施資料分區策略")

        if not issues:
            recommendations.append("✅ 資料驗證通過，品質良好")

        return recommendations

    def print_validation_report(self, results: Dict[str, Any]):
        """列印驗證報告"""
        print("\n" + "="*50)
        print("資料驗證報告")
        print("="*50)

        # 總結
        summary = results['summary']
        if 'new_table' in summary:
            nt = summary['new_table']
            print("基本統計:" )
            print(f"  總記錄數: {nt['total_rows']:,}")
            print(f"  唯一股票數: {nt['unique_symbols']:,}")
            print(f"  市場數: {nt['markets']}")
            print(f"  日期範圍: {nt['date_range']}")

        if 'market_distribution' in summary:
            print("市場分佈:")
            for market, count in summary['market_distribution'].items():
                print(f"  {market}: {count:,}")

        if 'top_symbols' in summary:
            print("資料最豐富的股票:")
            for symbol in summary['top_symbols'][:5]:
                print(f"  {symbol['symbol']} ({symbol['market']}): {symbol['records']:,} 記錄")

        # 問題
        issues = results['issues']
        if issues:
            print("⚠️ 發現的問題:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
        else:
            print("\n✅ 未發現重大問題")

        # 建議
        recommendations = results['recommendations']
        if recommendations:
            print("💡 建議:")
            for rec in recommendations:
                print(f"  • {rec}")

        print("\n" + "="*50)

def main():
    """主函數"""
    config = ValidationConfig()

    validator = DataValidator(config)
    results = validator.run_comprehensive_validation()
    validator.print_validation_report(results)

    # 返回狀態
    if results['issues']:
        print(f"\n❌ 驗證完成，發現 {len(results['issues'])} 個問題")
        return 1
    else:
        print("\n✅ 驗證完成，資料品質良好")
        return 0

if __name__ == "__main__":
    sys.exit(main())
