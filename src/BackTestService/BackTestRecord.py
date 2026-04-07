from abc import ABC, abstractmethod

import pandas as pd
from pandas import DataFrame


class IBackTestRecord(ABC):
    @property
    @abstractmethod
    def Data(self) -> DataFrame:
        raise NotImplementedError

    @abstractmethod
    def RunRecord(self, inputData: list):
        """紀錄回測"""
        raise NotImplementedError

    @abstractmethod
    def RunFinish(self):
        """完成結果"""
        raise NotImplementedError


class TBackTestRecord(IBackTestRecord):
    def __init__(self, _columns: list[str], saveName: str):
        self._data: DataFrame = DataFrame(columns=_columns)
        self._saveName: str = saveName

    @property
    def Data(self) -> DataFrame:
        return self._data

    def RunFinish(self):
        self._data.set_index(self._data.columns[0], inplace=True)
        self._data.to_csv(self._saveName + ".csv")


class BackTestRecord_indexWithDate(TBackTestRecord):
    def RunRecord(self, inputData: list):
        inputDict = {}
        for i in range(len(inputData)):
            if i > len(self._data.columns) - 1:
                break
            inputDict[self._data.columns[i]] = [inputData[i]]
        self._data = pd.concat([self._data, DataFrame(inputDict)], ignore_index=True)


# 向後相容: BackTestRecord 別名 (舊程式碼相容)
# 在重構後原 BackTestRecord 已更名為 TBackTestRecord
# 此別名確保舊有 import 程式碼不會出錯
BackTestRecord = TBackTestRecord

# 匯出所有公開類別
__all__ = [
    'IBackTestRecord',
    'TBackTestRecord',
    'BackTestRecord',
    'BackTestRecord_indexWithDate',
]
