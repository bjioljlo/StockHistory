import threading
from datetime import datetime
import yaml

import pandas as pd
import yfinance as yf
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect

from Common import Tools


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
        try:
            with self.server_flask.app_context():
                dataframe = pd.read_sql(
                    sql=name, con=self.MySql_server.engine, index_col="Date"
                )
                return dataframe
        except Exception as e:
            print("SQL Error {}".format(e.args))
            return dataframe

    def readDividendYield(self, name: str):
        dataframe = pd.DataFrame()
        if not name.islower():
            name = name.lower()
        try:
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
            with self.server_flask.app_context():
                if not name.islower():
                    name = name.lower()
                df_result.to_sql(
                    name=name, con=self.MySql_server.engine, if_exists="replace"
                )
                print("Update stocks " + name + " OK!")

    def __SetMysqlServer(self):
        print("Loading database configuration from config.yml")
        
        try:
            with open('config.yml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        except FileNotFoundError:
            print("Error: config.yml not found in the project root.")
            return
        except yaml.YAMLError as e:
            print(f"Error parsing config.yml: {e}")
            return

        db_config = config.get('database', {})
        db_type = db_config.get('type', 'mysql')

        uri = None
        if db_type == 'mysql':
            mysql_config = db_config.get('mysql', {})
            user = mysql_config.get('user')
            password = mysql_config.get('password')
            host = mysql_config.get('host')
            port = mysql_config.get('port')
            db_name = mysql_config.get('databasename')
            uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}?local_infile=1"
        elif db_type == 'postgresql':
            # For PostgreSQL, you might need to run: pip install psycopg2-binary
            pg_config = db_config.get('postgresql', {})
            user = pg_config.get('user')
            password = pg_config.get('password')
            host = pg_config.get('host')
            port = pg_config.get('port')
            db_name = pg_config.get('databasename')
            uri = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
        elif db_type == 'sqlite':
            sqlite_config = db_config.get('sqlite', {})
            path = sqlite_config.get('path', 'default.db')
            uri = f"sqlite:///{path}" # Path is relative to the project root
        else:
            print(f"Unsupported database type in config.yml: {db_type}")
            return
            
        self.server_flask.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        self.server_flask.config["SQLALCHEMY_DATABASE_URI"] = uri
        
        # Connect to the database
        self.MySql_server = SQLAlchemy(self.server_flask)
        print(f"Successfully configured database: {db_type}")