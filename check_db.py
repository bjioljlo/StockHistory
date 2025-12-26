#!/usr/bin/env python3
"""
簡單檢查資料庫
"""

import mysql.connector

def check_db():
    print("開始檢查資料庫連接...")
    try:
        print("嘗試連接到資料庫...")
        connection = mysql.connector.connect(
            host="localhost",
            user="demo",
            password="~Demo123",
            database="demo",
            port=3307
        )
        print("資料庫連接成功!")

        cursor = connection.cursor()

        # 獲取表格數量
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'demo'")
        table_count = cursor.fetchone()[0]

        print(f"表格數量: {table_count}")

        # 獲取樣本表格
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'demo' LIMIT 5")
        sample_tables = [row[0] for row in cursor.fetchall()]
        print(f"樣本表格: {sample_tables}")

        cursor.close()
        connection.close()
        print("檢查完成!")

    except Exception as e:
        print(f"錯誤: {e}")

if __name__ == "__main__":
    check_db()
