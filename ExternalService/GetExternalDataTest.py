import os
import sys
import time
from datetime import datetime
from io import StringIO

import pandas as pd
import requests

import Common.InfomationType as info
from TGetExternalData import TGetExternalData
import StockInfos
from Common import Tools


class GetExternalDataTest(TGetExternalData):
    """測試用爬取股票財務報告 請勿在別的地方使用"""

    # TODO : 要完成其他測試用的GET方法 2025/3/2
    def get_allstock_monthly_report(self, start: datetime):
        try:
            return super().get_allstock_monthly_report(start)
        except Exception:
            print(
                "".join(["{}:取得".format(sys._getframe().f_code.co_name)]),
                "月營收的資料:",
                str(start),
            )
            if not Tools.Have_MonthRP(start):
                return pd.DataFrame()
            m_data = pd.DataFrame()
            year = start.year
            file = "monthly_report_" + str(start.year) + "_" + str(start.month)
            fileName = self.filePath + "/" + self.fileName_monthRP + "/" + file

            if m_data.empty:
                if not os.path.isfile(fileName + ".csv"):
                    # 假如是西元，轉成民國
                    if year > 1990:
                        year -= 1911
                    url = (
                        "https://mops.twse.com.tw/nas/t21/sii/t21sc03_"
                        + str(year)
                        + "_"
                        + str(start.month)
                        + "_0.html"
                    )
                    if year <= 98:
                        url = (
                            "https://mops.twse.com.tw/nas/t21/sii/t21sc03_"
                            + str(year)
                            + "_"
                            + str(start.month)
                            + ".html"
                        )

                    # 下載該年月的網站，並用pandas轉換成 dataframe
                    r = requests.get(url, headers=Tools.get_random_Header())
                    r.encoding = "big5-hkscs"

                    try:
                        dfs = pd.read_html(StringIO(r.text), encoding="big-5")
                    except Exception:
                        return pd.DataFrame()

                    df = pd.concat(
                        [df for df in dfs if df.shape[1] <= 11 and df.shape[1] > 5]
                    )

                    if "levels" in dir(df.columns):
                        df.columns = df.columns.get_level_values(1)
                        df = df.rename(columns={"公司 代號": "公司代號"})
                    else:
                        df = df[list(range(0, 10))]
                        column_index = df.index[(df[0] == "公司代號")][0]
                        df.columns = df.iloc[column_index]

                    df["當月營收"] = pd.to_numeric(df["當月營收"], "coerce")
                    df = df[~df["當月營收"].isnull()]
                    df = df[df["公司代號"] != "合計"]

                    df.to_csv(fileName + ".csv", index=False)
                    # 偽停頓
                    time.sleep(1.5)

                m_data = pd.read_csv(fileName)
                m_data.drop(m_data.tail(1).index, inplace=True)
                # 整理一下資料
                m_data.rename(columns={"公司代號": "code"}, inplace=True)
                m_data[[ "code"]] = m_data[[ "code"]].astype(int)
                m_data.set_index("code", inplace=True)
            return m_data

    def get_stock_history(
        self,
        number: str,
        start=datetime.strptime("2005-1-1", "%Y-%m-%d"),
    ) -> pd.DataFrame:
        try:
            return super().get_stock_history(number, start)
        except Exception:
            print(
                ".".join(
                    [
                        "取得",
                        str(number),
                        "的資料從",
                        str(start),
                        "到今天:{}".format(sys._getframe().f_code.co_name),
                    ]
                )
            )
            start_time = start
            if type(start_time) is str:
                start_time = datetime.strptime(start_time, "%Y-%m-%d")
            if type(number) is not str:
                number = str(number)
            data_time = datetime.strptime("2005-1-1", "%Y-%m-%d")
            result = pd.DataFrame()

            if not StockInfos.ts.codes.__contains__(number):
                print("無此檔股票")
                return result
            if start_time < data_time:
                print("日期請大於西元2005年")
                return result
            file = str(number)
            filename = (
                self.filePath
                + "\\"
                + self.fileName_stockInfo
                + "\\"
                + file
                + "_2000-1-1_2021-8-7"
            )
            m_history = pd.DataFrame()
            if not os.path.isfile(filename + ".csv"):
                return result
            m_history = pd.read_csv(
                filename + ".csv", index_col="Date", parse_dates=["Date"]
            )
            # 整理一下資料
            mask = m_history.index >= start_time
            result = m_history[mask]
            result = result.dropna(axis=0, how="any")
            return result

    def get_allstock_financial_statement(self, start: datetime, type: info.FS_type):
        try:
            super().get_allstock_financial_statement(start, type)
        except Exception:
            Temp_data = pd.DataFrame()
            season = int(((start.month - 1) / 3) + 1)
            file = str(start.year) + "-season" + str(season) + "-" + type.value
            fileName = self.filePath + "/" + self.fileName_season + "/" + file
            if Temp_data.empty:
                if os.path.isfile(fileName + ".csv"):
                    print("已經有" + str(start.month) + "月財務報告")
                else:
                    self._financial_statement(start.year, season, type)
                    print("下載" + str(start.month) + "月財務報告ＯＫ")
                stock = pd.read_csv(fileName + ".csv")
                # 整理一下資料
                stock.rename(columns={"公司代號": "code"}, inplace=True)
                stock.set_index("code", inplace=True)
                if info.FS_type.SCF == type:
                    if stock["投資活動之淨現金流入（流出）"].dtype == object:
                        stock["投資活動之淨現金流入（流出）"] = pd.to_numeric(
                            stock["投資活動之淨現金流入（流出）"].str.replace("--", "0")
                        )
                    if stock["營業活動之淨現金流入（流出）"].dtype == object:
                        stock["營業活動之淨現金流入（流出）"] = pd.to_numeric(
                            stock["營業活動之淨現金流入（流出）"].str.replace("--", "0")
                        )
                    if stock["籌資活動之淨現金流入（流出）"].dtype == object:
                        stock["籌資活動之淨現金流入（流出）"] = pd.to_numeric(
                            stock["籌資活動之淨現金流入（流出）"].str.replace("--", "0")
                        )
            else:
                stock = Temp_data
            return stock