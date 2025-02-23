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
    def __init__(self, _columns: list[str]):
        self._data: DataFrame = DataFrame(columns=_columns)

    @property
    def Data(self) -> DataFrame:
        return self._data

    def RunFinish(self):
        self._data.set_index(self._data.columns[0], inplace=True)


class BackTestRecord_indexWithDate(TBackTestRecord):
    def RunRecord(self, inputData: list):
        inputDict = {}
        for i in range(len(inputData)):
            inputDict[self._data.columns[i]] = [inputData[i]]
        self._data = pd.concat([self._data, DataFrame(inputDict)], ignore_index=True)
