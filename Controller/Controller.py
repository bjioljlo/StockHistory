from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Callable

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel

from Model.Model import IModel
from StockInfos import UserInfoDatas
from View.View import IWindow

MAIN_TITALLIST = ["股票號碼", "股票名稱"]
PICK__TITALLIST = [
    "股票號碼",
    "股票名稱",
    "每股參考淨值",
    "基本每股盈餘（元）",
    "毛利率(%)",
    "營業利益率(%)",
    "資產總額",
    "負債總額",
    "股本",
    "權益總額",
    "本期綜合損益總額（稅後）",
    "PBR",
    "PER",
    "PEG",
    "ROE",
    "殖利率",
]


class controllers(Enum):
    Main = 1
    Pick = 2
    BackTest = 3


class IController(ABC):
    def __init__(self):
        super().__init__()
        self.GetController: GetControllerEvent = None

    @abstractmethod
    def GetView(self) -> IWindow:
        raise NotImplementedError

    @abstractmethod
    def ShowWindow(self):
        raise NotImplementedError

    @abstractmethod
    def GetEndDate(self) -> datetime:
        raise NotImplementedError

    @abstractmethod
    def GetStockNumber(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def SetStockNumber(self, stockNumber: str):
        raise NotImplementedError


GetControllerEvent = Callable[[controllers], IController]


class TController(IController):
    def __init__(self, _view: IWindow = None, _model: IModel = None) -> None:
        super(TController, self).__init__()
        self.View = _view
        self.Model = _model

    @property
    def View(self):
        if self._View is None:
            raise
        return self._View

    @View.setter
    def View(self, _view: IWindow):
        self._View = _view

    @property
    def Model(self):
        if self._Model is None:
            raise
        return self._Model

    @Model.setter
    def Model(self, _model: IModel):
        self._Model = _model

    def GetView(self) -> IWindow:
        return self.View

    def ShowWindow(self):
        self.GetView().GetFormUI().show()


# 讓Controller都可以用
def creat_treeView_model(parent, titalList, UserInfoData: UserInfoDatas = None):
    model = QStandardItemModel(0, titalList.__len__(), parent)
    for i in range(0, titalList.__len__()):
        model.setHeaderData(i, Qt.Horizontal, titalList[i])
    if UserInfoData is not None:
        set_treeView(model, UserInfoData.StockList)
    return model


def set_treeView2(model, inputdataFram):
    i = 0
    array_Num = []
    for index, row in inputdataFram.iterrows():
        array_Num = [
            row["每股參考淨值"],
            row["基本每股盈餘（元）"],
            row["毛利率(%)"],
            row["營業利益率(%)"],
            row["資產總額"],
            row["負債總額"],
            row["股本"],
            row["權益總額"],
            row["本期綜合損益總額（稅後）"],
        ]  # ,row["PBR"],row["PER"],row["ROE"]]
        try:
            array_Num.append(row["PBR"])
        except Exception:
            array_Num.append(float(0))
        try:
            array_Num.append(row["PER"])
        except Exception:
            array_Num.append(float(0))
        try:
            array_Num.append(float(row["PEG"]))
        except Exception:
            array_Num.append(float(0))
        try:
            array_Num.append(float(row["ROE"]))
        except Exception:
            array_Num.append(float(0))
        try:
            array_Num.append(float(row["Yield"]))
        except Exception:
            array_Num.append(float(0))
        add_stock_List(model, index, row["公司名稱"], i, array_Num)
        i = i + 1


def set_treeView(model, inputList):
    i = 0
    for key, value in inputList.items():  # 放入stockList
        add_stock_List(model, value.number, value.name, i)
        i = i + 1


def add_stock_List(model, stockNum, stockName, rowNum, array=None):
    model.insertRow(rowNum)
    model.setData(model.index(rowNum, 0), stockNum)
    model.setData(model.index(rowNum, 1), stockName)
    if array is not None:
        for i in range(len(array)):
            model.setData(model.index(rowNum, i + 2), array[i])
