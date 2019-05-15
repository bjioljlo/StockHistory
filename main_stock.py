from PyQt5 import QtWidgets
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtCore import Qt
from PyQt5 import QtCore
from UI_main import Ui_MainWindow
from UI_pick import Ui_MainWindow2
import sys
import datetime
import get_stock_info
import get_stock_history
import matplotlib.pyplot as plt
import draw_figur as df

main_titalList = ["股票號碼","股票名稱"]
pick_titalList = ["股票號碼","股票名稱","毛利率(%)","營業利益率(%)"]

#主畫面
class MyWindow(QtWidgets.QMainWindow,Ui_MainWindow):
    def __init__(self):
        super(MyWindow,self).__init__()
        self.setupUi(self)
#挑股票畫面
class MyPicWindow(QtWidgets.QMainWindow,Ui_MainWindow2):
    def __init__(self):
        super(MyPicWindow,self).__init__()
        self.setupUi(self)

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
        input_SMA_list = [myshow.input_SMA1,myshow.input_SMA2,myshow.input_SMA3]
        for i in input_SMA_list:
            if i.toPlainText() != "":
                df.draw_SMA(m_history,int(i.toPlainText()),stockInfo)

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
        check_price_isCheck(m_history,get_stock_info.Get_stock_info(stock_number))
        check_SMA_isCheck(m_history,get_stock_info.Get_stock_info(stock_number))
        check_KD_isCheck(m_history,get_stock_info.Get_stock_info(stock_number))
        check_Volume_isCheck(m_history,get_stock_info.Get_stock_info(stock_number))
    df.draw_Show()
def button_openPickWindow_click():
        mypick.show()
def button_moveToInput_click():
    Index = myshow.treeView.currentIndex()
    mModel = myshow.treeView.model()
    data = mModel.item(Index.row(),0).text()
    text = str(data)
    myshow.input_stockNumber.setPlainText(text)
def button_addStock_click():
    stocknum = myshow.input_stockNumber.toPlainText()
    get_stock_info.Add_stock_info(stocknum)
    myshow.treeView.setModel(creat_treeView_model(myshow.treeView,main_titalList,False))#設定treeView功能
def button_deletStock_click():
    stocknum = myshow.input_stockNumber.toPlainText()
    get_stock_info.Delet_stock_info(stocknum)
    myshow.treeView.setModel(creat_treeView_model(myshow.treeView,main_titalList,False))#設定treeView功能
def button_pick_click():
    date = myshow.date_startDate.date()
    GPM = mypick.input_GPM.toPlainText()
    OPR = mypick.input_OPR.toPlainText()
    #
    AllFS = get_stock_history.get_allstock_financial_statement(date)
    AllFS1 = AllFS["毛利率(%)"] > int(GPM)
    AllFS2 = AllFS["營業利益率(%)"] > int(OPR)
    resultAllFS = AllFS[AllFS1 & AllFS2]
    mypick.treeView_pick.setModel(creat_treeView_model(mypick.treeView_pick,pick_titalList))#設定treeView功能
    set_treeView2(mypick.treeView_pick.model(),resultAllFS)
    #
    ddd = get_stock_history.get_stock_monthly_report('2330',date)
def button_moveToInputFromPick_click():
        Index = mypick.treeView_pick.currentIndex()
        mModel = mypick.treeView_pick.model()
        data = mModel.item(Index.row(),0).text()
        text = str(data)
        myshow.input_stockNumber.setPlainText(text)

def set_treeView2(model,inputdataFram):
    i = 0
    for index,row in inputdataFram.iterrows():
        add_stock_List(model,index,row['公司名稱'],i,row['毛利率(%)'],row['營業利益率(%)'])
        i = i + 1
def set_treeView(model,inputList):
    i = 0
    for key,value in inputList.items():#放入stockList
        add_stock_List(model,value.number,value.name,i)
        i = i+1
def creat_treeView_model(parent,titalList,IsEmpty = True):
    model = QStandardItemModel(0,titalList.__len__(),parent)
    for i in range(0,titalList.__len__()):
        model.setHeaderData(i,Qt.Horizontal,titalList[i])
    if IsEmpty == False:
        set_treeView(model,get_stock_info.stock_list)
    return model
def add_stock_List(model,stockNum,stockName,rowNum,num1 = None,num2 = None):
    model.insertRow(rowNum)
    model.setData(model.index(rowNum,0),stockNum)
    model.setData(model.index(rowNum,1),stockName)
    if num1 != None:
        model.setData(model.index(rowNum,2),num1)
        model.setData(model.index(rowNum,3),num2)
    
def Init_mainWindow():#初始化mainwindow
    myshow.button_addStock.clicked.connect(button_addStock_click)#設定button功能
    myshow.button_deletStock.clicked.connect(button_deletStock_click)#設定button功能
    myshow.treeView.setModel(creat_treeView_model(myshow.treeView,main_titalList,False))#設定treeView功能
    myshow.button_moveToInput.clicked.connect(button_moveToInput_click)#設定button功能
    myshow.button_getStockHistory.clicked.connect(button_getStockHistory)#設定button功能
    myshow.button_openPickWindow.clicked.connect(button_openPickWindow_click)#設定button功能
    #設定日期
    date = QtCore.QDate(datetime.datetime.today().year,datetime.datetime.today().month,datetime.datetime.today().day) 
    myshow.date_startDate.setMaximumDate(date)
    myshow.date_startDate.setDate(QtCore.QDate(2018,1,1))
def Init_pickWindow():#初始化挑股票畫面
    mypick.button_pick.clicked.connect(button_pick_click)#設定button功能
    mypick.button_moveToInput.clicked.connect(button_moveToInputFromPick_click)#設定button功能
    mypick.treeView_pick.setModel(creat_treeView_model(mypick.treeView_pick,pick_titalList))#設定treeView功能


app = QtWidgets.QApplication(sys.argv)
myshow = MyWindow()
mypick = MyPicWindow()
#從這中間加ＵＩ設定---------------
Init_mainWindow()
Init_pickWindow()
#從這中間加ＵＩ設定---------------
myshow.show()
sys.exit(app.exec_())

