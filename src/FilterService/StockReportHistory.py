import sys
from abc import ABC, abstractmethod

import pandas
from pandas import DataFrame, Series

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
            return Temp[_type.value]
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
        # 確保兩個表都是 Series，如果不是則轉換
        if isinstance(tableFirst, DataFrame):
            if tableFirst.empty:
                return DataFrame(), DataFrame()
            # 如果是 DataFrame，取第一個欄位
            tableFirst = tableFirst.iloc[:, 0] if tableFirst.shape[1] > 0 else Series()
        
        if isinstance(tableSecond, DataFrame):
            if tableSecond.empty:
                return DataFrame(), DataFrame()
            # 如果是 DataFrame，取第一個欄位
            tableSecond = tableSecond.iloc[:, 0] if tableSecond.shape[1] > 0 else Series()
        
        # 檢查是否為空 - 修復：正確處理 Series 和 DataFrame 的 empty 檢查
        if (isinstance(tableFirst, Series) and tableFirst.empty) or \
           (isinstance(tableSecond, Series) and tableSecond.empty):
            return DataFrame(), DataFrame()
        
        # 新增檢查：確保兩個 Series 都有有效的索引才能進行 align
        if isinstance(tableFirst, Series) and isinstance(tableSecond, Series):
            if tableFirst.empty or tableSecond.empty or \
               tableFirst.index.empty or tableSecond.index.empty:
                return DataFrame(), DataFrame()
        
        # 確保兩個表使用相同的索引進行對齊
        # 使用內連接（inner join）來確保只保留兩個表都有的索引
        tableFirst_aligned, tableSecond_aligned = tableFirst.align(tableSecond, join='inner', fill_value=0)
        return tableFirst_aligned, tableSecond_aligned


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
        if self._number is None:
            raise TypeError("please set number! type now:" + str(self._number))
        table_result = DataFrame()
        table_OCFPerShare = self.OCFPerShare.get_ReportByNumber(date, self._number, base_today=base_today)
        if table_OCFPerShare.empty:
            return DataFrame()
        self._StockPrice.number = self._number
        stock_price = self._StockPrice.get_PriceByDateAndType(
            date, info.Price_type.Close
        )  # get_stock_price(self._number,date,stock_data_kind.AdjClose)
        
        # 修復：將 stock_price 轉換為 Series，如果它是數值類型
        if isinstance(stock_price, (int, float)):
            stock_price = Series([stock_price], index=[self._number])
        
        table_OCFPerShare, stock_price = self.check_and_convert_to_series(
            table_OCFPerShare, stock_price
        )
        table_result[self._name] = stock_price / table_OCFPerShare
        return table_result

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
        # Get the full table of up/down data
        daily_ad_data = self._AD_RP.get_ALL_Report(None)
        if daily_ad_data.empty:
            self._adl_data = pandas.DataFrame(columns=[self._name])
            return

        # Ensure data is sorted by date
        daily_ad_data = daily_ad_data.sort_index()

        # Calculate the daily difference
        daily_diff = daily_ad_data["上漲"] - daily_ad_data["下跌"]
        
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
        up = daily_ad_data["上漲"]
        down = daily_ad_data["下跌"]
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
