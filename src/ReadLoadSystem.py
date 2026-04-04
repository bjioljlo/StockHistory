import pandas as pd
from pandas import DataFrame

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
        """#讀取月資料"""
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
