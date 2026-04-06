from typing import List
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel

from src.StockInfos import UserInfoDatas


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


def creat_treeView_model(parent, titleList: List[str], UserInfoData: UserInfoDatas = None):
    """建立 TreeView 的標準模型"""
    model = QStandardItemModel(0, len(titleList), parent)
    for i in range(len(titleList)):
        model.setHeaderData(i, Qt.Horizontal, titleList[i])
    if UserInfoData is not None:
        set_treeView(model, UserInfoData.StockList)
    return model


def set_treeView2(model, inputdataFram):
    """將 DataFrame 資料設定到 TreeView 模型"""
    import twstock
    i = 0
    for index, row in inputdataFram.iterrows():
        array_Num = [
            row["book_value_per_share"],
            row["consolidated_eps"],
            row["gross_margin"],
            row["operating_margin"],
            row["operating_margin"],
            row["total_liabilities"],
            row["capital"],
            row["equity"],
            row["consolidated_net_income"],
        ]
        
        # 安全地取得選擇性欄位
        for field in ["PBR", "PER", "PEG", "ROE", "Yield"]:
            try:
                array_Num.append(float(row[field]))
            except (KeyError, TypeError, ValueError):
                array_Num.append(float(0))

        # 動態獲取公司名稱
        stock_name = ""
        try:
            stock_name = row["公司名稱"]
        except (KeyError, TypeError):
            try:
                stock_code = str(index)
                if stock_code in twstock.codes:
                    stock_name = twstock.codes[stock_code].name
            except Exception:
                stock_name = ""

        add_stock_List(model, index, stock_name, i, array_Num)
        i = i + 1


def set_treeView(model, inputList):
    """將股票清單資料設定到 TreeView 模型"""
    i = 0
    for key, value in inputList.items():
        add_stock_List(model, value.number, value.name, i)
        i = i + 1


def add_stock_List(model, stockNum, stockName, rowNum, array=None):
    """新增一筆股票資料到 TreeView 模型"""
    model.insertRow(rowNum)
    model.setData(model.index(rowNum, 0), stockNum)
    model.setData(model.index(rowNum, 1), stockName)
    if array is not None:
        for i in range(len(array)):
            model.setData(model.index(rowNum, i + 2), array[i])