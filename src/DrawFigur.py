import matplotlib
matplotlib.use('Qt5Agg')  # 使用 Qt5Agg 後端以匹配 PyQt5
import matplotlib.pyplot as plt
import mplfinance as mpf
import numpy as np
import pandas as pd
import seaborn as sns
import talib
from pandas import DataFrame
import threading

class DrawFigur:
    def __init__(self) -> None:
        self.show_volume = False
        self.PICS = []
        self.panelCount = 0
        self.lock = threading.Lock()

    def draw_stock(self, table: DataFrame, number: int, adl_data: DataFrame = None):
        """繪製股票 K 線圖，可選包含 ADL 指標

        Args:
            table: 股票價格數據，需包含 High, Low, Close, Volume 欄位
            number: 股票代號
            adl_data: 可選的 ADL 數據 DataFrame，用於在主圖中顯示 ADL 指標
        """
        import pandas as pd

        mc = mpf.make_marketcolors(
            up="r", down="g", edge="", wick="inherit", volume="inherit"
        )
        s = mpf.make_mpf_style(base_mpf_style="charles", marketcolors=mc)

        # Process ADL data if provided
        if adl_data is not None and not adl_data.empty:
            try:
                # Filter ADL data to only include dates that exist in main table
                # This ensures dimensions match exactly
                common_indices = table.index.intersection(adl_data.index)

                if len(common_indices) > 0:
                    # Get column name from adl_data (could be 'ADL' or a numeric column)
                    adl_column = adl_data.columns[0] if len(adl_data.columns) > 0 else None

                    if adl_column is not None:
                        # Create a Series with the exact same index as table
                        adl_values = adl_data.reindex(table.index)[adl_column]

                        # Add to PICS before plotting
                        self.panelCount = self.panelCount + 1
                        self.PICS.append(
                            mpf.make_addplot(adl_values, panel=self.panelCount, color='blue', ylabel='ADL')
                        )
            except Exception as e:
                print(f"處理 ADL 數據時發生錯誤: {e}")
                import traceback
                traceback.print_exc()

        mpf.plot(
            table,
            type="candle",
            volume=self.show_volume,
            style=s,
            addplot=self.PICS,
            figsize=(13, 7),
            title=str(number),
        )

    def draw_SMA(self, table: DataFrame, day: int):
        mclose = talib.SMA(
            np.array(table["Close"]), day
        )  # 用np.array才可以將均線和蠟燭圖放一起
        self.PICS.append(mpf.make_addplot(mclose, panel=0))

    def draw_BollingerBands(self, table: DataFrame):
        upper, middle, lower = talib.BBANDS(np.array(table["Close"]))
        self.PICS.append(mpf.make_addplot(upper, panel=0))
        self.PICS.append(mpf.make_addplot(middle, panel=0))
        self.PICS.append(mpf.make_addplot(lower, panel=0))

    def draw_KD(self, table: DataFrame):
        table["k"], table["d"] = talib.STOCH(
            table["High"], table["Low"], table["Close"]
        )
        table["k"].fillna(value=0, inplace=True)
        table["d"].fillna(value=0, inplace=True)
        self.panelCount = self.panelCount + 1
        self.PICS.append(
            mpf.make_addplot(
                table["k"], panel=self.panelCount, ylabel="KD", color="red"
            )
        )
        self.PICS.append(
            mpf.make_addplot(table["d"], panel=self.panelCount, color="blue")
        )

    def draw_Volume(self):
        self.show_volume = True
        self.panelCount = self.panelCount + 1

    def draw_RSI(self, table: DataFrame):
        mRSI = talib.RSI(np.array(table["Close"]))
        self.panelCount = self.panelCount + 1
        self.PICS.append(mpf.make_addplot(mRSI, panel=self.panelCount, ylabel="RSI"))

    def draw_ADL(self, table: DataFrame, reference_data: DataFrame = None):
        self.panelCount = self.panelCount + 1
        # If reference_data is provided (the main stock chart data),
        # filter ADL data to match its index to avoid dimension mismatch in mplfinance
        if reference_data is not None and not table.empty:
            table = table[table.index.isin(reference_data.index)]
        if not table.empty:
            self.PICS.append(
                mpf.make_addplot(table, panel=self.panelCount, color="blue", ylabel="ADL")
            )

    def draw_MACD(self, table: DataFrame):
        self.panelCount = self.panelCount + 1
        macd, macdsignal, macdhist = talib.MACD(table["Close"])
        self.PICS.append(
            mpf.make_addplot(macd, panel=self.panelCount, ylabel="MACD", color="blue")
        )
        self.PICS.append(
            mpf.make_addplot(macdsignal, panel=self.panelCount, color="red")
        )
        self.PICS.append(mpf.make_addplot(macdhist, type="bar", panel=self.panelCount))

    def draw_RP(self, table: DataFrame, stockNum: int, columnName: str, title: str, ylabel: str):
        """繪製報表圖表，使用獨立的 matplotlib 視窗"""
        try:
            with self.lock:
                # 檢查資料是否有效
                if table is None or table.empty:
                    print("警告：沒有數據可以繪圖")
                    return

                if columnName not in table.columns:
                    print(f"錯誤：欄位 '{columnName}' 不存在於數據中")
                    print(f"可用的欄位: {list(table.columns)}")
                    return

                # 檢查是否有 NaN 或無限值
                if table[columnName].isna().any():
                    print(f"警告：數據包含 NaN 值，將進行清理")
                    table = table.dropna(subset=[columnName])

                if table.empty:
                    print("警告：數據清理後為空，無法繪圖")
                    return

                plot_table = table.copy()

                # 單一股票區間查詢常使用 MultiIndex(symbol, report_date)，
                # matplotlib 無法直接將 tuple 作為 x 軸類別值處理，改用最後一層日期索引繪圖。
                if isinstance(plot_table.index, pd.MultiIndex):
                    plot_table.index = plot_table.index.get_level_values(-1)

                plot_series = plot_table[columnName]
                if isinstance(plot_series, DataFrame):
                    plot_series = plot_series.iloc[:, 0]

                # 創建新的圖形，使用唯一的編號避免衝突
                fig = plt.figure(num=f"Chart_{stockNum}_{str(title)}")
                plt.clf()  # 清除圖形內容

                ax = fig.add_subplot(111)
                ax.plot(plot_table.index, plot_series, label=str(title), linewidth=2)

                # 設置標籤和標題
                ax.set_xlabel("Date", fontsize=12)
                ax.set_ylabel(str(ylabel), fontsize=12)
                ax.set_title(f"{stockNum} - {str(title)}", fontsize=14, fontweight='bold')

                # 旋轉 x 軸標籤以便閱讀
                plt.xticks(rotation=45, ha='right')

                # 添加網格和圖例
                ax.grid(True, alpha=0.3)
                ax.legend(loc='best')

                # 調整佈局以避免標籤被切掉
                plt.tight_layout()

                # 使用 show() 顯示圖表，但不阻塞主線程
                plt.show(block=False)
                plt.pause(0.001)  # 讓 matplotlib 處理事件

        except Exception as e:
            print(f"繪圖時發生錯誤: {e}")
            import traceback
            traceback.print_exc()

    def draw_BackTestResult(self, _data: DataFrame, outputFolder: str = ""):
        plt.figure(figsize=(15, 10))
        sns.lineplot(x="date", y="資產比例", data=_data)
        sns.set_style("darkgrid")
        plt.xlabel("date")
        plt.ylabel("%")
        plt.savefig(outputFolder + "ReportPic.png")
        plt.close()

    def Clear_PICS(self):
        with self.lock:
            self.PICS = []
            self.panelCount = 0
            self.show_volume = False
