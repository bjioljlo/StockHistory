from tkinter import N
import requests
from datetime import datetime,timedelta
import pandas as pd
import talib
import get_stock_info
import os
import numpy as np
from io import StringIO
import time
from enum import Enum
import tools
import update_stock_info
import Infomation_type as info

fileName_monthRP = "monthRP"
fileName_stockInfo = "stockInfo"
fileName_yield = "yieldInfo"
fileName_season = "seasonInfo"
fileName_index = "indexInfo"

no_use_stock = []

five_word_ETF = ['00692','00878','00646','00881','00733']

Holiday_trigger = False

load_memery = {}

class Season_Report():
    def __init__(self,_FS_type:info.FS_type,_type:Enum) -> None:
        self._FS_type = _FS_type
        self._type = _type
    def get_ALL_Report(self,date):
        return get_allstock_financial_statement(date,self._FS_type)
    def get_ReportByType(self,date,_type) -> pd.Series:
        Temp = self.get_ALL_Report(date)
        return Temp[_type.name]
    def get_ReportByNumber(self,date,number:int) -> pd.Series:
        Temp = self.get_ALL_Report(date)
        return Temp[Temp.index == number]
    def get_ReportByTypeAndNumber(self,date,_type,number:int):
        Temp = self.get_ReportByType(date,_type)
        return Temp[_type.name][number]
CPL_RP = Season_Report(info.FS_type.CPL,info.CPL_type)
BS_RP = Season_Report(info.FS_type.BS,info.BS_type)
PLA_RP = Season_Report(info.FS_type.PLA,info.PLA_type)
SCF_RP = Season_Report(info.FS_type.SCF,info.SCF_type)
class Month_Report(Season_Report):
    def __init__(self,_type:Enum) -> None:
        self._type = _type
    def get_ALL_Report(self, date):
        return get_allstock_monthly_report(date)
Month_RP = Month_Report(info.Month_type)
class Day_Report(Season_Report):
    def __init__(self, _type:Enum) -> None:
        self._type = _type
    def get_ALL_Report(self, date):
        return get_allstock_yield(date)
Yield_RP = Day_Report(info.Day_type)

class stock_data_kind(Enum):
    AdjClose = 'Adj Close'
    Volume = 'Volume'

filePath = os.getcwd()#取得目錄路徑


def check_no_use_stock(number):
    try:
        number = int(number)
    except:
        print("check_no_use_stock error:" + number)
        return False
    for num in range(0,no_use_stock.__len__()):
        if(int(number) == no_use_stock[num]):
            print(str(number))
            return True
    return False
def check_ETF_stock(number):
    try:
        number = str(number)
    except:
        print("check_ETF_stock error:" + number)
        return False
    for num in range(0,five_word_ETF.__len__()):
        if(str(number) == five_word_ETF[num]):
            print(str(number))
            return True
    return False

def get_stock_RecordHight(number,date,flashDay,recordDays):#取得number在flashDay天內天是否在recordDays內創新高
    All_data = get_stock_history(number,date+timedelta(days=-200),reGetInfo=False,UpdateInfo=False)
    mask = All_data.index <= date
    data = All_data[mask]
    data = data.sort_index(ascending=False)
    Pass = True
    for index,row in data.iterrows():
        Pass = True
        if check_no_use_stock(number) == True:
            print('get_stock_price: ' + str(number) + ' in no use')
            return False
        Now_day = index
        Now_price = row['Adj Close']
        mask = All_data.index <= Now_day
        data2 = All_data[mask]
        data2 = data2.sort_index(ascending=False)
        for i in range(recordDays):
            try:
                Temp_price = data2.iloc[i+1]['Adj Close']
            except:
                return False
            if Temp_price <= Now_price:
                continue
            else:
                Pass = False
                flashDay = flashDay -1
                if flashDay <= 0:
                    return False
                break
        if Pass:
            return True
def get_stock_MA(number,date,MA_day):#取得某股票某天的均線
    Temp_MA = 0
    Temp_date = date
    Temp_MA_day = MA_day
    All_data = get_stock_history(number,Temp_date+timedelta(days=-100),reGetInfo=False,UpdateInfo=False)
    Temp_MA = talib.SMA(All_data['Adj Close'],Temp_MA_day)[Temp_date]
    return Temp_MA
def get_stock_yield(number,date):#取得某股票某天的殖利率
    data = get_allstock_yield(date)
    if type(number) == str:
        number = int(number)
    mask = data.index == number
    data = data[mask]
    return data
def get_stock_Operating(number,date):#取得營業利益率
    data = get_allstock_financial_statement(date,info.FS_type.PLA)
    if type(number) == str:
        number = int(number)
    mask = data.index == number
    data = data[mask]
    return data
def get_stock_SCF(number,date):#取得現金流量表
    data = get_allstock_financial_statement(date,info.FS_type.SCF)
    if type(number) == str:
        number = int(number)
    mask = data.index == number
    data = data[mask]
    return data
def get_stock_FreeCF(number,date):#取得自由現金流
    try:
        FreeSCF_Margin_temp = SCF_RP.get_ReportByNumber(date,number)
    except:
        print(str(date) + "現金流量表未出喔")
        return None
    if FreeSCF_Margin_temp.empty:
        print(str(date) + "現金流量表未出喔")
        return None
    Temp_Business = int(FreeSCF_Margin_temp.at[number,'營業活動之淨現金流入（流出）'])
    Temp_Invest = int(FreeSCF_Margin_temp.at[number,'投資活動之淨現金流入（流出）'])
    Temp_Free = int(Temp_Business+Temp_Invest)
    return Temp_Free
def get_stock_price(number,date,kind,isSMA = False):#取得某股票某天的ＡＤＪ價格
    global Holiday_trigger
    if check_no_use_stock(number) == True:
        print(''.join(['get_stock_price: ' , str(number) , ' in no use']))
        return None
    stock_data = get_stock_history(number,date,reGetInfo=False,UpdateInfo=False)
    if kind == stock_data_kind.Volume:
        stock_data = get_stock_history(number,tools.backWorkDays(date,15) ,reGetInfo=False,UpdateInfo=False)
        stock_data = tools.smooth_Data(stock_data,5)
    if stock_data.empty == True:
        return None
    result = stock_data[kind.value]
    # if kind == stock_data_kind.Volume:
    #     result = tools.smooth_Data(result,5)
    result = stock_data[stock_data.index == date]
    if result.empty == True:
        if Holiday_trigger == True:
            return None
        if type(date) != str:
            date = tools.DateTime2String(date)
        if datetime.strptime(date,"%Y-%m-%d").isoweekday() in [1,2,3,4,5]:
            stock_data = get_stock_history(number,date,reGetInfo=False,UpdateInfo=False) #只會重新抓硬碟資料
            result = stock_data[stock_data.index == date]
            if result.empty == True:
                print(''.join(['get_stock_price: ','星期',str(datetime.strptime(date,"%Y-%m-%d").isoweekday())]))
                print(''.join(['get_stock_price: ',str(number),'--', date , ' is no data. Its holiday?']))
                Holiday_trigger = True
                return None
        else:
            return None
    result = result[kind.value]
    close = result[date]
    Holiday_trigger = False
    return close
def get_stock_monthly_report(number,start):#爬某月某個股票月營收
    if get_stock_info.ts.codes.__contains__(number) == False:
        print("無此檔股票")
        return
    if int(start.month) == int(datetime.today().month) and int(start.year) == int(datetime.today().year):
        print("本月還沒過完無資資訊")
        return
    if int(start.month) == int(tools.changeDateMonth(datetime.today(),-1).month) and int(datetime.today().day) < 15 and int(start.year) == int(datetime.today().year):
        print("還沒15號沒有上個月的資料")
        return
    if int(start.day) < 15:
        start = start.replace(day = 15)
    # df = get_allstock_monthly_report(start)
    df = Month_RP.get_ALL_Report(start)
    if type(number) == str:
        number = int(number)
    df = df[df.index == number]
    return df
def get_allstock_monthly_report(start):#爬某月所有股票月營收
    if start.day < 15 :#還沒超過15號，拿前兩個月
        print("get_allstock_monthly_report:未到15號取上個月報表")
        start = tools.changeDateMonth(start,-1)
    year = start.year
    m_data = pd.DataFrame()
    fileName = filePath + '/' + fileName_monthRP + '/' + str(start.year)+'-'+str(start.month)+'monthly_report.csv'
    if fileName in load_memery:
        return load_memery[fileName]
    
    #去資料庫抓資料
    m_data = update_stock_info.read_Dividend_yield('Monthly_report_'+ str(start.year) + '_' + str(start.month))
    if m_data.empty == True:
        if os.path.isfile(fileName) == False:
            # 假如是西元，轉成民國
            if year > 1990:
                year -= 1911
            url = 'https://mops.twse.com.tw/nas/t21/sii/t21sc03_'+str(year)+'_'+str(start.month)+'_0.html'
            if year <= 98:
                url = 'https://mops.twse.com.tw/nas/t21/sii/t21sc03_'+str(year)+'_'+str(start.month)+'.html'
            
            # 下載該年月的網站，並用pandas轉換成 dataframe
            r = requests.get(url, headers = tools.get_random_Header())
            r.encoding = 'big5-hkscs'

            dfs = pd.read_html(StringIO(r.text), encoding='big-5')

            df = pd.concat([df for df in dfs if df.shape[1] <= 11 and df.shape[1] > 5])
            
            if 'levels' in dir(df.columns):
                df.columns = df.columns.get_level_values(1)
            else:
                df = df[list(range(0,10))]
                column_index = df.index[(df[0] == '公司代號')][0]
                df.columns = df.iloc[column_index]
            
            df['當月營收'] = pd.to_numeric(df['當月營收'], 'coerce')
            df = df[~df['當月營收'].isnull()]
            df = df[df['公司代號'] != '合計']
            
            df.to_csv(fileName,index = False)
            # 偽停頓
            time.sleep(1.5)
            
        m_data = pd.read_csv(fileName)
        m_data.drop(m_data.tail(1).index,inplace=True)
        #整理一下資料
        m_data.rename(columns = {"公司代號":"code"},inplace = True)
        m_data[["code"]] = m_data[["code"]].astype(int)
        m_data.set_index("code",inplace = True)
        #存到資料庫
        update_stock_info.saveTable('Monthly_report_'+ str(start.year) + '_' + str(start.month),m_data)
    load_memery[fileName] = m_data
    return m_data      
def get_allstock_financial_statement(start,type):#爬某季所有股票歷史財報
    print("get_allstock_financial_statement:" + str(type))
    season = int(((start.month - 1)/3)+1)
    Temp_data = pd.DataFrame()
    if tools.CheckFS_season(start) == False:
        print('Season rp is no data yet!')
        return pd.DataFrame()
    fileName = filePath + '/' + fileName_season + '/' + str(start.year)+"-season"+str(season)+"-"+type.value+".csv"
    if fileName in load_memery:
        return load_memery[fileName]
    Temp_data = update_stock_info.read_Dividend_yield(str(start.year)+"-season"+str(season)+"-"+type.value)
    if Temp_data.empty == True:
        if os.path.isfile(fileName) == True:
            print("已經有" + str(start.month)+ "月財務報告")
        financial_statement(start.year,season,type)
        print("下載" + str(start.month)+ "月財務報告ＯＫ")
    if Temp_data.empty == True:
        stock = pd.read_csv(fileName)
        #整理一下資料
        stock.rename(columns = {"公司代號":"code"},inplace = True)
        stock.set_index("code",inplace = True)
        if info.FS_type.SCF == type:
            if stock["投資活動之淨現金流入（流出）"].dtype == object: 
                stock["投資活動之淨現金流入（流出）"] = pd.to_numeric(stock["投資活動之淨現金流入（流出）"].str.replace('--', '0'))
            if stock["營業活動之淨現金流入（流出）"].dtype == object: 
                stock["營業活動之淨現金流入（流出）"] = pd.to_numeric(stock["營業活動之淨現金流入（流出）"].str.replace('--', '0'))
            if stock["籌資活動之淨現金流入（流出）"].dtype == object: 
                stock["籌資活動之淨現金流入（流出）"] = pd.to_numeric(stock["籌資活動之淨現金流入（流出）"].str.replace('--', '0'))
        update_stock_info.saveTable(str(start.year)+"-season"+str(season)+"-"+type.value,stock)
    else:
        stock = Temp_data
    load_memery[fileName] = stock
    return stock
def get_allstock_yield(start):#爬某天所有股票殖利率
    fileName = filePath + '/' + fileName_yield + '/' + str(start.year) + '-' + str(start.month) + '-' + str(start.day) + '_Dividend_yield' 
    m_yield = pd.DataFrame()
    if fileName in load_memery:
        return load_memery[fileName]
    #去資料庫抓資料
    m_yield = update_stock_info.read_Dividend_yield('Dividend_yield_'+ str(start.year) + '_' + str(start.month) + '_' + str(start.day))

    if m_yield.empty == True:
        if os.path.isfile(fileName + '.csv') == False:
            url = 'https://www.twse.com.tw/exchangeReport/BWIBBU_d?response=csv&date=' + str(start.year)+str(start.month).zfill(2)+str(start.day).zfill(2)+ '&selectType=ALL'
            response = requests.get(url,tools.get_random_Header())
            save_stock_file(fileName,response,1,2)
            # 偽停頓
            time.sleep(1)
        try:
            m_yield = pd.read_csv(fileName + '.csv')
        except:
            m_yield = pd.read_csv(fileName + '.csv',encoding = 'ANSI')
        #整理一下資料
        m_yield.rename(columns = {"證券代號":"code"},inplace = True)
        m_yield.set_index("code",inplace = True)
        #存到資料庫
        update_stock_info.saveTable('Dividend_yield_'+ str(start.year) + '_' + str(start.month) + '_' + str(start.day),m_yield)
    load_memery[fileName] = m_yield
    return m_yield
def get_stock_history(number,start,reGetInfo = False,UpdateInfo = True) -> pd.DataFrame:#爬某個股票的歷史紀錄
    print(''.join(["取得" , str(number) , "的資料從" , str(start) ,"到今天"]))
    start_time = start
    if type(start_time) == str:
        start_time  = datetime.strptime(start_time,"%Y-%m-%d")
    if type(number) != str:
        number = str(number)
    data_time = datetime.strptime('2005-1-1',"%Y-%m-%d")
    now_time = datetime.today()
    result = pd.DataFrame()

    if get_stock_info.ts.codes.__contains__(number) == False:
        print("無此檔股票")
        return result
    if start_time < data_time:
        print('日期請大於西元2000年')
        return

    m_history = load_stock_file(filePath +'/' + fileName_stockInfo  + '/' + str(number) + '_TW.csv',str(number))
    
    if m_history.empty == True:
        if os.path.isfile(filePath +'/' + fileName_stockInfo  + '/' + str(number) + '_TW.csv') == False:
            # 去ＹＦ讀取資料
            update_stock_info.yf_info(str(number) + info.local_type.Taiwan)
            # 偽停頓
            time.sleep(1.5)
        else:
            if reGetInfo == True:
                # 去ＹＦ讀取資料
                update_stock_info.yf_info(str(number) + info.local_type.Taiwan)
                # 偽停頓
                time.sleep(1.5)
        m_history = load_stock_file(filePath +'/' + fileName_stockInfo  + '/' + str(number) + '_TW.csv',str(number))
       
    mask = m_history.index >= start_time
    result = m_history[mask]
    result = result.dropna(axis = 0,how = 'any')
    return result
def get_stock_AD_index(date,getNew = False):#取得上漲和下跌家數
    print('get_stock_AD_index')
    ADindex_result = pd.DataFrame(columns=['Date','上漲','下跌']).set_index('Date')
    if type(date) == str:
        date = datetime.strptime(date,"%Y-%m-%d")
    time = date 
    str_date = tools.DateTime2String(time)
    time_yesterday = tools.backWorkDays(time,1)

    while (get_stock_price(2330,time_yesterday,stock_data_kind.AdjClose) == None):
        time_yesterday = tools.backWorkDays(time_yesterday,1)#加一天
    
    str_yesterday = tools.DateTime2String(time_yesterday)
    fileName = filePath +'/' + fileName_index + '/' + 'AD_index'
    
    ADindex_result = load_other_file(fileName,'AD_index')
    if ADindex_result.empty == True:
        if os.path.isfile(fileName + '.csv') == True:
            ADindex_result = pd.read_csv(fileName + '.csv', index_col='Date', parse_dates=['Date'])
            load_memery[fileName] = ADindex_result
        else:
            print('no AD_index csv file')
            
    up = 0
    down = 0
    if ADindex_result.empty == False and (ADindex_result.index == time).__contains__(True):
        return ADindex_result[ADindex_result.index == time]
    for key,value in get_stock_info.ts.codes.items():
        if value.market == "上市" and len(value.code) == 4 and value.type == "股票":
            if check_no_use_stock(value.code) == True:
                print('get_stock_price: ' + str(value.code) + ' in no use')
                continue
            #====test 測完請拿掉
            # if int(value.code) < 9000:
            #     continue
            #====test 測完請拿掉
            m_history = get_stock_history(value.code,str_yesterday,reGetInfo=False,UpdateInfo=False)['Close']
            try:
                if m_history[str_yesterday] > m_history[str_date]:
                    down = down + 1
                elif m_history[str_yesterday] < m_history[str_date]:
                    up = up + 1
            except:
                print("get " + str(value.code) + " info fail!")
                m_temp = get_stock_history(2330,str_yesterday,reGetInfo=False,UpdateInfo=False)['Close']
                if (m_temp.index == time).__contains__(True) != True:
                    return pd.DataFrame()
                m_temp = get_stock_history(2330,str_date,reGetInfo=False,UpdateInfo=False)['Close']
                if (m_temp.index == time).__contains__(True) != True:
                    return pd.DataFrame()
    ADindex_result_new = pd.DataFrame({'Date':[time],'上漲':[up],'下跌':[down]}).set_index('Date')
    ADindex_result = ADindex_result.append(ADindex_result_new)
    ADindex_result = ADindex_result.sort_index()
    update_stock_info.saveTable('AD_index',ADindex_result)
    load_memery[fileName] = ADindex_result
    df = ADindex_result[ADindex_result.index == time]
    return df
def get_ADL_index(date,ADL_yesterday):#取得騰落數值
    ADL_today = get_stock_AD_index(date)
    if ADL_today.empty == True:
        return None
    ADL_today = ADL_today['上漲'] - ADL_today['下跌']
    return ADL_yesterday + ADL_today[date]
def get_ADLs_index(date):#取得騰落百分比
    ADLs_today = get_stock_AD_index(date)
    if ADLs_today.empty == True:
        return None
    ADLs_today = (ADLs_today['上漲']/(ADLs_today['上漲']+ADLs_today['下跌'])) - 0.5
    return float(ADLs_today)
def get_Operating_Margin_up(number,date):#取得營業利益成長率
    m_date_start = date
    data_result = None
    Timer = 2
    if type(date) == str:
        m_date_start = datetime.strptime(date,"%Y-%m-%d")
    Operating_Margin_now = get_stock_Operating(number,m_date_start)
    Operating_Margin_old = get_stock_Operating(number,tools.changeDateMonth(m_date_start,-12))
    while Operating_Margin_now.empty:
        print("日期:"+str(m_date_start)+" ("+ str(number) + ")的營業利益率未出喔")
        m_date_start = tools.changeDateMonth(m_date_start,-3)
        Operating_Margin_now = get_stock_Operating(number,m_date_start)
        Operating_Margin_old = get_stock_Operating(number,tools.changeDateMonth(m_date_start,-12))
        if Timer == 0:
            break
        Timer = Timer - 1
    Operating_Margin_temp = ((Operating_Margin_now['營業利益率(%)'] - Operating_Margin_old['營業利益率(%)'])/Operating_Margin_old['營業利益率(%)']) * 100
    Operating_Margin_now.insert(0,'營業利益率成長率(%)',Operating_Margin_temp)
    data_result = pd.concat([data_result,Operating_Margin_now])
    return data_result
def get_Operating_Margin_up(date):#取得營業利益成長率
    m_date_start = date
    data_result = pd.DataFrame()
    Timer = 2
    if type(date) == str:
        m_date_start = datetime.strptime(date,"%Y-%m-%d")
    Operating_Margin_now = get_allstock_financial_statement(m_date_start,info.FS_type.PLA)
    Operating_Margin_old = get_allstock_financial_statement(tools.changeDateMonth(m_date_start,-12),info.FS_type.PLA)
    while Operating_Margin_now.empty:
        print("日期:"+str(m_date_start)+" ("+")的營業利益率未出喔")
        m_date_start = tools.changeDateMonth(m_date_start,-3)
        Operating_Margin_now = get_allstock_financial_statement(m_date_start,info.FS_type.PLA)
        Operating_Margin_old = get_allstock_financial_statement(tools.changeDateMonth(m_date_start,-12),info.FS_type.PLA)
        if Timer == 0:
            break
        Timer = Timer - 1
    data_result['營業利益率成長率(%)'] = ((Operating_Margin_now['營業利益率(%)'] - Operating_Margin_old['營業利益率(%)'])/Operating_Margin_old['營業利益率(%)']) * 100
    return data_result
def get_stock_ROE(date):#取得ROE
    m_date_start = date
    data_result = pd.DataFrame()
    Timer = 2
    if type(date) == str:
        m_date_start = datetime.strptime(date,"%Y-%m-%d")
    BOOK_data = get_allstock_financial_statement(m_date_start,info.FS_type.BS)
    CPL_data = get_allstock_financial_statement(m_date_start,info.FS_type.CPL)
    if BOOK_data.empty:
        print("日期:"+str(m_date_start)+" ("+")的季報表未出喔")
        return pd.DataFrame()
    data_result['ROE'] = round((CPL_data['本期綜合損益總額（稅後）']/BOOK_data['權益總額']),4) * 100
    return data_result
def get_stock_PEG(number,date):#取得本益成長比
    print(''.join([str(number),':取得PEG在',str(date)]))
    if check_no_use_stock(number) == True:
        print(str(number) + ' in no use')
        return None
    PE_data = get_allstock_yield(date)
    OMUR_data = get_Operating_Margin_up(number,date)
    if OMUR_data.empty == True or PE_data.empty == True :
        return None
    try:
        data_PEG = PE_data.at[number,'本益比'] / OMUR_data.at[number,'營業利益率成長率(%)']
    except KeyError:
        return None
    return data_PEG
def get_stock_PEG(date):#取得本益成長比
    print(''.join(['取得PEG在',str(date)]))
    PE_data = get_allstock_yield(date)
    OMUR_data = get_Operating_Margin_up(date)
    if OMUR_data.empty == True or PE_data.empty == True :
        return None
    try:
        PE_data['PEG'] = PE_data['本益比'] / OMUR_data['營業利益率成長率(%)']
    except KeyError:
        return None
    return PE_data
def get_stock_Debt(date) -> pd.DataFrame:#取得資產負債比率
    print(''.join(['取得資產負債率在',str(date)]))
    Temp = BS_RP.get_ReportByType(date=date,_type=info.BS_type.資產總額)
    Temp_Debt = BS_RP.get_ReportByType(date=date,_type=info.BS_type.負債總額)
    if Temp.empty or Temp_Debt.empty:
        return None
    try:
        Temp_result = Temp_Debt / Temp
    except KeyError:
        return None
    return pd.DataFrame(Temp_result,columns=['資產負債率'])

def save_stock_file(fileName,stockData,start_index = 0,end_index = 0):#存下歷史資料
    with open(fileName + '.csv', 'w') as f:
        if start_index == end_index == 0:
            f.writelines(stockData.text)
        else:
            stringText = stockData.text
            stringText = stringText.replace(",\r\n","\r\n")
            stringText = stringText.replace("-","0")
            for i in range(10):
                stringText = stringText.replace(str(i) + ",",str(i))
            pos = stringText.index('\n')
            pos2 = stringText.rindex('\r\n""\r\n')
            f.writelines(stringText[pos + 1:pos2])
def load_stock_file(fileName,stockName = ''):#讀取歷史資料
    if fileName in load_memery:
        return load_memery[fileName]
    df = pd.DataFrame()
    if stockName != '':
        df = update_stock_info.readStockDay(stockName + info.local_type.Taiwan)
    if df.empty == True:
        try:
            df = pd.read_csv(fileName + '.csv', index_col='Date', parse_dates=['Date'])
        except:
            print("no " + stockName + info.local_type.Taiwan + " csv file")
            return df
        update_stock_info.saveTable(stockName + info.local_type.Taiwan,df)
    
    df = df.dropna(how='any',inplace=False)#將某些null欄位去除
    try:
        df['Volume'] = df['Volume'].astype('int')
    except:
        print('no Volume')
    
    load_memery[fileName] = df
    return df
def delet_stock_file(fileName):#刪除歷史資料
    if os.path.isfile(fileName) == True:
        os.remove(fileName)

#大盤綜合資料-------------   
#取得騰落進階指標資料
def get_ADLs(start_time,end_time):
    now_time = start_time
    data = pd.DataFrame(columns = ['Date','ADLs']).set_index('Date')
    while now_time <= end_time:
        #週末直接跳過
        if now_time.isoweekday() in [6,7]:
            print(str(now_time) + 'is 星期' + str(now_time.isoweekday()))
            now_time = tools.backWorkDays(now_time,-1)#加一天
            continue
        #先看看台積有沒有資料，如果沒有表示這天是非週末假日跳過 
        if get_stock_price(2330,now_time,stock_data_kind.AdjClose) == None:
            print(str(now_time) + "這天沒開市")
            now_time = tools.backWorkDays(now_time,-1)#加一天
            continue
        ADLs_value = get_ADLs_index(now_time)
        if ADLs_value == None:
            now_time = tools.backWorkDays(now_time,-1)#加一天
            continue
        temp_data = pd.DataFrame({'Date':[now_time],'ADLs':[ADLs_value]}).set_index('Date')
        data = data.append(temp_data)
        now_time = tools.backWorkDays(now_time,-1)
    return data
#取得騰落指標資料
def get_ADL(start_time,end_time):
    ADL_yesterday = 0
    #第一天指標為0
    data = pd.DataFrame(columns = ['Date','ADL']).set_index('Date')
    now_time = start_time
    while now_time <= end_time:
        #週末直接跳過
        if now_time.isoweekday() in [6,7]:
            print(str(now_time) + 'is 星期' + str(now_time.isoweekday()))
            now_time = tools.backWorkDays(now_time,-1)#加一天
            continue
        #先看看台積有沒有資料，如果沒有表示這天是非週末假日跳過 
        if get_stock_price(2330,now_time,stock_data_kind.AdjClose) == None:
            print(str(now_time) + "這天沒開市")
            now_time = tools.backWorkDays(now_time,-1)#加一天
            continue

        ADL_value = get_ADL_index(now_time,ADL_yesterday)
        if ADL_value == None:
            now_time = tools.backWorkDays(now_time,-1)#加一天
            continue

        temp_data = pd.DataFrame({'Date':[now_time],'ADL':[ADL_value]}).set_index('Date')
        data = data.append(temp_data)
        ADL_yesterday = ADL_value
        now_time = tools.backWorkDays(now_time,-1)
    return data

#個股篩選-------------  
#取得月營收逐步升高的篩選
def get_monthRP_up(time,avgNum,upNum):#time = 取得資料的時間 avgNum = 平滑曲線月份 upNum = 連續成長月份
    print('get_monthRP_up: start:'+ str(time) )
    fileName ='get_monthRP_up:' + str(time.year) +str(time.month) + str(avgNum) + str(upNum)
    if fileName in load_memery:
        print('get_monthRP_up: end' )
        return load_memery[fileName]
    
    data = {}
    if upNum <= 0 or avgNum <= 0:
        return pd.DataFrame()
    for i in range(avgNum+upNum):
        temp_now = tools.changeDateMonth(time,-(i+1))
        data['%d-%d-01'%(temp_now.year, temp_now.month)] = get_allstock_monthly_report(temp_now)

    result = pd.DataFrame({k:result['當月營收'] for k,result in data.items()}).transpose()
    result.index = pd.to_datetime(result.index)
    result = result.sort_index()
    
    method2 = result.rolling(avgNum,min_periods=avgNum).mean()
    method2 = (method2 > method2.shift()).iloc[-upNum:].sum()
    final_result = method2[method2 >= upNum]
    final_result = pd.DataFrame(final_result)
    try:
        final_result = final_result.drop('全部國內上市公司合計',axis = 0)
    except:
        final_result = final_result

    final_result = final_result.rename(index=int)
    final_result.index.name = 'code'
    load_memery[fileName] = final_result
    print('get_monthRP_up: end' )
    return final_result
#取得同期營業利益成長率升高篩選
def get_OMGR_up(time,upNum):#time = 取得資料的時間 upNum = 連續成長多少季
    print('get_OMGR_up: start:'+ str(time) )
    fileName = "get_OMGR_up_" + str(time.year) + str(time.month) + str(upNum)
    if fileName in load_memery:
        print('get_OMGR_up: end' )
        return load_memery[fileName]
    data = {}
    if upNum <= 0:
        return pd.DataFrame()
    k = 0
    Timer = 2
    for i in range(upNum + 5):
        temp_now = tools.changeDateMonth(time,-((i+k)*3))
        temp_data = get_allstock_financial_statement(temp_now,info.FS_type.PLA)
        while temp_data.empty:
            k = k + 1
            temp_now = tools.changeDateMonth(time,-((i+k)*3))
            temp_data = get_allstock_financial_statement(temp_now,info.FS_type.PLA)
            if Timer == 0:
                break
            Timer = Timer - 1
        data['%d-%d-1'%(temp_now.year, temp_now.month)] = get_allstock_financial_statement(temp_now,info.FS_type.PLA)
    
    result = pd.DataFrame({k:result['營業利益率(%)'] for k,result in data.items()}).transpose()
    result.index = pd.to_datetime(result.index)
    result = result.sort_index()
    count = 0
    final_result = pd.DataFrame()
    for index,row in result.iterrows():
        count = count + 1
        if count < 5:
            continue
        else:           
            a_string = str(index.year -1)+'-'+str(index.month).zfill(2)
            temp = round(((row - result[a_string])/result[a_string]) * 100,2)
            final_result = final_result.append(temp,ignore_index=True)
    method2 = (final_result > final_result.shift()).iloc[-upNum:].sum()
    method2 = method2[method2 >= upNum]
    method2 = pd.DataFrame(method2)
    load_memery[fileName] = method2
    print('get_OMGR_up: end' )
    return method2
#取得FCF連續升高篩選
def get_FCF_up(time,upNum):#time = 取得資料的時間 upNum = 連續成長多少季
    print('get_FCF_up: start:'+ str(time))
    fileName = "get_FCF_up_" + str(time.year) + str(time.month) + str(upNum)
    Timer = 2
    if fileName in load_memery:
        print('get_FCF_up: end' )
        return load_memery[fileName]
    data = {}
    if upNum <= 0:
        return pd.DataFrame()
    k = 0
    for i in range(upNum+1):
        temp_now = tools.changeDateMonth(time,-((i+k)*3))
        temp_data = get_allstock_financial_statement(temp_now,info.FS_type.SCF)
        while temp_data.empty:
            k = k + 1
            temp_now = tools.changeDateMonth(time,-((i+k)*3))
            temp_data = get_allstock_financial_statement(temp_now,info.FS_type.SCF)
            if Timer == 0:
                break
            Timer = Timer - 1
        temp_result = temp_data
        if temp_result["投資活動之淨現金流入（流出）"].dtype == object: 
            temp_result["投資活動之淨現金流入（流出）"] = pd.to_numeric(temp_result["投資活動之淨現金流入（流出）"].str.replace('--', '0'))
        temp_result[['投資活動之淨現金流入（流出）']] = temp_result[['投資活動之淨現金流入（流出）']].astype(int)
        temp_result['自由現金流入（流出）'] = temp_result['營業活動之淨現金流入（流出）'] + temp_result['投資活動之淨現金流入（流出）']
        data['%d-%d-1'%(temp_now.year, temp_now.month)] = temp_result
    result = pd.DataFrame({k:result['自由現金流入（流出）'] for k,result in data.items()}).transpose()
    result.index = pd.to_datetime(result.index)
    result = result.sort_index()
    method2 = (result > result.shift()).iloc[-upNum:].sum()
    method2 = method2[method2 >= upNum]
    method2 = pd.DataFrame(method2)
    load_memery[fileName] = method2
    print('get_FCF_up: end' )
    return method2
#取得ROE逐步升高的篩選
def get_ROE_up(time,upNum):#time = 取得資料的時間 upNum = 連續成長多少季
    print('get_ROE_up: start:'+ str(time))
    fileName = "get_ROE_up_" + str(time.year) + str(time.month) + str(upNum)
    Timer = 2
    k = 0
    if fileName in load_memery:
        print('get_ROE_up: end' )
        return load_memery[fileName]
    data = {}
    if upNum <= 0:
        return pd.DataFrame()
    for i in range(upNum+1):
        temp_now = tools.changeDateMonth(time,-((i+k)*3))
        temp_data = get_stock_ROE(temp_now)
        while temp_data.empty:
            k = k + 1
            temp_now = tools.changeDateMonth(time,-((i+k)*3))
            temp_data = get_stock_ROE(temp_now)
            if Timer == 0:
                break
            Timer = Timer - 1
        temp_result = temp_data
        data['%d-%d-1'%(temp_now.year, temp_now.month)] = temp_result
    result = pd.DataFrame({k:result['ROE'] for k,result in data.items()}).transpose()
    result.index = pd.to_datetime(result.index)
    result = result.sort_index()
    method2 = (result > result.shift()).iloc[-upNum:].sum()
    method2 = method2[method2 >= upNum]
    method2 = pd.DataFrame(method2)
    load_memery[fileName] = method2
    print('get_ROE_up: end' )
    return method2
#取得EPS逐步升高的篩選
def get_EPS_up(time,upNum):#time = 取得資料的時間 upNum = 連續成長多少季
    print('get_EPS_up: start:'+ str(time))
    fileName = "get_EPS_up_" + str(time.year) + str(time.month) + str(upNum)
    Timer = 2
    k = 0
    if fileName in load_memery:
        print('get_EPS_up: end' )
        return load_memery[fileName]
    data = {}
    if upNum <= 0:
        return pd.DataFrame()
    for i in range(upNum+1):
        temp_now = tools.changeDateMonth(time,-((i+k)*3))
        temp_data = get_allstock_financial_statement(temp_now,info.FS_type.CPL)
        while temp_data.empty:
            k = k + 1
            temp_now = tools.changeDateMonth(time,-((i+k)*3))
            temp_data = get_allstock_financial_statement(temp_now,info.FS_type.CPL)
            if Timer == 0:
                break
            Timer = Timer - 1
        temp_result = temp_data
        data['%d-%d-1'%(temp_now.year, temp_now.month)] = temp_result
    result = pd.DataFrame({k:result['基本每股盈餘（元）'] for k,result in data.items()}).transpose()
    result.index = pd.to_datetime(result.index)
    result = result.sort_index()
    method2 = (result > result.shift()).iloc[-upNum:].sum()
    method2 = method2[method2 >= upNum]
    method2 = pd.DataFrame(method2)
    load_memery[fileName] = method2
    print('get_ROE_up: end' )
    return method2
#取得本益比篩選 #股價/每股盈餘(EPS)
def get_PER_range(time,PER_start,PER_end,data = pd.DataFrame()):#time = 取得資料的時間 PER_start = PER最小值 PER_end PER最大值
    print('get_PER_range: start')
    PER_data = pd.DataFrame(columns = ['code','PER'])
    if PER_start == PER_end == 0:
        return PER_data
    if PER_end < 0 or PER_start < 0 or PER_end < PER_start:
        print("PER range number wrong!")
        return PER_data
    
    PE_date = time
    All_PER = data
    if type(time) == str:
        PE_date = datetime.strptime(time,"%Y-%m-%d")
    PE_data = get_allstock_yield(PE_date)
    if All_PER.empty == True:
        All_PER = PE_data
    mask1 = All_PER['本益比'] >= PER_start
    mask2 = All_PER['本益比'] <= PER_end
    PER_data = All_PER[(mask1 & mask2)]
    PER_data.rename(columns = {'本益比':'PER'},inplace= True)
    print('get_PER_range: end')
    return PER_data['PER']
#取得本益成長比(PEG)篩選
def get_PEG_range(time,PEG_start,PEG_end,data = pd.DataFrame()):#time = 取得資料的時間 PEG_start = PEG最小值 PEG_end PEG最大值
    print('get_PEG_range: start')
    PEG_data = pd.DataFrame(columns = ['code','PEG'])
    if PEG_start == PEG_end == 0:
        return PEG_end
    if PEG_end < 0 or PEG_start < 0 or PEG_end < PEG_start:
        print("PEG range number wrong!")
        return PEG_data
    PEG_date = time
    All_PEG = data
    if type(time) == str:
        PEG_date = datetime.strptime(time,"%Y-%m-%d")
    if All_PEG.empty == True:
        All_PEG = get_stock_PEG(PEG_date)
    
    All_PEG_Temp = pd.DataFrame(columns={'PEG'})
    All_PEG_Temp['PEG'] = All_PEG['PEG']
    mask1 = All_PEG_Temp['PEG'] >= PEG_start
    mask2 = All_PEG_Temp['PEG'] <= PEG_end
    PEG_data = All_PEG_Temp[(mask1 & mask2)]
    print('get_PEG_range: end')
    return PEG_data
    
#取得平均日成交金額篩選
def get_AVG_value(time,volume,days,data = pd.DataFrame()):#time = 取得資料的時間 volume = 平均成交金額 days = 平均天數
    print('get_AVG_value: start')
    Volume_Time = time
    if type(Volume_Time) == str:
        Volume_Time = datetime.strptime(time,"%Y-%m-%d")
    All_monthRP = data
    if All_monthRP.empty == True:
        All_monthRP = get_allstock_monthly_report(Volume_Time)
    Volume_data = pd.DataFrame(columns = ['code','volume'])
    for i in range(0,len(All_monthRP)):
        Temp_AvgVolume = 0
        AvgDays = days
        NoDataDays = 10
        Temp_Volume_Time = Volume_Time
        while AvgDays > 0:
            if NoDataDays == 0:
                break
            Temp_Volume = get_stock_price(str(All_monthRP.iloc[i].name),
                                            tools.DateTime2String(Temp_Volume_Time),
                                            stock_data_kind.Volume)
            if Temp_Volume == None:
                if Temp_Volume_Time == Volume_Time:
                    break
                NoDataDays = NoDataDays - 1
                Temp_Volume_Time = Temp_Volume_Time + timedelta(days=-1)
                continue
            Temp_AvgVolume = Temp_AvgVolume + Temp_Volume
            AvgDays = AvgDays - 1
            NoDataDays = 10
            Temp_Volume_Time = Temp_Volume_Time + timedelta(days=-1)
        Temp_AvgVolume = Temp_AvgVolume / days
        if Temp_AvgVolume >= volume:
            Temp_number = int(All_monthRP.iloc[i].name)
            Volume_data.loc[(len(Volume_data)+1)] = {'code':Temp_number,'volume':Temp_AvgVolume}
        print('get_AVG_value: ' + str(All_monthRP.iloc[i].name) + '/' + str(Temp_AvgVolume))
    Volume_data['code'] = Volume_data['code'].astype('int')
    Volume_data['volume'] = Volume_data['volume'].astype('int')
    Volume_data.set_index('code',inplace=True)
    print('get_AVG_value: end')
    return Volume_data
#取得股價淨值比篩選  #股價/每股淨值 = PBR 
def get_PBR_range(time,PBR_start,PBR_end,data = pd.DataFrame()):#time = 取得資料的時間 PBR_start = PBR最小值 PBR_end PBR最大值
    print('get_PBR_rang: start')
    PBR_data = pd.DataFrame(columns = ['code','PBR'])
    if PBR_start == PBR_end == 0:
        return PBR_data
    if PBR_end < 0 or PBR_start < 0 or PBR_end < PBR_start:
        print("PBR range number wrong!")
        return PBR_data
    
    PBR_date = time
    All_PBR = data
    if type(time) == str:
        PBR_date = datetime.strptime(time,"%Y-%m-%d")
    Book_data = get_allstock_yield(PBR_date)
    if All_PBR.empty == True:
        All_PBR = Book_data
    
    mask1 = All_PBR['股價淨值比'] >= PBR_start
    mask2 = All_PBR['股價淨值比'] <= PBR_end
    PBR_data = All_PBR[(mask1 & mask2)]
    PBR_data.rename(columns = {'股價淨值比':'PBR'},inplace= True)
    print('get_PBR_rang: end')
    return PBR_data['PBR']
#取得股東權益報酬率 #ROE(股東權益報酬率) = 稅後淨利/股東權益
def get_ROE_range(time,ROE_start,ROE_end,data = pd.DataFrame()):#time = 取得資料的時間 ROE_start = ROE最小值 ROE_end ROE最大值
    print('get_ROE_rang: start')
    ROE_data = pd.DataFrame(columns = ['code','ROE'])
    #股東權益＝資產 － 負債 （資產負債表中）
    #稅後淨利 = (本期綜合損益)
    if ROE_start == ROE_end == 0:
        return ROE_data
    if ROE_end < 0 or ROE_start < 0 or ROE_end < ROE_start:
        print("ROE range number wrong!")
        return ROE_data
    
    ROE_date = time
    All_ROE = data
    if type(time) == str:
        ROE_date = datetime.strptime(time,"%Y-%m-%d")

    BOOK_data = get_allstock_financial_statement(ROE_date,info.FS_type.BS)
    CPL_data = get_allstock_financial_statement(ROE_date,info.FS_type.CPL)
    Timer = 2
    while BOOK_data.empty or CPL_data.empty:
        ROE_date = tools.changeDateMonth(ROE_date,-3)
        BOOK_data = get_allstock_financial_statement(ROE_date,info.FS_type.BS)
        CPL_data = get_allstock_financial_statement(ROE_date,info.FS_type.CPL)
        if Timer == 0:
            break
        Timer = Timer - 1
    if All_ROE.empty == True:
        All_ROE = BOOK_data

    All_ROE_Temp = pd.DataFrame(columns={'ROE'})
    All_ROE_Temp['ROE'] = round((CPL_data["本期綜合損益總額（稅後）"]/BOOK_data['權益總額']),4) * 100
    mask1 = All_ROE_Temp['ROE'] >= ROE_start
    mask2 = All_ROE_Temp['ROE'] <= ROE_end
    ROE_data = All_ROE_Temp[(mask1 & mask2)]
    print('get_ROE_rang: end')
    return ROE_data
#取得股價篩選
def get_price_range(time,high,low,data = pd.DataFrame()):#time = 取得資料的時間 high = 最高價 low = 最低價
    print('get_price_rang: start')
    price_data = pd.DataFrame(columns=['code','price'])
    if high == low == 0:
        return price_data
    if high < low or high < 0 or low < 0:
        print("price range number wrong!")
        return price_data
    price_time = time
    All_price = data
    if type(time) == str:
        price_time = datetime.strptime(time,"%Y-%m-%d")
    if All_price.empty == True:
        return price_data
    for index,row in All_price.iterrows():
        if check_no_use_stock(index):
            continue
        Temp_price = get_stock_price(index,price_time,stock_data_kind.AdjClose)
        if Temp_price == None:
            continue
        if (Temp_price > low) and (Temp_price < high):
            Temp_number = int(index)
            price_data =price_data.append({'code':Temp_number,'price':Temp_price},ignore_index=True)
    price_data['code'] = price_data['code'].astype('int')
    price_data.set_index('code',inplace=True)
    print('get_price_rang: end')
    return price_data    
#取得殖利率篩選 #(股息÷股價) × 100%
def get_yield_range(time,high,low,data = pd.DataFrame()):#time = 取得資料的時間 high = 殖利率最高值 low = 殖利率最低值
    print('get_yield_range: start')
    yield_data_result = pd.DataFrame(columns=['公司代號','殖利率'])
    if high == low == 0:
        return yield_data_result
    if high < 0 or low < 0 or low > high:
        print("yield range number wrong!")
        return yield_data_result
    yield_date = time
    All_yield = data
    if type(time) == str:
        yield_date = datetime.strptime(time,"%Y-%m-%d")
    yield_data = get_allstock_yield(yield_date)
    if All_yield.empty == True:
        All_yield = yield_data

    mask1 = All_yield['殖利率(%)'] >= low
    mask2 = All_yield['殖利率(%)'] <= high
    yield_data_result = All_yield[(mask1 & mask2)]
    yield_data_result.rename(columns={'殖利率(%)':'殖利率'},inplace=True)
    print('get_yield_range: end')
    return yield_data_result
#取得創新高篩選
def get_RecordHigh_range(time,Day,RecordHighDay,data = pd.DataFrame()):#time = 取得資料的時間 Day = 往前找多少天的創新高 RecordHighDay = 找創新高的區間
    print('get_RecordHigh: start')
    RH_result = pd.DataFrame(columns=['code','創新高']).astype('int')
    get_infos = 3
    if Day == RecordHighDay == 0:
        return RH_result
    if Day < 0 or RecordHighDay < 0:
        print("yield range number wrong!")
        return RH_result
    
    RH_date = time
    All_data = data
    if type(time) == str:
        RH_date = datetime.strptime(time,"%Y-%m-%d")
    if All_data.empty == True:
        return RH_result
    for index,row in All_data.iterrows():
        if get_stock_info.ts.codes.__contains__(str(index)) == False:
            print(''.join([str(index),":無此檔股票"]))
            continue 
        if get_stock_RecordHight(index,RH_date,Day,RecordHighDay) == True:
            Temp_number = int(index)
            RH_result = RH_result.append({'code':Temp_number,'創新高':1},ignore_index=True)   
            get_infos = get_infos - 1
            if get_infos <= 0:
                break
    RH_result.set_index('code',inplace=True) 
    RH_result = RH_result.astype('int')
    print('RecordHigh: end')
    return RH_result
#取得交易量篩選
def get_volume(volumeNum,date,data = pd.DataFrame(),getMax = False):
    Temp_index = 0
    Temp_volume2 = 0
    volume_data = pd.DataFrame(columns=['code','volume'])
    if volumeNum <= 0:
        return volume_data
    All_data = data
    if All_data.empty == True:
        print("get_volume:輸入的data是空的")
        return volume_data

    for index,row in All_data.iterrows():
        Temp_volume = get_stock_price(str(index),tools.DateTime2String(date),stock_data_kind.Volume,isSMA=True)
        while (Temp_volume == None):
            if check_no_use_stock(index):
                break
            date = date + timedelta(days=-1)#加一天
            Temp_volume = get_stock_price(str(index),tools.DateTime2String(date),stock_data_kind.Volume,isSMA=True)
        if Temp_volume != None and Temp_volume >= volumeNum:
            Temp_number = int(index)
            volume_data = volume_data.append({'code':Temp_number,'volume':Temp_volume},ignore_index=True)
            if(getMax):
                if Temp_volume > Temp_volume2:
                    if(Temp_index != 0):
                        volume_data = volume_data.drop(index = Temp_index)
                    Temp_index = index
                    Temp_volume2 = Temp_volume
                else:
                    volume_data = volume_data.drop(index = index)
            else:
                pass
    volume_data['code'] = volume_data['code'].astype('int')
    volume_data.set_index('code',inplace=True)
    return volume_data

#爬取歷史財報並存檔
def financial_statement(year, season, type):#year = 年 season = 季 type = 財報種類
    myear = year
    if year>= 1000:
        myear -= 1911
    
    if type == info.FS_type.CPL:
        url = 'https://mops.twse.com.tw/mops/web/ajax_t163sb04'
    elif type == info.FS_type.BS:
        url = 'https://mops.twse.com.tw/mops/web/ajax_t163sb05'
    elif type == info.FS_type.PLA:
        url = 'https://mops.twse.com.tw/mops/web/ajax_t163sb06'
    elif type == info.FS_type.SCF:
        url = 'https://mops.twse.com.tw/mops/web/ajax_t163sb20'
    else:
        print('type does not match')

    # url = 'http://mops.twse.com.tw/mops/web/ajax_t163sb06'
    form_data = {
        'encodeURIComponent':1,
        'step':1,
        'firstin':1,
        'off':1,
        'TYPEK':'sii',
        'year': myear,
        'season': season,
    }
    response = requests.post(url,form_data,headers = tools.get_random_Header())
    #response.encoding = 'utf8'

    if type == info.FS_type.PLA:
        df = translate_dataFrame(response.text)
    else:
        df = translate_dataFrame2(response.text,type,myear,season)

    df.to_csv(filePath + "/" + fileName_season + "/" + str(year)+"-season"+str(season)+"-"+type.value+".csv",index=False)
    # 偽停頓
    time.sleep(5)
def remove_td(column):
    remove_one = column.split('<')
    remove_two = remove_one[0].split('>')
    return remove_two[1].replace(",","")
def translate_dataFrame(response):
    table_array = response.split('<table')
    tr_array = table_array[1].split('<tr')
    
    data = []
    index = []
    column = []
    for i in range(len(tr_array)):
        td_array = tr_array[i].split('<td')
        if(len(td_array)>1):
            code = remove_td(td_array[1])
            name = remove_td(td_array[2])
            revenue = remove_td(td_array[3])
            profitRatio = remove_td(td_array[4])
            profitMargin = remove_td(td_array[5])
            preTaxIncomeMargin = remove_td(td_array[6])
            afterTaxIncomeMargin = remove_td(td_array[7])
            if(revenue == '&nbsp;'):
                continue
            if(revenue == ''):
                continue
            if(i > 1):
                if name == '公司名稱':
                    continue
                data.append([name,code,revenue,profitRatio,profitMargin,preTaxIncomeMargin,afterTaxIncomeMargin])
                #index.append(name)
            if(i == 1):
                column.append('公司名稱')
                column.append(code)
                column.append(revenue)
                column.append(profitRatio)
                column.append(profitMargin)
                column.append(preTaxIncomeMargin)
                column.append(afterTaxIncomeMargin)
    return pd.DataFrame(data = data,columns=column)
def translate_dataFrame2(response,type,year,season = 1):
    table_array = response.split('<table')
    tr_array_array = [table_array[2].split('<tr'),
                table_array[3].split('<tr'),
                table_array[4].split('<tr'),
                table_array[5].split('<tr'),
                table_array[6].split('<tr'),
                table_array[7].split('<tr')]
    column_pos_array = np.array([[24,42,43,52,56],
                                [5,8,9,18,22],
                                [5,8,9,18,22],
                                [25,44,45,53,57],
                                [16,34,35,44,48],
                                [5,8,9,17,21]])
    if(year <= 111):
        column_pos_array = np.array([[24,42,43,53,57],
                                [5,8,9,19,23],
                                [5,8,9,19,23],
                                [25,44,45,53,57],
                                [16,34,35,45,49],
                                [5,8,9,18,22]])   
    if(year == 109):
        if (season == 1):
            column_pos_array = np.array([[24,42,43,52,56],
                                [5,8,9,18,22],
                                [5,8,9,18,22],
                                [25,44,45,53,57],
                                [16,34,35,44,48],
                                [5,8,9,17,21]])    
        else:
            column_pos_array = np.array([[24,42,43,53,57],
                                [5,8,9,19,23],
                                [5,8,9,19,23],
                                [25,44,45,53,57],
                                [16,34,35,45,49],
                                [5,8,9,18,22]])   
    if(year == 108):
        column_pos_array = np.array([[24,42,43,52,56],
                                [5,8,9,18,22],
                                [5,8,9,18,22],
                                [25,44,45,53,57],
                                [16,34,35,44,48],
                                [5,8,9,17,21]])                      
    if(year == 107):
        column_pos_array = np.array([[25,42,43,52,56],
                                [5,8,9,18,22],
                                [5,8,9,18,22],
                                [26,44,45,53,57],
                                [14,32,33,42,46],
                                [5,8,9,17,21]])
    if(year == 106):
        column_pos_array = np.array([[23,40,41,50,54],
                                [5,8,9,17,21],
                                [5,8,9,18,22],
                                [23,41,42,50,54],
                                [14,32,33,42,46],
                                [5,8,9,17,21]])                            
    if(year < 106):
        column_pos_array = np.array([[22,39,40,49,53],
                                [5,8,9,17,21],
                                [5,8,9,18,22],
                                [23,41,42,50,54],
                                [14,32,33,42,46],
                                [5,8,9,17,21]])
    if(year < 103):
        column_pos_array = np.array([[22,39,40,49,52],
                                [5,8,9,17,20],
                                [5,8,9,18,21],
                                [23,41,42,50,53],
                                [14,32,33,42,45],
                                [5,8,9,17,20]])
    # if (year < 105):
    #     column_pos_array = np.array([[23,40,41,50,54],
    #                             [5,8,9,17,21],
    #                             [5,8,9,18,22],
    #                             [23,41,42,50,54],
    #                             [14,32,33,42,46],
    #                             [5,8,9,17,21]
    #                             ])
    if (type == info.FS_type.CPL):
        if(year < 108):
            column_pos_array = np.array([[14,21],
                                        [15,22],
                                        [23,30],
                                        [15,22],
                                        [16,23],
                                        [11,18]])
        if(year < 106):
            column_pos_array = np.array([[14,21],
                                        [15,22],
                                        [21,28],
                                        [15,22],
                                        [16,23],
                                        [11,18]])
        if(year < 104):
            column_pos_array = np.array([[15,22],
                                        [15,22],
                                        [21,28],
                                        [15,22],
                                        [16,23],
                                        [11,18]])
        if(year == 108):
            column_pos_array = np.array([[15,22],
                                        [15,22],
                                        [23,30],
                                        [15,22],
                                        [16,23],
                                        [11,18]])
        elif(year > 108):
            column_pos_array = np.array([[15,22],
                                        [15,22],
                                        [23,30],
                                        [15,22],
                                        [16,23],
                                        [11,18]])
    if (type == info.FS_type.SCF):
        column_pos_array = np.array([[3,4,5],
                                    [3,4,5],
                                    [3,4,5],
                                    [3,4,5],
                                    [3,4,5],
                                    [3,4,5]])
    data = []
    index = []
    column = []

    for k in range(len(tr_array_array)):
        tr_array = tr_array_array[k]
        for i in range(len(tr_array)):
            if i == 1:
                td_array = tr_array[i].split('<th')
            else:    
                td_array = tr_array[i].split('<td')

            if(len(td_array)>1):
                code = remove_td(td_array[1])
                name = remove_td(td_array[2])
                revenue = remove_td(td_array[column_pos_array[k][0]])
                profitRatio = remove_td(td_array[column_pos_array[k][1]])
                if (type == info.FS_type.BS):
                    profitMargin = remove_td(td_array[column_pos_array[k][2]])
                    preTaxIncomeMargin = remove_td(td_array[column_pos_array[k][3]])
                    afterTaxIncomeMargin = remove_td(td_array[column_pos_array[k][4]])
                if (type == info.FS_type.SCF):
                    profitMargin2 = remove_td(td_array[column_pos_array[k][2]])
                if(i > 1):
                    if name == '公司名稱':
                        continue
                    if (type == info.FS_type.CPL):
                        data.append([name,code,revenue,profitRatio])
                    elif (type == info.FS_type.SCF):
                        data.append([name,code,revenue,profitRatio,profitMargin2])
                    else:
                        data.append([name,code,revenue,profitRatio,profitMargin,preTaxIncomeMargin,afterTaxIncomeMargin])
                    #index.append(name)
                if(i == 1 and k == 0) :
                    column.append('公司名稱')
                    column.append('公司代號')
                    column.append(revenue)
                    column.append(profitRatio)
                    if (type == info.FS_type.BS):
                        column.append(profitMargin)
                        column.append(preTaxIncomeMargin)
                        column.append(afterTaxIncomeMargin)
                    if (type == info.FS_type.SCF):
                        column.append(profitMargin2)

    return pd.DataFrame(data = data,columns=column)

def load_other_file(fileName,file = ''):
    if fileName in load_memery:
        return load_memery[fileName]
    df = pd.DataFrame()
    if file != '':
        df = update_stock_info.readStockDay(file)
    if df.empty == True:
        try:
            df = pd.read_csv(fileName + '.csv', index_col='Date', parse_dates=['Date'])
        except:
            print("no " + fileName + " csv file")
    
    df = df.dropna(how='any',inplace=False)#將某些null欄位去除
    load_memery[fileName] = df
    return df
