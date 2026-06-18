"""
Stock Data Synchronizer Module

Responsible for:
- Synchronizing data between SQL and MongoDB
- Unified table handling
- Data format conversion for database storage
- Replace and upsert operations
"""
import pandas as pd


class StockDataSynchronizer:
    def __init__(self, sql_service, mongo_service, read_load_system=None, config=None, **kwargs):
        self._sql_service = sql_service
        self._mongo_service = mongo_service
        # read_load_system and config are deprecated and no longer used, kept for backward compatibility

    def sync_table_to_mongo(self, table_name: str):
        """
        Reads a table from MySQL and saves it to MongoDB.
        """
        print(f"Syncing table {table_name} to MongoDB...")

        df = pd.DataFrame()

        # Special handling for stock data tables
        if table_name.lower() == 'stock_daily_prices':
            # For unified stock table, we need to create separate collections for each stock
            print("Syncing unified stock_daily_prices table to MongoDB collections...")
            self._sync_unified_stock_table_to_mongo()
            return
        elif table_name.lower() in ['ad_index']:
            # AD_index is a special index table
            df = self._sql_service.readDividendYield(table_name)
        else:
            # Other non-stock tables use original logic
            df = self._sql_service.readStockDay(table_name)
            if df.empty:
                df = self._sql_service.readDividendYield(table_name)

        if not df.empty:
            self._mongo_service.saveTable(table_name, df)
            print(f"Successfully synced table {table_name} to MongoDB.")
        else:
            print(f"Skipping empty table: {table_name}")

    def _sync_unified_stock_table_to_mongo(self):
        """
        Sync unified stock_daily_prices table to individual MongoDB collections
        """
        try:
            # Get all unique symbols from unified table
            query = "SELECT DISTINCT symbol FROM stock_daily_prices"
            with self._sql_service.server_flask.app_context():
                unique_symbols_df = pd.read_sql(query, con=self._sql_service.MySql_server.engine)

            if unique_symbols_df.empty:
                print("No symbols found in stock_daily_prices table")
                return

            total_symbols = len(unique_symbols_df)
            print(f"Found {total_symbols} unique symbols to sync")

            for i, row in unique_symbols_df.iterrows():
                symbol = row['symbol']
                print(f"Syncing symbol {symbol} ({i+1}/{total_symbols})...")

                # Read all data for this stock from unified table
                df = self._sql_service.readStockDay(symbol)
                if not df.empty:
                    self._mongo_service.saveTable(symbol.lower(), df)
                    print(f"Successfully synced {symbol} to MongoDB")
                else:
                    print(f"No data found for symbol {symbol}")

        except Exception as e:
            print(f"Error syncing unified stock table to MongoDB: {e}")

    def replace_stock_data(self, stock_name: str, df_result: pd.DataFrame) -> bool:
        """
        Saves a DataFrame to the unified stock_daily_prices table, overwriting existing data for this stock.
        """
        if df_result.empty:
            print(f"No data to replace for {stock_name}.")
            return True

        try:
            # Prepare data format for unified table
            symbol = stock_name.upper().replace('.TW', '').replace('.US', '').replace('.HK', '')
            market = self._determine_market(stock_name)

            df_to_write = df_result.reset_index()
            df_to_write['symbol'] = symbol
            df_to_write['market'] = market
            df_to_write = df_to_write.rename(columns={
                'Date': 'date',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Adj Close': 'adj_close',
                'Volume': 'volume'
            })

            # Use SqlService's public upsert method (handles duplicate key updates)
            return self._sql_service.upsert_data('stock_daily_prices', df_to_write, ['symbol', 'date'])

        except Exception as e:
            print(f"Error during table replace for {stock_name}: {e}")
            return False

    def upsert_stock_data(self, stock_name: str, df_result: pd.DataFrame) -> bool:
        """
        Upsert stock data to the unified stock_daily_prices table.
        """
        if df_result.empty:
            print(f"No data to upsert for {stock_name}.")
            return True

        try:
            # Prepare data format for unified table
            symbol = stock_name.upper().replace('.TW', '').replace('.US', '').replace('.HK', '')
            market = self._determine_market(stock_name)

            df_upsert = df_result.reset_index()
            df_upsert['symbol'] = symbol
            df_upsert['market'] = market
            df_upsert = df_upsert.rename(columns={
                'Date': 'date',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Adj Close': 'adj_close',
                'Volume': 'volume'
            })

            # Use SqlService's public upsert method (handles duplicate key updates)
            return self._sql_service.upsert_data('stock_daily_prices', df_upsert, ['symbol', 'date'])

        except Exception as e:
            print(f"Error during upsert for {stock_name}: {e}")
            return False

    def _determine_market(self, stock_name: str) -> str:
        """Determine market type"""
        name_lower = stock_name.lower()
        if name_lower.endswith('.tw') or (name_lower.replace('.tw', '').isdigit() and len(name_lower.replace('.tw', '')) >= 4):
            return 'TW'
        elif len(name_lower) <= 5 and not name_lower.replace('.', '').isdigit():
            return 'US'
        else:
            return 'OTHER'
