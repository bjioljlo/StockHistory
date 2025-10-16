import os

import pandas as pd
from pandas import DataFrame

import Common.InfomationType as info
from SqlService import SqlService


class ReadLoadSystem:
    def __init__(self, sqlservice: SqlService) -> None:
        self.load_memery = {}
        self._sqlservice = sqlservice

    @property
    def Memery(self) -> dict:
        return self.load_memery

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

    def load_stock_file(self, fileName: str, stockName: str = ""):
        """#讀取歷史資料"""
        if fileName in self.load_memery:  # 快取
            return self.load_memery[fileName]
        df = DataFrame()
        if stockName != "":  # mysql
            df = self._sqlservice.readStockDay(stockName + info.local_type.Taiwan)
        if df.empty:  # 本機端存檔
            try:
                df = pd.read_csv(
                    fileName + ".csv", index_col="Date", parse_dates=["Date"]
                )
            except Exception:
                print("no " + stockName + info.local_type.Taiwan + " csv file")
                print(Exception)
                return df
            self._sqlservice.saveTable(stockName + info.local_type.Taiwan, df)

        df = df.dropna(how="any", inplace=False)  # 將某些null欄位去除
        try:
            df["Volume"] = df["Volume"].astype("int")
        except Exception:
            print("no Volume" + Exception)

        self.load_memery[fileName] = df
        return df

    def load_other_file(self, fileName: str, file: str = ""):
        """#讀取資料"""
        if fileName in self.load_memery:  # 快取
            return self.load_memery[fileName]
        df = DataFrame()
        if file != "":  # mysql
            df = self._sqlservice.readStockDay(file)
        if df.empty:  # 本機端存檔
            try:
                df = pd.read_csv(
                    fileName + ".csv", index_col="Date", parse_dates=["Date"]
                )
            except Exception:
                print("no " + fileName + " csv file")
                return df

        df = df.dropna(how="any", inplace=False)  # 將某些null欄位去除
        self.load_memery[fileName] = df
        return df

    def delet_stock_file(self, fileName: str):
        """#刪除歷史資料"""
        if os.path.isfile(fileName):
            os.remove(fileName)

    def load_month_file(self, fileName: str, file: str = ""):
        """#讀取月資料"""
        if fileName in self.load_memery:  # 快取
            return self.load_memery[fileName]
        df = DataFrame()
        if file != "":
            df = self._sqlservice.readDividendYield(file)
        if df.empty:
            try:
                df = pd.read_csv(
                    fileName + ".csv",
                    index_col="code",
                    parse_dates=["code"],
                )
            except UnicodeDecodeError as e:
                print("no " + fileName + " csv file" + " " + str(e))
                return df
            except pd.errors.EmptyDataError as e:
                print("no " + fileName + " csv file" + " " + str(e))
                return df
            except FileNotFoundError as e:
                print("no " + fileName + " csv file" + " " + str(e))
                return df
        self.load_memery[fileName] = df
        return df
