from PyQt5 import QtWidgets
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtCore import Qt
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
                "權益總額","本期綜合損益總額（稅後）","PBR","PER","ROE"]

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
    #存更新日期
    #get_stock_info.Update_date = str(datetime.datetime(2020,5,21))[0:10]
    #get_stock_info.Save_Update_date()
    date = myshow.date_startDate.date()
    str_date = str(date.year())+'-'+ str(date.month())+'-'+str(date.day())
    if myshow.input_stockNumber.toPlainText() == "":
        for key,value in get_stock_info.stock_list.items():
            m_history = get_stock_history.get_stock_history(key,str_date)
        return
    elif myshow.input_stockNumber.toPlainText() == "Update":
        for key,value in get_stock_info.ts.codes.items():
            if value.market == "上市" and len(value.code) == 4:
                if get_stock_history.check_no_use_stock(value.code) == True:
                    print('get_stock_price: ' + str(value.code) + ' in no use')
                    continue
                m_history = get_stock_history.get_stock_history(value.code,str_date)
                print("get " + str(value.code) + " info susess!")
        #存更新日期
        get_stock_info.Update_date = str(datetime.datetime.today())[0:10]
        get_stock_info.Save_Update_date()
        return  
    else:
        stock_number = myshow.input_stockNumber.toPlainText()
        if myshow.check_UseNewInfo.isChecked():
            m_history = get_stock_history.get_stock_history(stock_number,str_date,False)
        else:
            m_history = get_stock_history.get_stock_history(stock_number,str_date,False,False)
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
    volume_date = tools.QtDate2DateTime(myshow.date_endDate.date())
    GPM = mypick.input_GPM.toPlainText()
    OPR = mypick.input_OPR.toPlainText()
    EPS = mypick.input_EPS.toPlainText()
    RPS = mypick.input_RPS.toPlainText()
    
    resultAllFS = pd.DataFrame()
    resultAllFS = get_financial_statement(volume_date,GPM,OPR,EPS,RPS)

    if volume_date.isoweekday() == 6:
        volume_date = volume_date + datetime.timedelta(days=-1)#加一天
    elif volume_date.isoweekday() == 7:
        volume_date = volume_date + datetime.timedelta(days=-2)#加2天
    else:
        pass
    
    resultAllFS = get_price_range(int(mypick.input_price_high.toPlainText()),int(mypick.input_price_low.toPlainText()),tools.changeDateMonth(volume_date,0),resultAllFS)
    resultAllFS = get_volume(int(mypick.input_volum.toPlainText()),tools.changeDateMonth(volume_date,0),resultAllFS)


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
        return
    if (int(myshow.date_endDate.date().month()) == int(datetime.datetime.today().month)):
        print("本月還沒過完無資資訊")
        return
    data_result = None
    data_result = get_monthRP(myshow.date_endDate.date(),
                                myshow.date_startDate.date(),
                                myshow.input_stockNumber.toPlainText())
    df.draw_monthRP(data_result,myshow.input_stockNumber.toPlainText())
def button_monthRP_Up_click():#月營收逐步升高篩選
    date = tools.QtDate2DateTime(myshow.date_endDate.date())
    
    if date.isoweekday() == 6:
        date = date + datetime.timedelta(days=-1)#加一天
    elif date.isoweekday() == 7:
        date = date + datetime.timedelta(days=-2)#加2天
    else:
        pass
        

    FS_data = pd.DataFrame()
    result_data = pd.DataFrame()
    BOOK_data = pd.DataFrame()
    PER_data = pd.DataFrame()

    FS_data = get_financial_statement(date)
    result_data = get_stock_history.get_monthRP_up(tools.changeDateMonth(date,0),
                                                int(mypick.input_monthRP_smoothAVG.toPlainText()),
                                                int(mypick.input_monthRP_UpMpnth.toPlainText()))
    BOOK_data = get_stock_history.get_PBR_rang(tools.changeDateMonth(date,0),
                                                float(mypick.input_PBR_low.toPlainText()),
                                                float(mypick.input_PBR_high.toPlainText()))
    PER_data = get_stock_history.get_PER_range(tools.changeDateMonth(date,0),
                                                float(mypick.input_PER_low.toPlainText()),
                                                float(mypick.input_PER_high.toPlainText()))
    ROE_data = get_stock_history.get_ROE_rang(tools.changeDateMonth(date,0),
                                                float(mypick.input_ROE_low.toPlainText()),
                                                float(mypick.input_ROE_high.toPlainText()))
    pick_data = FS_data
    if result_data.empty == False:            
        pick_data = pd.merge(pick_data,result_data,left_index=True,right_index=True,how='left')
        pick_data = pick_data.dropna(axis=0,how='any')
    
    if BOOK_data.empty == False:
        pick_data = pd.merge(pick_data,BOOK_data,left_index=True,right_index=True,how='left')
        pick_data = pick_data.dropna(axis=0,how='any')
    
    if PER_data.empty == False:
        pick_data = pd.merge(pick_data,PER_data,left_index=True,right_index=True,how='left')
        pick_data = pick_data.dropna(axis=0,how='any')
    
    if ROE_data.empty == False:
        pick_data = pd.merge(pick_data,ROE_data,left_index=True,right_index=True,how='left')
        pick_data = pick_data.dropna(axis=0,how='any')

    pick_data = get_price_range(int(mypick.input_price_high.toPlainText()),int(mypick.input_price_low.toPlainText()),tools.changeDateMonth(date,0),pick_data)
    pick_data = pick_data.dropna(axis=0,how='any')

    pick_data = get_volume(int(mypick.input_volum.toPlainText()),tools.changeDateMonth(date,0),pick_data)
    pick_data = pick_data.dropna(axis=0,how='any')

    print("總挑選數量:" + str(len(pick_data)))
    mypick.treeView_pick.setModel(creat_treeView_model(mypick.treeView_pick,pick_titalList))#設定treeView功能
    set_treeView2(mypick.treeView_pick.model(),pick_data)
def button_backtest_click():#月營收回測開始紐
        if mybacktest.check_monthRP_pick.isChecked() == mybacktest.check_PER_pick.isChecked() == mybacktest.check_volume_pick.isChecked() == False:
            print("都沒選是要回測個毛線！")
            return
        else:
            backtest_stock.set_check(mybacktest.check_monthRP_pick.isChecked(),
                mybacktest.check_PER_pick.isChecked(),
                mybacktest.check_volume_pick.isChecked(),
                mybacktest.check_pickOneStock.isChecked(),
                mybacktest.check_price_pick.isChecked(),
                mybacktest.check_PBR_pick.isChecked(),
                mybacktest.check_ROE_pick.isChecked())
        date_start = tools.QtDate2DateTime(mybacktest.date_start.date())
        date_end = tools.QtDate2DateTime(mybacktest.date_end.date())
        money_start = int(mybacktest.input_startMoney.toPlainText())
        change_days = int(mybacktest.input_changeDays.toPlainText())
        smoothAVG = int(mybacktest.input_monthRP_smoothAVG.toPlainText())
        upMonth = int(mybacktest.input_monthRP_UpMpnth.toPlainText())
        PER_start = float(mybacktest.input_PER_start.toPlainText())
        PER_end = float(mybacktest.input_PER_end.toPlainText())
        volumeAVG = int(mybacktest.input_volume_money.toPlainText())
        volumeDays = int(mybacktest.input_volumeAVG_days.toPlainText())
        price_high = int(mybacktest.input_price_high.toPlainText())
        price_low = int(mybacktest.input_price_low.toPlainText())
        PBR_end = float(mybacktest.input_PBR_end.toPlainText())
        PBR_start = float(mybacktest.input_PBR_start.toPlainText())
        ROE_end = float(mybacktest.input_ROE_end.toPlainText())
        ROE_start = float(mybacktest.input_ROE_start.toPlainText())
        backtest_stock.backtest_monthRP_Up(change_days,smoothAVG,upMonth,date_start,date_end,money_start,PER_start,PER_end,
                                                volumeAVG,volumeDays,price_high,price_low,PBR_start,PBR_end,ROE_start,ROE_end)
def button_backtest_click2():
    backtest_stock.set_check(mybacktest.check_monthRP_pick.isChecked(),
                                mybacktest.check_PER_pick.isChecked(),
                                mybacktest.check_volume_pick.isChecked(),
                                mybacktest.check_pickOneStock.isChecked(),
                                mybacktest.check_price_pick.isChecked(),
                                mybacktest.check_PBR_pick.isChecked(),
                                mybacktest.check_ROE_pick.isChecked())
    date_start = tools.QtDate2DateTime(mybacktest.date_start.date())
    date_end = tools.QtDate2DateTime(mybacktest.date_end.date())
    money_start = int(mybacktest.input_startMoney.toPlainText())
    change_days = int(mybacktest.input_changeDays.toPlainText())
    PER_start = float(mybacktest.input_PER_start.toPlainText())
    PER_end = float(mybacktest.input_PER_end.toPlainText())
    PBR_end = float(mybacktest.input_PBR_end.toPlainText())
    PBR_start = float(mybacktest.input_PBR_start.toPlainText())
    Pick_amount = int(mybacktest.input_StockAmount.toPlainText())
    backtest_stock.backtest_PERandPBR(change_days,date_start,date_end,money_start,PER_start,PER_end,PBR_start,PBR_end,Pick_amount)

#取得月營收的資料
def get_monthRP(date_end,date_start,Number):#end = 後面時間 start = 前面時間 Number = 股票號碼
    date_end_str = str(date_end.year()) + '-' + str(date_end.month()) + '-' + str(date_end.day())
    m_date_end = datetime.datetime.strptime(date_end_str,"%Y-%m-%d")

    date_start_str = str(date_start.year()) + '-' + str(date_start.month()) + '-' + str(date_start.day())
    m_date_start = datetime.datetime.strptime(date_start_str,"%Y-%m-%d")

    stockNum = Number
    data_result = None
    while (m_date_start <= m_date_end):
        try:
            monthRP_temp = get_stock_history.get_stock_monthly_report(stockNum,m_date_start)
        except:
            print(str(m_date_start) + "月營收未出喔")
            m_date_start = tools.changeDateMonth(m_date_start,+1)
            continue
        monthRP_temp.insert(0,'日期',m_date_start)
        monthRP_temp['當月營收'] = int(monthRP_temp['當月營收'])/1000
        data_result = pd.concat([data_result,monthRP_temp])
        m_date_start = tools.changeDateMonth(m_date_start,+1)
    if m_date_start>m_date_end and m_date_end.year == m_date_start.year:
        try:
            monthRP_temp = get_stock_history.get_stock_monthly_report(stockNum,m_date_start)
            monthRP_temp.insert(0,'日期',m_date_start)
            monthRP_temp['當月營收'] = int(monthRP_temp['當月營收'])/1000
            data_result = pd.concat([data_result,monthRP_temp])
        except:
            print(str(m_date_start) + "月營收未出喔")
    data_result.set_index('日期',inplace=True)
    return data_result

#取得各種財報數字篩選
def get_financial_statement(date,GPM = '0' ,OPR ='0' ,EPS ='0',RPS ='0'):
    FS_type = get_stock_history.FS_type.PLA
    resultAllFS1 = []
    resultAllFS2 = []
    resultAllFS3 = []
    this = pd.DataFrame()
    FS_type = get_stock_history.FS_type.PLA
    volume_date = date
    for i in range(4):
        try:
            this = get_stock_history.get_allstock_financial_statement(date,FS_type)
            print(str(date.month)+ "月財務報告ＯＫ")
            break
        except:
            print(str(date.month)+ "月財務報告未出跳下一個月")
            date = tools.changeDateMonth(date,-1)
            continue
    this1 = this["毛利率(%)"] > float(GPM)
    this2 = this["營業利益率(%)"] > float(OPR)
    resultAllFS1 = this[this1 & this2]
            
    FS_type = get_stock_history.FS_type.BS
    this = get_stock_history.get_allstock_financial_statement(date,FS_type)
    this1 = this["每股參考淨值"] > float(RPS)
    resultAllFS2 = this[this1]

    FS_type = get_stock_history.FS_type.CPL
    this = get_stock_history.get_allstock_financial_statement(date,FS_type)
    this1 = this["基本每股盈餘（元）"] > float(EPS)
    resultAllFS3 = this[this1]

    resultAllFS_temp = pd.merge(resultAllFS1,resultAllFS2,left_index=True,right_index=True) 
    resultAllFS = pd.merge(resultAllFS3,resultAllFS_temp,left_index=True,right_index=True)

    return resultAllFS

#取得交易量篩選
def get_volume(volumeNum,date,data = pd.DataFrame(),getMax = False):
    Temp_index = 0
    Temp_volume2 = 0
    if data.empty == False:
        for index,row in data.iterrows():
            Temp_volume = get_stock_history.get_stock_price(str(index),tools.DateTime2String(date),get_stock_history.stock_data_kind.Volume)
            while (Temp_volume == None):
                if get_stock_history.check_no_use_stock(index):
                    break
                date = date + datetime.timedelta(days=-1)#加一天
                Temp_volume = get_stock_history.get_stock_price(str(index),tools.DateTime2String(date),get_stock_history.stock_data_kind.Volume)
            if Temp_volume != None and Temp_volume >= volumeNum:
                if(mypick.check_volum_Max.isChecked()):
                    if Temp_volume > Temp_volume2:
                        if(Temp_index != 0):
                            data = data.drop(index = Temp_index)
                        Temp_index = index
                        Temp_volume2 = Temp_volume
                    else:
                        data = data.drop(index = index)
                else:
                    pass
                 
            else:
                data = data.drop(index = index)
    else:
        print("get_volume:輸入的data是空的")
    return data

#取得股價篩選
def get_price_range(high,low,date,data = pd.DataFrame()):
    if high == 0 and low == 0:
        return data
    if high < low:
        return data
    if data.empty == False:
        for index,row in data.iterrows():
            Temp_price = get_stock_history.get_stock_price(str(index),tools.DateTime2String(date),
                                                        get_stock_history.stock_data_kind.AdjClose)
            while(Temp_price == None):
                if get_stock_history.check_no_use_stock(index):
                    break
                date = date + datetime.timedelta(days=-1)#加一天
                Temp_price = get_stock_history.get_stock_price(str(index),tools.DateTime2String(date),get_stock_history.stock_data_kind.Volume)
            if Temp_price != None and Temp_price >= low and Temp_price <= high:
                print("OK")
            else:
                data = data.drop(index = index)
    else:
        print("get_price_range:輸入的data是空的")
    return data

def set_treeView2(model,inputdataFram):
    i = 0
    for index,row in inputdataFram.iterrows():
        array_Num = [row['每股參考淨值'],row["基本每股盈餘（元）"],
                row["毛利率(%)"],row["營業利益率(%)"],row["資產總額"],row["負債總額"],row["股本"],
                row["權益總額"],row["本期綜合損益總額（稅後）"]]#,row["PBR"],row["PER"],row["ROE"]]
        try:
            array_Num.append(row["PBR"])
        except:
            array_Num.append(float(0))
        try:
            array_Num.append(row["PER"])
        except:
            array_Num.append(float(0))
        try:
            array_Num.append(float(row["ROE"]))
        except:
            array_Num.append(float(0))
            
        
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
    Date = datetime.datetime.strptime(get_stock_info.Update_date[0:10],"%Y-%m-%d")
    date = QtCore.QDate(Date.year,Date.month,Date.day)
    today = QtCore.QDate(datetime.datetime.today().year,datetime.datetime.today().month,datetime.datetime.today().day)
    myshow.date_startDate.setMaximumDate(today)
    myshow.date_startDate.setMinimumDate(QtCore.QDate(2000,1,1))
    myshow.date_startDate.setDate(QtCore.QDate((datetime.datetime.today().year -1),datetime.datetime.today().month,datetime.datetime.today().day))
    myshow.date_endDate.setMaximumDate(today)
    myshow.date_endDate.setMinimumDate(QtCore.QDate(2001,1,1))
    myshow.date_endDate.setDate(date)
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
    mypick.input_volum.setPlainText("0")
    mypick.input_price_high.setPlainText("0")
    mypick.input_price_low.setPlainText("0")
    mypick.input_PBR_high.setPlainText("0")
    mypick.input_PBR_low.setPlainText("0")
    mypick.input_PER_high.setPlainText("0")
    mypick.input_PER_low.setPlainText("0")
    mypick.input_ROE_high.setPlainText("0")
    mypick.input_ROE_low.setPlainText("0")
def Init_backtestWindow():#初始化回測畫面
    mybacktest.button_backtest.clicked.connect(button_backtest_click)#設定button功能
    mybacktest.button_backtest_2.clicked.connect(button_backtest_click2)
    date = QtCore.QDate(datetime.datetime.today().year,datetime.datetime.today().month,datetime.datetime.today().day) 

    mybacktest.date_end.setMaximumDate(date)
    mybacktest.date_end.setMinimumDate(QtCore.QDate(2013,1,1))
    date = date.addMonths(0)
    mybacktest.date_end.setDate(date)

    mybacktest.date_start.setMaximumDate(date)
    mybacktest.date_start.setMinimumDate(QtCore.QDate(2013,1,1))
    date = date.addYears(-1)
    mybacktest.date_start.setDate(date)

    mybacktest.input_startMoney.setPlainText('100000')
    mybacktest.input_changeDays.setPlainText('20')
    mybacktest.input_monthRP_smoothAVG.setPlainText('0')
    mybacktest.input_monthRP_UpMpnth.setPlainText('0')
    mybacktest.input_PER_start.setPlainText('0')
    mybacktest.input_PER_end.setPlainText('0')
    mybacktest.input_volume_money.setPlainText('0')
    mybacktest.input_volumeAVG_days.setPlainText('0')
    mybacktest.input_price_high.setPlainText('0')
    mybacktest.input_price_low.setPlainText("0")
    mybacktest.input_PBR_start.setPlainText('0')
    mybacktest.input_PBR_end.setPlainText('0')
    mybacktest.input_ROE_start.setPlainText('0')
    mybacktest.input_ROE_end.setPlainText('0')
    mybacktest.input_StockAmount.setPlainText('0')
    


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
sys.exit(app.exec_())

