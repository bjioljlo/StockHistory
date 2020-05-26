from PyQt5 import QtWidgets
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtCore import Qt,QCoreApplication
from PyQt5 import QtCore
from UI_main import Ui_MainWindow
from UI_pick import Ui_MainWindow2
from UI_backtest import Ui_MainWindow3
import sys
import datetime
import get_stock_info
import get_stock_history
import matplotlib.pyplot as plt
import draw_figur as df
import pandas as pd
import tools
import backtest_stock

main_titalList = ["股票號碼","股票名稱"]
pick_titalList = ["股票號碼","股票名稱","每股參考淨值","基本每股盈餘（元）",
                "毛利率(%)","營業利益率(%)","資產總額","負債總額","股本",
                "權益總額","本期綜合損益總額（稅後）"]

#主畫面
class MyWindow(QtWidgets.QMainWindow,Ui_MainWindow):
    def __init__(self):
        super(MyWindow,self).__init__()
        self.setupUi(self)
#挑股票畫面
class MyPickWindow(QtWidgets.QMainWindow,Ui_MainWindow2):
    def __init__(self):
        super(MyPickWindow,self).__init__()
        self.setupUi(self)
#回測畫面
class MyBacktestWindow(QtWidgets.QMainWindow,Ui_MainWindow3):
    def __init__(self):
        super(MyBacktestWindow,self).__init__()
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
        #     check_price_isCheck(m_history,value)
        #     check_SMA_isCheck(m_history,value)
        #     check_KD_isCheck(m_history,value)
        #     check_Volume_isCheck(m_history,value)
            return
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
def button_openBackWindow_click():
        mybacktest.show()
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
    date = tools.QtDate2DateTime(myshow.date_startDate.date())
    GPM = mypick.input_GPM.toPlainText()
    OPR = mypick.input_OPR.toPlainText()
    EPS = mypick.input_EPS.toPlainText()
    RPS = mypick.input_RPS.toPlainText()

    resultAllFS = get_financial_statement(date,GPM,OPR,EPS,RPS)
    mypick.treeView_pick.setModel(creat_treeView_model(mypick.treeView_pick,pick_titalList))#設定treeView功能
    set_treeView2(mypick.treeView_pick.model(),resultAllFS)
def button_moveToInputFromPick_click():
        Index = mypick.treeView_pick.currentIndex()
        mModel = mypick.treeView_pick.model()
        data = mModel.item(Index.row(),0).text()
        text = str(data)
        myshow.input_stockNumber.setPlainText(text)
def button_monthRP_click():#某股票月營收曲線
    if (myshow.input_stockNumber.toPlainText() == ''):
        print('請輸入股票號碼')
        get_stock_history.get_PER_range('2019-03-04',10,15)
        return
    data_result = None
    data_result = get_monthRP(datetime.datetime.today(),
                                myshow.date_startDate.date(),
                                myshow.input_stockNumber.toPlainText())
    df.draw_monthRP(data_result,myshow.input_stockNumber.toPlainText())
def button_monthRP_Up_click():#月營收逐步升高篩選
    date = tools.QtDate2DateTime(myshow.date_startDate.date())
    result_data = get_stock_history.get_monthRP_up(tools.changeDateMonth(date,-1),
                                int(mypick.input_monthRP_smoothAVG.toPlainText()),
                                int(mypick.input_monthRP_UpMpnth.toPlainText()))

    FS_data = get_financial_statement(tools.changeDateMonth(date,0))
    pick_data = pd.merge(result_data,FS_data,left_index=True,right_index=True)
    
    pick_data = pick_data.drop(columns=[0])
    mypick.treeView_pick.setModel(creat_treeView_model(mypick.treeView_pick,pick_titalList))#設定treeView功能
    set_treeView2(mypick.treeView_pick.model(),pick_data)
def button_backtest_click():#月營收回測開始紐
        date_start = tools.QtDate2DateTime(mybacktest.date_start.date())
        # date_start = tools.DateTime2String(date_start)
        date_end = tools.QtDate2DateTime(mybacktest.date_end.date())
        money_start = int(mybacktest.input_startMoney.toPlainText())
        change_days = int(mybacktest.input_changeDays.toPlainText())
        smoothAVG = int(mybacktest.input_monthRP_smoothAVG.toPlainText())
        upMonth = int(mybacktest.input_monthRP_UpMpnth.toPlainText())
        PER_start = int(mybacktest.input_PER_start.toPlainText())
        PER_end = int(mybacktest.input_PER_end.toPlainText())
        volumeAVG = int(mybacktest.input_volume_money.toPlainText())
        volumeDays = int(mybacktest.input_volumeAVG_days.toPlainText())
        backtest_stock.backtest_monthRP_Up(change_days,smoothAVG,upMonth,date_start,date_end,money_start,PER_start,PER_end,
                                                volumeAVG,volumeDays)


#取得月營收的資料
def get_monthRP(date_start,date_end,Number):#start = 後面時間 end = 前面時間 Number = 股票號碼
    date = date_end
    date_str = str(date.year()) + '-' + str(date.month()) + '-' + str(date.day())
    date_end = datetime.datetime.strptime(date_str,"%Y-%m-%d")
    date_now = date_start
    date_now = tools.changeDateMonth(date_now,-1)
    stockNum = Number
    data_result = None
    while (date_end < date_now):
        try:
            monthRP_temp = get_stock_history.get_stock_monthly_report(stockNum,date_end)
        except:
            break
        monthRP_temp.insert(0,'日期',date_end)
        monthRP_temp['當月營收'] = int(monthRP_temp['當月營收'])/1000
        data_result = pd.concat([data_result,monthRP_temp])
        date_end = tools.changeDateMonth(date_end,+1)
    data_result.set_index('日期',inplace=True)
    return data_result

#取得月營收逐步升高的篩選資料
# def get_monthRP_up(time,avgNum,upNum):#time = 取得資料的時間 avgNum = 平滑曲線月份 upNum = 連續成長月份
#     data = {}
#     for i in range(avgNum+upNum):
#         temp_now = tools.changeDateMonth(time,-i)
#         data['%d-%d-01'%(temp_now.year, temp_now.month)] = get_stock_history.get_allstock_monthly_report(temp_now)

#     result = pd.DataFrame({k:result['當月營收'] for k,result in data.items()}).transpose()
#     result.index = pd.to_datetime(result.index)
#     result = result.sort_index()

#     method2 = result.rolling(avgNum,min_periods=avgNum).mean()
#     method2 = (method2 > method2.shift()).iloc[-upNum:].sum()
#     final_result = method2[method2 >= upNum]

#     final_result = pd.DataFrame(final_result)
#     return final_result

#取得各種財報數字篩選
def get_financial_statement(date,GPM = '0' ,OPR ='0' ,EPS ='0',RPS ='0'):
    FS_type = get_stock_history.FS_type.cc
    resultAllFS1 = []
    resultAllFS2 = []
    resultAllFS3 = []

    FS_type = get_stock_history.FS_type.cc
    this = get_stock_history.get_allstock_financial_statement(date,FS_type)
    this1 = this["毛利率(%)"] > float(GPM)
    this2 = this["營業利益率(%)"] > float(OPR)
    resultAllFS1 = this[this1 & this2]
            
    FS_type = get_stock_history.FS_type.bb
    this = get_stock_history.get_allstock_financial_statement(date,FS_type)
    this1 = this["每股參考淨值"] > float(RPS)
    resultAllFS2 = this[this1]

    FS_type = get_stock_history.FS_type.aa
    this = get_stock_history.get_allstock_financial_statement(date,FS_type)
    this1 = this["基本每股盈餘（元）"] > float(EPS)
    resultAllFS3 = this[this1]

    resultAllFS_temp = pd.merge(resultAllFS1,resultAllFS2,left_index=True,right_index=True) 
    resultAllFS = pd.merge(resultAllFS3,resultAllFS_temp,left_index=True,right_index=True)
    return resultAllFS

def set_treeView2(model,inputdataFram):
    i = 0
    for index,row in inputdataFram.iterrows():
        array_Num = [row['每股參考淨值'],row["基本每股盈餘（元）"],
                row["毛利率(%)"],row["營業利益率(%)"],row["資產總額"],row["負債總額"],row["股本"],
                row["權益總額"],row["本期綜合損益總額（稅後）"]]
        add_stock_List(model,index,row['公司名稱'],i,array_Num)
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
def add_stock_List(model,stockNum,stockName,rowNum,array = None):
    model.insertRow(rowNum)
    model.setData(model.index(rowNum,0),stockNum)
    model.setData(model.index(rowNum,1),stockName)
    if array != None:
        for i in range(len(array)):
            model.setData(model.index(rowNum,i+2),array[i])
    
def Init_mainWindow():#初始化mainwindow
    myshow.button_addStock.clicked.connect(button_addStock_click)#設定button功能
    myshow.button_deletStock.clicked.connect(button_deletStock_click)#設定button功能
    myshow.treeView.setModel(creat_treeView_model(myshow.treeView,main_titalList,False))#設定treeView功能
    myshow.button_moveToInput.clicked.connect(button_moveToInput_click)#設定button功能
    myshow.button_getStockHistory.clicked.connect(button_getStockHistory)#設定button功能
    myshow.button_openPickWindow.clicked.connect(button_openPickWindow_click)#設定button功能
    myshow.button_getMonthRP.clicked.connect(button_monthRP_click)#設定button功能
    #設定日期
    date = QtCore.QDate(datetime.datetime.today().year,datetime.datetime.today().month,datetime.datetime.today().day) 
    myshow.date_startDate.setMaximumDate(date)
    myshow.date_startDate.setMinimumDate(QtCore.QDate(2013,1,1))
    myshow.date_startDate.setDate(QtCore.QDate(2019,1,1))
def Init_pickWindow():#初始化挑股票畫面
    mypick.button_pick.clicked.connect(button_pick_click)#設定button功能
    mypick.button_moveToInput.clicked.connect(button_moveToInputFromPick_click)#設定button功能
    mypick.treeView_pick.setModel(creat_treeView_model(mypick.treeView_pick,pick_titalList))#設定treeView功能
    mypick.button_pick_2.clicked.connect(button_monthRP_Up_click)#設定button功能
    mypick.button_openBackWindow.clicked.connect(button_openBackWindow_click)#設定button功能
    mypick.input_EPS.setPlainText("0")
    mypick.input_GPM.setPlainText("0")
    mypick.input_OPR.setPlainText("0")
    mypick.input_RPS.setPlainText("0")
    mypick.input_monthRP_smoothAVG.setPlainText("0")
    mypick.input_monthRP_UpMpnth.setPlainText("0")
def Init_backtestWindow():#初始化回測畫面
    mybacktest.button_backtest.clicked.connect(button_backtest_click)#設定button功能
    date = QtCore.QDate(datetime.datetime.today().year,datetime.datetime.today().month,datetime.datetime.today().day) 
    mybacktest.date_start.setMaximumDate(date)
    mybacktest.date_start.setMinimumDate(QtCore.QDate(2013,1,1))
    mybacktest.date_start.setDate(QtCore.QDate(2013,1,1))
    mybacktest.date_end.setMaximumDate(date)
    mybacktest.date_end.setDate(date)
    mybacktest.date_end.setMinimumDate(QtCore.QDate(2013,1,1))
    mybacktest.input_startMoney.setPlainText('100000')
    mybacktest.input_changeDays.setPlainText('25')
    mybacktest.input_monthRP_smoothAVG.setPlainText('4')
    mybacktest.input_monthRP_UpMpnth.setPlainText('5')
    mybacktest.input_PER_start.setPlainText('10')
    mybacktest.input_PER_end.setPlainText('15')
    mybacktest.input_volume_money.setPlainText('1000000')
    mybacktest.input_volumeAVG_days.setPlainText('20')
    


app = QtWidgets.QApplication(sys.argv)
myshow = MyWindow()
mypick = MyPickWindow()
mybacktest = MyBacktestWindow()
#從這中間加ＵＩ設定---------------
Init_mainWindow()
Init_pickWindow()
Init_backtestWindow()
#從這中間加ＵＩ設定---------------
myshow.show()
QCoreApplication.quit
sys.exit(app.exec_())

