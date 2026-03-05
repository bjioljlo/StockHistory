import threading
from datetime import datetime
from typing import Dict, Any

import pandas as pd
import yfinance as yf
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text

from src.Common import Tools
from src.Common.ConfigService import load_config, get_config_path


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

    def upsert_data(self, table_name: str, data_df: pd.DataFrame, key_columns: list[str]):
        """
        Upserts data into a table. Updates existing rows based on key_columns and inserts new ones.
        Note: This implementation reads the entire table into memory and is best for small to medium tables.

        Args:
            table_name (str): The name of the target table.
            data_df (pd.DataFrame): The new data to upsert.
            key_columns (list[str]): The list of primary key column names (e.g., ['id']).

        Returns:
            bool: True if successful, False otherwise.
        """
        if not all(col in data_df.columns for col in key_columns):
            print(f"Error: Key columns {key_columns} not found in the DataFrame.")
            return False

        if not table_name.islower():
            table_name = table_name.lower()

        try:
            with self.server_flask.app_context():
                with self.MySql_server.engine.begin() as connection:
                    
                    try:
                        existing_df = pd.read_sql_table(table_name, connection)
                    except Exception:
                        # Table doesn't exist yet
                        existing_df = pd.DataFrame(columns=data_df.columns)

                    # Combine old and new data
                    combined_df = pd.concat([existing_df, data_df], ignore_index=True)

                    # Drop duplicates based on the primary key, keeping the last entry (the new data)
                    upsert_df = combined_df.drop_duplicates(subset=key_columns, keep='last')

                    # Write the final, merged data back, replacing the entire table
                    upsert_df.to_sql(
                        name=table_name,
                        con=connection,
                        if_exists='replace',
                        index=False
                    )
                    print(f"Upsert successful for table '{table_name}'. Final row count: {len(upsert_df)}")
                    return True
        except Exception as e:
            print(f"SQL Error during upsert into {table_name}: {e}")
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
            config = load_config(get_config_path())
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

                query = """
                SELECT symbol, date, company_name, pe_ratio, dividend_yield, pb_ratio
                FROM dividend_yield
                WHERE """ + where_clause + """
                ORDER BY symbol, date DESC
                LIMIT """ + str(limit)

                # 如果有參數，使用參數化查詢，否則直接執行
                if params:
                    df = pd.read_sql(query, con=self.MySql_server.engine, params=params)
                else:
                    df = pd.read_sql(query, con=self.MySql_server.engine)
                return df

        except Exception as e:
            print(f"SQL Error in read_dividend_yield: {e}")
            return pd.DataFrame()

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

                query = """
                SELECT symbol, company_name, report_year, report_month,
                       revenue_current_month, revenue_last_month,
                       revenue_last_year_same_month, revenue_ytd,
                       revenue_last_year_ytd, notes
                FROM monthly_reports
                WHERE """ + where_clause + """
                ORDER BY symbol, report_year DESC, report_month DESC
                LIMIT """ + str(limit)

                # 如果有參數，使用參數化查詢，否則直接執行
                if params:
                    df = pd.read_sql(query, con=self.MySql_server.engine, params=params)
                else:
                    df = pd.read_sql(query, con=self.MySql_server.engine)
                return df

        except Exception as e:
            print(f"SQL Error in read_monthly_reports: {e}")
            return pd.DataFrame()

    def read_quarterly_reports(self, symbol: str = None, report_type: str = None,
                             start_year: int = None, end_year: int = None,
                             limit: int = 1000) -> pd.DataFrame:
        """
        從統一的quarterly_reports表格讀取季報數據

        Args:
            symbol: 股票代號，為None時返回所有股票
            report_type: 報表類型 ('PLA', 'BS', 'CPL', 'SCF')
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
                    conditions.append("report_type = :report_type")
                    params['report_type'] = report_type.upper()

                if start_year:
                    conditions.append("report_year >= :start_year")
                    params['start_year'] = start_year

                if end_year:
                    conditions.append("report_year <= :end_year")
                    params['end_year'] = end_year

                where_clause = " AND ".join(conditions) if conditions else "1=1"

                query = """
                SELECT symbol, company_name, report_year, report_season, report_type,
                       revenue, gross_margin, operating_margin, pre_tax_margin, net_margin,
                       consolidated_net_income, consolidated_eps,
                       total_assets, total_liabilities, equity, capital, book_value_per_share,
                       operating_cash_flow, investing_cash_flow, financing_cash_flow
                FROM quarterly_reports
                WHERE """ + where_clause + """
                ORDER BY symbol, report_year DESC, report_season DESC
                LIMIT """ + str(limit)

                # 如果有參數，使用參數化查詢，否則直接執行
                if params:
                    df = pd.read_sql(query, con=self.MySql_server.engine, params=params)
                else:
                    df = pd.read_sql(query, con=self.MySql_server.engine)
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
                    conditions.append("date >= :start_date")
                    params['start_date'] = start_date

                if end_date:
                    conditions.append("date <= :end_date")
                    params['end_date'] = end_date

                where_clause = " AND ".join(conditions) if conditions else "1=1"

                query = f"""
                SELECT date, 上漲, 下跌
                FROM ad_index
                WHERE {where_clause}
                ORDER BY date DESC
                LIMIT {limit}
                """

                # 如果有參數，使用參數化查詢，否則直接執行
                if params:
                    df = pd.read_sql(query, con=self.MySql_server.engine, params=params)
                else:
                    df = pd.read_sql(query, con=self.MySql_server.engine)
                
                # 設定索引
                if not df.empty:
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.set_index('date')
                    # 重命名欄位以符合原有格式
                    df = df.rename(columns={'up_count': '上漲', 'down_count': '下跌'})
                
                return df

        except Exception as e:
            print(f"SQL Error in read_ad_index: {e}")
            return pd.DataFrame()
