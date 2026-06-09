"""
SqlService - SQL 資料庫連線與操作

StockHistory 專用版本，包含 yfInfo 等獨有方法。
基礎 CRUD 繼承自 pydb_core.sql_service。
"""

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
        self.server_flask: Flask = Flask(__name__)
        self.MySql_server: SQLAlchemy = None
        self._CantUseStocks = []

    @property
    def CantUseStocks(self):
        return self._CantUseStocks

    def RunMysql(self):
        temp_thread = threading.Thread(target=self.__SetMysqlServer)
        temp_thread.start()

    def readStockDay(self, name: str):
        dataframe = pd.DataFrame()
        if not name.islower():
            name = name.lower()
        if self.MySql_server is None:
            print("Database connection not initialized")
            return dataframe
        symbol = name.upper().replace('.TW', '').replace('.US', '').replace('.HK', '')
        try:
            with self.server_flask.app_context():
                query = f"""
                SELECT date as Date, open as Open, high as High, low as Low,
                       close as Close, adj_close as `Adj Close`, volume as Volume
                FROM stock_daily_prices
                WHERE symbol = '{symbol}'
                ORDER BY date
                """
                dataframe = pd.read_sql(query, con=self.MySql_server.engine, index_col="Date")
                if not isinstance(dataframe.index, pd.DatetimeIndex):
                    dataframe.index = pd.to_datetime(dataframe.index)
                return dataframe
        except Exception as e:
            print("SQL Error {}".format(e.args))
            return dataframe

    def readDividendYield(self, name: str):
        dataframe = pd.DataFrame()
        try:
            with self.server_flask.app_context():
                dataframe = pd.read_sql(sql=name, con=self.MySql_server.engine, index_col="code")
                return dataframe
        except Exception as e:
            print("SQL Error {}".format(e.args))
            return dataframe

    def saveTable(self, _name: str, _df=pd.DataFrame()):
        if not _name.islower():
            _name = _name.lower()
        try:
            with self.server_flask.app_context():
                _df.to_sql(name=_name, con=self.MySql_server.engine, if_exists="replace")
                return True
        except Exception as e:
            print("SQL Error {}".format(e.args))
            return False

    def insert_into_table(self, table_name: str, data_df: pd.DataFrame):
        if not table_name.islower():
            table_name = table_name.lower()
        try:
            with self.server_flask.app_context():
                data_df.to_sql(name=table_name, con=self.MySql_server.engine, if_exists="append", index=False)
                print(f"Successfully inserted {len(data_df)} rows into {table_name}.")
                return True
        except Exception as e:
            print(f"SQL Error during insertion into {table_name}: {e}")
            return False

    def insert_data(self, table_name: str, data_df: pd.DataFrame):
        if not table_name.islower():
            table_name = table_name.lower()
        try:
            with self.server_flask.app_context():
                data_df.to_sql(name=table_name, con=self.MySql_server.engine, if_exists="append", index=False)
                print(f"Successfully inserted {len(data_df)} rows into {table_name}.")
                return True
        except Exception as e:
            print(f"SQL Error during insertion into {table_name}: {e}")
            return False

    def upsert_data(self, table_name: str, data_df: pd.DataFrame, key_columns: list[str]):
        if not all(col in data_df.columns for col in key_columns):
            print(f"Error: Key columns {key_columns} not found in the DataFrame.")
            return False
        if not table_name.islower():
            table_name = table_name.lower()
        try:
            with self.server_flask.app_context():
                with self.MySql_server.engine.begin() as connection:
                    inspector = inspect(connection)
                    if table_name not in inspector.get_table_names():
                        data_df.to_sql(name=table_name, con=connection, if_exists='replace', index=False)
                        print(f"Table '{table_name}' created and {len(data_df)} rows inserted.")
                        return True
                    success_count = 0
                    for _, row in data_df.iterrows():
                        columns = list(data_df.columns)
                        placeholders = ', '.join([f':{col}' for col in columns])
                        column_names = ', '.join([f'`{col}`' for col in columns])
                        update_columns = [col for col in columns if col not in key_columns]
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
                        row_dict = {}
                        for col in columns:
                            value = row[col]
                            if pd.isna(value) or value is None:
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
        if data_df.empty:
            print("No data to upsert")
            return True
        table_name = 'dividend_yield'
        try:
            with self.server_flask.app_context():
                with self.MySql_server.engine.begin() as connection:
                    inspector = inspect(connection)
                    if table_name not in inspector.get_table_names():
                        create_table_sql = """
                        CREATE TABLE IF NOT EXISTS dividend_yield (
                            id BIGINT AUTO_INCREMENT PRIMARY KEY,
                            symbol VARCHAR(20) NOT NULL,
                            date DATE NOT NULL,
                            company_name VARCHAR(100),
                            pe_ratio DECIMAL(10,2),
                            dividend_yield DECIMAL(5,2),
                            pb_ratio DECIMAL(10,2),
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
                    clean_df = data_df.copy()
                    for col in ['pe_ratio', 'dividend_yield', 'pb_ratio']:
                        if col in clean_df.columns:
                            clean_df[col] = clean_df[col].fillna(0.0)
                    for col in ['company_name']:
                        if col in clean_df.columns:
                            clean_df[col] = clean_df[col].fillna('')
                    values_list = []
                    params_dict = {}
                    for idx, (_, row) in enumerate(clean_df.iterrows()):
                        symbol = row.get('symbol')
                        date = row.get('date')
                        company_name = row.get('company_name')
                        pe_ratio = row.get('pe_ratio', 0.0)
                        dividend_yield = row.get('dividend_yield', 0.0)
                        pb_ratio = row.get('pb_ratio', 0.0)
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
                    values_clause = ','.join(values_list)
                    sql = f"""
                    INSERT INTO dividend_yield (symbol, date, company_name, pe_ratio, dividend_yield, pb_ratio)
                    VALUES {values_clause}
                    ON DUPLICATE KEY UPDATE
                    company_name = VALUES(company_name), pe_ratio = VALUES(pe_ratio),
                    dividend_yield = VALUES(dividend_yield), pb_ratio = VALUES(pb_ratio),
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
        try:
            with self.server_flask.app_context():
                with self.MySql_server.engine.connect() as connection:
                    inspector = inspect(connection)
                    return inspector.get_table_names()
        except Exception as e:
            print(f"SQL Error getting table names: {e}")
            return []

    def get_table_columns(self, table_name: str) -> list[dict]:
        if not table_name.islower():
            table_name = table_name.lower()
        try:
            with self.server_flask.app_context():
                with self.MySql_server.engine.connect() as connection:
                    inspector = inspect(connection)
                    if table_name not in inspector.get_table_names():
                        print(f"Table '{table_name}' does not exist")
                        return []
                    columns = inspector.get_columns(table_name)
                    result = []
                    for col in columns:
                        result.append({
                            'name': col['name'], 'type': str(col['type']),
                            'nullable': col['nullable'], 'default': col['default'],
                            'primary_key': col.get('primary_key', False)
                        })
                    return result
        except Exception as e:
            print(f"SQL Error getting columns for table '{table_name}': {e}")
            return []

    def yfInfo(self, name: str):
        """#獲取股票資訊"""
        if name in self._CantUseStocks:
            print("CantUseStock:" + str(name))
            return
        start_date = datetime(2005, 1, 1)
        end_date = datetime.today()
        df_result = yf.download([name], start_date, end_date)
        if df_result.empty:
            self._CantUseStocks.append(name)
            print("yahoo no data:" + str(name))
        else:
            df_result = Tools.TidyTicketData(df_result, name)
            symbol = name.upper().replace('.TW', '').replace('.US', '').replace('.HK', '')
            market = self._determine_market(name)
            df_result = df_result.reset_index()
            df_result['symbol'] = symbol
            df_result['market'] = market
            df_result = df_result.rename(columns={
                'Date': 'date', 'Open': 'open', 'High': 'high', 'Low': 'low',
                'Close': 'close', 'Adj Close': 'adj_close', 'Volume': 'volume'
            })
            self._insert_stock_data_to_unified_table(df_result)
            print("Update stocks " + name + " OK!")

    def _determine_market(self, stock_name: str) -> str:
        name_lower = stock_name.lower()
        if name_lower.endswith('.tw') or (name_lower.replace('.tw', '').isdigit() and len(name_lower.replace('.tw', '')) >= 4):
            return 'TW'
        elif len(name_lower) <= 5 and not name_lower.replace('.', '').isdigit():
            return 'US'
        else:
            return 'OTHER'

    def _insert_stock_data_to_unified_table(self, df: pd.DataFrame):
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
                        open = VALUES(open), high = VALUES(high), low = VALUES(low),
                        close = VALUES(close), adj_close = VALUES(adj_close),
                        volume = VALUES(volume), updated_at = CURRENT_TIMESTAMP
                        """)
                        row_dict = {}
                        for col in ['symbol', 'market', 'date', 'open', 'high', 'low', 'close', 'adj_close', 'volume']:
                            value = row[col] if col in row.index else None
                            if pd.isna(value) or value is None:
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
            uri = f"mysql+pymysql://{mysql_config['user']}:{mysql_config['password']}@{mysql_config['host']}:{mysql_config['port']}/{mysql_config['databasename']}?local_infile=1"
            pool_config = {
                'pool_size': mysql_config.get('pool_size', 5),
                'max_overflow': mysql_config.get('max_overflow', 10),
                'pool_timeout': mysql_config.get('pool_timeout', 30),
                'pool_recycle': mysql_config.get('pool_recycle', 3600),
                'pool_pre_ping': True
            }
        elif db_type == 'postgresql':
            pg_config = db_config.get('postgresql', {})
            uri = f"postgresql://{pg_config['user']}:{pg_config['password']}@{pg_config['host']}:{pg_config['port']}/{pg_config['databasename']}"
            pool_config = {'pool_size': 5, 'max_overflow': 10, 'pool_timeout': 30, 'pool_recycle': 3600, 'pool_pre_ping': True}
        elif db_type == 'sqlite':
            sqlite_config = db_config.get('sqlite', {})
            uri = f"sqlite:///{sqlite_config.get('path', 'default.db')}"
        else:
            print(f"Unsupported database type: {db_type}")
            return
        self.server_flask.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        self.server_flask.config["SQLALCHEMY_DATABASE_URI"] = uri
        self.server_flask.config["SQLALCHEMY_ENGINE_OPTIONS"] = pool_config
        self.MySql_server = SQLAlchemy(self.server_flask)
        print(f"Successfully configured database: {db_type} with connection pooling")

    def read_dividend_yield(self, symbol: str = None, start_date: str = None, end_date: str = None, limit: int = 1000) -> pd.DataFrame:
        if self.MySql_server is None:
            return pd.DataFrame()
        try:
            with self.server_flask.app_context():
                conditions, params = [], {}
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
                where = " AND ".join(conditions) if conditions else "1=1"
                query = text("SELECT symbol, date, company_name, pe_ratio, dividend_yield, pb_ratio FROM dividend_yield WHERE " + where + " ORDER BY symbol, date DESC LIMIT :limit")
                params['limit'] = limit
                return pd.read_sql(query, con=self.MySql_server.engine, params=params)
        except Exception as e:
            print(f"SQL Error in read_dividend_yield: {e}")
            return pd.DataFrame()

    def get_latest_dividend_yield_date(self) -> str | None:
        try:
            with self.server_flask.app_context():
                query = text("SELECT MAX(date) AS latest_date FROM dividend_yield")
                result = pd.read_sql(query, con=self.MySql_server.engine)
                if not result.empty and 'latest_date' in result.columns and result.iloc[0]['latest_date'] is not None:
                    return str(result.iloc[0]['latest_date'])
                return None
        except Exception as e:
            print(f"SQL Error: {e}")
            return None

    def read_ad_index(self, start_date: str = None, end_date: str = None, limit: int = 1000) -> pd.DataFrame:
        if self.MySql_server is None:
            return pd.DataFrame()
        try:
            with self.server_flask.app_context():
                conditions, params = [], {}
                if start_date: conditions.append("date >= %(start_date)s"); params['start_date'] = start_date
                if end_date: conditions.append("date <= %(end_date)s"); params['end_date'] = end_date
                where = " AND ".join(conditions) if conditions else "1=1"
                query = f"SELECT date, up_count, down_count FROM ad_index WHERE {where} ORDER BY date DESC LIMIT %(limit)s"
                params['limit'] = limit
                df = pd.read_sql(query, con=self.MySql_server.engine, params=params)
                if not df.empty:
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.set_index('date')
                return df
        except Exception as e:
            print(f"SQL Error: {e}")
            return pd.DataFrame()

    def read_adl(self, start_date: str = None, end_date: str = None, limit: int = 1000) -> pd.DataFrame:
        if self.MySql_server is None:
            return pd.DataFrame()
        try:
            with self.server_flask.app_context():
                conditions, params = [], {}
                if start_date: conditions.append("date >= %(start_date)s"); params["start_date"] = start_date
                if end_date: conditions.append("date <= %(end_date)s"); params["end_date"] = end_date
                where = " AND ".join(conditions) if conditions else "1=1"
                query = f"SELECT date, adl FROM adl WHERE {where} ORDER BY date DESC LIMIT %(limit)s"
                params["limit"] = limit
                df = pd.read_sql(query, con=self.MySql_server.engine, params=params)
                if not df.empty:
                    df["date"] = pd.to_datetime(df["date"])
                    df = df.set_index("date")
                    df = df.rename(columns={"adl": "ADL"})
                return df
        except Exception as e:
            print(f"SQL Error: {e}")
            return pd.DataFrame()

    def save_adl_data(self, adl_df: pd.DataFrame) -> bool:
        if self.MySql_server is None or adl_df.empty:
            return False
        try:
            normalized_df = adl_df.copy().sort_index()
            normalized_df.index = pd.to_datetime(normalized_df.index)
            if "ADL" not in normalized_df.columns:
                normalized_df = normalized_df.rename(columns={normalized_df.columns[0]: "ADL"})
            df_to_save = normalized_df.reset_index()
            df_to_save.columns = ["date", "adl"]
            with self.server_flask.app_context():
                with self.MySql_server.engine.begin() as connection:
                    df_to_save.to_sql(name="adl", con=connection, if_exists="replace", index=False)
            return True
        except Exception as e:
            print(f"SQL Error: {e}")
            return False


__all__ = ['SqlService']
