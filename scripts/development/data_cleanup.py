#!/usr/bin/env python3
"""
資料清理腳本
清理和修正遷移後發現的資料問題
"""

import sys
import os
import mysql.connector
from datetime import datetime
from typing import List, Dict, Any
import logging
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CleanupConfig:
    """清理配置"""
    host: str = "localhost"
    user: str = "demo"
    password: str = "~Demo123"
    database: str = "demo"
    port: int = 3307
    dry_run: bool = False

class DataCleaner:
    """資料清理器"""

    def __init__(self, config: CleanupConfig):
        self.config = config
        self.connection = None
        self.stats = {
            'fixed_ohlc': 0,
            'removed_duplicates': 0,
            'fixed_nulls': 0,
            'removed_invalid_dates': 0,
            'removed_negative_prices': 0,
            'removed_zero_volume': 0
        }

    def connect(self):
        """建立資料庫連接"""
        try:
            self.connection = mysql.connector.connect(
                host=self.config.host,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                port=self.config.port,
                autocommit=True  # 確保自動提交
            )
            logger.info("資料庫連接成功")
        except Exception as e:
            logger.error(f"資料庫連接失敗: {e}")
            raise

    def fix_ohlc_logic_errors(self) -> int:
        """修正 OHLC 邏輯錯誤"""
        logger.info("修正 OHLC 邏輯錯誤...")

        cursor = self.connection.cursor()

        try:
            # 找出有 OHLC 邏輯錯誤的記錄
            cursor.execute("""
                SELECT symbol, date, open, high, low, close
                FROM stock_daily_prices
                WHERE NOT (low <= open AND open <= high
                      AND low <= close AND close <= high
                      AND low <= high)
            """)

            invalid_records = cursor.fetchall()
            fixed_count = 0
            unfixed_issues = []

            for record in invalid_records:
                symbol, date, open_price, high, low, close = record

                # 修正策略：重新計算合理的高低價
                # 使用開盤價和收盤價的範圍來修正
                new_low = min(open_price, close) if open_price and close else (open_price or close or 0)
                new_high = max(open_price, close) if open_price and close else (open_price or close or 0)

                # 確保新計算的值合理
                if new_low > 0 and new_high >= new_low:
                    if not self.config.dry_run:
                        # 先檢查記錄是否存在
                        cursor.execute("""
                            SELECT COUNT(*) FROM stock_daily_prices
                            WHERE symbol = %s AND date = %s
                        """, (symbol, date))
                        exists = cursor.fetchone()[0]

                        if exists > 0:
                            cursor.execute("""
                                UPDATE stock_daily_prices
                                SET low = %s, high = %s
                                WHERE symbol = %s AND date = %s
                            """, (new_low, new_high, symbol, date))

                            if cursor.rowcount > 0:
                                logger.debug(f"成功修正記錄: {symbol} {date} - low:{low}->{new_low}, high:{high}->{new_high}")
                            else:
                                logger.warning(f"更新失敗: {symbol} {date} - 記錄存在但更新失敗")
                        else:
                            logger.warning(f"記錄不存在: {symbol} {date}")

                    fixed_count += 1
                    logger.debug(f"修正記錄: {symbol} {date} - low:{low}->{new_low}, high:{high}->{new_high}")
                else:
                    # 記錄無法修正的問題
                    issue_reason = self._analyze_ohlc_issue(open_price, high, low, close, new_low, new_high)
                    unfixed_issues.append({
                        'symbol': symbol,
                        'date': date,
                        'original': {'open': open_price, 'high': high, 'low': low, 'close': close},
                        'attempted_fix': {'low': new_low, 'high': new_high},
                        'issue': issue_reason
                    })

            # 強制提交以確保更改被保存
            if not self.config.dry_run:
                self.connection.commit()
                logger.info(f"已提交 {fixed_count} 個 OHLC 修正")

            logger.info(f"修正了 {fixed_count} 個 OHLC 邏輯錯誤")
            logger.info(f"發現 {len(unfixed_issues)} 個無法自動修正的 OHLC 問題")

            # 將無法修正的問題存儲在實例變數中，供後續報告
            self.unfixed_ohlc_issues = unfixed_issues

            self.stats['fixed_ohlc'] = fixed_count
            return fixed_count

        finally:
            cursor.close()

    def _analyze_ohlc_issue(self, open_price, high, low, close, new_low, new_high) -> str:
        """分析 OHLC 問題的具體原因"""
        issues = []

        if new_low <= 0:
            issues.append("修正後的最低價 <= 0")

        if new_high < new_low:
            issues.append("修正後的最高價 < 最低價")

        if open_price is None or close is None:
            issues.append("開盤價或收盤價為空值")

        if not issues:
            issues.append("未知問題")

        return "; ".join(issues)

    def remove_duplicate_records(self) -> int:
        """移除重複記錄，保留最新的（基於更新時間）"""
        logger.info("清理重複記錄...")

        cursor = self.connection.cursor()

        try:
            # 找出重複記錄（保留更新時間最新的）
            cursor.execute("""
                SELECT symbol, date, COUNT(*) as count,
                       GROUP_CONCAT(updated_at ORDER BY updated_at DESC) as timestamps
                FROM stock_daily_prices
                GROUP BY symbol, date
                HAVING count > 1
            """)

            duplicates = cursor.fetchall()
            removed_count = 0

            for symbol, date, count, timestamps_str in duplicates:
                # 解析時間戳，保留最新的記錄
                timestamps = timestamps_str.split(',')

                if not self.config.dry_run:
                    # 刪除除最新記錄外的所有重複記錄
                    # 使用子查詢找到非最新的記錄
                    cursor.execute("""
                        DELETE t1 FROM stock_daily_prices t1
                        INNER JOIN stock_daily_prices t2
                        ON t1.symbol = t2.symbol AND t1.date = t2.date
                        WHERE t1.symbol = %s AND t1.date = %s
                        AND t1.updated_at < t2.updated_at
                    """, (symbol, date))

                    # 檢查實際刪除了多少記錄
                    deleted_this_time = cursor.rowcount
                    removed_count += deleted_this_time

                logger.debug(f"清理重複: {symbol} {date} - 找到 {count} 個重複")

            if not self.config.dry_run and removed_count > 0:
                self.connection.commit()

            logger.info(f"移除了 {removed_count} 個重複記錄")
            self.stats['removed_duplicates'] = removed_count
            return removed_count

        finally:
            cursor.close()

    def remove_invalid_date_records(self) -> int:
        """移除無效日期記錄"""
        logger.info("清理無效日期記錄...")

        cursor = self.connection.cursor()

        try:
            # 找出無效日期記錄
            cursor.execute("""
                SELECT COUNT(*) as invalid_count
                FROM stock_daily_prices
                WHERE date < '2000-01-01' OR date > CURDATE()
            """)

            invalid_count = cursor.fetchone()[0]

            if invalid_count > 0:
                if not self.config.dry_run:
                    cursor.execute("""
                        DELETE FROM stock_daily_prices
                        WHERE date < '2000-01-01' OR date > CURDATE()
                    """)
                    self.connection.commit()

                logger.info(f"移除了 {invalid_count} 個無效日期記錄")
            else:
                logger.info("沒有發現無效日期記錄")

            self.stats['removed_invalid_dates'] = invalid_count
            return invalid_count

        finally:
            cursor.close()

    def fix_null_values(self) -> int:
        """修正空值（用預設值填補）"""
        logger.info("修正空值...")

        cursor = self.connection.cursor()

        try:
            # 統計各欄位的空值
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN open IS NULL THEN 1 ELSE 0 END) as null_open,
                    SUM(CASE WHEN close IS NULL THEN 1 ELSE 0 END) as null_close,
                    SUM(CASE WHEN high IS NULL THEN 1 ELSE 0 END) as null_high,
                    SUM(CASE WHEN low IS NULL THEN 1 ELSE 0 END) as null_low
                FROM stock_daily_prices
            """)

            null_counts = cursor.fetchone()
            null_open, null_close, null_high, null_low = null_counts

            fixed_count = 0

            # 修正空值策略：用收盤價填補開盤價，用開盤價填補收盤價
            if null_open > 0 or null_close > 0:
                if not self.config.dry_run:
                    cursor.execute("""
                        UPDATE stock_daily_prices
                        SET open = COALESCE(open, close),
                            close = COALESCE(close, open)
                        WHERE open IS NULL OR close IS NULL
                    """)
                fixed_count += null_open + null_close

            # 對於高低價，使用開盤收盤價的平均或其他邏輯
            if null_high > 0 or null_low > 0:
                if not self.config.dry_run:
                    # 用開盤收盤價的最大最小值來估計
                    cursor.execute("""
                        UPDATE stock_daily_prices
                        SET
                            high = COALESCE(high, GREATEST(open, close)),
                            low = COALESCE(low, LEAST(open, close))
                        WHERE high IS NULL OR low IS NULL
                    """)
                fixed_count += null_high + null_low

            if not self.config.dry_run and fixed_count > 0:
                self.connection.commit()

            logger.info(f"修正了 {fixed_count} 個空值")
            self.stats['fixed_nulls'] = fixed_count
            return fixed_count

        finally:
            cursor.close()

    def remove_negative_price_records(self) -> int:
        """移除負數價格記錄"""
        logger.info("清理負數價格記錄...")

        cursor = self.connection.cursor()

        try:
            # 統計負數價格記錄
            cursor.execute("""
                SELECT COUNT(*) as negative_count
                FROM stock_daily_prices
                WHERE open < 0 OR high < 0 OR low < 0 OR close < 0
            """)

            negative_count = cursor.fetchone()[0]

            if negative_count > 0:
                if not self.config.dry_run:
                    cursor.execute("""
                        DELETE FROM stock_daily_prices
                        WHERE open < 0 OR high < 0 OR low < 0 OR close < 0
                    """)
                    self.connection.commit()

                logger.info(f"移除了 {negative_count} 個負數價格記錄")
            else:
                logger.info("沒有發現負數價格記錄")

            self.stats['removed_negative_prices'] = negative_count
            return negative_count

        finally:
            cursor.close()

    def remove_zero_volume_records(self) -> int:
        """移除零成交量記錄（保留合理的少量記錄）"""
        logger.info("清理零成交量記錄...")

        cursor = self.connection.cursor()

        try:
            # 統計零成交量記錄（允許少量正常記錄）
            cursor.execute("""
                SELECT COUNT(*) as zero_volume_count
                FROM stock_daily_prices
                WHERE volume = 0
            """)

            zero_volume_count_result = cursor.fetchone()
            zero_volume_count = zero_volume_count_result[0] if zero_volume_count_result else 0

            # 允許少量零成交量記錄（例如1000個以內）
            threshold = 1000
            records_to_remove = max(0, zero_volume_count - threshold)

            if records_to_remove > 0:
                if not self.config.dry_run:
                    # 簡化刪除邏輯：直接刪除超過閾值的所有零成交量記錄
                    # （由於數量巨大，這是最簡單有效的方法）
                    cursor.execute("""
                        DELETE FROM stock_daily_prices
                        WHERE volume = 0
                        LIMIT %s
                    """, (records_to_remove,))
                    self.connection.commit()

                logger.info(f"移除了 {records_to_remove} 個多餘的零成交量記錄")
            else:
                logger.info("零成交量記錄數量在合理範圍內")

            self.stats['removed_zero_volume'] = records_to_remove
            return records_to_remove

        finally:
            cursor.close()

    def report_unfixed_ohlc_issues(self):
        """報告無法修正的 OHLC 問題"""
        if not hasattr(self, 'unfixed_ohlc_issues') or not self.unfixed_ohlc_issues:
            print("\n[SUCCESS] 所有 OHLC 問題都已修正")
            return

        print(f"\n[WARNING] 發現 {len(self.unfixed_ohlc_issues)} 個無法自動修正的 OHLC 問題:")
        print("-" * 80)

        # 分組統計問題類型
        issue_types = {}
        for issue in self.unfixed_ohlc_issues:
            issue_type = issue['issue']
            if issue_type not in issue_types:
                issue_types[issue_type] = []
            issue_types[issue_type].append(issue)

        for issue_type, issues in issue_types.items():
            print(f"\n[*] 問題類型: {issue_type} ({len(issues)} 個)")
            print("   範例記錄:")

            # 顯示前3個範例
            for i, issue in enumerate(issues[:3]):
                orig = issue['original']
                attempted = issue['attempted_fix']
                print(f"   {i+1}. {issue['symbol']} {issue['date']}")
                print(f"      原始: O={orig['open']}, H={orig['high']}, L={orig['low']}, C={orig['close']}")
                print(f"      嘗試修正: L={attempted['low']}, H={attempted['high']}")

        if len(self.unfixed_ohlc_issues) > 10:
            print(f"\n   ...還有 {len(self.unfixed_ohlc_issues) - 10} 個類似問題")

        print("\n[TIP] 建議:")
        print("   • 這些記錄可能需要人工檢查和修正")
        print("   • 考慮聯繫資料來源確認正確的 OHLC 值")
        print("   • 或使用更複雜的修正演算法")

    def run_full_cleanup(self) -> Dict[str, Any]:
        """執行完整清理"""
        logger.info("=== 開始資料清理 ===")

        if self.config.dry_run:
            logger.info("DRY RUN 模式：只會顯示要進行的操作，不會實際修改資料")

        try:
            self.connect()

            results = {
                'ohlc_fixed': self.fix_ohlc_logic_errors(),
                'duplicates_removed': self.remove_duplicate_records(),
                'invalid_dates_removed': self.remove_invalid_date_records(),
                'nulls_fixed': self.fix_null_values(),
                'negative_prices_removed': self.remove_negative_price_records(),
                'zero_volume_removed': self.remove_zero_volume_records()
            }

            # 清理後重新分析表格
            cursor = self.connection.cursor()
            cursor.execute("ANALYZE TABLE stock_daily_prices")
            # 消耗 ANALYZE TABLE 的結果集以避免 Unread result found 錯誤
            analyze_result = cursor.fetchall()
            logger.info(f"ANALYZE TABLE result: {analyze_result}")
            cursor.close()

            logger.info("=== 清理完成統計 ===")
            logger.info(f"修正 OHLC 錯誤: {results['ohlc_fixed']}")
            logger.info(f"移除重複記錄: {results['duplicates_removed']}")
            logger.info(f"移除無效日期: {results['invalid_dates_removed']}")
            logger.info(f"修正空值: {results['nulls_fixed']}")
            logger.info(f"移除負數價格: {results['negative_prices_removed']}")
            logger.info(f"移除零成交量: {results['zero_volume_removed']}")

            total_changes = sum(results.values())
            logger.info(f"總計處理記錄: {total_changes}")

            return results

        except Exception as e:
            logger.error(f"清理失敗: {e}")
            raise
        finally:
            if self.connection:
                self.connection.close()

def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description='資料清理工具')
    parser.add_argument('--dry-run', action='store_true', help='僅模擬運行，不實際修改資料庫')
    parser.add_argument('--host', default='localhost', help='資料庫主機')
    parser.add_argument('--port', type=int, default=3307, help='資料庫端口')
    parser.add_argument('--user', default='demo', help='資料庫用戶名')
    parser.add_argument('--password', default='~Demo123', help='資料庫密碼')
    parser.add_argument('--database', default='demo', help='資料庫名稱')

    args = parser.parse_args()

    config = CleanupConfig(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database,
        dry_run=args.dry_run
    )

    cleaner = DataCleaner(config)

    try:
        results = cleaner.run_full_cleanup()

        if config.dry_run:
            print("\n[DRY RUN] 完成 - 這是預估的清理結果")
        else:
            print("\n[SUCCESS] 資料清理完成")

        print(f"修正 OHLC 錯誤: {results['ohlc_fixed']}")
        print(f"移除重複記錄: {results['duplicates_removed']}")
        print(f"移除無效日期: {results['invalid_dates_removed']}")
        print(f"修正空值: {results['nulls_fixed']}")
        print(f"移除負數價格: {results['negative_prices_removed']}")
        print(f"移除零成交量: {results['zero_volume_removed']}")

        total = sum(results.values())
        if total > 0:
            print(f"\n[STATS] 總計處理了 {total} 筆記錄")
        else:
            print("\n[CLEAN] 資料已經很乾淨了")

        # 報告無法修正的 OHLC 問題
        if hasattr(cleaner, 'unfixed_ohlc_issues') and cleaner.unfixed_ohlc_issues:
            cleaner.report_unfixed_ohlc_issues()

        return 0

    except Exception as e:
        print(f"\n[ERROR] 清理失敗: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
