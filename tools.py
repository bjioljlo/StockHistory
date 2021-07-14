import datetime
import random
import pandas as pd

def changeDateMonth(date,change_month):
    temp_month = date.month + change_month
    print("changeDateMonth:" + str(date.month) + " to " + str(temp_month))
    if(temp_month >= 13):
        year = temp_month//12
        month = temp_month%12
        if(month == 0):
            month = 12
        date = datetime.datetime(year = date.year + year,month = month,day = check_monthDate(month,date.day))
    elif(temp_month <= 0):
        temp_month = abs(temp_month)
        year = temp_month//12
        month = temp_month%12
        year = year - 1
        if(month == 0):
            month = 12
        else:
            month = 12 - month
        date = datetime.datetime(year = date.year + year,month = month,day = check_monthDate(month,date.day))
    else:
        date = datetime.datetime(year = date.year,month = temp_month,day = check_monthDate(temp_month,date.day))

    return date
def smooth_Data(data,everage):# data = 資料  everage = 往前多少資料平均
    result = data.rolling(everage,min_periods = everage).mean()
    return result
def QtDate2DateTime(date):
    date_str = str(date.year()) + '-' + str(date.month()) + '-' + str(date.day())
    date_result = datetime.datetime.strptime(date_str,"%Y-%m-%d")
    return date_result
def DateTime2String(date):
    date_str = str(date.year) + '-' + str(date.month) + '-' + str(date.day)
    return date_str
def check_monthDate(month,day):#確認日期正確性
    result_day = day
    if(day > 28):
        if(month == 2):
            result_day = 28
        elif(month in [4,6,9,11] and day == 31):
            result_day = 30
        else:
            result_day = day
    return result_day
def backWorkDays(date,days):#取得往後算days工作天後的日期
    input_date = date
    input_days = days
    if type(input_date) == str:
        input_date = datetime.datetime.strptime(date,"%Y-%m-%d")
    while input_days > 0:
        input_date = input_date - datetime.timedelta(days=1)#減一天
        if input_date.isoweekday() in [6,7]:
            continue
        input_days = input_days - 1
    return input_date
def MixDataFrames(DataFrames = {},index = '公司代號'):#合併報表
    result_data = pd.DataFrame()
    first = True
    for key,value in DataFrames.items():
        if result_data.empty == True and first == True:
            result_data = value
            first = False
        else:
            result_data = pd.merge(result_data,value,on=index,how='inner')
    return result_data
def get_random_Header():#取得隨機header
    headers_site = [ 'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11',
            'Opera/9.25 (Windows NT 5.1; U; en)',
            'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
            'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Kubuntu)',
            'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12',
            'Lynx/2.8.5rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/1.2.9',
            'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Ubuntu/11.04 Chromium/16.0.912.77 Chrome/16.0.912.77 Safari/535.7',
            'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:10.0) Gecko/20100101 Firefox/10.0 ']
    headers = {'User-Agent':headers_site[random.randrange(headers_site.__len__())]}
    return headers
def Total_with_Handling_fee_and_Tax(stock_price,amount,buyIn = True,persent = 0.1425,Use_fee_tax = True):#交易手續費和交易稅
        if Use_fee_tax == False:
            return (stock_price * amount)
        if buyIn == False:#賣出
            return (stock_price * amount) - ((stock_price * amount)*((persent + 0.3)/100))
        return (stock_price * amount) + ((stock_price * amount)*((persent)/100))#買入
def Count_Stock_Amount(money,price):#計算你可以買多少股      
    return (int)(money/(price*(100.1425/100)))
    
