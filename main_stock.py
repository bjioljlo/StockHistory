from PyQt5 import QtWidgets
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtCore import Qt
from PyQt5 import QtCore
from UI_main import Ui_MainWindow
from UI_pick import Ui_MainWindow2
from UI_backtest import Ui_MainWindow3
import sys
from datetime import datetime,timedelta
import get_stock_info
import get_stock_history
import update_stock_info
import draw_figur as df
import pandas as pd
import tools
import backtest_stock
import threading



main_titalList = ["股票號碼","股票名稱"]
pick_titalList = ["股票號碼","股票名稱","每股參考淨值","基本每股盈餘（元）",
                "毛利率(%)","營業利益率(%)","資產總額","負債總額","股本",
                "權益總額","本期綜合損益總額（稅後）","PBR","PER","PEG","ROE","殖利率"]
lock = threading.Lock()

class BackTestParameter():
    def __init__(self):
        self.date_start = tools.QtDate2DateTime(mybacktest.date_start.date())
        self.date_end = tools.QtDate2DateTime(mybacktest.date_end.date())
        self.money_start = int(mybacktest.input_startMoney.toPlainText())
        self.change_days = int(mybacktest.input_changeDays.toPlainText())
        self.smoothAVG = int(mybacktest.input_monthRP_smoothAVG.toPlainText())
        self.upMonth = int(mybacktest.input_monthRP_UpMpnth.toPlainText())
        self.PER_start = float(mybacktest.input_PER_start.toPlainText())
        self.PER_end = float(mybacktest.input_PER_end.toPlainText())
        self.volumeAVG = int(mybacktest.input_volume_money.toPlainText())
        self.volumeDays = int(mybacktest.input_volumeAVG_days.toPlainText())
        self.price_high = int(mybacktest.input_price_high.toPlainText())
        self.price_low = int(mybacktest.input_price_low.toPlainText())
        self.PBR_end = float(mybacktest.input_PBR_end.toPlainText())
        self.PBR_start = float(mybacktest.input_PBR_start.toPlainText())
        self.ROE_end = float(mybacktest.input_ROE_end.toPlainText())
        self.ROE_start = float(mybacktest.input_ROE_start.toPlainText())
        self.Pick_amount = int(mybacktest.input_StockAmount.toPlainText())
        self.buy_number = str(mybacktest.input_stockNumber.toPlainText())
        self.Dividend_yield_high = float(mybacktest.input_yield_start.toPlainText())
        self.Dividend_yield_low = float(mybacktest.input_yield_end.toPlainText())
        self.buy_day = int(mybacktest.input_buyDay.toPlainText())
        self.Record_high_day = int(mybacktest.input_RecordHigh.toPlainText())

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
    else:
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
def check_BollingerBands_isCheck(m_history,stockInfo):
    if myshow.check_BollingerBands.isChecked() == True:
        df.draw_BollingerBands(m_history,12,stockInfo)
def check_RSI_isCheck(m_history,stockInfo):
    if myshow.check_RSI.isChecked() == True:
        df.draw_RSI(m_history,stockInfo)
def Check_ADL_isCheck():
    if myshow.check_ADL.isChecked() == True:
        Data_ADL = get_stock_history.get_ADL(tools.QtDate2DateTime(myshow.date_startDate.date()),tools.QtDate2DateTime(myshow.date_endDate.date()))
        df.draw_ADL(Data_ADL)
def Check_ADLs_isCheck():
    if myshow.check_ADLs.isChecked() == True:
        Data_ADLs = get_stock_history.get_ADLs(tools.QtDate2DateTime(myshow.date_startDate.date()),tools.QtDate2DateTime(myshow.date_endDate.date()))
        df.draw_ADLs(Data_ADLs)
def Check_MACD_isCheck(m_history):
    if myshow.check_MACD.isChecked() == True:
        df.draw_MACD(m_history)

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
def button_moveToInputFromPick_click():
        Index = mypick.treeView_pick.currentIndex()
        mModel = mypick.treeView_pick.model()
        data = mModel.item(Index.row(),0).text()
        text = str(data)
        myshow.input_stockNumber.setPlainText(text)

#第1頁的UI
def button_getStockHistory():#某股票蠟燭圖
    #存更新日期
    date = myshow.date_startDate.date()
    end_date = tools.QtDate2DateTime(myshow.date_endDate.date())
    str_date = str(date.year())+'-'+ str(date.month())+'-'+str(date.day())
    df.Clear_PICS()
    if myshow.input_stockNumber.toPlainText() == "":
        for key,value in get_stock_info.stock_list.items():
            m_history = get_stock_history.get_stock_history(key,str_date)
        return
    elif myshow.input_stockNumber.toPlainText() == "Update":
        str_date = [str_date]
        new_thread = threading.Thread(target=Update_StockData_threading,args=str_date)
        new_thread.setDaemon(True)
        new_thread.start()
        return  
    else:
        stock_number = myshow.input_stockNumber.toPlainText()
        if myshow.check_UseNewInfo.isChecked():
            m_history = get_stock_history.get_stock_history(stock_number,str_date,reGetInfo=False)
        else:
            m_history = get_stock_history.get_stock_history(stock_number,str_date,reGetInfo=False,UpdateInfo=False)
        if myshow.check_ADL.isChecked() or myshow.check_ADLs.isChecked():
            mask = m_history.index <= end_date
            m_history = m_history[mask]
        check_SMA_isCheck(m_history,get_stock_info.Get_stock_info(stock_number))
        check_Volume_isCheck(m_history,get_stock_info.Get_stock_info(stock_number))  
        check_KD_isCheck(m_history,get_stock_info.Get_stock_info(stock_number))
        check_BollingerBands_isCheck(m_history,get_stock_info.Get_stock_info(stock_number))
        check_RSI_isCheck(m_history,get_stock_info.Get_stock_info(stock_number))
        Check_ADL_isCheck()
        Check_ADLs_isCheck()
        Check_MACD_isCheck(m_history)
        check_price_isCheck(m_history,get_stock_info.Get_stock_info(stock_number))#壹定要在最後面檢查 
def button_monthRP_click():#某股票月營收曲線
    if (myshow.input_stockNumber.toPlainText() == ''):
        print('請輸入股票號碼')
        return
    if (int(myshow.date_endDate.date().month()) == int(datetime.today().month)):
        print("本月還沒過完無資資訊")
        return
    if int(myshow.date_endDate.date().month()) == int(tools.changeDateMonth(datetime.today(),-1).month) and (int(datetime.today().day)) < 15 :
        print("還沒15號沒有上個月的資料")
        return
    data_result = None
    data_result = get_monthRP(myshow.date_endDate.date(),
                                myshow.date_startDate.date(),
                                myshow.input_stockNumber.toPlainText())
    df.draw_monthRP(data_result,myshow.input_stockNumber.toPlainText())
def button_Dividend_yield_click():#某股票殖利率曲線
    if (myshow.input_stockNumber.toPlainText() == ''):
        print('請輸入股票號碼')
        return
    if (int(myshow.date_endDate.date().day()) == int(datetime.today().day)):
        print("今天還沒過完無資資訊")
        return
    data_result = None
    data_result = get_Dividend_yield(myshow.date_endDate.date(),
                                myshow.date_startDate.date(),
                                myshow.input_stockNumber.toPlainText())
    df.draw_Dividend_yield(data_result,myshow.input_stockNumber.toPlainText())
def button_Operating_Margin_click():#某股票營業利益率曲線
    if (myshow.input_stockNumber.toPlainText() == ''):
        print('請輸入股票號碼')
        return
    if (int(myshow.date_endDate.date().day()) == int(datetime.today().day)):
        print("今天還沒過完無資資訊")
        return
    data_result = None
    data_result = get_Operating_Margin(myshow.date_endDate.date(),
                                myshow.date_startDate.date(),
                                myshow.input_stockNumber.toPlainText())
    df.draw_Operating_Margin(data_result,myshow.input_stockNumber.toPlainText())
def button_Operating_Margin_Ratio_click():#某股票營業利益成長率曲線
    if (myshow.input_stockNumber.toPlainText() == ''):
        print('請輸入股票號碼')
        return
    if (int(myshow.date_endDate.date().day()) == int(datetime.today().day)):
        print("今天還沒過完無資資訊")
        return
    data_result_up = None
    data_result_up = get_Operating_Margin_Ratio(myshow.date_endDate.date(),
                                myshow.date_startDate.date(),
                                myshow.input_stockNumber.toPlainText())
    df.draw_Operating_Margin_Ratio(data_result_up,myshow.input_stockNumber.toPlainText())
def button_ROE_Ratio_click():#某股票ROE曲線
    if (myshow.input_stockNumber.toPlainText() == ''):
        print('請輸入股票號碼')
        return
    if (int(myshow.date_endDate.date().day()) == int(datetime.today().day)):
        print("今天還沒過完無資資訊")
        return
    data_result_up = None
    data_result_up = get_ROE(myshow.date_endDate.date(),
                                myshow.date_startDate.date(),
                                myshow.input_stockNumber.toPlainText())
    df.draw_ROE(data_result_up,myshow.input_stockNumber.toPlainText())
def button_SCF_click():#某股票營業現金流
    if (myshow.input_stockNumber.toPlainText() == ''):
        print('請輸入股票號碼')
        return
    if (int(myshow.date_endDate.date().day()) == int(datetime.today().day)):
        print("今天還沒過完無資資訊")
        return
    data_result_up = None
    data_result_up = get_SCF(myshow.date_endDate.date(),
                                myshow.date_startDate.date(),
                                myshow.input_stockNumber.toPlainText())
    df.draw_SCF(data_result_up,myshow.input_stockNumber.toPlainText())
def button_FreeSCF_click():#某股票自由現金流
    if (myshow.input_stockNumber.toPlainText() == ''):
        print('請輸入股票號碼')
        return
    if (int(myshow.date_endDate.date().day()) == int(datetime.today().day)):
        print("今天還沒過完無資資訊")
        return
    data_result_up = None
    data_result_up = get_FreeSCF_Margin(myshow.date_endDate.date(),
                                myshow.date_startDate.date(),
                                myshow.input_stockNumber.toPlainText())
    df.draw_FreeSCF(data_result_up,myshow.input_stockNumber.toPlainText())

#第2頁的UI
def button_pick_click():#其他數值篩選
    volume_date = tools.QtDate2DateTime(myshow.date_endDate.date())
    GPM = mypick.input_GPM.toPlainText()
    OPR = mypick.input_OPR.toPlainText()
    EPS = mypick.input_EPS.toPlainText()
    RPS = mypick.input_RPS.toPlainText()
    
    resultAllFS = pd.DataFrame()
    resultAllFS = get_financial_statement(volume_date,GPM,OPR,EPS,RPS)

    if volume_date.isoweekday() == 6:
        volume_date = volume_date + timedelta(days=-1)#加一天
    elif volume_date.isoweekday() == 7:
        volume_date = volume_date + timedelta(days=-2)#加2天
    else:
        pass
    
    price_data = get_stock_history.get_price_range(volume_date,int(mypick.input_price_high.toPlainText()),int(mypick.input_price_low.toPlainText()),resultAllFS)
    if price_data.empty == False:
        resultAllFS = tools.MixDataFrames({'pick':resultAllFS,'recordHigh':price_data})
        resultAllFS = resultAllFS.dropna(axis=0,how='any')
    resultAllFS = get_stock_history.get_volume(int(mypick.input_volum.toPlainText()),tools.changeDateMonth(volume_date,0),resultAllFS)


    mypick.treeView_pick.setModel(creat_treeView_model(mypick.treeView_pick,pick_titalList))#設定treeView功能
    set_treeView2(mypick.treeView_pick.model(),resultAllFS)
def button_monthRP_Up_click():#全部篩選
    date = tools.QtDate2DateTime(myshow.date_endDate.date())
    if date.isoweekday() == 6:
        date = date + timedelta(days=-1)#加一天
    elif date.isoweekday() == 7:
        date = date + timedelta(days=-2)#加2天
    else:
        pass
    try:
        GPM = mypick.input_GPM.value()
        OPR = mypick.input_OPR.value()
        EPS = mypick.input_EPS.value()
        RPS = mypick.input_RPS.value() 
        monthRP_smoothAVG = mypick.input_monthRP_smoothAVG.value()
        monthRP_UpMpnth = mypick.input_monthRP_UpMpnth.value()
        PBR_low = mypick.input_PBR_low.value()
        PBR_high = mypick.input_PBR_high.value()
        PER_low = mypick.input_PER_low.value()
        PER_high = mypick.input_PER_high.value()
        ROE_low = mypick.input_ROE_low.value()
        ROE_high = mypick.input_ROE_high.value()
        yiled_high = mypick.input_yiled_high.value()
        yiled_low = mypick.input_yiled_low.value()
        OMGR = mypick.input_OMGR.value()
        price_high = mypick.input_price_high.value()
        price_low = mypick.input_price_low.value()
        flash_Day = mypick.input_flash_Day.value()
        record_Day = mypick.input_record_Day.value()
        volum = mypick.input_volum.value()
        PEG_low = mypick.input_PEG_low.value()
        PEG_high = mypick.input_PEG_high.value()
    except:
        print("Get value error")
        return
    FS_data = pd.DataFrame()
    pick_data = pd.DataFrame()
    result_data = pd.DataFrame()
    BOOK_data = pd.DataFrame()
    PER_data = pd.DataFrame()
    yield_data = pd.DataFrame()
    PEG_data = pd.DataFrame()

    FS_data = get_financial_statement(date,GPM,OPR,EPS,RPS)
    result_data = get_stock_history.get_monthRP_up(tools.changeDateMonth(date,0),monthRP_smoothAVG,monthRP_UpMpnth)
    BOOK_data = get_stock_history.get_PBR_range(tools.changeDateMonth(date,0),PBR_low,PBR_high)
    PER_data = get_stock_history.get_PER_range(tools.changeDateMonth(date,0),PER_low,PER_high)
    ROE_data = get_stock_history.get_ROE_range(tools.changeDateMonth(date,0),ROE_low,ROE_high)
    yield_data = get_stock_history.get_yield_range(tools.changeDateMonth(date,0),yiled_high,yiled_low)
    OMGR_data = get_stock_history.get_OMGR_up(tools.changeDateMonth(date,0),OMGR)
    PEG_data = get_stock_history.get_PEG_range(tools.changeDateMonth(date,0),PEG_low,PEG_high)
    
    pick_data = FS_data
    if monthRP_smoothAVG > 0 or monthRP_UpMpnth > 0:            
        pick_data = pd.merge(pick_data,result_data,left_index=True,right_index=True,how='left')
        pick_data = pick_data.dropna(axis=0,how='any')
    
    if PBR_low > 0 or PBR_high > 0:
        pick_data = pd.merge(pick_data,BOOK_data,left_index=True,right_index=True,how='left')
        pick_data = pick_data.dropna(axis=0,how='any')
    
    if PER_low > 0 or PER_high > 0:
        pick_data = pd.merge(pick_data,PER_data,left_index=True,right_index=True,how='left')
        pick_data = pick_data.dropna(axis=0,how='any')
    if PEG_low > 0 or PEG_high > 0:
        pick_data = pd.merge(pick_data,PEG_data,left_index=True,right_index=True,how='left')
        pick_data = pick_data.dropna(axis=0,how='any')
    if ROE_low > 0 or ROE_high > 0:
        pick_data = pd.merge(pick_data,ROE_data,left_index=True,right_index=True,how='left')
        pick_data = pick_data.dropna(axis=0,how='any')
    
    if yiled_high > 0 or yiled_low > 0:
        pick_data = pd.merge(pick_data,yield_data,left_index=True,right_index=True,how='left')
        pick_data = pick_data.dropna(axis=0,how='any')
    
    if OMGR > 0:
        pick_data = pd.merge(pick_data,OMGR_data,left_index=True,right_index=True,how='left')
        pick_data = pick_data.dropna(axis=0,how='any')
    
    if price_high > 0 or price_low > 0:
        price_data = get_stock_history.get_price_range(date,price_high,price_low,pick_data)
        pick_data = tools.MixDataFrames({'pick':pick_data,'price':price_data})
        pick_data = pick_data.dropna(axis=0,how='any')

    if flash_Day > 0 or record_Day > 0:
        record_data = get_stock_history.get_RecordHigh_range(date,flash_Day,record_Day,pick_data)
        pick_data = tools.MixDataFrames({'pick':pick_data,'recordHigh':record_data})
        pick_data = pick_data.dropna(axis=0,how='any')

    if volum > 0:
        volume_data =get_stock_history.get_volume(volum * 10000,tools.changeDateMonth(date,0),pick_data,mypick.check_volum_Max.isChecked())
        pick_data = tools.MixDataFrames({'pick':pick_data,'volumeData':volume_data})
        pick_data = pick_data.dropna(axis=0,how='any')

    print("總挑選數量:" + str(len(pick_data)))
    mypick.treeView_pick.setModel(creat_treeView_model(mypick.treeView_pick,pick_titalList))#設定treeView功能
    set_treeView2(mypick.treeView_pick.model(),pick_data)
#第3頁的UI
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
        _data = backtest_stock.backtest_monthRP_Up_Fast(BackTestParameter())
        df.draw_backtest(_data)
def button_backtest_click2():#PER PBR 回測開始紐
    backtest_stock.set_check(mybacktest.check_monthRP_pick.isChecked(),
                                mybacktest.check_PER_pick.isChecked(),
                                mybacktest.check_volume_pick.isChecked(),
                                mybacktest.check_pickOneStock.isChecked(),
                                mybacktest.check_price_pick.isChecked(),
                                mybacktest.check_PBR_pick.isChecked(),
                                mybacktest.check_ROE_pick.isChecked())
    _data = backtest_stock.backtest_PERandPBR_Fast(BackTestParameter())
    df.draw_backtest(_data)
def button_backtest_click3():#定期定額
    _data = backtest_stock.backtest_Regular_quota_Fast(BackTestParameter())
    df.draw_backtest(_data)
def button_backtest_click4():#創新高
    backtest_stock.set_check(mybacktest.check_monthRP_pick.isChecked(),
                                mybacktest.check_PER_pick.isChecked(),
                                mybacktest.check_volume_pick.isChecked(),
                                mybacktest.check_pickOneStock.isChecked(),
                                mybacktest.check_price_pick.isChecked(),
                                mybacktest.check_PBR_pick.isChecked(),
                                mybacktest.check_ROE_pick.isChecked())
    _data = backtest_stock.backtest_Record_high_Fast(BackTestParameter())
    df.draw_backtest(_data)
def button_backtest_click5():#KD篩選
    backtest_stock.set_check(mybacktest.check_monthRP_pick.isChecked(),
                                mybacktest.check_PER_pick.isChecked(),
                                mybacktest.check_volume_pick.isChecked(),
                                mybacktest.check_pickOneStock.isChecked(),
                                mybacktest.check_price_pick.isChecked(),
                                mybacktest.check_PBR_pick.isChecked(),
                                mybacktest.check_ROE_pick.isChecked())
    _data = backtest_stock.backtest_KD_pick(BackTestParameter())
    df.draw_backtest(_data)
def button_backtest_click6():#PEG篩選
    backtest_stock.set_check(mybacktest.check_monthRP_pick.isChecked(),
                                mybacktest.check_PER_pick.isChecked(),
                                mybacktest.check_volume_pick.isChecked(),
                                mybacktest.check_pickOneStock.isChecked(),
                                mybacktest.check_price_pick.isChecked(),
                                mybacktest.check_PBR_pick.isChecked(),
                                mybacktest.check_ROE_pick.isChecked())
    _data = backtest_stock.backtest_PEG_pick_Fast(BackTestParameter())
    df.draw_backtest(_data)
    
#取得月營收的資料
def get_monthRP(date_end,date_start,Number):#end = 後面時間 start = 前面時間 Number = 股票號碼
    date_end_str = str(date_end.year()) + '-' + str(date_end.month()) + '-' + str(date_end.day())
    m_date_end = datetime.strptime(date_end_str,"%Y-%m-%d")

    date_start_str = str(date_start.year()) + '-' + str(date_start.month()) + '-' + str(date_start.day())
    m_date_start = datetime.strptime(date_start_str,"%Y-%m-%d")

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
    # if m_date_start>m_date_end and m_date_end.year == m_date_start.year:
    #     try:
    #         monthRP_temp = get_stock_history.get_stock_monthly_report(stockNum,m_date_start)
    #         monthRP_temp.insert(0,'日期',m_date_start)
    #         monthRP_temp['當月營收'] = int(monthRP_temp['當月營收'])/1000
    #         data_result = pd.concat([data_result,monthRP_temp])
    #     except:
    #         print(str(m_date_start) + "月營收未出喔")
    data_result.set_index('日期',inplace=True)
    return data_result
#取得殖利率的資料
def get_Dividend_yield(date_end,date_start,Number):#end = 後面時間 start = 前面時間 Number = 股票號碼
    date_end_str = str(date_end.year()) + '-' + str(date_end.month()) + '-' + str(date_end.day())
    m_date_end = datetime.strptime(date_end_str,"%Y-%m-%d")

    date_start_str = str(date_start.year()) + '-' + str(date_start.month()) + '-' + str(date_start.day())
    m_date_start = datetime.strptime(date_start_str,"%Y-%m-%d")

    stockNum = Number
    data_result = None
    
    while (m_date_start <= m_date_end):
         #週末直接跳過
        if m_date_start.isoweekday() in [6,7]:
            print(str(m_date_start) + 'is 星期' + str(m_date_start.isoweekday()))
            m_date_start = tools.backWorkDays(m_date_start,-1)#加一天
            continue
        #先看看台積有沒有資料，如果沒有表示這天是非週末假日跳過 
        if get_stock_history.get_stock_price(2330,m_date_start,get_stock_history.stock_data_kind.AdjClose) == None:
            print(str(m_date_start) + "這天沒開市")
            m_date_start = tools.backWorkDays(m_date_start,-1)#加一天
            continue
        try:
            Dividend_yield_temp = get_stock_history.get_stock_yield(stockNum,m_date_start)
        except:
            print(str(m_date_start) + "殖利率未出喔")
            m_date_start = tools.backWorkDays(m_date_start,-1)#加一天
            continue
        Dividend_yield_temp.insert(0,'Date',m_date_start)
        data_result = pd.concat([data_result,Dividend_yield_temp])
        m_date_start = tools.backWorkDays(m_date_start,-1)#加一天
    data_result.set_index('Date',inplace=True)
    return data_result
#取得營業利益率的資料
def get_Operating_Margin(date_end,date_start,Number):#end = 後面時間 start = 前面時間 Number = 股票號碼
    date_end_str = str(date_end.year()) + '-' + str(date_end.month()) + '-' + str(date_end.day())
    m_date_end = datetime.strptime(date_end_str,"%Y-%m-%d")

    date_start_str = str(date_start.year()) + '-' + str(date_start.month()) + '-' + str(date_start.day())
    m_date_start = datetime.strptime(date_start_str,"%Y-%m-%d")

    m_date_start_day = int(date_start.day())
    if m_date_start_day > 28:
        m_date_start_day = 28
    stockNum = Number
    data_result = None
    while (m_date_start <= m_date_end):
        #週末直接跳過
        if m_date_start.isoweekday() in [6,7]:
            print(str(m_date_start) + 'is 星期' + str(m_date_start.isoweekday()))
            m_date_start = tools.backWorkDays(m_date_start,1)#加一天
            continue
        #先看看台積有沒有資料，如果沒有表示這天是非週末假日跳過 
        if get_stock_history.get_stock_price(2330,m_date_start,get_stock_history.stock_data_kind.AdjClose) == None:
            print(str(m_date_start) + "這天沒開市")
            m_date_start = tools.backWorkDays(m_date_start,1)#加一天
            continue
        try:
            Operating_Margin_temp = get_stock_history.get_stock_Operating(stockNum,m_date_start)
        except:
            print(str(m_date_start) + "營業利益率未出喔")
            m_date_start = tools.backWorkDays(m_date_start,1)#加一天
            break
            continue
        Operating_Margin_temp.insert(0,'Date',m_date_start)
        data_result = pd.concat([data_result,Operating_Margin_temp])
        m_date_start = tools.changeDateMonth(m_date_start,3)#加一季
        m_date_start = m_date_start.replace(day = m_date_start_day)
    data_result.set_index('Date',inplace=True)
    return data_result
#取得營業現金流的資料
def get_SCF(date_end,date_start,Number):#end = 後面時間 start = 前面時間 Number = 股票號碼
    date_end_str = str(date_end.year()) + '-' + str(date_end.month()) + '-' + str(date_end.day())
    m_date_end = datetime.strptime(date_end_str,"%Y-%m-%d")

    date_start_str = str(date_start.year()) + '-' + str(date_start.month()) + '-' + str(date_start.day())
    m_date_start = datetime.strptime(date_start_str,"%Y-%m-%d")

    m_date_start_day = int(date_start.day())
    if m_date_start_day > 28:
        m_date_start_day = 28
    stockNum = Number
    data_result = None
    while (m_date_start <= m_date_end):
        #週末直接跳過
        if m_date_start.isoweekday() in [6,7]:
            print(str(m_date_start) + 'is 星期' + str(m_date_start.isoweekday()))
            m_date_start = tools.backWorkDays(m_date_start,1)#加一天
            continue
        #先看看台積有沒有資料，如果沒有表示這天是非週末假日跳過 
        if get_stock_history.get_stock_price(2330,m_date_start,get_stock_history.stock_data_kind.AdjClose) == None:
            print(str(m_date_start) + "這天沒開市")
            m_date_start = tools.backWorkDays(m_date_start,1)#加一天
            continue
        try:
            Operating_Margin_temp = get_stock_history.get_stock_SCF(stockNum,m_date_start)
        except:
            print(str(m_date_start) + "營業現金流未出喔")
            m_date_start = tools.backWorkDays(m_date_start,1)#加一天
            break
            continue
        Operating_Margin_temp.insert(0,'Date',m_date_start)
        data_result = pd.concat([data_result,Operating_Margin_temp])
        m_date_start = tools.changeDateMonth(m_date_start,3)#加一季
        m_date_start = m_date_start.replace(day = m_date_start_day)
    data_result.set_index('Date',inplace=True)
    return data_result
#取得自由現金流的資料
def get_FreeSCF_Margin(date_end,date_start,Number):#end = 後面時間 start = 前面時間 Number = 股票號碼
    date_end_str = str(date_end.year()) + '-' + str(date_end.month()) + '-' + str(date_end.day())
    m_date_end = datetime.strptime(date_end_str,"%Y-%m-%d")

    date_start_str = str(date_start.year()) + '-' + str(date_start.month()) + '-' + str(date_start.day())
    m_date_start = datetime.strptime(date_start_str,"%Y-%m-%d")

    m_date_start_day = int(date_start.day())
    if m_date_start_day > 28:
        m_date_start_day = 28
    stockNum = int(Number)
    data_result = pd.DataFrame(columns = ['Date','FreeCF'])
    while (m_date_start <= m_date_end):
        #週末直接跳過
        if m_date_start.isoweekday() in [6,7]:
            print(str(m_date_start) + 'is 星期' + str(m_date_start.isoweekday()))
            m_date_start = tools.backWorkDays(m_date_start,1)#加一天
            continue
        #先看看台積有沒有資料，如果沒有表示這天是非週末假日跳過 
        if get_stock_history.get_stock_price(2330,m_date_start,get_stock_history.stock_data_kind.AdjClose) == None:
            print(str(m_date_start) + "這天沒開市")
            m_date_start = tools.backWorkDays(m_date_start,1)#加一天
            continue
        try:
            FreeSCF_Margin_temp = get_stock_history.get_stock_SCF(stockNum,m_date_start)
        except:
            print(str(m_date_start) + "現金流量表未出喔")
            m_date_start = tools.backWorkDays(m_date_start,1)#加一天
            continue
        if FreeSCF_Margin_temp.empty:
            print(str(m_date_start) + "現金流量表未出喔")
            break
        Temp_Business = int(FreeSCF_Margin_temp.at[stockNum,'營業活動之淨現金流入（流出）'])
        Temp_Invest = int(FreeSCF_Margin_temp.at[stockNum,'投資活動之淨現金流入（流出）'])
        Temp_Free = int(Temp_Business+Temp_Invest)
        data_result = data_result.append({'Date':m_date_start,'FreeCF':Temp_Free},ignore_index=True)
        m_date_start = tools.changeDateMonth(m_date_start,3)#加一季
        m_date_start = m_date_start.replace(day = m_date_start_day)
    data_result.set_index('Date',inplace=True)
    return data_result
#取得各種財報數字篩選
def get_financial_statement(date,GPM = '0' ,OPR ='0' ,EPS ='0',RPS ='0'):
    resultAllFS1 = []
    resultAllFS2 = []
    resultAllFS3 = []
    this = pd.DataFrame()
    FS_type = get_stock_history.FS_type.PLA
    volume_date = date
    for i in range(12):
        try:
            this = get_stock_history.get_allstock_financial_statement(volume_date,FS_type)
            if this.empty:
                volume_date = tools.changeDateMonth(volume_date,-1)
                continue
            print(str(volume_date.month)+ "月財務報告ＯＫ")
            break
        except:
            print(str(volume_date.month)+ "月財務報告未出跳下一個月")
            volume_date = tools.changeDateMonth(volume_date,-1)
            continue
    this1 = this["毛利率(%)"] > float(GPM)
    this2 = this["營業利益率(%)"] > float(OPR)
    resultAllFS1 = this[this1 & this2]
            
    FS_type = get_stock_history.FS_type.BS
    this = get_stock_history.get_allstock_financial_statement(volume_date,FS_type)
    this1 = this["每股參考淨值"] > float(RPS)
    resultAllFS2 = this[this1]

    FS_type = get_stock_history.FS_type.CPL
    this = get_stock_history.get_allstock_financial_statement(volume_date,FS_type)
    this1 = this["基本每股盈餘（元）"] > float(EPS)
    resultAllFS3 = this[this1]

    resultAllFS_temp = tools.MixDataFrames({'resultAllFS1':resultAllFS1,'resultAllFS2':resultAllFS2})
    resultAllFS = tools.MixDataFrames({'resultAllFS3':resultAllFS3,'resultAllFS_temp':resultAllFS_temp})

    return resultAllFS
#取得營業利益率成長率資料(與去年同季相比)
def get_Operating_Margin_Ratio(date_end,date_start,Number):
    date_end_str = str(date_end.year()) + '-' + str(date_end.month()) + '-' + str(date_end.day())
    m_date_end = datetime.strptime(date_end_str,"%Y-%m-%d")

    date_start_str = str(date_start.year()) + '-' + str(date_start.month()) + '-' + str(date_start.day())
    m_date_start = datetime.strptime(date_start_str,"%Y-%m-%d")

    m_date_start_day = int(date_start.day())
    if m_date_start_day > 28:
        m_date_start_day = 28
    stockNum = Number
    data_result = None
    while (m_date_start <= m_date_end):
        #週末直接跳過
        if m_date_start.isoweekday() in [6,7]:
            print(str(m_date_start) + 'is 星期' + str(m_date_start.isoweekday()))
            m_date_start = tools.backWorkDays(m_date_start,1)#加一天
            continue
        #先看看台積有沒有資料，如果沒有表示這天是非週末假日跳過 
        if get_stock_history.get_stock_price(2330,m_date_start,get_stock_history.stock_data_kind.AdjClose) == None:
            print(str(m_date_start) + "這天沒開市")
            m_date_start = tools.backWorkDays(m_date_start,1)#加一天
            continue
        try:
            Operating_Margin_now = get_stock_history.get_stock_Operating(stockNum,m_date_start)
            Operating_Margin_old = get_stock_history.get_stock_Operating(stockNum,tools.changeDateMonth(m_date_start,-12))
        except:
            print(str(m_date_start) + "營業利益率未出喔")
            m_date_start = tools.backWorkDays(m_date_start,1)#加一天
            continue
        if Operating_Margin_now.empty:
            print(str(m_date_start) + "營業利益率未出喔")
            m_date_start = tools.changeDateMonth(m_date_start,3)#加一季
            continue
        Operating_Margin_temp = ((Operating_Margin_now['營業利益率(%)'] - Operating_Margin_old['營業利益率(%)'])/Operating_Margin_old['營業利益率(%)']) * 100
        Operating_Margin_now.insert(0,'營業利益率成長率(%)',Operating_Margin_temp)
        Operating_Margin_now.insert(0,'Date',m_date_start)
        data_result = pd.concat([data_result,Operating_Margin_now])
        m_date_start = tools.changeDateMonth(m_date_start,3)#加一季
        m_date_start = m_date_start.replace(day = m_date_start_day)
    data_result.set_index('Date',inplace=True)
    return data_result
#取得ROE資料
def get_ROE(date_end,date_start,Number):
    date_end_str = str(date_end.year()) + '-' + str(date_end.month()) + '-' + str(date_end.day())
    m_date_end = datetime.strptime(date_end_str,"%Y-%m-%d")

    date_start_str = str(date_start.year()) + '-' + str(date_start.month()) + '-' + str(date_start.day())
    m_date_start = datetime.strptime(date_start_str,"%Y-%m-%d")

    m_date_start_day = int(date_start.day())
    if m_date_start_day > 28:
        m_date_start_day = 28
    stockNum = int(Number)
    data_result = pd.DataFrame(columns = ['Date','ROE'])
    while (m_date_start <= m_date_end):
        #週末直接跳過
        if m_date_start.isoweekday() in [6,7]:
            print(str(m_date_start) + 'is 星期' + str(m_date_start.isoweekday()))
            m_date_start = tools.backWorkDays(m_date_start,1)#加一天
            continue
        #先看看台積有沒有資料，如果沒有表示這天是非週末假日跳過 
        if get_stock_history.get_stock_price(2330,m_date_start,get_stock_history.stock_data_kind.AdjClose) == None:
            print(str(m_date_start) + "這天沒開市")
            m_date_start = tools.backWorkDays(m_date_start,1)#加一天
            continue
        try:
            BOOK_data = get_stock_history.get_allstock_financial_statement(m_date_start,get_stock_history.FS_type.BS)
            CPL_data = get_stock_history.get_allstock_financial_statement(m_date_start,get_stock_history.FS_type.CPL)
        except:
            print(str(m_date_start) + "營業利益率未出喔")
            m_date_start = tools.backWorkDays(m_date_start,1)#加一天
            continue
        if BOOK_data.empty or CPL_data.empty:
            break
        Temp_Book = int(BOOK_data.at[stockNum,'權益總額']) 
        Temp_CPL = int(CPL_data.at[stockNum,"本期綜合損益總額（稅後）"])
        Temp_ROE = round((Temp_CPL/Temp_Book),4) * 100
        data_result = data_result.append({'Date':m_date_start,'ROE':Temp_ROE},ignore_index=True)
        m_date_start = tools.changeDateMonth(m_date_start,3)#加一季
        m_date_start = m_date_start.replace(day = m_date_start_day)
    data_result.set_index('Date',inplace=True)
    return data_result

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
            array_Num.append(float(row["PEG"]))
        except:
            array_Num.append(float(0))
        try:
            array_Num.append(float(row["ROE"]))
        except:
            array_Num.append(float(0))
        try:
            array_Num.append(float(row["殖利率"]))
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
#異步更新所有台股資料
def Update_StockData_threading(str_date):
    lock.acquire()
    for key,value in get_stock_info.ts.codes.items():
        if value.market == "上市" and len(value.code) == 4:
            if get_stock_history.check_no_use_stock(value.code) == True:
                print('get_stock_price: ' + str(value.code) + ' in no use')
                continue
            m_history = get_stock_history.get_stock_history(value.code,str_date)
            print("get " + str(value.code) + " info susess!")
    #存更新日期
    get_stock_info.Update_date = str(datetime.today())[0:10]
    get_stock_info.Save_Update_date()    
    lock.acquire()

def Init_mainWindow():#初始化mainwindow
    myshow.button_addStock.clicked.connect(button_addStock_click)#設定button功能
    myshow.button_deletStock.clicked.connect(button_deletStock_click)#設定button功能
    myshow.treeView.setModel(creat_treeView_model(myshow.treeView,main_titalList,False))#設定treeView功能
    myshow.button_moveToInput.clicked.connect(button_moveToInput_click)#設定button功能
    myshow.button_getStockHistory.clicked.connect(button_getStockHistory)#設定button功能
    myshow.button_openPickWindow.clicked.connect(button_openPickWindow_click)#設定button功能
    myshow.button_getMonthRP.clicked.connect(button_monthRP_click)#設定button功能
    myshow.button_getDividend_yield.clicked.connect(button_Dividend_yield_click)#設定button功能
    myshow.button_runSchedule.clicked.connect(update_stock_info.RunScheduleNow)#設定button功能
    #myshow.button_runSchedule.clicked.connect(tools.get_SP500_list)設定button功能
    myshow.button_stopSchedule.clicked.connect(update_stock_info.stopThreadSchedule)#設定button功能
    myshow.button_getOperating_Margin.clicked.connect(button_Operating_Margin_click)#設定button功能
    myshow.button_Operating_Margin_Ratio.clicked.connect(button_Operating_Margin_Ratio_click)
    myshow.button_getROE.clicked.connect(button_ROE_Ratio_click)
    myshow.button_getFreeCF.clicked.connect(button_FreeSCF_click)
    myshow.button_getSCF.clicked.connect(button_SCF_click)
    #設定日期
    Date = datetime.strptime(get_stock_info.Update_date[0:10],"%Y-%m-%d")
    date = QtCore.QDate(Date.year,Date.month,Date.day)
    today = QtCore.QDate(datetime.today().year,datetime.today().month,datetime.today().day)
    myshow.date_startDate.setMaximumDate(today)
    myshow.date_startDate.setMinimumDate(QtCore.QDate(2000,1,1))
    enddate = tools.changeDateMonth(tools.QtDate2DateTime(date),-6)
    yesterday = tools.backWorkDays(datetime.today(),1)
    end_yesterday = tools.changeDateMonth(yesterday,-6)
    myshow.date_startDate.setDate(QtCore.QDate((end_yesterday.year),(end_yesterday.month),(end_yesterday.day)))
    myshow.date_endDate.setMaximumDate(today)
    myshow.date_endDate.setMinimumDate(QtCore.QDate(2001,1,1))
    myshow.date_endDate.setDate(QtCore.QDate((yesterday.year),(yesterday.month),(yesterday.day)))
    myshow.input_SMA1.setPlainText("5")
    myshow.input_SMA2.setPlainText("20")
    myshow.input_SMA3.setPlainText("60")
def Init_pickWindow():#初始化挑股票畫面
    mypick.button_pick.clicked.connect(button_pick_click)#設定button功能
    mypick.button_moveToInput.clicked.connect(button_moveToInputFromPick_click)#設定button功能
    mypick.treeView_pick.setModel(creat_treeView_model(mypick.treeView_pick,pick_titalList))#設定treeView功能
    mypick.button_pick_2.clicked.connect(button_monthRP_Up_click)#設定button功能
    mypick.button_openBackWindow.clicked.connect(button_openBackWindow_click)#設定button功能
    mypick.input_EPS.setValue(0)
    mypick.input_GPM.setValue(0)
    mypick.input_OPR.setValue(0)
    mypick.input_RPS.setValue(0)
    mypick.input_OMGR.setValue(0)
    mypick.input_monthRP_smoothAVG.setValue(0)
    mypick.input_monthRP_UpMpnth.setValue(0)
    mypick.input_volum.setValue(0)
    mypick.input_price_high.setValue(0)
    mypick.input_price_low.setValue(0)
    mypick.input_PBR_high.setValue(0)
    mypick.input_PBR_low.setValue(0)
    mypick.input_PER_high.setValue(0)
    mypick.input_PER_low.setValue(0)
    mypick.input_ROE_high.setValue(0)
    mypick.input_ROE_low.setValue(0)
    mypick.input_yiled_high.setValue(0)
    mypick.input_yiled_low.setValue(0)
    mypick.input_flash_Day.setValue(0)
    mypick.input_record_Day.setValue(0)
    mypick.input_PEG_high.setValue(0)
    mypick.input_PEG_low.setValue(0)
def Init_backtestWindow():#初始化回測畫面
    mybacktest.button_backtest.clicked.connect(button_backtest_click)#設定button功能
    mybacktest.button_backtest_2.clicked.connect(button_backtest_click2)
    mybacktest.button_backtest_3.clicked.connect(button_backtest_click3)
    mybacktest.button_backtest_4.clicked.connect(button_backtest_click4)
    mybacktest.button_backtest_5.clicked.connect(button_backtest_click5)
    mybacktest.button_backtest_6.clicked.connect(button_backtest_click6)
    date = QtCore.QDate(datetime.today().year,datetime.today().month,datetime.today().day) 

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
    mybacktest.input_stockNumber.setPlainText('2330')
    mybacktest.input_yield_start.setPlainText('0')
    mybacktest.input_yield_end.setPlainText('0')
    mybacktest.input_buyDay.setPlainText('15')
    mybacktest.input_RecordHigh.setPlainText('60')

app = QtWidgets.QApplication(sys.argv)
myshow = MyWindow()
mypick = MyPickWindow()
mybacktest = MyBacktestWindow()
#從這中間加ＵＩ設定---------------
Init_mainWindow()
Init_pickWindow()
Init_backtestWindow()
#從這中間加ＵＩ設定---------------
update_stock_info.RunMysql()
myshow.show()
sys.exit(app.exec_())



