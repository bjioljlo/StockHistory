from pandas import DataFrame
import pandas as pd
import os
import update_stock_info
import Infomation_type as info

load_memery = {}

def save_stock_file(fileName:str,stockData,start_index:int = 0,end_index:int = 0):
    '''#存下歷史資料'''
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
def load_stock_file(fileName:str,stockName:str = ''):
    '''#讀取歷史資料'''
    if fileName in load_memery:#快取
        return load_memery[fileName]
    df = DataFrame()
    if stockName != '':#mysql
        df = update_stock_info.readStockDay(stockName + info.local_type.Taiwan)
    if df.empty == True:#本機端存檔
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
def load_other_file(fileName:str,file:str = ''):
    '''#讀取資料'''
    if fileName in load_memery:#快取
        return load_memery[fileName]
    df = DataFrame()
    if file != '':#mysql
        df = update_stock_info.readStockDay(file)
    if df.empty == True:#本機端存檔
        try:
            df = pd.read_csv(fileName + '.csv', index_col='Date', parse_dates=['Date'])
        except:
            print("no " + fileName + " csv file")
    
    df = df.dropna(how='any',inplace=False)#將某些null欄位去除
    load_memery[fileName] = df
    return df
def delet_stock_file(fileName:str):
    '''#刪除歷史資料'''
    if os.path.isfile(fileName) == True:
        os.remove(fileName)
def load_month_file(fileName:str,file:str = ''):
    '''#讀取月資料'''
    if fileName in load_memery:#快取
        return load_memery[fileName]
    df = DataFrame()
    if file != '':
        df = update_stock_info.read_Dividend_yield(file)
    if df.empty:
        try:
            df = pd.read_csv(fileName + '.csv', index_col='code', parse_dates=['code'])
        except:
            print("no " + fileName + " csv file")
    load_memery[fileName] = df
    return df