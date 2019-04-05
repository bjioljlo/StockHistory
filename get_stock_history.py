import requests
import datetime
import pandas as pd
import get_stock_info
import os
import numpy as np

filePath = os.getcwd()#取得目錄路徑
def get_stock_financial_statement(number,start):#爬某個股票的歷史財報
    if get_stock_info.ts.codes.__contains__(number) == False:
        print("無此檔股票")
        return    
    stock = financial_statement(start.year(),start.month())
    stock = stock.astype(float)
    return stock.loc[get_stock_info.Get_stock_info(number).name]
    
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

def financial_statement(year, season):
    if year>= 1000:
        year -= 1911
    url = 'http://mops.twse.com.tw/mops/web/ajax_t163sb06'
    form_data = {
        'encodeURIComponent':1,
        'step':1,
        'firstin':1,
        'off':1,
        'TYPEK':'sii',
        'year': year,
        'season': season,
    }
    response = requests.post(url,form_data)
    response.encoding = 'utf8'
    df = translate_dataFrame(response.text)
    df.to_csv(str(year)+"-"+str(season)+"season-FS.csv")
    return df
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
                data.append([code,revenue,profitRatio,profitMargin,preTaxIncomeMargin,afterTaxIncomeMargin])
                index.append(name)
            if(i == 1):
                column.append(code)
                column.append(revenue)
                column.append(profitRatio)
                column.append(profitMargin)
                column.append(preTaxIncomeMargin)
                column.append(afterTaxIncomeMargin)
    return pd.DataFrame(data = data,index = index,columns=column)