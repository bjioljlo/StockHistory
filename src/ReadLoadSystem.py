import pandas as pd
from pandas import DataFrame
from datetime import datetime
from sqlalchemy import text

from src.SqlService import SqlService


class ReadLoadSystem:
    def __init__(self, sqlservice: SqlService) -> None:
        self._sqlservice = sqlservice

    def save_stock_file(
        self, fileName: str, stockData, start_index: int = 0, end_index: int = 0
    ):
        """#存下歷史資料"""
        with open(fileName + ".csv", "w") as f:
            if start_index == end_index == 0:
                f.writelines(stockData.text)
            else:
                stringText = stockData.text
                stringText = stringText.replace(",\r\n", "\r\n")
                stringText = stringText.replace("-", "0")
                for i in range(10):
                    stringText = stringText.replace(str(i) + ",", str(i))
                pos = stringText.index("\n")
                # pos2 = stringText.rindex('\r\n""\r\n')
                pos2 = stringText.rindex("\r\n")
                pos = pos + 1
                f.writelines(stringText[pos:pos2])

    def load_month_file(self, fileName: str, file: str = ""):
        df = DataFrame()
        if file != "":
            df = self._sqlservice.readDividendYield(file)
        if df.empty:
            try:
                df = pd.read_csv(fileName + ".csv")
                # 設定code欄位為索引，如果存在的話
                if "code" in df.columns:
                    df.set_index("code", inplace=True)
                # 使用混合快取服務更新快取
                if hasattr(self, '_cache_service') and self._cache_service and file:
                    try:
                        self._cache_service.set_stock_data(file, df)
                        print(f"已將 {file} 存到混合快取")
                    except Exception as e:
                        print(f"儲存 {file} 到緩存失敗: {e}")
            except UnicodeDecodeError as e:
                print("no " + fileName + " csv file" + " " + str(e))
                return df
            except pd.errors.EmptyDataError as e:
                print("no " + fileName + " csv file" + " " + str(e))
                return df
            except FileNotFoundError as e:
                print("no " + fileName + " csv file" + " " + str(e))
                return df
        return df

    def calculate_ad_index_for_date(self, date: datetime) -> pd.DataFrame:
        """
        計算指定日期的漲跌指數 (AD Index)

        Args:
            date: 目標日期

        Returns:
            DataFrame 包含 up_count, down_count
        """
        date_str = date.strftime('%Y-%m-%d')

        # 讀取指定日期所有有收盤價的股票，過濾排除ETF
        query = text("""
            SELECT DISTINCT symbol FROM stock_daily_prices
            WHERE date = :target_date
            AND symbol NOT LIKE '%%ETF%%'
            AND symbol NOT LIKE '%%0050%%'
            AND symbol NOT LIKE '%%0051%%'
            AND symbol NOT LIKE '%%0052%%'
            AND symbol NOT LIKE '%%0053%%'
            AND symbol NOT LIKE '%%0055%%'
            AND symbol NOT LIKE '%%0056%%'
            AND symbol NOT LIKE '%%0057%%'
            AND symbol NOT LIKE '%%006201%%'
            AND symbol NOT LIKE '%%00631L%%'
            AND symbol NOT LIKE '%%00632R%%'
            AND symbol REGEXP '^[0-9]{4}$'
        """)

        with self._sqlservice.server_flask.app_context():
            stock_list = pd.read_sql(query,
                                     con=self._sqlservice.MySql_server.engine,
                                     params={'target_date': date_str})

        up_count = 0
        down_count = 0
        unchanged_count = 0

        for _, stock in stock_list.iterrows():
            symbol = stock['symbol']
            history = self._sqlservice.readStockDay(symbol)

            if history.empty or date_str not in history.index:
                continue

            today_close = history.loc[date_str, 'Close']
            prev_idx = history.index.get_loc(date_str) - 1

            if prev_idx < 0:
                unchanged_count += 1
                continue

            prev_close = history.iloc[prev_idx]['Close']

            if today_close > prev_close:
                up_count += 1
            elif today_close < prev_close:
                down_count += 1
            else:
                unchanged_count += 1

        result = pd.DataFrame([{
            'date': date,
            'up_count': up_count,
            'down_count': down_count,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }])

        result['date'] = pd.to_datetime(result['date'])
        result = result.set_index('date')

        return result
