from PyQt5 import QtWidgets
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtCore import Qt
from PyQt5 import QtCore
from UI_main import Ui_MainWindow
import sys
import datetime
import get_stock_info
import get_stock_history
import matplotlib.pyplot as plt
import draw_figur as df

class MyWindow(QtWidgets.QMainWindow,Ui_MainWindow):
    def __init__(self):
        super(MyWindow,self).__init__()
        self.setupUi(self)

def button_getStockHistory():
    date = myshow.date_startDate.date()
    str_date = str(date.year())+'-'+ str(date.month())+'-'+str(date.day())
    if myshow.input_stockNumber.toPlainText() == "":
        for key,value in get_stock_info.stock_list.items():
            m_history = get_stock_history.get_stock_history(key,str_date)
            check_price_isCheck(m_history,value)
            check_SMA_isCheck(m_history,value)
            check_KD_isCheck(m_history,value)
            check_Volume_isCheck(m_history,value)
    else:
        stock_number = myshow.input_stockNumber.toPlainText()
        m_history = get_stock_history.get_stock_history(stock_number,str_date)
        #
        ooofofofof= get_stock_history.get_stock_financial_statement(stock_number,date)
        #
        check_price_isCheck(m_history,get_stock_info.Get_stock_info(stock_number))
        check_SMA_isCheck(m_history,get_stock_info.Get_stock_info(stock_number))
        check_KD_isCheck(m_history,get_stock_info.Get_stock_info(stock_number))
        check_Volume_isCheck(m_history,get_stock_info.Get_stock_info(stock_number))
    df.draw_Show()
def check_price_isCheck(m_history,stockInfo):
    if myshow.check_stock.isChecked():
        df.draw_stock(m_history,stockInfo)
def check_Volume_isCheck(m_history,stockInfo):
    if myshow.check_volume.isChecked():
        df.draw_Volume(m_history,stockInfo)
def check_KD_isCheck(m_history,stockInfo):
    if myshow.check_KD.isChecked():
        df.draw_KD(m_history,stockInfo)
def check_SMA_isCheck(m_history,stockInfo):
    if myshow.check_SMA.isChecked() == True:
        for i in input_SMA_list:
            if i.toPlainText() != "":
                df.draw_SMA(m_history,int(i.toPlainText()),stockInfo)

def button_moveToInput_click():
    Index = myshow.treeView.currentIndex()
    mIndex = Index.siblingAtColumn(0)
    data = myshow.treeView.model().data(mIndex)
    text = str(data)
    myshow.input_stockNumber.setPlainText(text)
def button_addStock_click():
    stocknum = myshow.input_stockNumber.toPlainText()
    get_stock_info.Add_stock_info(stocknum)
    myshow.treeView.setModel(creat_treeView_model(myshow.treeView))#設定treeView功能
def button_deletStock_click():
    stocknum = myshow.input_stockNumber.toPlainText()
    get_stock_info.Delet_stock_info(stocknum)
    myshow.treeView.setModel(creat_treeView_model(myshow.treeView))#設定treeView功能
def set_treeView(model):
    i = 0
    for key,value in get_stock_info.stock_list.items():#放入stockList
        add_stock_List(model,value.number,value.name,i)
        i = i+1
def creat_treeView_model(parent):
    model = QStandardItemModel(0,2,parent)
    model.setHeaderData(0,Qt.Horizontal,"股票號碼")
    model.setHeaderData(1,Qt.Horizontal,"股票名稱")
    set_treeView(model)
    return model
def add_stock_List(model,stockNum,stockName,rowNum):
    model.insertRow(rowNum)
    model.setData(model.index(rowNum,0),stockNum)
    model.setData(model.index(rowNum,1),stockName)
    


app = QtWidgets.QApplication(sys.argv)
myshow = MyWindow()
#從這中間加ＵＩ設定---------------
myshow.button_addStock.clicked.connect(button_addStock_click)#設定button功能
myshow.button_deletStock.clicked.connect(button_deletStock_click)#設定button功能
myshow.treeView.setModel(creat_treeView_model(myshow.treeView))#設定treeView功能
myshow.button_moveToInput.clicked.connect(button_moveToInput_click)#設定button功能
myshow.button_getStockHistory.clicked.connect(button_getStockHistory)#設定button功能
#設定日期
date = QtCore.QDate(datetime.datetime.today().year,datetime.datetime.today().month,datetime.datetime.today().day) 
myshow.date_startDate.setMaximumDate(date)
myshow.date_startDate.setDate(QtCore.QDate(2010,1,1))

input_SMA_list = [myshow.input_SMA1,
                    myshow.input_SMA2,
                    myshow.input_SMA3]
#從這中間加ＵＩ設定---------------
myshow.show()
sys.exit(app.exec_())

