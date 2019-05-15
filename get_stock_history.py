import requests
import datetime
import pandas as pd
import get_stock_info
import os
import numpy as np
from io import StringIO
import time

filePath = os.getcwd()#取得目錄路徑
def get_stock_monthly_report(number,start):#爬某月某個股票月營收
    if get_stock_info.ts.codes.__contains__(number) == False:
        print("無此檔股票")
        return
    if os.path.isfile(filePath + '/' + str(start.year())+'-'+str(start.month())+'monthly_report.csv') == False:
        get_allstock_monthly_report(start)
    df = pd.read_csv(filePath + '/' + str(start.year())+'-'+str(start.month())+'monthly_report.csv',index_col='公司代號', parse_dates=['公司代號'])
    return df.loc[int(number)]
def get_allstock_monthly_report(start):#爬某月所有股票月營收
    year = start.year()
    if os.path.isfile(filePath + '/' + str(start.year())+'-'+str(start.month())+'monthly_report.csv') == False:
        # 假如是西元，轉成民國
        if year > 1990:
            year -= 1911
        url = 'http://mops.twse.com.tw/nas/t21/sii/t21sc03_'+str(year)+'_'+str(start.month())+'_0.html'
        if year <= 98:
            url = 'http://mops.twse.com.tw/nas/t21/sii/t21sc03_'+str(year)+'_'+str(start.month())+'.html'
        
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
        
        df.to_csv(str(start.year())+'-'+str(start.month())+'monthly_report.csv',index = False)
        # 偽停頓
        time.sleep(5)
    df = pd.read_csv(filePath + '/' + str(start.year())+'-'+str(start.month())+'monthly_report.csv',index_col='公司代號', parse_dates=['公司代號'])
    return df      
def get_allstock_financial_statement(start):#爬某季所有股票歷史財報
    season = int(((start.month() - 1)/3)+1)
    if os.path.isfile(filePath + '/' + str(start.year())+"-"+str(season)+"season-FS.csv") == False:
        financial_statement(start.year(),season)
    stock = pd.read_csv(filePath + '/' + str(start.year())+"-"+str(season)+"season-FS.csv",index_col='公司代號', parse_dates=['公司代號'])
    return stock
def get_stock_financial_statement(number,start):#爬某個股票的歷史財報
    season = int(((start.month() - 1)/3)+1)
    if get_stock_info.ts.codes.__contains__(number) == False:
        print("無此檔股票")
        return
    if os.path.isfile(filePath + '/' + str(start.year())+"-"+str(season)+"season-FS.csv") == False:
        financial_statement(start.year(),season)            
    stock = pd.read_csv(filePath + '/' + str(start.year())+"-"+str(season)+"season-FS.csv",index_col='公司代號', parse_dates=['公司代號'])
    return stock.loc[int(number)]
def get_stock_history(number,start):#爬某個股票的歷史紀錄
    if get_stock_info.ts.codes.__contains__(number) == False:
        print("無此檔股票")
        return
    if os.path.isfile(filePath + '/' + str(number) + '_' + str(start) + '.csv') == False:
        base_time = datetime.datetime.strptime('1970-1-1',"%Y-%m-%d")
        now_time = datetime.datetime.today()
        start_time  = datetime.datetime.strptime(start,"%Y-%m-%d")
        period1 = (start_time - base_time).total_seconds()
        period2 = (now_time - base_time).total_seconds()
        period1 = int(period1)
        period2 = int(period2)
        site = "https://query1.finance.yahoo.com/v7/finance/download/" + str(number) +".TW?period1="+str(period1)+"&period2="+str(period2)+"&interval=1d&events=history&crumb=hP2rOschxO0"
        response = requests.post(site)
        save_stock_file(filePath + '/' + str(number) + '_' + str(start),response)
        # 偽停頓
        time.sleep(5)

    m_history = load_stock_file(filePath + '/' + str(number) + '_' + str(start))
    return m_history
def save_stock_file(fileName,stockData):#存下歷史資料
    with open(fileName + '.csv', 'w') as f:
        f.writelines(stockData.text)
def load_stock_file(fileName):#讀取歷史資料
    df = pd.read_csv(fileName + '.csv', index_col='Date', parse_dates=['Date'])
    df = df.dropna(how='any',inplace=False)#將某些null欄位去除
    df.loc[df['Volume'] > 1000000000] = df.loc[df['Volume'] > 1000000000]/1000
    return df

def financial_statement(year, season):#爬取歷史財報並存檔
    myear = year
    if year>= 1000:
        myear -= 1911
    
    url = 'http://mops.twse.com.tw/mops/web/ajax_t163sb06'
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
    df = translate_dataFrame(response.text)
    df.to_csv(str(year)+"-"+str(season)+"season-FS.csv",index=False)
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