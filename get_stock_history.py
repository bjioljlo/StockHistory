import requests
import datetime
import pandas as pd
import get_stock_info
import os
import numpy as np
from io import StringIO
import time
from enum import Enum
import tools

fileName_monthRP = "monthRP"
fileName_stockInfo = "stockInfo"

no_use_stock = [1603,5259,1262,2475,3519,3579,9157]

Holiday_trigger = False

load_memery = {}

class FS_type(Enum):
    aa = 'Consolidated-profit-and-loss-summary'  #'綜合損益彙總表'
    bb = 'Balance-sheet' #'資產負債彙總表'
    cc = 'Profit-and-loss-analysis-summary'  #'營益分析彙總表'

class stock_data_kind(Enum):
    AdjClose = 'Adj Close'
    Volume = 'Volume'

filePath = os.getcwd()#取得目錄路徑

def check_no_use_stock(number):
    try:
        temp = int(number)
    except:
        print("check_no_use_stock error:" + number)
        return False
    for num in range(0,no_use_stock.__len__()):
        if(int(number) == no_use_stock[num]):
            print(str(number))
            return True
    return False

def get_stock_price(number,date,kind):#取得某股票某天的ＡＤＪ價格
    global Holiday_trigger
    if check_no_use_stock(number) == True:
        print('get_stock_price: ' + str(number) + ' in no use')
        return None
    stock_data = get_stock_history(number,date,False,False)
    if stock_data.empty == True:
        return None
    result = stock_data[stock_data.index == date]
    if result.empty == True:
        if Holiday_trigger == True:
            return None
        if datetime.datetime.strptime(date,"%Y-%m-%d").isoweekday() in [1,2,3,4,5]:
            #stock_data = get_stock_history(number,date,True,False) #會重新爬取資料
            stock_data = get_stock_history(number,date,False,False) #只會重新抓硬碟資料
            result = stock_data[stock_data.index == date]
            if result.empty == True:
                print('get_stock_price: ' +'星期' + str(datetime.datetime.strptime(date,"%Y-%m-%d").isoweekday()))
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
    #if os.path.isfile(filePath + '/' + fileName_monthRP + '/' + str(start.year)+'-'+str(start.month)+'monthly_report.csv') == False:
    #    get_allstock_monthly_report(start)
    #df = pd.read_csv(filePath + '/' + fileName_monthRP + '/' + str(start.year)+'-'+str(start.month)+'monthly_report.csv',index_col='公司代號', parse_dates=['公司代號'])
    df = get_allstock_monthly_report(start)
    return df.loc[[str(number)]]
def get_allstock_monthly_report(start):#爬某月所有股票月營收
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
        
        # 偽瀏覽器
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        # 下載該年月的網站，並用pandas轉換成 dataframe
        r = requests.get(url, headers=headers)
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
        time.sleep(5)
    df = pd.read_csv(fileName,index_col='公司代號', parse_dates=['公司代號'])
    load_memery[fileName] = df
    return df      
def get_allstock_financial_statement(start,type):#爬某季所有股票歷史財報
    season = int(((start.month - 1)/3)+1)
    fileName = filePath + '/' + str(start.year)+"-season"+str(season)+"-"+type.value+".csv"
    if fileName in load_memery:
        return load_memery[fileName]
    if os.path.isfile(fileName) == False:
        financial_statement(start.year,season,type)
    stock = pd.read_csv(fileName,index_col='公司代號', parse_dates=['公司代號'])
    load_memery[fileName] = stock
    return stock
def get_stock_financial_statement(number,start):#爬某個股票的歷史財報
    #season = int(((start.month() - 1)/3)+1)
    type = FS_type.cc
    if get_stock_info.ts.codes.__contains__(number) == False:
        print("無此檔股票")
        return
    #if os.path.isfile(filePath + '/' + str(start.year())+"-season"+str(season)+"-"+type.value+".csv") == False:
    #    financial_statement(start.year(),season,FS_type.cc)            
    #stock = pd.read_csv(filePath + '/' + str(start.year())+"-season"+str(season)+"-"+type.value+".csv",index_col='公司代號', parse_dates=['公司代號'])
    stock = get_allstock_financial_statement(start,type)
    return stock.loc[int(number)]
def get_stock_history(number,start,reGetInfo = False,UpdateInfo = True):#爬某個股票的歷史紀錄
    print("取得" + str(number) + "的資料從" + str(start) +"到今天")
    start_time = start
    if type(start_time) == str:
        start_time  = datetime.datetime.strptime(start,"%Y-%m-%d")
    data_time = datetime.datetime.strptime('2000-1-1',"%Y-%m-%d")
    now_time = datetime.datetime.today()
    result = pd.DataFrame()
    if UpdateInfo == False:
        now_time = datetime.datetime.strptime(get_stock_info.Update_date[0:10],"%Y-%m-%d")
        #now_time = datetime.datetime.strptime('2020-1-2',"%Y-%m-%d")

    if get_stock_info.ts.codes.__contains__(number) == False:
        print("無此檔股票")
        return result
    if start_time < data_time:
        print('日期請大於西元2000年')
        return

    if os.path.isfile(filePath +'/' + fileName_stockInfo  + '/' + str(number) + '_' + '2000-1-1' +
                                                            '_' +
                                                            str(now_time.year) +
                                                            '-' + str(now_time.month) + 
                                                            '-' + str(now_time.day) + '.csv') == False:
        base_time = datetime.datetime.strptime('1970-1-1',"%Y-%m-%d")
        data_time  = datetime.datetime.strptime('2000-1-1',"%Y-%m-%d")
        period1 = (data_time - base_time).total_seconds()
        period2 = (now_time - base_time).total_seconds()
        period1 = int(period1)
        period2 = int(period2)
        site = "https://query1.finance.yahoo.com/v7/finance/download/" + str(number) +".TW?period1="+str(period1)+"&period2="+str(period2)+"&interval=1d&events=history&crumb=hP2rOschxO0"
        response = requests.get(site)#post(site)
        save_stock_file(filePath +'/' + fileName_stockInfo  + '/' + str(number) + '_' + '2000-1-1' +
                                                            '_' +
                                                            str(now_time.year) +
                                                            '-' + str(now_time.month) + 
                                                            '-' + str(now_time.day),response)
        # 偽停頓
        time.sleep(5)
    else:
        if reGetInfo == True:
            base_time = datetime.datetime.strptime('1970-1-1',"%Y-%m-%d")
            data_time  = datetime.datetime.strptime('2000-1-1',"%Y-%m-%d")
            period1 = (data_time - base_time).total_seconds()
            period2 = (now_time - base_time).total_seconds()
            period1 = int(period1)
            period2 = int(period2)
            site = "https://query1.finance.yahoo.com/v7/finance/download/" + str(number) +".TW?period1="+str(period1)+"&period2="+str(period2)+"&interval=1d&events=history&crumb=hP2rOschxO0"
            response = requests.get(site)#post(site)
            save_stock_file(filePath +'/' + fileName_stockInfo  + '/' + str(number) + '_' + '2000-1-1' +
                                                                '_' +
                                                                str(now_time.year) +
                                                                '-' + str(now_time.month) + 
                                                                '-' + str(now_time.day),response)
            # 偽停頓
            time.sleep(5)


    m_history = load_stock_file(filePath +'/' + fileName_stockInfo  + '/' + str(number) + '_' + '2000-1-1' +
                                                            '_' +
                                                            str(now_time.year) +
                                                            '-' + str(now_time.month) + 
                                                            '-' + str(now_time.day))
    
    mask = m_history.index >= start
    result = m_history[mask]
    result = result.dropna(axis = 0,how = 'any')
    return result
def save_stock_file(fileName,stockData):#存下歷史資料
    with open(fileName + '.csv', 'w') as f:
        f.writelines(stockData.text)
def load_stock_file(fileName):#讀取歷史資料
    if fileName in load_memery:
        return load_memery[fileName]
#    if os.path.getsize(fileName + '.csv') < 200:
 #       df = pd.read_csv(fileName + '.csv')
  #  else:
    df = pd.read_csv(fileName + '.csv', index_col='Date', parse_dates=['Date'])
    df = df.dropna(how='any',inplace=False)#將某些null欄位去除
    df['Volume'] = df['Volume'].astype('int')
    #df.loc[df['Volume'] > 1000000000] = df.loc[df['Volume'] > 1000000000]/1000
    load_memery[fileName] = df
    return df

#取得月營收逐步升高的篩選資料
def get_monthRP_up(time,avgNum,upNum):#time = 取得資料的時間 avgNum = 平滑曲線月份 upNum = 連續成長月份
    print('get_monthRP_up: start:'+ str(time) )
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
    print('get_monthRP_up: end' )
    return final_result

#取得本益比篩選
def get_PER_range(time,PER_start,PER_end):#time = 取得資料的時間 PER_start = PER最小值 PER_end PER最大值
    print('get_PER_range: start')
    PER_data = pd.DataFrame(columns = ['公司代號','PER'])
    EPS_date = datetime.datetime.strptime(time,"%Y-%m-%d")
    Use_EPS_date = datetime.datetime(EPS_date.year - 1,12,1)
    EPS_data = get_allstock_financial_statement(Use_EPS_date,FS_type.aa)
    for i in range(0,len(EPS_data)):
        Temp_stock_price = None
        Temp_stock_price = get_stock_price(str(EPS_data.iloc[i].name),time,stock_data_kind.AdjClose)
        Temp_stock_EPS = EPS_data.iloc[i]['基本每股盈餘（元）']
        if Temp_stock_price == None:
            continue
        Temp_PER = round((Temp_stock_price/Temp_stock_EPS),0)
        if Temp_PER < 0:
            continue
        print('get_PER_range:' + str(EPS_data.iloc[i].name) + '--' + str(Temp_stock_price) + '/' +  str(Temp_stock_EPS) + '= ' + str(Temp_PER))
        if (Temp_PER > PER_start) and (Temp_PER < PER_end):
            Temp_number = int(EPS_data.iloc[i].name)
            PER_data.loc[(len(PER_data)+1)] = {'公司代號':Temp_number,'PER':Temp_PER}
    PER_data['公司代號'] = PER_data['公司代號'].astype('int')
    PER_data.set_index('公司代號',inplace=True)

    print('get_PER_range: end')
    return PER_data

#取得平均日成交金額篩選
def get_AVG_value(time,volume,days,data = pd.DataFrame):#time = 取得資料的時間 volume = 平均成交金額 days = 平均天數
    print('get_AVG_value: start')
    Volume_Time = time
    if type(Volume_Time) == str:
        Volume_Time = datetime.datetime.strptime(time,"%Y-%m-%d")
    All_monthRP = data
    if All_monthRP.empty == True:
        All_monthRP = get_allstock_monthly_report(Volume_Time)
    Volume_data = pd.DataFrame(columns = ['公司代號','Volume'])
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
                Temp_Volume_Time = Temp_Volume_Time + datetime.timedelta(days=-1)
                continue
            Temp_AvgVolume = Temp_AvgVolume + Temp_Volume
            AvgDays = AvgDays - 1
            NoDataDays = 10
            Temp_Volume_Time = Temp_Volume_Time + datetime.timedelta(days=-1)
        Temp_AvgVolume = Temp_AvgVolume / days
        if Temp_AvgVolume >= volume:
            Temp_number = int(All_monthRP.iloc[i].name)
            Volume_data.loc[(len(Volume_data)+1)] = {'公司代號':Temp_number,'Volume':Temp_AvgVolume}
        print('get_AVG_value: ' + str(All_monthRP.iloc[i].name) + '/' + str(Temp_AvgVolume))
    Volume_data['公司代號'] = Volume_data['公司代號'].astype('int')
    Volume_data['Volume'] = Volume_data['Volume'].astype('int')
    Volume_data.set_index('公司代號',inplace=True)
    print('get_AVG_value: end')
    return Volume_data
    

def financial_statement(year, season, type):#爬取歷史財報並存檔
    myear = year
    if year>= 1000:
        myear -= 1911
    
    if type == FS_type.aa:
        url = 'https://mops.twse.com.tw/mops/web/ajax_t163sb04'
    elif type == FS_type.bb:
        url = 'https://mops.twse.com.tw/mops/web/ajax_t163sb05'
    elif type == FS_type.cc:
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
    response = requests.post(url,form_data)
    response.encoding = 'utf8'

    if type == FS_type.cc:
        df = translate_dataFrame(response.text)
    else:
        df = translate_dataFrame2(response.text,type,myear)
        
    df.to_csv(str(year)+"-season"+str(season)+"-"+type.value+".csv",index=False)
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
def translate_dataFrame2(response,type,year):
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
                                [25,43,44,52,56],
                                [14,32,33,42,46],
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
    if (type == FS_type.aa):
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
                if (type == FS_type.bb):
                    profitMargin = remove_td(td_array[column_pos_array[k][2]])
                    preTaxIncomeMargin = remove_td(td_array[column_pos_array[k][3]])
                    afterTaxIncomeMargin = remove_td(td_array[column_pos_array[k][4]])
                if(i > 1):
                    if name == '公司名稱':
                        continue
                    if (type == FS_type.aa):
                        data.append([name,code,revenue,profitRatio])
                    else:
                        data.append([name,code,revenue,profitRatio,profitMargin,preTaxIncomeMargin,afterTaxIncomeMargin])
                    #index.append(name)
                if(i == 1 and k == 0) :
                    column.append('公司名稱')
                    column.append('公司代號')
                    column.append(revenue)
                    column.append(profitRatio)
                    if (type == FS_type.bb):
                        column.append(profitMargin)
                        column.append(preTaxIncomeMargin)
                        column.append(afterTaxIncomeMargin)

    return pd.DataFrame(data = data,columns=column)