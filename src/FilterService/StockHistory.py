import sys
from abc import ABC, abstractmethod
from datetime import datetime

import talib
import twstock
from pandas import DataFrame, Series, concat

from src.Common import InfomationType as info
from src.ExternalService.ExternalDataFactory import ExternalDataFactory, ExternalDataTypeEnum


class IStock(ABC):
    """股票歷史資料"""

    @abstractmethod
    def get_ALL(self) -> DataFrame:
        pass


class TStock(IStock):
    """股票歷史資料實作"""

    @property
    def number(self) -> str:
        if self._number is None:
            raise
        return self._number

    @number.setter
    def number(self, number: str):
        self._number = number

    def __init__(self, number: int = None) -> None:
        self._number = number

    @abstractmethod
    def get_ALL(self) -> DataFrame:
        raise NotImplementedError(
            "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name)
        )

    def get_PriceByDate(self, date: datetime):
        Temp = self.get_ALL()
        try:
            Temp_Result = Temp[Temp.index == date]
            if Temp_Result.empty:
                raise
            return Temp_Result
        except Exception:
            if Temp.empty:
                print("".join([str(date), "的", str(self._number), "price表沒出"]))
            else:
                print("".join([str(date), "的", str(self._number), "公司尚未成立"]))
            return DataFrame()


class OriginalStock(TStock):
    """股票一般未處理歷史資料"""

    @abstractmethod
    def get_ALL(self) -> DataFrame:
        raise NotImplementedError(
            "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name)
        )

    def get_PriceByType(self, _type: info.Price_type):
        Temp = self.get_ALL()
        try:
            return Temp[_type.value]
        except Exception:
            print("".join([str(self._number), "的", str(self._number), "price表沒出"]))
            return DataFrame()

    def get_PriceByDateAndType(self, date: datetime, _type: info.Price_type):
        Temp = self.get_PriceByType(_type)
        try:
            return float(Temp[date])
        except Exception:
            if not Temp.empty:
                print("".join([str(date), "的", str(self._number), "公司尚未成立"]))
            return None


class OriginalStockByYahoo(OriginalStock):
    """股票一般未處理歷史資料(Yahoo資料)"""
    
    def __init__(self, externalDataFactory: ExternalDataFactory, number: int = None) -> None:
        super().__init__(number)
        self._external_data_fctory = externalDataFactory
    
    def get_ALL(self) -> DataFrame:
        main_GetExternalData = self._external_data_fctory.Get_instance(self)
        return main_GetExternalData.get_stock_history(str(self._number))


class OriginalStockTest(OriginalStock):
    """unitTest 用的股票歷史資料其他請勿使用"""
    
    def __init__(self, externalDataFactory: ExternalDataFactory, number: int = None) -> None:
        super().__init__(number)
        self._external_data_fctory = externalDataFactory

    def get_ALL(self) -> DataFrame:
        main_GetExternalData = self._external_data_fctory.Get_instance(
            ExternalDataTypeEnum.Test
        )
        return main_GetExternalData.get_stock_history(str(self._number))


class VirtualStockFuc(TStock):
    """對輸入的資訊做處理"""

    @property
    def number(self) -> str:
        if self.Stock.number is None:
            raise
        return self.Stock.number

    @number.setter
    def number(self, number: str):
        self.Stock.number = number

    def __init__(self, Stock: TStock) -> None:
        super().__init__(Stock._number)
        self.Stock = Stock

    @abstractmethod
    def get_ALL(self):
        raise NotImplementedError(
            "{} is virutal! Must be overwrited.".format(sys._getframe().f_code.co_name)
        )


class RangeDate_Stock(VirtualStockFuc):
    """取得兩個日期之間的資料"""

    @property
    def StartDate(self):
        if self._date is None:
            self._date = datetime.strptime("2005-1-1", "%Y-%m-%d")
        return self._date

    @property
    def EndDate(self):
        if self._date2 is None:
            self._date2 = datetime.today()
        return self._date2

    @StartDate.setter
    def StartDate(self, date: datetime):
        self._date = date

    @EndDate.setter
    def EndDate(self, date: datetime):
        self._date2 = date

    def __init__(
        self, Stock: TStock, startDate: datetime = None, endDate: datetime = None
    ) -> None:
        super().__init__(Stock)
        self.StartDate = startDate
        self.EndDate = endDate

    def get_ALL(self):
        Temp = self.Stock.get_ALL()
        mask1 = Temp.index >= self.StartDate
        mask2 = Temp.index <= self.EndDate
        Temp = Temp[(mask1 & mask2)]
        return Temp


class SMA_Stock(VirtualStockFuc):
    """將輸入轉均線的資料"""

    @property
    def AvgDay(self):
        if self._avgDay is None:
            raise
        return self._avgDay

    @property
    def PriceType(self):
        if self._type is None:
            raise
        return self._type

    @AvgDay.setter
    def AvgDay(self, day: int):
        self._avgDay = day

    @PriceType.setter
    def PriceType(self, _type: info.Price_type):
        self._type = _type

    def __init__(
        self, Stock: TStock, avgDay: int = None, type: info.Price_type = None
    ) -> None:
        super().__init__(Stock)
        self.AvgDay = avgDay
        self.PriceType = type

    def get_ALL(self):
        Temp = self.Stock.get_ALL()
        try:
            mclose = talib.SMA(
                Temp[self.PriceType], self.AvgDay
            )  # 不用np.array也可以將均線和蠟燭圖放一起
            return mclose
        except Exception:
            return DataFrame()


class RecordHigh_Stock(VirtualStockFuc):
    """是否創新高"""

    def set_valuse(self, _endDate, _flashDay, _recordDays, _atype):
        self._endDate = _endDate
        self._flashDay = _flashDay
        self._recordDays = _recordDays
        self._atype = _atype

    def __init__(
        self,
        Stock: TStock,
        endDate: datetime = None,
        flashDay: int = None,
        recordDays: int = None,
        atype: info.Price_type = None,
    ) -> None:
        super().__init__(Stock)
        self.set_valuse(endDate, flashDay, recordDays, atype)

    def get_ALL(self):
        if (
            not self._endDate
            or not self._flashDay
            or not self._recordDays
            or not self._atype
        ):
            raise
        aRange = RangeDate_Stock(self.Stock, None, self._endDate)
        try:
            All_data = aRange.get_ALL().sort_index(ascending=False)
            for k in range(self._flashDay):
                Now_price = All_data.iloc[k][self._atype]
                Pass = True
                for i in range(self._recordDays):
                    try:
                        Temp_price = All_data.iloc[k + i + 1][self._atype]
                    except IndexError:
                        return False
                    if Temp_price <= Now_price:
                        continue
                    else:
                        Pass = False
                        break
                if Pass:
                    return True
            return False
        except Exception:
            return False


class VirtualStockFilterFuc(TStock):
    """對輸入股票的歷史資料做篩選"""

    def __init__(self, Stock: TStock, Date: datetime) -> None:
        super().__init__(Stock._number)
        self._Stock = Stock
        self._date = Date


class StockPriceBetterMA(VirtualStockFilterFuc):
    """對輸入股票的歷史資料 篩選出價格高於均線"""

    def __init__(self, Stock: SMA_Stock, Data: DataFrame, Date: datetime) -> None:
        self._Stock = Stock
        self._date = Date
        self._data = Data

    def get_ALL(self):
        return self.get_FilterBetterMA(self._data)

    def get_FilterBetterMA(self, data: DataFrame):
        print(
            "{} / {} is Start!".format(
                "StockPriceBetterMA", sys._getframe().f_code.co_name
            )
        )
        result_data = data.copy()  # 使用 copy() 避免修改原始 DataFrame
        result = DataFrame(columns=["code", "price_better_ma"])
        
        for number, row in data.iterrows():
            # 確保 number 是字串類型，這樣可以避免索引類型不匹配的問題
            stock_number = str(number)
            self._Stock.number = stock_number
            
            Temp_MA = self._Stock.get_PriceByDate(self._date)
            Temp = self._Stock.Stock.get_PriceByDate(self._date)
            
            if Temp.empty or Temp_MA.empty:
                try:
                    # 使用字串類型的索引進行刪除
                    result_data.drop(index=stock_number, inplace=True)
                except KeyError:
                    # 如果索引不存在，嘗試使用原始的 number 類型
                    try:
                        result_data.drop(index=number, inplace=True)
                    except KeyError:
                        pass  # 如果索引不存在，跳過
                continue
            
            # 處理 Temp 和 Temp_MA 數據
            if type(Temp) is DataFrame:
                Temp = Temp[self._Stock._type][self._date]
            elif type(Temp) is Series:
                Temp = Temp[self._date]
            elif type(Temp) is list:
                Temp = Temp[self._date]
            
            if type(Temp_MA) is DataFrame:
                Temp_MA = Temp_MA[self._Stock._type][self._date]
            elif type(Temp_MA) is Series:
                Temp_MA = Temp_MA[self._date]
            elif type(Temp_MA) is list:
                Temp_MA = Temp_MA[self._date]
            
            try:
                # 檢查價格是否高於移動平均線
                if Temp_MA > Temp:
                    try:
                        # 使用字串類型的索引進行刪除
                        result_data.drop(index=stock_number, inplace=True)
                    except KeyError:
                        # 如果索引不存在，嘗試使用原始的 number 類型
                        try:
                            result_data.drop(index=number, inplace=True)
                        except KeyError:
                            pass  # 如果索引不存在，跳過
                else:
                    result = concat(
                        [result, DataFrame({"code": stock_number, "price_better_ma": Temp}, index=[1])],
                        ignore_index=True,
                    )
            except Exception as e:
                print(f"處理股票 {stock_number} 時發生錯誤: {e}")
                continue
        
        print(
            "{} / {} is End!".format(
                "StockPriceBetterMA", sys._getframe().f_code.co_name
            )
        )
        
        # 確保返回的結果是過濾後的數據，而不是原始數據
        if not result.empty:
            result.set_index("code", inplace=True)
            return result
        else:
            # 如果沒有符合條件的數據，返回空DataFrame
            print("所有數據都被過濾掉，返回空結果")
            return DataFrame()


class StockRecordHigh(VirtualStockFilterFuc):
    """對輸入股票的歷史資料 篩選出幾日內創新高"""

    def __init__(
        self,
        Stock: RecordHigh_Stock,
        endDate: datetime,
        flashDay: int,
        recordDays: int,
        data: DataFrame,
        atype: info.Price_type,
    ) -> None:
        self._Stock = Stock
        self._Stock._endDate = endDate
        self._Stock._flashDay = flashDay
        self._Stock._recordDays = recordDays
        self._Stock._atype = atype
        self.__data = data

    def get_ALL(self):
        return self.get_FilterRecordHigh(self.__data)

    def get_FilterRecordHigh(self, data: DataFrame):
        result_data = data.copy()  # 使用 copy() 避免修改原始 DataFrame
        result = DataFrame(columns=["code", "RecordHigh"])
        
        for number, row in data.iterrows():
            # 確保 number 是字串類型
            stock_number = str(number)
            self._Stock.number = stock_number
            
            Temp = self._Stock.get_ALL()
            if not Temp:
                try:
                    # 使用字串類型的索引進行刪除
                    result_data.drop(index=stock_number, inplace=True)
                except KeyError:
                    # 如果索引不存在，嘗試使用原始的 number 類型
                    try:
                        result_data.drop(index=number, inplace=True)
                    except KeyError:
                        pass  # 如果索引不存在，跳過
                print("".join([str(number), "/////", str(row)]))
            else:
                result = concat(
                    [
                        result,
                        DataFrame({"code": stock_number, "RecordHigh": Temp}, index=[1]),
                    ],
                    ignore_index=True,
                )
        
        # 確保返回的結果是過濾後的數據
        if not result.empty:
            result.set_index("code", inplace=True)
            return result
        else:
            # 如果沒有符合條件的數據，返回空DataFrame
            print("歷史高點篩選：所有數據都被過濾掉，返回空結果")
            return DataFrame()


class StockFilter(VirtualStockFilterFuc):
    """對輸入股票的歷史資料 篩選出某兩個數字內"""

    def __init__(
        self,
        Stock: TStock,
        Name: str,
        Max: int,
        Min: int,
        Data: DataFrame,
        Date: datetime,
        Type: info.Price_type,
    ) -> None:
        super().__init__(Stock, Date)
        self.__max = Max
        self.__min = Min
        self.__data = Data
        self._type = Type
        self._name = Name

    def get_ALL(self):
        return self.__get_Filter(
            self._name, self.__max, self.__min, self.__data, self._date, self._type
        )

    def __get_Filter(
        self, name, max, min, data: DataFrame, date: datetime, atype: info.Price_type
    ):
        print("{} / {} is Start!".format("StockFilter", sys._getframe().f_code.co_name))
        
        # 如果輸入數據為空，直接返回空DataFrame
        if data.empty:
            print("輸入數據為空，返回空結果")
            return DataFrame()
        
        result_data = data.copy()  # 使用 copy() 避免修改原始 DataFrame
        result = DataFrame(columns=["code", name])
        
        # 確保索引類型一致，統一轉換為字串類型進行處理
        for number, row in data.iterrows():
            # 確保 number 是字串類型，這樣可以避免索引類型不匹配的問題
            stock_number = str(number)
            self._Stock.number = stock_number
            
            Temp = self._Stock.get_PriceByDate(date)
            if Temp.empty:
                try:
                    # 使用字串類型的索引進行刪除
                    result_data.drop(index=stock_number, inplace=True)
                except KeyError:
                    # 如果索引不存在，嘗試使用原始的 number 類型
                    try:
                        result_data.drop(index=number, inplace=True)
                    except KeyError:
                        pass  # 如果索引不存在，跳過
                continue
            
            # 處理 Temp 數據
            if type(Temp) is DataFrame:
                Temp = Temp[atype][date]
            elif type(Temp) is Series:
                Temp = Temp[date]
            elif type(Temp) is list:
                Temp = Temp[date]
            
            try:
                if Temp > max or Temp < min:
                    try:
                        # 使用字串類型的索引進行刪除
                        result_data.drop(index=stock_number, inplace=True)
                    except KeyError:
                        # 如果索引不存在，嘗試使用原始的 number 類型
                        try:
                            result_data.drop(index=number, inplace=True)
                        except KeyError:
                            pass  # 如果索引不存在，跳過
                else:
                    result = concat(
                        [result, DataFrame({"code": stock_number, name: Temp}, index=[1])],
                        ignore_index=True,
                    )
            except Exception as e:
                print(f"處理股票 {stock_number} 時發生錯誤: {e}")
                continue
        
        print("{} / {} is End!".format("StockFilter", sys._getframe().f_code.co_name))
        
        # 確保返回的結果是過濾後的數據，而不是原始數據
        if not result.empty:
            result.set_index("code", inplace=True)
            return result
        else:
            # 如果沒有符合條件的數據，返回空DataFrame
            print("所有數據都被過濾掉，返回空結果")
            return DataFrame()


class StockFilterInfo(VirtualStockFilterFuc):
    """對輸入股票的歷史資料 篩選出產業別"""

    def __init__(
        self, Stock: TStock, Data: DataFrame, Date: datetime, GrouopName: str
    ) -> None:
        super().__init__(Stock, Date)
        self._groupName = GrouopName
        self.__data = Data

    def get_ALL(self):
        return self.__get_Filter(self.__data, self._date, self._groupName)

    def __get_Filter(self, data: DataFrame, date: datetime, groupName: str):
        print(
            "{} / {} is Start!".format(
                "StockFilterInfo", sys._getframe().f_code.co_name
            )
        )
        result_data = data
        for number, row in data.iterrows():
            self._Stock.number = str(number)
            Temp = self._Stock.get_ALL()
            if Temp.empty:
                result_data.drop(index=int(number), inplace=True)
                continue
            if twstock.codes[self._Stock.number].group != groupName:
                result_data.drop(index=int(number), inplace=True)
        print(
            "{} / {} is End!".format("StockFilterInfo", sys._getframe().f_code.co_name)
        )
        return result_data


class StockAvgVolMultiple(VirtualStockFilterFuc):
    """檢查是否超過平均成交量的特定倍數"""

    def __init__(self, Stock: SMA_Stock, Data: DataFrame, Date: datetime, Multiple) -> None:
        self._Stock = Stock
        self._date = Date
        self._data = Data
        self._multiple = Multiple

    def get_ALL(self):
        return self.get_FilterAvgVolMultiple(self._data)
    
    def get_FilterAvgVolMultiple(self, data: DataFrame):
        print(
            "{} / {} is Start!".format(
                "StockAvgVolMultiple", sys._getframe().f_code.co_name
            )
        )
        result_data = data.copy()  # 使用 copy() 避免修改原始 DataFrame
        result = DataFrame(columns=["code", "volume_multiple"])
        
        for number, row in data.iterrows():
            # 確保 number 是字串類型，這樣可以避免索引類型不匹配的問題
            stock_number = str(number)
            self._Stock.number = stock_number
            
            Temp_MA = self._Stock.get_PriceByDate(self._date)
            Temp = self._Stock.Stock.get_PriceByDate(self._date)
            
            if Temp.empty or Temp_MA.empty:
                try:
                    # 使用字串類型的索引進行刪除
                    result_data.drop(index=stock_number, inplace=True)
                except KeyError:
                    # 如果索引不存在，嘗試使用原始的 number 類型
                    try:
                        result_data.drop(index=number, inplace=True)
                    except KeyError:
                        pass  # 如果索引不存在，跳過
                continue
            
            # 處理 Temp 和 Temp_MA 數據
            if type(Temp) is DataFrame:
                Temp = Temp[self._Stock._type][self._date]
            elif type(Temp) is Series:
                Temp = Temp[self._date]
            elif type(Temp) is list:
                Temp = Temp[self._date]
            
            if type(Temp_MA) is DataFrame:
                Temp_MA = Temp_MA[self._Stock._type][self._date]
            elif type(Temp_MA) is Series:
                Temp_MA = Temp_MA[self._date]
            elif type(Temp_MA) is list:
                Temp_MA = Temp_MA[self._date]
            
            try:
                # 檢查成交量是否超過平均成交量的特定倍數
                if Temp_MA * self._multiple > Temp:
                    try:
                        # 使用字串類型的索引進行刪除
                        result_data.drop(index=stock_number, inplace=True)
                    except KeyError:
                        # 如果索引不存在，嘗試使用原始的 number 類型
                        try:
                            result_data.drop(index=number, inplace=True)
                        except KeyError:
                            pass  # 如果索引不存在，跳過
                else:
                    result = concat(
                        [result, DataFrame({"code": stock_number, "volume_multiple": Temp}, index=[1])],
                        ignore_index=True,
                    )
            except Exception as e:
                print(f"處理股票 {stock_number} 時發生錯誤: {e}")
                continue
        
        print(
            "{} / {} is End!".format(
                "StockAvgVolMultiple", sys._getframe().f_code.co_name
            )
        )
        
        # 確保返回的結果是過濾後的數據，而不是原始數據
        if not result.empty:
            result.set_index("code", inplace=True)
            return result
        else:
            # 如果沒有符合條件的數據，返回空DataFrame
            print("所有數據都被過濾掉，返回空結果")
            return DataFrame()
