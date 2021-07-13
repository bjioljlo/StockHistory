import pandas as pd
import os #讀取路徑套件
import twstock as ts #抓取台灣股票資料套件
import numpy as np #
import datetime

filePath = os.getcwd()#取得目錄路徑
stock_list = {}#要追蹤股票的ＬＩＳＴ
Update_date = ''#更新日期
Save_name = 'stock_info_list.npy'
Update_date_name = 'Update_date.npy'

class data_stock_info():#股票資訊結構
    def __init__(self,number,name,type,start,market,group,):
        self.name = name
        self.number = number
        self.type = type
        self.start = start
        self.market = market
        self.group = group    
def Add_stock_info(number):#新增追蹤股票
    if stock_list.__contains__(number):
        print("此股票已經在清單中")
        return
    if ts.codes.__contains__(number) == False:
        print("無此檔股票")
        return
    m_stock = ts.codes[number]
    m_info = data_stock_info(m_stock.code,m_stock.name,m_stock.type,m_stock.start,m_stock.market,m_stock.group)
    stock_list[number]  = m_info
    Save_stock_info()
def Delet_stock_info(number):#刪除追蹤股票
    if stock_list.__contains__(number) == False:
        print("此股票已經不在清單中")
        return
    del stock_list[number]
    Save_stock_info()
def Save_stock_info():#存檔追蹤股票
    np.save(Save_name,stock_list)
def Save_Update_date():#存檔更新日期
    np.save(Update_date_name,Update_date)
def Load_stock_info():#讀取追蹤股票
    if os.path.isfile(filePath + '/' + Save_name):
        m_stock_list = np.load(Save_name,None,True).item()
    else:
        m_stock_list = {}
        Save_stock_info()
    return m_stock_list
def Load_Update_date():#讀取更新日期
    if os.path.isfile(filePath + '/' + Update_date_name):
        m_Update_date = np.load(Update_date_name).item()
        print("上次存檔時間:" + str(m_Update_date))
    else:
        m_Update_date = str(datetime.datetime.today())
        print('沒存檔時間:'+ str(m_Update_date))
    return m_Update_date 
def Show_all_stock_info():#顯示所有追蹤股票
    if len(stock_list) == 0:
        print('No stock List in there!')
        return
    for m_stock_info in stock_list:
        print(str(m_stock_info) + " : " + stock_list[m_stock_info].name)
def Get_stock_info(number):#取得某隻追蹤股票資訊
    if stock_list.__contains__(number):
        return stock_list[number]
    else:
        return "no this stock infomation"

stock_list = Load_stock_info()
Update_date = Load_Update_date()
Show_all_stock_info()