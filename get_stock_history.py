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

no_use_stock = [1603,5259]

Holiday_trigger = False

class FS_type(Enum):
    aa = '綜合損益彙總表'
    bb = '資產負債彙總表'
    cc = '營益分析彙總表'

filePath = os.getcwd()#取得目錄路徑

def check_no_use_stock(number):
    for num in range(0,no_use_stock.__len__()):
        if(int(number) == no_use_stock[num]):
            print(str(number))
            return True
    return False
    

def get_stock_price(number,date):#取得某股票某天的ＡＤＪ價格
    global Holiday_trigger
    if check_no_use_stock(number) == True:
        print(str(number) + ' in no use')
        return None
    stock_data = get_stock_history(number,date,False,False)
    result = stock_data[stock_data.index == date]
    if result.empty == True:
        if Holiday_trigger == True:
            return None
        if datetime.datetime.strptime(date,"%Y-%m-%d").isoweekday() in [1,2,3,4,5]:
            stock_data = get_stock_history(number,date,True,False)
            result = stock_data[stock_data.index == date]
            if result.empty == True:
                print('星期' + str(datetime.datetime.strptime(date,"%Y-%m-%d").isoweekday()))
                print(str(number) + '--' + date + ' is no data. Its holiday?')
                Holiday_trigger = True
                return None
        else:
            return None
    result = result['Adj Close']
    close = result[date]
    Holiday_trigger = False
    return close
def get_stock_monthly_report(number,start):#爬某月某個股票月營收
    if get_stock_info.ts.codes.__contains__(number) == False:
        print("無此檔股票")
        return
    if os.path.isfile(filePath + '/' + fileName_monthRP + '/' + str(start.year)+'-'+str(start.month)+'monthly_report.csv') == False:
        get_allstock_monthly_report(start)
    df = pd.read_csv(filePath + '/' + fileName_monthRP + '/' + str(start.year)+'-'+str(start.month)+'monthly_report.csv',index_col='公司代號', parse_dates=['公司代號'])
    return df.loc[[int(number)]]
def get_allstock_monthly_report(start):#爬某月所有股票月營收
    year = start.year
    if os.path.isfile(filePath + '/' + fileName_monthRP + '/' + str(start.year)+'-'+str(start.month)+'monthly_report.csv') == False:
        # 假如是西元，轉成民國
        if year > 1990:
            year -= 1911
        url = 'http://mops.twse.com.tw/nas/t21/sii/t21sc03_'+str(year)+'_'+str(start.month)+'_0.html'
        if year <= 98:
            url = 'http://mops.twse.com.tw/nas/t21/sii/t21sc03_'+str(year)+'_'+str(start.month)+'.html'
        
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
        
        df.to_csv(filePath + '/' +fileName_monthRP + '/' + str(start.year)+'-'+str(start.month)+'monthly_report.csv',index = False)
        # 偽停頓
        time.sleep(5)
    df = pd.read_csv(filePath + '/' + fileName_monthRP + '/' + str(start.year)+'-'+str(start.month)+'monthly_report.csv',index_col='公司代號', parse_dates=['公司代號'])
    return df      
def get_allstock_financial_statement(start,type):#爬某季所有股票歷史財報
    season = int(((start.month - 1)/3)+1)
    if os.path.isfile(filePath + '/' + str(start.year)+"-"+str(season)+"-"+type.value+".csv") == False:
        financial_statement(start.year,season,type)
    stock = pd.read_csv(filePath + '/' + str(start.year)+"-"+str(season)+"-"+type.value+".csv",index_col='公司代號', parse_dates=['公司代號'])
    return stock
def get_stock_financial_statement(number,start):#爬某個股票的歷史財報
    season = int(((start.month() - 1)/3)+1)
    type = FS_type.cc
    if get_stock_info.ts.codes.__contains__(number) == False:
        print("無此檔股票")
        return
    if os.path.isfile(filePath + '/' + str(start.year())+"-"+str(season)+"-"+type.value+".csv") == False:
        financial_statement(start.year(),season,FS_type.cc)            
    stock = pd.read_csv(filePath + '/' + str(start.year())+"-"+str(season)+"-"+type.value+".csv",index_col='公司代號', parse_dates=['公司代號'])
    return stock.loc[int(number)]
def get_stock_history(number,start,reGetInfo = False,UpdateInfo = True):#爬某個股票的歷史紀錄
    start_time  = datetime.datetime.strptime(start,"%Y-%m-%d")
    data_time = datetime.datetime.strptime('2000-1-1',"%Y-%m-%d")
    now_time = datetime.datetime.today()
    if UpdateInfo == False:
        now_time = datetime.datetime.strptime('2019-6-24',"%Y-%m-%d")

    if get_stock_info.ts.codes.__contains__(number) == False:
        print("無此檔股票")
        return
    if start_time < data_time:
        print('日期請大於西元2000年')
        return
    
    if os.path.isfile(filePath + '/' + str(number) + '_' + '2000-1-1' +
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
        response = requests.post(site)
        save_stock_file(filePath + '/' + str(number) + '_' + '2000-1-1' +
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
            response = requests.post(site)
            save_stock_file(filePath + '/' + str(number) + '_' + '2000-1-1' +
                                                                '_' +
                                                                str(now_time.year) +
                                                                '-' + str(now_time.month) + 
                                                                '-' + str(now_time.day),response)
            # 偽停頓
            time.sleep(5)


    m_history = load_stock_file(filePath + '/' + str(number) + '_' + '2000-1-1' +
                                                            '_' +
                                                            str(now_time.year) +
                                                            '-' + str(now_time.month) + 
                                                            '-' + str(now_time.day))
    time.sleep(0.1)# 偽停頓
    mask = m_history.index >= start
    result = m_history[mask]
    result = result.dropna(axis = 0,how = 'any')
    return result
def save_stock_file(fileName,stockData):#存下歷史資料
    with open(fileName + '.csv', 'w') as f:
        f.writelines(stockData.text)
def load_stock_file(fileName):#讀取歷史資料
    if os.path.getsize(fileName + '.csv') < 200:
        df = pd.read_csv(fileName + '.csv')
        return df
    df = pd.read_csv(fileName + '.csv', index_col='Date', parse_dates=['Date'])
    df = df.dropna(how='any',inplace=False)#將某些null欄位去除
    df.loc[df['Volume'] > 1000000000] = df.loc[df['Volume'] > 1000000000]/1000
    return df

#取得月營收逐步升高的篩選資料
def get_monthRP_up(time,avgNum,upNum):#time = 取得資料的時間 avgNum = 平滑曲線月份 upNum = 連續成長月份
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
    return final_result


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
        
    df.to_csv(str(year)+"-"+str(season)+"-"+type.value+".csv",index=False)
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