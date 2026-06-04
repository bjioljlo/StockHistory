import threading
from datetime import datetime
from typing import Dict, Any

import pandas as pd
import yfinance as yf
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text

from src.Common import Tools
from pyutils_core.config import get_config


class SqlService:
    def __init__(self) -> None:
        self.server_flask: Flask = Flask(__name__)  # 初始化server
        self.MySql_server: SQLAlchemy = None
        self._CantUseStocks = [] # 無法使用的股票

    @property
    def CantUseStocks(self):
        return  self._CantUseStocks

    def RunMysql(self):
        temp_thread = threading.Thread(target=self.__SetMysqlServer)
        temp_thread.start()

    def readStockDay(self, name: str):
        dataframe = pd.DataFrame()
        if not name.islower():
            name = name.lower()

        # 檢查資料庫連線是否已初始化
        if self.MySql_server is None:
            print("Database connection not initialized")
            return dataframe

        # 處理股票代碼，移除可能的副檔名
        symbol = name.upper().replace('.TW', '').replace('.US', '').replace('.HK', '')

        try:
            with self.server_flask.app_context():
                # 從統一的 stock_daily_prices 表格讀取資料
                query = f"""
                SELECT date as Date, open as Open, high as High, low as Low,
                       close as Close, adj_close as `Adj Close`, volume as Volume
                FROM stock_daily_prices
                WHERE symbol = '{symbol}'
                ORDER BY date
                """
                dataframe = pd.read_sql(query, con=self.MySql_server.engine, index_col="Date")

                # 確保索引是 DatetimeIndex，處理 datetime.date 物件
                if not isinstance(dataframe.index, pd.DatetimeIndex):
                    dataframe.index = pd.to_datetime(dataframe.index)

                return dataframe
        except Exception as e:
            print("SQL Error {}".format(e.args))
            return dataframe

    def readDividendYield(self, name: str):
        dataframe = pd.DataFrame()
        if not name.islower():
            name = name.lower()
        try:
            # 使用獨立的應用程式上下文，避免線程問題
            with self.server_flask.app_context():
                dataframe = pd.read_sql(
                    sql=name, con=self.MySql_server.engine, index_col="code"
                )
                return dataframe
        except Exception as e:
            print("SQL Error {}".format(e.args))
            return dataframe

    def saveTable(self, _name: str, _df=pd.DataFrame()):
        if not _name.islower():
            _name = _name.lower()
        try:
            with self.server_flask.app_context():
                _df.to_sql(
                    name=_name, con=self.MySql_server.engine, if_exists="replace"
                )
                return True
        except Exception as e:
            print("SQL Error {}".format(e.args))
            return False

    def insert_into_table(self, table_name: str, data_df: pd.DataFrame):
        """
        Inserts data from a DataFrame into a specified table.

        Args:
            table_name (str): The name of the table to insert data into.
            data_df (pd.DataFrame): The DataFrame containing the data to insert.

        Returns:
            bool: True if insertion was successful, False otherwise.
        """
        if not table_name.islower():
            table_name = table_name.lower()

        try:
            with self.server_flask.app_context():
                data_df.to_sql(
                    name=table_name,
                    con=self.MySql_server.engine,
                    if_exists="append",  # Use 'append' to insert new rows
                    index=False          # Do not write DataFrame index as a column
                )
                print(f"Successfully inserted {len(data_df)} rows into {table_name}.")
                return True
        except Exception as e:
            print(f"SQL Error during insertion into {table_name}: {e}")
            return False

    def insert_data(self, table_name: str, data_df: pd.DataFrame):
        """
        安全的數據插入方法 - 只插入，不替換
        """
        if not table_name.islower():
            table_name = table_name.lower()

        try:
            with self.server_flask.app_context():
                data_df.to_sql(
                    name=table_name,
                    con=self.MySql_server.engine,
                    if_exists="append",  # 使用append而不是replace
                    index=False
                )
                print(f"Successfully inserted {len(data_df)} rows into {table_name}.")
                return True
        except Exception as e:
            print(f"SQL Error during insertion into {table_name}: {e}")
            return False

    def upsert_data(self, table_name: str, data_df: pd.DataFrame, key_columns: list[str]):
        """
        真正的Upsert操作 - 使用ON DUPLICATE KEY UPDATE而不是replace
        修復時間戳欄位處理問題
        """
        if not all(col in data_df.columns for col in key_columns):
            print(f"Error: Key columns {key_columns} not found in the DataFrame.")
            return False

        if not table_name.islower():
            table_name = table_name.lower()

        try:
            with self.server_flask.app_context():
                with self.MySql_server.engine.begin() as connection:

                    # 檢查表格是否存在
                    inspector = inspect(connection)
                    if table_name not in inspector.get_table_names():
                        # 表格不存在，直接插入
                        data_df.to_sql(
                            name=table_name,
                            con=connection,
                            if_exists='replace',
                            index=False
                        )
                        print(f"Table '{table_name}' created and {len(data_df)} rows inserted.")
                        return True

                    # 表格存在，使用真正的UPSERT操作
                    success_count = 0
                    for _, row in data_df.iterrows():
                        # 構建INSERT ... ON DUPLICATE KEY UPDATE語句
                        columns = list(data_df.columns)
                        placeholders = ', '.join([f':{col}' for col in columns])
                        column_names = ', '.join([f'`{col}`' for col in columns])

                        # 構建UPDATE部分
                        update_columns = [col for col in columns if col not in key_columns]

                        # 添加時間戳欄位到更新列表，確保created_at和updated_at被正確處理
                        timestamp_columns = ['created_at', 'updated_at']
                        for ts_col in timestamp_columns:
                            if ts_col not in update_columns and ts_col in columns:
                                update_columns.append(ts_col)

                        update_clause = ', '.join([f'`{col}` = VALUES(`{col}`)' for col in update_columns])

                        sql = f"""
                        INSERT INTO `{table_name}` ({column_names})
                        VALUES ({placeholders})
                        ON DUPLICATE KEY UPDATE
                        {update_clause},
                        updated_at = CURRENT_TIMESTAMP
                        """

                        # 處理NaN值並構建參數字典
                        row_dict = {}
                        for col in columns:
                            value = row[col]
                            if pd.isna(value) or value is None:
                                # 對於數值欄位使用0，其他使用None
                                if col in ['open', 'high', 'low', 'close', 'adj_close', 'volume',
                                         'dividend_yield', 'pe_ratio', 'pb_ratio']:
                                    row_dict[col] = 0.0 if col != 'volume' else 0
                                else:
                                    row_dict[col] = None
                            else:
                                row_dict[col] = value

                        connection.execute(text(sql), row_dict)
                        success_count += 1

                    print(f"Successfully upserted {success_count} rows to table '{table_name}'.")
                    return True

        except Exception as e:
            print(f"SQL Error during upsert into {table_name}: {e}")
            return False

    def upsert_dividend_yield(self, data_df: pd.DataFrame) -> bool:
        """
        專門用於股息殖利率數據的Upsert操作 (批量插入，避免逐行卡住)
        使用 scripts/migration 中的欄位結構
        """
        if data_df.empty:
            print("No data to upsert")
            return True

        table_name = 'dividend_yield'

        try:
            with self.server_flask.app_context():
                with self.MySql_server.engine.begin() as connection:

                    # 檢查表格是否存在
                    inspector = inspect(connection)
                    if table_name not in inspector.get_table_names():
                        # 建立表格
                        create_table_sql = """
                        CREATE TABLE IF NOT EXISTS dividend_yield (
                            id BIGINT AUTO_INCREMENT PRIMARY KEY,
                            symbol VARCHAR(20) NOT NULL COMMENT '股票代號',
                            date DATE NOT NULL COMMENT '資料日期',
                            company_name VARCHAR(100) COMMENT '公司名稱',
                            pe_ratio DECIMAL(10,2) COMMENT '本益比',
                            dividend_yield DECIMAL(5,2) COMMENT '殖利率(%)',
                            pb_ratio DECIMAL(10,2) COMMENT '股價淨值比',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

                            UNIQUE KEY unique_symbol_date (symbol, date),
                            INDEX idx_symbol (symbol),
                            INDEX idx_date (date),
                            INDEX idx_symbol_date (symbol, date),
                            INDEX idx_dividend_yield (dividend_yield),
                            INDEX idx_pe_ratio (pe_ratio)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                        """
                        connection.execute(text(create_table_sql))
                        print(f"Table '{table_name}' created.")

                    # 批量UPSERT插入數據（避免逐行執行）
                    # 準備數據
                    clean_df = data_df.copy()
                    for col in ['pe_ratio', 'dividend_yield', 'pb_ratio']:
                        if col in clean_df.columns:
                            clean_df[col] = clean_df[col].fillna(0.0)
                    for col in ['company_name']:
                        if col in clean_df.columns:
                            clean_df[col] = clean_df[col].fillna('')

                    # 批量構建VALUES子句
                    values_list = []
                    params_dict = {}
                    for idx, (_, row) in enumerate(clean_df.iterrows()):
                        symbol = row.get('symbol')
                        date = row.get('date')
                        company_name = row.get('company_name')
                        pe_ratio = row.get('pe_ratio', 0.0)
                        dividend_yield = row.get('dividend_yield', 0.0)
                        pb_ratio = row.get('pb_ratio', 0.0)

                        # 避免參數重複，使用索引區分
                        param_keys = (f':symbol_{idx}', f':date_{idx}', f':company_name_{idx}',
                                     f':pe_ratio_{idx}', f':dividend_yield_{idx}', f':pb_ratio_{idx}')
                        values_list.append(f"({param_keys[0]}, {param_keys[1]}, {param_keys[2]}, {param_keys[3]}, {param_keys[4]}, {param_keys[5]})")

                        params_dict[f'symbol_{idx}'] = symbol
                        params_dict[f'date_{idx}'] = date
                        params_dict[f'company_name_{idx}'] = company_name
                        params_dict[f'pe_ratio_{idx}'] = pe_ratio
                        params_dict[f'dividend_yield_{idx}'] = dividend_yield
                        params_dict[f'pb_ratio_{idx}'] = pb_ratio

                    if not values_list:
                        print("No valid data to insert")
                        return True

                    # 批量執行一次INSERT ... ON DUPLICATE KEY UPDATE
                    values_clause = ','.join(values_list)
                    sql = f"""
                    INSERT INTO dividend_yield (symbol, date, company_name, pe_ratio, dividend_yield, pb_ratio)
                    VALUES {values_clause}
                    ON DUPLICATE KEY UPDATE
                    company_name = VALUES(company_name),
                    pe_ratio = VALUES(pe_ratio),
                    dividend_yield = VALUES(dividend_yield),
                    pb_ratio = VALUES(pb_ratio),
                    updated_at = CURRENT_TIMESTAMP
                    """

                    connection.execute(text(sql), params_dict)
                    print(f"Successfully upserted {len(clean_df)} rows to dividend_yield table.")
                    return True

        except Exception as e:
            print(f"SQL Error during dividend_yield upsert: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_all_table_names(self) -> list[str]:
        """
        Retrieves a list of all table names in the database.

        Returns:
            list[str]: A list of table names.
        """
        try:
            with self.server_flask.app_context():
                with self.MySql_server.engine.connect() as connection:
                    inspector = inspect(connection)
                    return inspector.get_table_names()
        except Exception as e:
            print(f"SQL Error getting table names: {e}")
            return []

    def get_table_columns(self, table_name: str) -> list[dict]:
        """
        Retrieves column information for a specified table.

        Args:
            table_name (str): The name of the table to get columns for.

        Returns:
            list[dict]: A list of dictionaries containing column information:
                - name: Column name
                - type: Column data type
                - nullable: Whether the column allows NULL values
                - default: Default value for the column
                - primary_key: Whether this column is part of the primary key
        """
        if not table_name.islower():
            table_name = table_name.lower()

        try:
            with self.server_flask.app_context():
                with self.MySql_server.engine.connect() as connection:
                    inspector = inspect(connection)

                    if table_name not in inspector.get_table_names():
                        print(f"Table '{table_name}' does not exist in the database")
                        return []

                    columns = inspector.get_columns(table_name)

                    # Format column information for easier use
                    result = []
                    for col in columns:
                        result.append({
                            'name': col['name'],
                            'type': str(col['type']),
                            'nullable': col['nullable'],
                            'default': col['default'],
                            'primary_key': col.get('primary_key', False)
                        })

                    return result

        except Exception as e:
            print(f"SQL Error getting columns for table '{table_name}': {e}")
            return []

    def yfInfo(self, name: str):
        if name in self._CantUseStocks:
            print("CantUseStock:" + str(name))
            return
        start_date = datetime(2005, 1, 1)
        end_date = datetime.today()  # 設定資料起訖日期
        df_result = yf.download([name], start_date, end_date)
        if df_result.empty:
            self._CantUseStocks.append(name)
            print("yahoo no data:" + str(name))
        else:
            df_result = Tools.TidyTicketData(df_result, name)

            # 處理股票代碼和市場資訊
            symbol = name.upper().replace('.TW', '').replace('.US', '').replace('.HK', '')
            market = self._determine_market(name)

            # 轉換資料格式以適應新的統一表格
            df_result = df_result.reset_index()
            df_result['symbol'] = symbol
            df_result['market'] = market
            df_result = df_result.rename(columns={
                'Date': 'date',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Adj Close': 'adj_close',
                'Volume': 'volume'
            })

            # 插入到統一的 stock_daily_prices 表格
            self._insert_stock_data_to_unified_table(df_result)
            print("Update stocks " + name + " OK!")

    def _determine_market(self, stock_name: str) -> str:
        """確定市場類型"""
        name_lower = stock_name.lower()
        if name_lower.endswith('.tw') or (name_lower.replace('.tw', '').isdigit() and len(name_lower.replace('.tw', '')) >= 4):
            return 'TW'
        elif len(name_lower) <= 5 and not name_lower.replace('.', '').isdigit():
            return 'US'
        else:
            return 'OTHER'

    def _insert_stock_data_to_unified_table(self, df: pd.DataFrame):
        """將股票資料插入到統一的 stock_daily_prices 表格"""
        if df.empty:
            return False

        try:
            print(f"Inserting {len(df)} rows to unified table using upsert...")
            with self.server_flask.app_context():
                with self.MySql_server.engine.begin() as connection:
                    success_count = 0
                    for _, row in df.iterrows():
                        insert_sql = text("""
                        INSERT INTO stock_daily_prices (symbol, market, date, open, high, low, close, adj_close, volume)
                        VALUES (:symbol, :market, :date, :open, :high, :low, :close, :adj_close, :volume)
                        ON DUPLICATE KEY UPDATE
                        open = VALUES(open),
                        high = VALUES(high),
                        low = VALUES(low),
                        close = VALUES(close),
                        adj_close = VALUES(adj_close),
                        volume = VALUES(volume),
                        updated_at = CURRENT_TIMESTAMP
                        """)

                        # 處理 NaN 值，並確保欄位名稱正確
                        row_dict = {}
                        for col in ['symbol', 'market', 'date', 'open', 'high', 'low', 'close', 'adj_close', 'volume']:
                            value = row[col] if col in row.index else None
                            if pd.isna(value) or value is None:
                                # 對於數值欄位，使用 0 作為預設值
                                if col in ['open', 'high', 'low', 'close', 'adj_close', 'volume']:
                                    row_dict[col] = 0.0 if col != 'volume' else 0
                                else:
                                    row_dict[col] = None
                            else:
                                row_dict[col] = value

                        connection.execute(insert_sql, row_dict)
                        success_count += 1

                    print(f"Successfully inserted/updated {success_count} rows to unified table")
            return True

        except Exception as e:
            print(f"Insertion failed: {e}")
            return False

    def __SetMysqlServer(self):
        print("Loading database configuration...")

        try:
            config = get_config()
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return

        db_config = config.get('database', {})
        db_type = db_config.get('type', 'mysql')

        uri = None
        pool_config = {}

        if db_type == 'mysql':
            mysql_config = db_config.get('mysql', {})
            user = mysql_config.get('user')
            password = mysql_config.get('password')
            host = mysql_config.get('host')
            port = mysql_config.get('port')
            db_name = mysql_config.get('databasename')

            # Connection pool settings
            pool_config = {
                'pool_size': mysql_config.get('pool_size', 5),
                'max_overflow': mysql_config.get('max_overflow', 10),
                'pool_timeout': mysql_config.get('pool_timeout', 30),
                'pool_recycle': mysql_config.get('pool_recycle', 3600),
                'pool_pre_ping': True
            }

            uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}?local_infile=1"

        elif db_type == 'postgresql':
            # For PostgreSQL, you might need to run: pip install psycopg2-binary
            pg_config = db_config.get('postgresql', {})
            user = pg_config.get('user')
            password = pg_config.get('password')
            host = pg_config.get('host')
            port = pg_config.get('port')
            db_name = pg_config.get('databasename')

            # Connection pool settings for PostgreSQL
            pool_config = {
                'pool_size': pg_config.get('pool_size', 5),
                'max_overflow': pg_config.get('max_overflow', 10),
                'pool_timeout': pg_config.get('pool_timeout', 30),
                'pool_recycle': pg_config.get('pool_recycle', 3600),
                'pool_pre_ping': True
            }

            uri = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"

        elif db_type == 'sqlite':
            sqlite_config = db_config.get('sqlite', {})
            path = sqlite_config.get('path', 'default.db')
            uri = f"sqlite:///{path}" # Path is relative to the project root
        else:
            print(f"Unsupported database type: {db_type}")
            return

        # Configure Flask-SQLAlchemy with connection pooling
        self.server_flask.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        self.server_flask.config["SQLALCHEMY_DATABASE_URI"] = uri
        self.server_flask.config["SQLALCHEMY_ENGINE_OPTIONS"] = pool_config

        # Connect to the database
        self.MySql_server = SQLAlchemy(self.server_flask)
        print(f"Successfully configured database: {db_type} with connection pooling")

    # ===== 新增的優化查詢方法 =====

    def read_dividend_yield(self, symbol: str = None, start_date: str = None,
                           end_date: str = None, limit: int = 1000) -> pd.DataFrame:
        """
        從統一的dividend_yield表格讀取股息殖利率數據

        Args:
            symbol: 股票代號，為None時返回所有股票
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            limit: 返回記錄數量限制

        Returns:
            pd.DataFrame: 股息殖利率數據
        """
        if self.MySql_server is None:
            print("Database connection not initialized")
            return pd.DataFrame()

        try:
            # 使用獨立的應用程式上下文，避免線程問題
            with self.server_flask.app_context():
                # 建構查詢條件
                conditions = []
                params = {}

                if symbol:
                    symbol = symbol.upper().replace('.TW', '').replace('.US', '').replace('.HK', '')
                    conditions.append("symbol = :symbol")
                    params['symbol'] = symbol

                if start_date:
                    conditions.append("date >= :start_date")
                    params['start_date'] = start_date

                if end_date:
                    conditions.append("date <= :end_date")
                    params['end_date'] = end_date

                where_clause = " AND ".join(conditions) if conditions else "1=1"

                query = text("""
                SELECT symbol, date, company_name, pe_ratio, dividend_yield, pb_ratio
                FROM dividend_yield
                WHERE """ + where_clause + """
                ORDER BY symbol, date DESC
                LIMIT :limit""")

                params['limit'] = limit
                df = pd.read_sql(query, con=self.MySql_server.engine, params=params)
                return df

        except Exception as e:
            print(f"SQL Error in read_dividend_yield: {e}")
            return pd.DataFrame()

    def get_latest_dividend_yield_date(self) -> str | None:
        """
        Get the most recent dividend yield date saved in SQL.

        Returns:
            The latest date as YYYY-MM-DD string, or None if there is no record.
        """
        if self.MySql_server is None:
            print("Database connection not initialized")
            return None

        try:
            with self.server_flask.app_context():
                query = text("SELECT MAX(date) AS latest_date FROM dividend_yield")
                result = pd.read_sql(query, con=self.MySql_server.engine)
                if not result.empty and 'latest_date' in result.columns:
                    latest_date = result.iloc[0]['latest_date']
                    if latest_date is not None:
                        return str(latest_date)
                return None
        except Exception as e:
            print(f"SQL Error in get_latest_dividend_yield_date: {e}")
            return None

    def read_monthly_reports(self, symbol: str = None, start_year: int = None,
                           end_year: int = None, limit: int = 1000) -> pd.DataFrame:
        """
        從統一的monthly_reports表格讀取月報數據

        Args:
            symbol: 股票代號，為None時返回所有股票
            start_year: 開始年份
            end_year: 結束年份
            limit: 返回記錄數量限制

        Returns:
            pd.DataFrame: 月報數據
        """
        if self.MySql_server is None:
            print("Database connection not initialized")
            return pd.DataFrame()

        try:
            # 使用獨立的應用程式上下文，避免線程問題
            with self.server_flask.app_context():
                # 建構查詢條件
                conditions = []
                params = {}

                if symbol:
                    symbol = symbol.upper().replace('.TW', '').replace('.US', '').replace('.HK', '')
                    conditions.append("symbol = :symbol")
                    params['symbol'] = symbol

                if start_year:
                    conditions.append("report_year >= :start_year")
                    params['start_year'] = start_year

                if end_year:
                    conditions.append("report_year <= :end_year")
                    params['end_year'] = end_year

                where_clause = " AND ".join(conditions) if conditions else "1=1"

                query = text("""
                SELECT *
                FROM monthly_reports
                WHERE """ + where_clause + """
                ORDER BY symbol, report_year DESC, report_month DESC
                LIMIT :limit""")

                params['limit'] = limit
                df = pd.read_sql(query, con=self.MySql_server.engine, params=params)
                return df

        except Exception as e:
            print(f"SQL Error in read_monthly_reports: {e}")
            return pd.DataFrame()

    def read_quarterly_reports(self, symbol: str = None, report_type: str = None,
                             start_year: int = None, end_year: int = None,
                             limit: int = 10000) -> pd.DataFrame:
        """
        從統一的quarterly_reports表格讀取季報數據

        Args:
            symbol: 股票代號，為None時返回所有股票
            report_type: 報表類型 ('PLA', 'BS', 'CPL', 'SCF') 或 InfomationType.FS_type
            start_year: 開始年份
            end_year: 結束年份
            limit: 返回記錄數量限制

        Returns:
            pd.DataFrame: 季報數據
        """
        if self.MySql_server is None:
            print("Database connection not initialized")
            return pd.DataFrame()

        try:
            # 使用獨立的應用程式上下文，避免線程問題
            with self.server_flask.app_context():
                # 建構查詢條件
                conditions = []
                params = {}

                if symbol:
                    symbol = symbol.upper().replace('.TW', '').replace('.US', '').replace('.HK', '')
                    conditions.append("symbol = :symbol")
                    params['symbol'] = symbol

                if report_type:
                    # 處理 InfomationType.FS_type 或字符串類型
                    if hasattr(report_type, 'value'):
                        # 如果是 InfomationType.FS_type 枚舉
                        report_type_value = report_type.value
                    else:
                        # 如果是字符串
                        report_type_value = str(report_type)

                    # 將長名稱轉換為短代碼
                    type_mapping = {
                        'profit-and-loss-analysis-summary': 'PLA',
                        'balance-sheet': 'BS',
                        'consolidated-profit-and-loss-summary': 'CPL',
                        'statement-of-cash-flows': 'SCF'
                    }

                    short_type = type_mapping.get(report_type_value, report_type_value)
                    conditions.append("report_type = :report_type")
                    params['report_type'] = short_type.upper()

                if start_year:
                    conditions.append("report_year >= :start_year")
                    params['start_year'] = start_year

                if end_year:
                    conditions.append("report_year <= :end_year")
                    params['end_year'] = end_year

                where_clause = " AND ".join(conditions) if conditions else "1=1"

                query = text("""
                SELECT symbol, company_name, report_year, report_season, report_type,
                       revenue, gross_margin, operating_margin, pre_tax_margin, net_margin,
                       consolidated_net_income, consolidated_eps,
                       total_assets, total_liabilities, equity, capital, book_value_per_share,
                       operating_cash_flow, investing_cash_flow, financing_cash_flow
                FROM quarterly_reports
                WHERE """ + where_clause + """
                ORDER BY symbol, report_year DESC, report_season DESC
                LIMIT :limit""")

                params['limit'] = limit
                df = pd.read_sql(query, con=self.MySql_server.engine, params=params)
                return df

        except Exception as e:
            print(f"SQL Error in read_quarterly_reports: {e}")
            return pd.DataFrame()

    def get_dividend_yield_stats(self, symbol: str = None, date: str = None) -> Dict[str, Any]:
        """
        獲取股息殖利率統計信息

        Args:
            symbol: 股票代號，為None時返回整體統計
            date: 指定日期，為None時返回最新數據

        Returns:
            Dict: 統計信息 (平均殖利率、最高、最低等)
        """
        if self.MySql_server is None:
            print("Database connection not initialized")
            return {}

        try:
            # 使用獨立的應用程式上下文，避免線程問題
            with self.server_flask.app_context():
                if symbol:
                    symbol = symbol.upper().replace('.TW', '').replace('.US', '').replace('.HK', '')

                # 確定查詢日期
                date_condition = ""
                params = {}
                if date:
                    date_condition = "AND date = :date"
                    params['date'] = date
                else:
                    date_condition = "AND date = (SELECT MAX(date) FROM dividend_yield)"

                if symbol:
                    date_condition += " AND symbol = :symbol"
                    params['symbol'] = symbol

                query = f"""
                SELECT
                    COUNT(*) as total_records,
                    AVG(dividend_yield) as avg_yield,
                    MAX(dividend_yield) as max_yield,
                    MIN(dividend_yield) as min_yield,
                    AVG(pe_ratio) as avg_pe,
                    AVG(pb_ratio) as avg_pb
                FROM dividend_yield
                WHERE dividend_yield > 0 {date_condition}
                """

                result = pd.read_sql(query, con=self.MySql_server.engine, params=params)

                if result.empty:
                    return {}

                row = result.iloc[0]
                return {
                    'total_records': int(row['total_records']),
                    'avg_yield': round(float(row['avg_yield'] or 0), 2),
                    'max_yield': round(float(row['max_yield'] or 0), 2),
                    'min_yield': round(float(row['min_yield'] or 0), 2),
                    'avg_pe': round(float(row['avg_pe'] or 0), 2),
                    'avg_pb': round(float(row['avg_pb'] or 0), 2)
                }

        except Exception as e:
            print(f"SQL Error in get_dividend_yield_stats: {e}")
            return {}

    def get_monthly_revenue_trend(self, symbol: str, years: int = 3) -> pd.DataFrame:
        """
        獲取月營收趨勢數據

        Args:
            symbol: 股票代號
            years: 分析年數

        Returns:
            pd.DataFrame: 營收趨勢數據 (年份, 月份, 營收, 增長率)
        """
        if self.MySql_server is None:
            print("Database connection not initialized")
            return pd.DataFrame()

        try:
            # 使用獨立的應用程式上下文，避免線程問題
            with self.server_flask.app_context():
                symbol = symbol.upper().replace('.TW', '').replace('.US', '').replace('.HK', '')

                query = f"""
                SELECT
                    report_year,
                    report_month,
                    revenue_current_month,
                    LAG(revenue_current_month, 12) OVER (ORDER BY report_year, report_month) as last_year_revenue,
                    CASE
                        WHEN LAG(revenue_current_month, 12) OVER (ORDER BY report_year, report_month) > 0
                        THEN ROUND(
                            (revenue_current_month - LAG(revenue_current_month, 12) OVER (ORDER BY report_year, report_month))
                            / LAG(revenue_current_month, 12) OVER (ORDER BY report_year, report_month) * 100, 2
                        )
                        ELSE NULL
                    END as growth_rate
                FROM monthly_reports
                WHERE symbol = :symbol
                  AND report_year >= YEAR(CURDATE()) - :years
                ORDER BY report_year DESC, report_month DESC
                """

                df = pd.read_sql(query, con=self.MySql_server.engine,
                               params={'symbol': symbol, 'years': years})
                return df

        except Exception as e:
            print(f"SQL Error in get_monthly_revenue_trend: {e}")
            return pd.DataFrame()

    def get_quarterly_financial_summary(self, symbol: str, year: int = None) -> Dict[str, Any]:
        """
        獲取季財務報表摘要

        Args:
            symbol: 股票代號
            year: 指定年份，為None時返回最新年份

        Returns:
            Dict: 財務摘要 (收入、利潤、資產負債等)
        """
        if self.MySql_server is None:
            print("Database connection not initialized")
            return {}

        try:
            # 使用獨立的應用程式上下文，避免線程問題
            with self.server_flask.app_context():
                symbol = symbol.upper().replace('.TW', '').replace('.US', '').replace('.HK', '')

                # 確定年份
                year_condition = ""
                params = {'symbol': symbol}
                if year:
                    year_condition = "AND report_year = :year"
                    params['year'] = year
                else:
                    year_condition = "AND report_year = (SELECT MAX(report_year) FROM quarterly_reports WHERE symbol = :symbol)"

                # 獲取損益表數據
                pla_query = f"""
                SELECT report_season, revenue, net_margin
                FROM quarterly_reports
                WHERE symbol = :symbol {year_condition} AND report_type = 'PLA'
                ORDER BY report_season
                """

                pla_df = pd.read_sql(pla_query, con=self.MySql_server.engine, params=params)

                # 獲取資產負債表數據
                bs_query = f"""
                SELECT report_season, total_assets, total_liabilities, equity
                FROM quarterly_reports
                WHERE symbol = :symbol {year_condition} AND report_type = 'BS'
                ORDER BY report_season
                """

                bs_df = pd.read_sql(bs_query, con=self.MySql_server.engine, params=params)

                # 合併數據
                result = {
                    'symbol': symbol,
                    'year': year,
                    'pla_data': pla_df.to_dict('records') if not pla_df.empty else [],
                    'bs_data': bs_df.to_dict('records') if not bs_df.empty else []
                }

                return result

        except Exception as e:
            print(f"SQL Error in get_quarterly_financial_summary: {e}")
            return {}

    def read_ad_index(self, start_date: str = None, end_date: str = None,
                     limit: int = 1000) -> pd.DataFrame:
        """
        讀取騰落指數數據

        Args:
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            limit: 返回記錄數量限制

        Returns:
            pd.DataFrame: 騰落指數數據
        """
        if self.MySql_server is None:
            print("Database connection not initialized")
            return pd.DataFrame()

        try:
            # 使用獨立的應用程式上下文，避免線程問題
            with self.server_flask.app_context():
                # 建構查詢條件
                conditions = []
                params = {}

                if start_date:
                    conditions.append("date >= %(start_date)s")
                    params['start_date'] = start_date

                if end_date:
                    conditions.append("date <= %(end_date)s")
                    params['end_date'] = end_date

                where_clause = " AND ".join(conditions) if conditions else "1=1"

                query = f"""
                SELECT date, up_count, down_count
                FROM ad_index
                WHERE {where_clause}
                ORDER BY date DESC
                LIMIT %(limit)s
                """

                # 使用參數化查詢
                params['limit'] = limit
                df = pd.read_sql(query, con=self.MySql_server.engine, params=params)

                # 設定索引
                if not df.empty:
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.set_index('date')

                return df

        except Exception as e:
            print(f"SQL Error in read_ad_index: {e}")
            return pd.DataFrame()

    def read_adl(self, start_date: str = None, end_date: str = None,
                 limit: int = 1000) -> pd.DataFrame:
        """
        讀取 ADL 歷史資料

        Args:
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            limit: 返回記錄數量限制

        Returns:
            pd.DataFrame: ADL 歷史資料，欄位為 `ADL`
        """
        if self.MySql_server is None:
            print("Database connection not initialized")
            return pd.DataFrame()

        try:
            with self.server_flask.app_context():
                conditions = []
                params = {}

                if start_date:
                    conditions.append("date >= %(start_date)s")
                    params["start_date"] = start_date

                if end_date:
                    conditions.append("date <= %(end_date)s")
                    params["end_date"] = end_date

                where_clause = " AND ".join(conditions) if conditions else "1=1"
                query = f"""
                SELECT date, adl
                FROM adl
                WHERE {where_clause}
                ORDER BY date DESC
                LIMIT %(limit)s
                """

                params["limit"] = limit
                df = pd.read_sql(query, con=self.MySql_server.engine, params=params)
                if not df.empty:
                    df["date"] = pd.to_datetime(df["date"])
                    df = df.set_index("date")
                    df = df.rename(columns={"adl": "ADL"})
                return df
        except Exception as e:
            print(f"SQL Error in read_adl: {e}")
            return pd.DataFrame()

    def save_adl_data(self, adl_df: pd.DataFrame) -> bool:
        """
        以完整重算結果覆蓋 ADL 歷史資料表。
        """
        if self.MySql_server is None:
            print("Database connection not initialized")
            return False

        if adl_df.empty:
            print("No ADL data to save.")
            return False

        try:
            normalized_df = adl_df.copy().sort_index()
            normalized_df.index = pd.to_datetime(normalized_df.index)

            if "ADL" not in normalized_df.columns:
                first_col = normalized_df.columns[0]
                normalized_df = normalized_df.rename(columns={first_col: "ADL"})

            df_to_save = normalized_df.reset_index()
            df_to_save.columns = ["date", "adl"]

            with self.server_flask.app_context():
                with self.MySql_server.engine.begin() as connection:
                    df_to_save.to_sql(
                        name="adl",
                        con=connection,
                        if_exists="replace",
                        index=False,
                    )
            return True
        except Exception as e:
            print(f"SQL Error in save_adl_data: {e}")
            return False
