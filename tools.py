import datetime

def changeDateMonth(date,change_month):
    temp_month = date.month + change_month
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
        elif(month == [4,6,9,11]):
            result_day = 30
        else:
            result_day = day
    return result_day

        
