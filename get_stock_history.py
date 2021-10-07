import requests
from datetime import datetime,timedelta
import pandas as pd
import get_stock_info
import os
import numpy as np
from io import StringIO
import time
from enum import Enum
import tools
import update_stock_info


fileName_monthRP = "monthRP"
fileName_stockInfo = "stockInfo"
fileName_yield = "yieldInfo"
fileName_season = "seasonInfo"
fileName_index = "indexInfo"

no_use_stock = [1603,5259,1262,2475,3519,
                3579,9157,3083,4576,6706,
                4439,4571,4572,4581,5283,
                6491,6592,6672,6715,6698,
                2025,5546,6598,4148,4552,
                8488,1341,6671,8499,2243,
                1902,2233,2448,3698,4725,
                5264,5305,8497]
five_word_ETF = ['00692','00878','00646','00881']

Holiday_trigger = False

load_memery = {}

class FS_type(Enum):
    CPL = 'Consolidated-profit-and-loss-summary'  #'綜合損益彙總表'
    BS = 'Balance-sheet' #'資產負債彙總表'
    PLA = 'Profit-and-loss-analysis-summary'  #'營益分析彙總表'

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
    while (flashDay > 0):
        if check_no_use_stock(number) == True:
            print('get_stock_price: ' + str(number) + ' in no use')
            return False
        Now_day = date
        Now_price = get_stock_price(number,Now_day,stock_data_kind.AdjClose)
        while (recordDays > 0):
            Temp_price = get_stock_price(number,Now_day,stock_data_kind.AdjClose)
            if Temp_price == None:
                Now_day = Now_day - timedelta(days = 1)
                continue
            if Temp_price > Now_price:
                return False
            Now_day = Now_day - timedelta(days = 1)
            recordDays = recordDays - 1
        date = date - timedelta(days = 1)
        flashDay = flashDay - 1
    return True
def get_stock_MA(number,date,MA_day):#取得某股票某天的均線
    Temp_MA = 0
    Temp_date = date
    Temp_MA_day = MA_day
    while(Temp_MA_day > 0):
        Temp_date = Temp_date + timedelta(days=-1)
        temp = get_stock_price(number,Temp_date,stock_data_kind.AdjClose)
        if temp == None:
            continue
        Temp_MA = Temp_MA + get_stock_price(number,Temp_date,stock_data_kind.AdjClose)
        Temp_MA_day = Temp_MA_day - 1
    Temp_MA = round(Temp_MA/MA_day,4)
    return Temp_MA
def get_stock_yield(number,date):#取得某股票某天的殖利率
    data = get_allstock_yield(date)
    return data.at[number,'殖利率(%)']
def get_stock_price(number,date,kind):#取得某股票某天的ＡＤＪ價格
    global Holiday_trigger
    if check_no_use_stock(number) == True:
        print('get_stock_price: ' + str(number) + ' in no use')
        return None
    stock_data = get_stock_history(number,date,reGetInfo=False,UpdateInfo=False)
    if stock_data.empty == True:
        return None
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
                print('get_stock_price: ' +'星期' + str(datetime.strptime(date,"%Y-%m-%d").isoweekday()))
                print('get_stock_price: ' +str(number) + '--' + date + ' is no data. Its holiday?')
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
    df = get_allstock_monthly_report(start)
    return df.loc[[str(number)]]
def get_allstock_monthly_report(start):#爬某月所有股票月營收
    if start.day < 15:#還沒超過15號，拿前一個月
        print("get_allstock_monthly_report:未到15號取上個月報表")
        start = tools.changeDateMonth(start,-1)
    year = start.year
    fileName = filePath + '/' + fileName_monthRP + '/' + str(start.year)+'-'+str(start.month)+'monthly_report.csv'
    if fileName in load_memery:
        return load_memery[fileName]
    
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
    df = pd.read_csv(fileName,index_col='公司代號', parse_dates=['公司代號'])
    load_memery[fileName] = df
    return df      
def get_allstock_financial_statement(start,type):#爬某季所有股票歷史財報
    print("get_allstock_financial_statement:" + str(type))
    for i in range(12):
        try:
            season = int(((start.month - 1)/3)+1)
            fileName = filePath + '/' + fileName_season + '/' + str(start.year)+"-season"+str(season)+"-"+type.value+".csv"
            if fileName in load_memery:
                return load_memery[fileName]
            if os.path.isfile(fileName) == True:
                print("已經有" + str(start.month)+ "月財務報告")
                break
            financial_statement(start.year,season,type)
            print("下載" + str(start.month)+ "月財務報告ＯＫ")
            break
        except:
            print(str(start.month)+ "月財務報告未出跳下一個月")
            start = tools.changeDateMonth(start,-1)
            continue
    
        
    stock = pd.read_csv(fileName,index_col='公司代號', parse_dates=['公司代號'])
    load_memery[fileName] = stock
    return stock
def get_allstock_yield(start):#爬某天所有股票殖利率
    fileName = filePath + '/' + fileName_yield + '/' + str(start.year) + '-' + str(start.month) + '-' + str(start.day) + '_Dividend_yield' 

    if fileName in load_memery:
        return load_memery[fileName]
    if os.path.isfile(fileName + '.csv') == False:
        url = 'https://www.twse.com.tw/exchangeReport/BWIBBU_d?response=csv&date=' + str(start.year)+str(start.month).zfill(2)+str(start.day).zfill(2)+ '&selectType=ALL'
        response = requests.get(url,tools.get_random_Header())
        save_stock_file(fileName,response,1,2)
        # 偽停頓
        time.sleep(1.5)

    try:
        m_yield = pd.read_csv(fileName + '.csv',index_col='證券代號',parse_dates=['證券代號'])
    except:
        m_yield = pd.read_csv(fileName + '.csv',index_col='證券代號',parse_dates=['證券代號'],encoding = 'ANSI')
    
    m_yield[["本益比"]] = m_yield[["本益比"]].astype(float)
    m_yield[["股價淨值比"]] = m_yield[["股價淨值比"]].astype(float)
    load_memery[fileName] = m_yield
    return m_yield
def get_stock_financial_statement(number,start):#爬某個股票的歷史財報
    #season = int(((start.month() - 1)/3)+1)
    type = FS_type.PLA
    if get_stock_info.ts.codes.__contains__(number) == False:
        print("無此檔股票")
        return
    stock = get_allstock_financial_statement(start,type)
    return stock.loc[int(number)]
def get_stock_history(number,start,reGetInfo = False,UpdateInfo = True):#爬某個股票的歷史紀錄
    print("取得" + str(number) + "的資料從" + str(start) +"到今天")
    start_time = start
    if type(start_time) == str:
        start_time  = datetime.strptime(start,"%Y-%m-%d")
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

    m_history = load_stock_file(filePath +'/' + fileName_stockInfo  + '/' + str(number) + '_' + '2000-1-1' +
                                                            '_' +
                                                            str(now_time.year) +
                                                            '-' + str(now_time.month) + 
                                                            '-' + str(now_time.day),str(number))
    
    if m_history.empty == True:
        if UpdateInfo == False:
            now_time = datetime.strptime(get_stock_info.Update_date[0:10],"%Y-%m-%d")

        if os.path.isfile(filePath +'/' + fileName_stockInfo  + '/' + str(number) + '_' + '2000-1-1' +
                                                            '_' +
                                                            str(now_time.year) +
                                                            '-' + str(now_time.month) + 
                                                            '-' + str(now_time.day) + '.csv') == False:
            base_time = datetime.strptime('1970-1-1',"%Y-%m-%d")
            data_time  = datetime.strptime('2000-1-1',"%Y-%m-%d")
            period1 = (data_time - base_time).total_seconds()
            period2 = (now_time - base_time).total_seconds()
            period1 = int(period1)
            period2 = int(period2)
            site = "https://query1.finance.yahoo.com/v7/finance/download/" + str(number) +".TW?period1="+str(period1)+"&period2="+str(period2)+"&interval=1d&events=history&crumb=hP2rOschxO0"
            response = requests.get(site,headers = tools.get_random_Header())#post(site)
            save_stock_file(filePath +'/' + fileName_stockInfo  + '/' + str(number) + '_' + '2000-1-1' +
                                                                '_' +
                                                                str(now_time.year) +
                                                                '-' + str(now_time.month) + 
                                                                '-' + str(now_time.day),response)
            # 偽停頓
            time.sleep(1.5)
            #刪除原本資料
            deleteDate = datetime.strptime(get_stock_info.Update_date[0:10],"%Y-%m-%d")
            if deleteDate != now_time:
                delet_stock_file(filePath +'/' + fileName_stockInfo  + '/' + str(number) + '_' + '2000-1-1' +
                                                            '_' +
                                                            str(deleteDate.year) +
                                                            '-' + str(deleteDate.month) + 
                                                            '-' + str(deleteDate.day)+ '.csv')
        else:
            if reGetInfo == True:
                base_time = datetime.strptime('1970-1-1',"%Y-%m-%d")
                data_time  = datetime.strptime('2000-1-1',"%Y-%m-%d")
                period1 = (data_time - base_time).total_seconds()
                period2 = (now_time - base_time).total_seconds()
                period1 = int(period1)
                period2 = int(period2)
                site = "https://query1.finance.yahoo.com/v7/finance/download/" + str(number) +".TW?period1="+str(period1)+"&period2="+str(period2)+"&interval=1d&events=history&crumb=hP2rOschxO0"
                response = requests.get(site,tools.get_random_Header())#post(site)
                save_stock_file(filePath +'/' + fileName_stockInfo  + '/' + str(number) + '_' + '2000-1-1' +
                                                                    '_' +
                                                                    str(now_time.year) +
                                                                    '-' + str(now_time.month) + 
                                                                    '-' + str(now_time.day),response)
                # 偽停頓
                time.sleep(1.5)
        m_history = load_stock_file(filePath +'/' + fileName_stockInfo  + '/' + str(number) + '_' + '2000-1-1' +
                                                                '_' +
                                                                str(now_time.year) +
                                                                '-' + str(now_time.month) + 
                                                                '-' + str(now_time.day),str(number))
        
    mask = m_history.index >= start
    result = m_history[mask]
    result = result.dropna(axis = 0,how = 'any')
    return result
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
        df = update_stock_info.readStockDay(stockName + '.TW')
    if df.empty == True:
        try:
            df = pd.read_csv(fileName + '.csv', index_col='Date', parse_dates=['Date'])
        except:
            print("no csv file")
    
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
def get_stock_AD_index(date):#取得上漲和下跌家數
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
    if fileName in load_memery:
        ADindex_result = load_memery[fileName]
    if os.path.isfile(fileName + '.csv') == True:
        ADindex_result = pd.read_csv(fileName + '.csv', index_col='Date', parse_dates=['Date'])
        load_memery[fileName] = ADindex_result
    up = 0
    down = 0
    if ADindex_result.empty == False and (ADindex_result.index == time).__contains__(True):
        return ADindex_result[ADindex_result.index == time]
    for key,value in get_stock_info.ts.codes.items():
        if value.market == "上市" and len(value.code) == 4:
            if check_no_use_stock(value.code) == True:
                print('get_stock_price: ' + str(value.code) + ' in no use')
                continue
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
    ADindex_result_new = pd.DataFrame({'Date':[time],'上漲':[up],'下跌':[down]}).set_index('Date')
    ADindex_result = ADindex_result.append(ADindex_result_new)
    ADindex_result = ADindex_result.sort_index()
    ADindex_result.to_csv(fileName + '.csv')
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

#取得月營收逐步升高的篩選資料
def get_monthRP_up(time,avgNum,upNum):#time = 取得資料的時間 avgNum = 平滑曲線月份 upNum = 連續成長月份
    print('get_monthRP_up: start:'+ str(time) )
    fileName = str(time.year) +str(time.month) + str(avgNum) + str(upNum)
    if fileName in load_memery:
        print('get_monthRP_up: end' )
        return load_memery[fileName]
    
    data = {}
    for i in range(avgNum+upNum):
        temp_now = tools.changeDateMonth(time,-i)
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
    final_result.index.name = '公司代號'
    load_memery[str(time.year) +str(time.month) + str(avgNum) + str(upNum)] = final_result
    print('get_monthRP_up: end' )
    return final_result

#取得本益比篩選
def get_PER_range(time,PER_start,PER_end,data = pd.DataFrame()):#time = 取得資料的時間 PER_start = PER最小值 PER_end PER最大值
    print('get_PER_range: start')
    PER_data = pd.DataFrame(columns = ['公司代號','PER'])
    if PER_start == PER_end == 0:
        return PER_data
    if PER_end < 0 or PER_start < 0 or PER_end < PER_start:
        print("PBR range number wrong!")
        return PER_data
    
    EPS_date = time
    All_PER = data
    if type(time) == str:
        EPS_date = datetime.strptime(time,"%Y-%m-%d")
    EPS_data = get_allstock_yield(EPS_date)
    if All_PER.empty == True:
        All_PER = EPS_data
    for index,row in All_PER.iterrows():
        Temp_PER = EPS_data.at[index,'本益比']
        if Temp_PER < 0:
            continue
        print('get_PER_range:' + str(index) + '= ' + str(Temp_PER))
        if (Temp_PER > PER_start) and (Temp_PER < PER_end):
            Temp_number = int(index)
            PER_data = PER_data.append({'公司代號':Temp_number,'PER':Temp_PER},ignore_index=True)
    PER_data['公司代號'] = PER_data['公司代號'].astype('int')
    PER_data.set_index('公司代號',inplace=True)

    print('get_PER_range: end')
    return PER_data

#取得平均日成交金額篩選
def get_AVG_value(time,volume,days,data = pd.DataFrame()):#time = 取得資料的時間 volume = 平均成交金額 days = 平均天數
    print('get_AVG_value: start')
    Volume_Time = time
    if type(Volume_Time) == str:
        Volume_Time = datetime.strptime(time,"%Y-%m-%d")
    All_monthRP = data
    if All_monthRP.empty == True:
        All_monthRP = get_allstock_monthly_report(Volume_Time)
    Volume_data = pd.DataFrame(columns = ['公司代號','volume'])
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
            Volume_data.loc[(len(Volume_data)+1)] = {'公司代號':Temp_number,'volume':Temp_AvgVolume}
        print('get_AVG_value: ' + str(All_monthRP.iloc[i].name) + '/' + str(Temp_AvgVolume))
    Volume_data['公司代號'] = Volume_data['公司代號'].astype('int')
    Volume_data['volume'] = Volume_data['volume'].astype('int')
    Volume_data.set_index('公司代號',inplace=True)
    print('get_AVG_value: end')
    return Volume_data
    
#取得股價淨值比篩選  #股價/每股淨值 = PBR 
def get_PBR_range(time,PBR_start,PBR_end,data = pd.DataFrame()):#time = 取得資料的時間 PBR_start = PBR最小值 PBR_end PBR最大值
    print('get_PBR_rang: start')
    PBR_data = pd.DataFrame(columns = ['公司代號','PBR'])
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
    for index,row in All_PBR.iterrows():
        if check_no_use_stock(index):
            continue
        Temp_PBR = Book_data.at[index,'股價淨值比']
        if Temp_PBR < 0:
            continue
        print('get_PBR_range:' + str(index) + '= ' + str(Temp_PBR))
        if (Temp_PBR > PBR_start) and (Temp_PBR < PBR_end):
            Temp_number = int(index)
            PBR_data = PBR_data.append({'公司代號':Temp_number,'PBR':Temp_PBR},ignore_index=True)
    PBR_data['公司代號'] = PBR_data['公司代號'].astype('int')
    PBR_data.set_index('公司代號',inplace=True)

    print('get_PBR_rang: end')
    return PBR_data
    
#取得股東權益報酬率 #ROE(股東權益報酬率) = 稅後淨利/股東權益
def get_ROE_range(time,ROE_start,ROE_end,data = pd.DataFrame()):#time = 取得資料的時間 ROE_start = ROE最小值 ROE_end ROE最大值
    print('get_ROE_rang: start')
    ROE_data = pd.DataFrame(columns = ['公司代號','ROE'])
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
    if ROE_date.month in [1,2,3]:
        Use_ROE_date = datetime(ROE_date.year - 1,12,1)
    else:
        Use_ROE_date = datetime(ROE_date.year,tools.changeDateMonth(ROE_date,-3).month ,tools.check_monthDate(tools.changeDateMonth(ROE_date,-3).month,ROE_date.day))
    BOOK_data = get_allstock_financial_statement(Use_ROE_date,FS_type.BS)
    CPL_data = get_allstock_financial_statement(Use_ROE_date,FS_type.CPL)
    if All_ROE.empty == True:
        All_ROE = BOOK_data
    for index,row in All_ROE.iterrows():
        if check_no_use_stock(index):
            continue
        Temp_Book = int(BOOK_data.at[index,'權益總額'])
        Temp_CPL = int(CPL_data.at[index,"本期綜合損益總額（稅後）"])
        Temp_ROE = round((Temp_CPL/Temp_Book),4) * 100
        if Temp_ROE < 0:
            continue
        print('get_ROE_range:' + str(index) + '--' + str(Temp_CPL) + '/' +  str(Temp_Book) + '= ' + str(Temp_ROE))
        if (Temp_ROE > ROE_start) and (Temp_ROE < ROE_end):
            Temp_number = int(index)
            ROE_data =ROE_data.append({'公司代號':Temp_number,'ROE':Temp_ROE},ignore_index=True)
    ROE_data['公司代號'] = ROE_data['公司代號'].astype('int')
    ROE_data.set_index('公司代號',inplace=True)

    print('get_ROE_rang: end')
    return ROE_data

#取得股價篩選
def get_price_range(time,high,low,data = pd.DataFrame()):#time = 取得資料的時間 high = 最高價 low = 最低價
    print('get_price_rang: start')
    price_data = pd.DataFrame(columns=['公司代號','price'])
    if high == low == 0:
        return price_data
    if high < low or high < 0 or low < 0:
        print("price range number wrong!")
        return price_data
    price_time = time
    All_price = data
    if type(time) == str:
        price_time = datetime.strptime(time,"%Y-%m-%d")
    if price_time.month in [1,2,3]:
        Use_price_time = datetime(price_time.year - 1,12,1)
    else:
        Use_price_time = datetime(price_time.year,tools.changeDateMonth(price_time,-3).month ,tools.check_monthDate(tools.changeDateMonth(price_time,-3).month,price_time.day))
    if All_price.empty == True:
        return price_data
    for index,row in All_price.iterrows():
        if check_no_use_stock(index):
            continue
        Temp_price = get_stock_price(index,Use_price_time,stock_data_kind.AdjClose)
        if Temp_price == None:
            continue
        if (Temp_price > low) and (Temp_price < high):
            Temp_number = int(index)
            price_data =price_data.append({'公司代號':Temp_number,'price':Temp_price},ignore_index=True)
    price_data['公司代號'] = price_data['公司代號'].astype('int')
    price_data.set_index('公司代號',inplace=True)

    print('get_price_rang: end')
    return price_data
    
#取得殖利率篩選
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
    for index,row in All_yield.iterrows():
        Temp_yield = yield_data.at[index,'殖利率(%)']
        if Temp_yield < 0 or Temp_yield == None:
            continue
        if (Temp_yield <= high) and (Temp_yield >= low):
            Temp_number = int(index)
            yield_data_result = yield_data_result.append({'公司代號':Temp_number,'殖利率':Temp_yield},ignore_index=True)
    yield_data_result['公司代號'] = yield_data_result['公司代號'].astype('int')
    yield_data_result.set_index('公司代號',inplace=True)    
    
    print('get_yield_range: end')
    return yield_data_result

#取得創新高篩選
def get_RecordHigh_range(time,Day,RecordHighDay,data = pd.DataFrame()):#time = 取得資料的時間 Day = 往前找多少天的創新高 RecordHighDay = 找創新高的區間
    print('get_RecordHigh: start')
    RH_result = pd.DataFrame(columns=['公司代號','創新高']).astype('int')
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
        if get_stock_RecordHight(index,RH_date,Day,RecordHighDay) == True:
            Temp_number = int(index)
            RH_result = RH_result.append({'公司代號':Temp_number,'創新高':1},ignore_index=True)          
    RH_result.set_index('公司代號',inplace=True) 
    RH_result = RH_result.astype('int')
    print('RecordHigh: end')
    return RH_result

#爬取歷史財報並存檔
def financial_statement(year, season, type):#year = 年 season = 季 type = 財報種類
    myear = year
    if year>= 1000:
        myear -= 1911
    
    if type == FS_type.CPL:
        url = 'https://mops.twse.com.tw/mops/web/ajax_t163sb04'
    elif type == FS_type.BS:
        url = 'https://mops.twse.com.tw/mops/web/ajax_t163sb05'
    elif type == FS_type.PLA:
        url = 'https://mops.twse.com.tw/mops/web/ajax_t163sb06'
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

    if type == FS_type.PLA:
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
    if(year == 110):
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
    if (type == FS_type.CPL):
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
                if (type == FS_type.BS):
                    profitMargin = remove_td(td_array[column_pos_array[k][2]])
                    preTaxIncomeMargin = remove_td(td_array[column_pos_array[k][3]])
                    afterTaxIncomeMargin = remove_td(td_array[column_pos_array[k][4]])
                if(i > 1):
                    if name == '公司名稱':
                        continue
                    if (type == FS_type.CPL):
                        data.append([name,code,revenue,profitRatio])
                    else:
                        data.append([name,code,revenue,profitRatio,profitMargin,preTaxIncomeMargin,afterTaxIncomeMargin])
                    #index.append(name)
                if(i == 1 and k == 0) :
                    column.append('公司名稱')
                    column.append('公司代號')
                    column.append(revenue)
                    column.append(profitRatio)
                    if (type == FS_type.BS):
                        column.append(profitMargin)
                        column.append(preTaxIncomeMargin)
                        column.append(afterTaxIncomeMargin)

    return pd.DataFrame(data = data,columns=column)