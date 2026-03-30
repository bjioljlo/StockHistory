import sys
from abc import ABC, abstractmethod

import pandas
from pandas import DataFrame, Series
import pandas as pd

from src.Common import InfomationType as info
from src.Common import Tools
from src.ExternalService.IGetExternalData import IGetExternalData

from .StockHistory import OriginalStock


class IReport(ABC):
    """指標歷史資料"""

    @abstractmethod
    def get_ALL_Report(self, date) -> DataFrame:
        raise NotImplementedError(
            "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name)
        )


class TReport(IReport):
    """指標歷史資料實作"""

    def __init__(self, name: str, Unit: int) -> None:
        self._name = name
        self._Unit = Unit

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    def get_ALL_Report(self, date, base_today=None) -> DataFrame:
        raise NotImplementedError(
            "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name)
        )

    def get_ReportByNumber(self, date, number: int, base_today=None) -> DataFrame:
        Temp = self.get_ALL_Report(date, base_today=base_today)
        
        if Temp.empty:
            print(f"{date}的{self._name}表沒出")
            return DataFrame()

        # 嘗試多種索引格式進行匹配
        search_keys = [str(number), number, f"{number:04d}"]
        
        for key in search_keys:
            if key in Temp.index:
                print(f"{date}的{number}公司成立")
                result = Temp.loc[key]

                # 確保返回 DataFrame 格式
                if isinstance(result, Series):
                    return result.to_frame().T
                elif isinstance(result, DataFrame):
                    return result
        
        print(f"{date}的{number}公司尚未成立")
        return DataFrame()

    def get_ReportByType(self, date, _type: info.StrEnum, base_today=None) -> Series:
        Temp = self.get_ALL_Report(date, base_today=base_today)
        try:
            return Temp[_type.get_sql_column()]
        except Exception:
            print("".join([str(date), "的", self._name, "表沒出"]))
            return DataFrame()

    def get_ReportByTypeAndNumber(self, date, _type: info.StrEnum, number: int, base_today=None):
        Temp = self.get_ReportByType(date, _type, base_today=base_today)
        try:
            return Temp[number]
        except Exception:
            if not Temp.empty:
                print("".join([str(date), "的", str(number), "公司尚未成立"]))
            return None

    def Next_date(self, date):
        return Tools.changeDateMonth(date, -self._Unit)
    
    def check_and_convert_to_series(self, tableFirst, tableSecond):
        """增強的數據對齊方法，處理不同類型的索引對齊問題"""
        print(f"check_and_convert_to_series: 處理數據對齊，tableFirst類型: {type(tableFirst)}, tableSecond類型: {type(tableSecond)}")
        
        # 確保兩個表都是 Series，如果不是則轉換
        if isinstance(tableFirst, DataFrame):
            if tableFirst.empty:
                print("check_and_convert_to_series: tableFirst 為空 DataFrame")
                return DataFrame(), DataFrame()
            # 如果是 DataFrame，取第一個欄位
            tableFirst = tableFirst.iloc[:, 0] if tableFirst.shape[1] > 0 else Series()
        
        if isinstance(tableSecond, DataFrame):
            if tableSecond.empty:
                print("check_and_convert_to_series: tableSecond 為空 DataFrame")
                return DataFrame(), DataFrame()
            # 如果是 DataFrame，取第一個欄位
            tableSecond = tableSecond.iloc[:, 0] if tableSecond.shape[1] > 0 else Series()
        
        # 檢查是否為空
        if (isinstance(tableFirst, Series) and tableFirst.empty) or \
           (isinstance(tableSecond, Series) and tableSecond.empty):
            print("check_and_convert_to_series: 其中一個 Series 為空")
            return DataFrame(), DataFrame()
        
        # 檢查索引類型和內容
        if isinstance(tableFirst, Series) and isinstance(tableSecond, Series):
            
            if tableFirst.empty or tableSecond.empty:
                print("check_and_convert_to_series: Series 為空")
                return DataFrame(), DataFrame()
            
            # 檢查是否有共同的索引
            common_index = tableFirst.index.intersection(tableSecond.index)
            
            if len(common_index) == 0:
                print("check_and_convert_to_series: 沒有共同索引，嘗試不同的對齊策略")
                
                # 策略1: 如果其中一個是單一值，嘗試廣播
                if len(tableFirst) == 1 and len(tableSecond) > 1:
                    print("check_and_convert_to_series: tableFirst 為單一值，嘗試廣播到 tableSecond")
                    tableFirst_aligned = Series([tableFirst.iloc[0]] * len(tableSecond), index=tableSecond.index)
                    tableSecond_aligned = tableSecond
                    return tableFirst_aligned, tableSecond_aligned
                
                if len(tableSecond) == 1 and len(tableFirst) > 1:
                    print("check_and_convert_to_series: tableSecond 為單一值，嘗試廣播到 tableFirst")
                    tableSecond_aligned = Series([tableSecond.iloc[0]] * len(tableFirst), index=tableFirst.index)
                    tableFirst_aligned = tableFirst
                    return tableFirst_aligned, tableSecond_aligned
                
                # 策略2: 如果索引類型不同，嘗試轉換
                if tableFirst.index.dtype != tableSecond.index.dtype:
                    print("check_and_convert_to_series: 索引類型不同，嘗試轉換")
                    try:
                        # 嘗試將兩個索引都轉換為字串
                        tableFirst.index = tableFirst.index.astype(str)
                        tableSecond.index = tableSecond.index.astype(str)
                        common_index = tableFirst.index.intersection(tableSecond.index)
                        print(f"check_and_convert_to_series: 轉換後共同索引: {common_index.tolist()}")
                        
                        if len(common_index) > 0:
                            tableFirst_aligned, tableSecond_aligned = tableFirst.align(tableSecond, join='inner', fill_value=0)
                            return tableFirst_aligned, tableSecond_aligned
                    except Exception as e:
                        print(f"check_and_convert_to_series: 索引轉換失敗: {e}")
                
                # 策略3: 如果都失敗，返回空結果
                print("check_and_convert_to_series: 所有對齊策略都失敗，返回空結果")
                return DataFrame(), DataFrame()
            
            # 有共同索引，正常對齊
            tableFirst_aligned, tableSecond_aligned = tableFirst.align(tableSecond, join='inner', fill_value=0)
            print(f"check_and_convert_to_series: 對齊成功，結果長度: {len(tableFirst_aligned)}")
            return tableFirst_aligned, tableSecond_aligned
        
        # 如果不是兩個 Series，返回原始數據
        return tableFirst, tableSecond


class AllStockReport(TReport):
    """指標歷史資料"""

    def __init__(self, _name: str, _Unit: int, _GetExternal: IGetExternalData) -> None:
        super().__init__(_name, _Unit)
        self._main_GetExternalData = _GetExternal


class Season_Report(AllStockReport):
    """以季為單位的指標歷史資料"""

    def __init__(
        self,
        name: str,
        Unit: int,
        GetExternal: IGetExternalData,
        _FS_type: info.FS_type,
    ):
        super().__init__(name, Unit, GetExternal)
        self._FS_type = _FS_type

    def get_ALL_Report(self, date, base_today=None) -> DataFrame:
        import Common.Tools as Tools
        safe_date = Tools.get_latest_season_report_date(date, base_today)
        return self._main_GetExternalData.get_allstock_financial_statement(
            safe_date, self._FS_type
        )


@staticmethod
def SeasonReportFactory(
    _FS_type: info.FS_type, _GetExternal: IGetExternalData
) -> Season_Report:
    return Season_Report(_FS_type.value, 3, _GetExternal, _FS_type)


class Month_Report(AllStockReport):
    """以月為單位的指標歷史資料"""

    def get_ALL_Report(self, date, base_today=None):
        import Common.Tools as Tools
        safe_date = Tools.get_latest_monthly_report_date(date, base_today)
        
        # 直接調用外部服務，讓它處理快取
        result_data = self._main_GetExternalData.get_allstock_monthly_report(safe_date)
        
        # 只在必要時進行後處理
        return result_data


class Day_Report(AllStockReport):
    """以日為單位的指標歷史資料"""

    def get_ALL_Report(self, date, base_today=None):
        import Common.Tools as Tools
        # 殖利率數據應該使用當前日期，不需要往回找
        # 只有在當天沒有交易數據時才往回找
        try:
            # 檢查當天是否有交易數據
            stock_data = self._main_GetExternalData.get_stock_history("2330", date)
            if date in stock_data.index:
                # 當天有交易數據，直接使用當天日期
                result = self._main_GetExternalData.get_allstock_yield(date)
                return result
            else:
                # 當天沒有交易數據，往回找最近的交易日
                safe_date = Tools.get_latest_daily_report_date(date, base_today)
                result = self._main_GetExternalData.get_allstock_yield(safe_date)
                return result
        except Exception:
            # 如果出錯，使用安全的日期獲取方式
            safe_date = Tools.get_latest_daily_report_date(date, base_today)
            result = self._main_GetExternalData.get_allstock_yield(safe_date)
            return result

    def Next_date(self, date):
        date = Tools.backWorkDays(date, self._Unit)
        while date not in self._main_GetExternalData.get_stock_history("2330").index:
            date = Tools.backWorkDays(date, self._Unit)
        return date


class ADL_Report(AllStockReport):
    """以日為單位的騰落指標歷史資料(AD)"""

    def get_ALL_Report(self, date):
        # The date parameter is ignored to fetch the full history for cumsum calculation.
        return self._main_GetExternalData.get_full_ad_index()

    def Next_date(self, date):
        date = Tools.backWorkDays(date, self._Unit)
        while date not in self._main_GetExternalData.get_stock_history("2330").index:
            date = Tools.backWorkDays(date, self._Unit)
        return date


class DividendYield_Report(AllStockReport):
    """以日為單位的股息殖利率歷史資料"""

    def get_ALL_Report(self, date, base_today=None):
        """從數據庫獲取股息殖利率數據"""
        try:
            # 使用SqlService從dividend_yield表格讀取數據
            result = self._main_GetExternalData.get_allstock_dividend_yield()
            
            # 數據清理和驗證
            if not result.empty: 

                # 確保索引是字串類型
                if 'symbol' in result.columns:
                    result['symbol'] = result['symbol'].astype(str)
                    result = result.set_index('symbol')
                elif 'code' in result.columns:
                    result['code'] = result['code'].astype(str)
                    result = result.set_index('code')

            return result
        except Exception as e:
            print(f"Error getting dividend yield data: {e}")
            return DataFrame()

    def get_ReportByType(self, date, _type: info.StrEnum, base_today=None) -> Series:
        """根據類型獲取特定欄位的數據"""
        Temp = self.get_ALL_Report(date, base_today=base_today)
        try:
            if _type == info.Day_type.Yield:
                # 返回殖利率欄位
                if 'dividend_yield' in Temp.columns:
                    return Temp.set_index('symbol')['dividend_yield']
                elif '殖利率(%)' in Temp.columns:
                    return Temp.set_index('code')['殖利率(%)']
            elif _type == info.Day_type.PER:
                # 返回本益比欄位
                if 'pe_ratio' in Temp.columns:
                    return Temp.set_index('symbol')['pe_ratio']
                elif '本益比' in Temp.columns:
                    return Temp.set_index('code')['本益比']
            elif _type == info.Day_type.PBR:
                # 返回股價淨值比欄位
                if 'pb_ratio' in Temp.columns:
                    return Temp.set_index('symbol')['pb_ratio']
                elif '股價淨值比' in Temp.columns:
                    return Temp.set_index('code')['股價淨值比']
            return Series()
        except Exception as e:
            print(f"Error getting report by type {_type}: {e}")
            return Series()

    def Next_date(self, date):
        """獲取下一個有效日期"""
        date = Tools.backWorkDays(date, self._Unit)
        # 確保日期有效（有交易日數據）
        while date not in self._main_GetExternalData.get_stock_history("2330").index:
            date = Tools.backWorkDays(date, self._Unit)
        return date


class Indicator(TReport):
    """指標處理"""

    def __init__(self, name: str, Unit: int) -> None:
        super().__init__(name, Unit)

class ROE_Indicator(Indicator):
    """#取得股東權益報酬率"""

    def __init__(self, name: str, CPL_RP: Season_Report, BS_RP: Season_Report) -> None:
        super().__init__(name, CPL_RP._Unit)
        self.CPL = CPL_RP
        self.BS = BS_RP

    def get_ALL_Report(self, date, base_today=None) -> DataFrame:
        table_result = DataFrame()
        table_CPL = self.CPL.get_ReportByType(date, info.CPL_type.type_0, base_today=base_today)
        table_BS = self.BS.get_ReportByType(date, info.BS_type.type_3, base_today=base_today)
        
        table_CPL, table_BS = self.check_and_convert_to_series(table_CPL, table_BS)
        if table_BS.empty or table_CPL.empty:
            return DataFrame()
        table_result[self._name] = round((table_CPL / table_BS), 4) * 100
        return table_result


class FreeCF_Indicator(Indicator):
    """#取得自由現金流"""

    def __init__(self, name: str, SCF_RP: Season_Report) -> None:
        super().__init__(name, SCF_RP._Unit)
        self.SCF = SCF_RP

    def get_ALL_Report(self, date, base_today=None) -> DataFrame:
        table_result = DataFrame()
        table_ICF = self.SCF.get_ReportByType(date, info.SCF_type.ICF, base_today=base_today)
        table_OCF = self.SCF.get_ReportByType(date, info.SCF_type.OCF, base_today=base_today)
        
        table_ICF, table_OCF = self.check_and_convert_to_series(table_ICF, table_OCF)
        if table_ICF.empty or table_OCF.empty:
            return DataFrame()
        # 計算自由現金流：投資資活動現金流量 + 營業活動現金流量
        table_result[self._name] = table_ICF + table_OCF
        return table_result


class Debt_Indicator(Indicator):
    """#取得資產負債比率"""

    def __init__(self, name: str, BS_RP: Season_Report) -> None:
        super().__init__(name, BS_RP._Unit)
        self.BS = BS_RP

    def get_ALL_Report(self, date, base_today=None) -> DataFrame:
        table_result = DataFrame()
        table_Assets = self.BS.get_ReportByType(date, info.BS_type.type_0, base_today=base_today)
        table_Debt = self.BS.get_ReportByType(date, info.BS_type.type_1, base_today=base_today)
        table_Assets, table_Debt = self.check_and_convert_to_series(table_Assets, table_Debt)
        if table_Debt.empty or table_Assets.empty:
            return DataFrame()
        table_result[self._name] = table_Debt / table_Assets
        return table_result


class MR_Growth_Indicator(Indicator):
    """#取得月營收成長率"""

    def __init__(self, name: str, monthRP: Month_Report) -> None:
        super().__init__(name, monthRP._Unit)
        self.monthRP = monthRP

    def get_ALL_Report(self, date, base_today=None):
        data_result = DataFrame()
        MR_now = self.monthRP.get_ReportByType(date, info.Month_type.MR, base_today=base_today)
        MR_old = self.monthRP.get_ReportByType(
            Tools.changeDateMonth(date, -12), info.Month_type.MR, base_today=base_today
        )
        MR_now, MR_old = self.check_and_convert_to_series(MR_now, MR_old)
        if MR_now.empty or MR_old.empty:
            return DataFrame()
        data_result[self._name] = ((MR_now - MR_old) / MR_old) * 100
        return data_result


class SR_Growth_Indicator(Indicator):
    """#取得季營收成長率"""

    def __init__(self, name: str, PLA_RP: Season_Report) -> None:
        super().__init__(name, PLA_RP._Unit)
        self.PLA_RP = PLA_RP

    def get_ALL_Report(self, date, base_today=None):
        data_result = DataFrame()
        SR_now = self.PLA_RP.get_ReportByType(date, info.PLA_type.type_0, base_today=base_today)
        SR_old = self.PLA_RP.get_ReportByType(
            Tools.changeDateMonth(date, -12), info.PLA_type.type_0, base_today=base_today
        )
        SR_now, SR_old = self.check_and_convert_to_series(SR_now, SR_old)
        if SR_now.empty or SR_old.empty:
            return DataFrame()
        data_result[self._name] = ((SR_now - SR_old) / SR_old) * 100
        return data_result


class OM_Growth_Indicator(Indicator):
    """#取得營業利益成長率"""

    def __init__(self, name: str, PLA_RP: Season_Report) -> None:
        super().__init__(name, PLA_RP._Unit)
        self.PLA = PLA_RP

    def get_ALL_Report(self, date, base_today=None) -> DataFrame:
        data_result = DataFrame()
        OM_now = self.PLA.get_ReportByType(date, info.PLA_type.type_2, base_today=base_today)
        OM_old = self.PLA.get_ReportByType(
            Tools.changeDateMonth(date, -12), info.PLA_type.type_2, base_today=base_today
        )
        OM_now, OM_old = self.check_and_convert_to_series(OM_now, OM_old)
        if OM_now.empty or OM_old.empty:
            return DataFrame()
        data_result[self._name] = ((OM_now - OM_old) / OM_old) * 100
        return data_result


class PEG_Indicator(Indicator):
    """#取得本益成長比"""

    def __init__(
        self, name: str, OM_Growth: OM_Growth_Indicator, Yield_RP: Day_Report
    ) -> None:
        super().__init__(name, OM_Growth._Unit)
        self.Yield = Yield_RP
        self.OM_Growth = OM_Growth

    def get_ALL_Report(self, date, base_today=None) -> DataFrame:
        table_result = DataFrame()
        table_PE = self.Yield.get_ReportByType(date, info.Day_type.PER, base_today=base_today)
        table_OM_Growth = self.OM_Growth.get_ALL_Report(date, base_today=base_today)
        
        table_PE, table_OM_Growth = self.check_and_convert_to_series(table_PE, table_OM_Growth)
        if table_OM_Growth.empty or table_PE.empty:
            return DataFrame()
        table_result[self._name] = table_PE / table_OM_Growth
        return table_result


class OCFPerShare_Indicator(Indicator):
    """#每股營業現金流"""

    def __init__(self, name: str, SCF_RP: Season_Report, BS_RP: Season_Report) -> None:
        super().__init__(name, SCF_RP._Unit)
        self.SCF_RP = SCF_RP
        self.BS_RP = BS_RP

    def get_ALL_Report(self, date, base_today=None):
        table_result = DataFrame()
        table_OCF = self.SCF_RP.get_ReportByType(date, info.SCF_type.OCF, base_today=base_today)
        table_BS = self.BS_RP.get_ReportByType(date, info.BS_type.type_2, base_today=base_today)
        table_OCF, table_BS = self.check_and_convert_to_series(table_OCF, table_BS)
        if table_OCF.empty or table_BS.empty:
            return DataFrame()
        table_result[self._name] = table_OCF / table_BS
        return table_result


class PCF_Indicator(Indicator):
    """#股價現金流量比率"""

    def __init__(
        self,
        name: str,
        OCFPerShare: OCFPerShare_Indicator,
        StockPrice: OriginalStock,
        GetExternal: IGetExternalData,
    ) -> None:
        super().__init__(name, 1)
        self.OCFPerShare = OCFPerShare
        self._number = None
        self._StockPrice = StockPrice
        self._main_GetExternalData = GetExternal

    def get_ALL_Report(self, date, base_today=None):
        """增強的 PCF 計算方法，包含詳細的錯誤處理和數據驗證"""
        if self._number is None:
            raise TypeError("please set number! type now:" + str(self._number))
        
        print(f"PCF_Indicator.get_ALL_Report: 開始計算 {self._number} 的 PCF，日期: {date}")
        table_result = DataFrame()
        
        try:
            # 獲取每股營業現金流數據
            print(f"PCF_Indicator: 獲取 {self._number} 的每股營業現金流數據")
            table_OCFPerShare = self.OCFPerShare.get_ReportByNumber(date, self._number, base_today=base_today)
            
            if table_OCFPerShare.empty:
                print(f"PCF計算失敗: {self._number} 的每股營業現金流數據為空")
                return DataFrame()
            
            print(f"PCF_Indicator: 每股營業現金流數據類型: {type(table_OCFPerShare)}")
            print(f"PCF_Indicator: 每股營業現金流數據內容: {table_OCFPerShare}")
            
            # 獲取股票價格
            print(f"PCF_Indicator: 獲取 {self._number} 的股票價格")
            self._StockPrice.number = self._number
            stock_price = self._StockPrice.get_PriceByDateAndType(
                date, info.Price_type.Close
            )
            
            print(f"PCF_Indicator: 股票價格原始值: {stock_price}，類型: {type(stock_price)}")
            
            # 檢查股票價格是否有效 - 增強檢查
            if stock_price == 0.0 or stock_price is None or pd.isna(stock_price):
                print(f"PCF計算失敗: {self._number} 的股票價格為空、為0或為NaN")
                return DataFrame()
            
            # 確保數據類型正確
            if isinstance(stock_price, (int, float)):
                print(f"PCF_Indicator: 將股票價格轉換為 Series")
                stock_price = Series([stock_price], index=[self._number])
            
            print(f"PCF_Indicator: 股票價格轉換後類型: {type(stock_price)}")
            print(f"PCF_Indicator: 股票價格轉換後內容: {stock_price}")
            
            # 檢查數據類型
            if not isinstance(table_OCFPerShare, (DataFrame, Series)):
                print(f"PCF計算失敗: table_OCFPerShare 數據類型錯誤: {type(table_OCFPerShare)}")
                return DataFrame()
            
            if not isinstance(stock_price, (DataFrame, Series)):
                print(f"PCF計算失敗: stock_price 數據類型錯誤: {type(stock_price)}")
                return DataFrame()
            
            # 對齊數據 - 使用增強的對齊方法
            print(f"PCF_Indicator: 開始數據對齊")
            table_OCFPerShare, stock_price = self.check_and_convert_to_series(
                table_OCFPerShare, stock_price
            )
            
            print(f"PCF_Indicator: 數據對齊完成")
            print(f"PCF_Indicator: 對齊後 table_OCFPerShare: {table_OCFPerShare}")
            print(f"PCF_Indicator: 對齊後 stock_price: {stock_price}")
            
            # 再次檢查對齊後的數據
            if table_OCFPerShare.empty or stock_price.empty:
                print(f"PCF計算失敗: 數據對齊後為空")
                return DataFrame()
            
            # 檢查每股營業現金流是否為0或NaN
            if isinstance(table_OCFPerShare, Series):
                if table_OCFPerShare.iloc[0] == 0 or pd.isna(table_OCFPerShare.iloc[0]):
                    print(f"PCF計算失敗: {self._number} 的每股營業現金流為0或NaN")
                    return DataFrame()
            elif isinstance(table_OCFPerShare, DataFrame):
                if table_OCFPerShare.iloc[0, 0] == 0 or pd.isna(table_OCFPerShare.iloc[0, 0]):
                    print(f"PCF計算失敗: {self._number} 的每股營業現金流為0或NaN")
                    return DataFrame()
            
            # 檢查股票價格是否為0或NaN
            if isinstance(stock_price, Series):
                if stock_price.iloc[0] == 0 or pd.isna(stock_price.iloc[0]):
                    print(f"PCF計算失敗: {self._number} 的股票價格為0或NaN")
                    return DataFrame()
            elif isinstance(stock_price, DataFrame):
                if stock_price.iloc[0, 0] == 0 or pd.isna(stock_price.iloc[0, 0]):
                    print(f"PCF計算失敗: {self._number} 的股票價格為0或NaN")
                    return DataFrame()
            
            # 計算 PCF
            print(f"PCF_Indicator: 開始計算 PCF")
            table_result[self._name] = stock_price / table_OCFPerShare
            print(f"PCF計算成功: {self._number} = {table_result[self._name].iloc[0] if not table_result.empty else 'N/A'}")
            return table_result
            
        except Exception as e:
            print(f"PCF計算失敗: {self._number} 計算錯誤 - {e}")
            import traceback
            traceback.print_exc()
            return DataFrame()

    def get_ReportByNumber(self, date, number: int) -> Series:
        self._number = number
        return super().get_ReportByNumber(date, number)

    def Next_date(self, date):  # 有用到每日的價格所以用天為單位
        date = Tools.backWorkDays(date, self._Unit)
        while (
            date not in self._main_GetExternalData.get_stock_history("2330", date).index
        ):  # get_stock_price(2330,date,stock_data_kind.AdjClose) == None:
            date = Tools.backWorkDays(date, self._Unit)
        return date

    @property
    def number(self):
        return self._number

    @number.setter
    def number(self, number: int):
        self._number = number


class Original_Indicator(Indicator):
    """直接取得指標歷史資料"""

    def __init__(self, name: str, Report: TReport, type: info.StrEnum) -> None:
        super().__init__(name, Report._Unit)
        self._Report = Report
        self._type = type

    def get_ALL_Report(self, date, base_today=None) -> DataFrame:
        table_result = DataFrame()
        table_temp = self._Report.get_ReportByType(date, self._type, base_today=base_today)
        if table_temp.empty:
            return DataFrame()
        table_result[self._name] = table_temp
        return table_result

    def Next_date(
        self,
        date,
    ):
        return self._Report.Next_date(date)

    @property
    def Report(self):
        return self._Report


class ADL_Indicator(Indicator):
    """騰落指標"""

    def __init__(self, name: str, AD_RP: ADL_Report) -> None:
        super().__init__(name, AD_RP._Unit)
        self._AD_RP = AD_RP
        self._adl_data = None  # Cache for the calculated ADL data

    def _calculate_adl(self):
        """Fetches all up/down data and calculates the cumulative ADL."""
        print("Calculating full ADL data...")
        persisted_adl_data = self._AD_RP._main_GetExternalData.get_full_adl()
        if not persisted_adl_data.empty:
            self._adl_data = persisted_adl_data.sort_index()
            print("Loaded persisted ADL data from MySQL.")
            return

        # Get the full table of up/down data
        daily_ad_data = self._AD_RP.get_ALL_Report(None)
        if daily_ad_data.empty:
            self._adl_data = pandas.DataFrame(columns=[self._name])
            return

        # Ensure data is sorted by date
        daily_ad_data = daily_ad_data.sort_index()

        # Calculate the daily difference
        daily_diff = daily_ad_data["up_count"] - daily_ad_data["down_count"]
        
        # Calculate the cumulative sum
        adl_series = daily_diff.cumsum()
        
        self._adl_data = pandas.DataFrame(adl_series)
        self._adl_data.columns = [self._name]
        print("Full ADL data calculated and cached.")

    def get_ALL_Report(self, date, base_today=None):
        # Calculate and cache the full ADL data if not already done
        if self._adl_data is None:
            self._calculate_adl()

        # Return the specific date's data from the cached DataFrame
        if self._adl_data.empty or date not in self._adl_data.index:
            return pandas.DataFrame()
        
        # Return as a DataFrame with the same structure as the original code
        return self._adl_data.loc[[date]]

    def Next_date(self, date):
        return self._AD_RP.Next_date(date)


class ADLs_Indicator(Indicator):
    """騰落比例指標"""

    def __init__(self, name: str, AD_RP: ADL_Report) -> None:
        super().__init__(name, AD_RP._Unit)
        self._AD_RP = AD_RP
        self._adls_data = None  # Cache for the calculated ADLS data

    def _calculate_adls(self):
        """Fetches all up/down data and calculates the ADL Ratio for all dates."""
        print("Calculating full ADLS data...")
        daily_ad_data = self._AD_RP.get_ALL_Report(None)
        if daily_ad_data.empty:
            self._adls_data = pandas.DataFrame(columns=[self._name])
            return

        # Ensure data is sorted by date
        daily_ad_data = daily_ad_data.sort_index()

        # Calculate the ratio
        up = daily_ad_data["up_count"]
        down = daily_ad_data["down_count"]
        total = up + down
        # Avoid division by zero
        ratio = (up / total.where(total != 0, 1)) - 0.5
        
        self._adls_data = pandas.DataFrame(ratio)
        self._adls_data.columns = [self._name]
        print("Full ADLS data calculated and cached.")

    def get_ALL_Report(self, date, base_today=None):
        # Calculate and cache the full ADLS data if not already done
        if self._adls_data is None:
            self._calculate_adls()

        # Return the specific date's data from the cached DataFrame
        if self._adls_data.empty or date not in self._adls_data.index:
            return pandas.DataFrame()
        
        # Return as a DataFrame with the same structure as the original code
        return self._adls_data.loc[[date]]

    def Next_date(self, date):
        return self._AD_RP.Next_date(date)
