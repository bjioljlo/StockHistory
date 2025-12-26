#!/usr/bin/env python3
"""
簡單的資料庫連接測試
"""

import mysql.connector

def test_connection():
    """測試資料庫連接"""
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="demo",
            password="~Demo123",
            database="demo",
            port=3307
        )

        cursor = connection.cursor()

        # 獲取表格數量
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'demo'")
        table_count = cursor.fetchone()[0]

        print(f"✅ 資料庫連接成功!")
        print(f"📊 表格數量: {table_count}")

        # 獲取樣本表格
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'demo' LIMIT 5")
        sample_tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 樣本表格: {sample_tables}")

        cursor.close()
        connection.close()

        return True

    except Exception as e:
        print(f"❌ 連接失敗: {e}")
        return False

if __name__ == "__main__":
    test_connection()
