
from datetime import datetime,timedelta
import random
import pandas as pd
import requests

MySql_server = None
threads = []
Season_RP_time_month =  [5 ,8 ,11,3 ]
Season_RP_time_day =    [15,31,14,31]

def changeDateMonth(date:datetime,change_month:int) -> datetime:
    temp_month = date.month + change_month
    
    # print("changeDateMonth:" + str(date.month) + " to " + str(temp_month))
    if(temp_month >= 13):
        year = temp_month//12
        month = temp_month%12
        if(month == 0):
            month = 12
        date = datetime(year = date.year + year,month = month,day = check_monthDate(month,date.day))
    elif(temp_month <= 0):
        temp_month = abs(temp_month)
        year = temp_month//12
        month = temp_month%12
        year = - 1 - year 
        if(month == 0):
            month = 12
        else:
            month = 12 - month
        date = datetime(year = date.year + year,month = month,day = check_monthDate(month,date.day))
    else:
        date = datetime(year = date.year,month = temp_month,day = check_monthDate(temp_month,date.day))
    Temp_date = date
    while date.isoweekday() in [6,7]:
        if Temp_date.day < 15:
            date = backWorkDays(date,-1)
        else:
            date = backWorkDays(date,1)
    return date
def smooth_Data(data:pd.DataFrame,everage) -> pd.DataFrame:# data = 資料  everage = 往前多少資料平均
    result = data.rolling(everage,min_periods = everage).mean()
    return result
def QtDate2DateTime(date) -> datetime:
    date_str = str(date.year()) + '-' + str(date.month()) + '-' + str(date.day())
    date_result = datetime.strptime(date_str,"%Y-%m-%d")
    return date_result
def DateTime2String(date:datetime) -> str:
    date_str = str(date.year) + '-' + str(date.month) + '-' + str(date.day)
    return date_str
def check_monthDate(month:int,day:int) -> int:#確認日期正確性
    result_day = day
    if(day > 28):
        if(month == 2):
            result_day = 28
        elif(month in [4,6,9,11] and day == 31):
            result_day = 30
        else:
            result_day = day
    return result_day
def backWorkDays(date,days:int) -> datetime:#取得往後算days工作天後的日期
    input_date = date
    input_days = abs(days)
    if type(input_date) == str:
        input_date = datetime.strptime(date,"%Y-%m-%d")
    while input_days > 0:
        if days < 0:
            input_date = input_date + timedelta(days=1)#加一天
        else:
            input_date = input_date - timedelta(days=1)#減一天
        
        if input_date.isoweekday() in [6,7]:
            continue
        input_days = input_days - 1
    return input_date
def MixDataFrames(DataFrames = {},index = 'code') -> pd.DataFrame:#合併報表
    result_data = pd.DataFrame()
    first = True
    for key,value in DataFrames.items():
        if result_data.empty == True and first == True:
            result_data = value
            first = False
        else:
            result_data = pd.merge(result_data,value,on=index,how='inner',suffixes=['', "_R"])
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
def get_SP500_list():#取得S&P500股票清單
    url = 'https://www.slickcharts.com/sp500'
    response = requests.get(url,headers= get_random_Header())
    data = pd.read_html(response.text)[0]
    # 欄位『Symbol』就是股票代碼
    stk_list = data.Symbol
    # 用 replace 將符號進行替換
    stk_list = data.Symbol.apply(lambda x: x.replace('.', '-'))
    return stk_list
def CheckFS_season(date):#檢查當季資料出來沒
    season = int(((date.month - 1)/3)+1)
    year = int(date.year)
    if season == 4:
        if datetime.today() > datetime(year+1,Season_RP_time_month[season-1],Season_RP_time_day[season-1]):
            return True
        else:
            return False
    else:
        if datetime.today() > datetime(year,Season_RP_time_month[season-1],Season_RP_time_day[season-1]):
            return True
        else:
            return False
def Have_MonthRP(date:datetime):#檢查當下月營收資料
    if date.month == datetime.now().month and date.year == datetime.now().year:#當月還沒出
        return False
    if date.year == datetime.now().year and int(date.month) == int(changeDateMonth(datetime.today(),-1).month) and (int(datetime.today().day)) < 15 :#還沒超過15號
        return False
    return True
def Have_DayRP(date:datetime):
    if date.month >= datetime.now().month and date.year >= datetime.now().year and date.day >= datetime.now().day:
        print(str(date) +'的日期不對，資料未出')
        return False
    return True
    
    
    
# def RunSchedule(func,UpdateTime):
#     schedule.every().day.at(UpdateTime).do(func)
#     temp_thread = threading.Thread(target=ScheduleStart)
#     temp_thread.start()
#     threads.append(temp_thread)

# def ScheduleStart():
#     t = threading.currentThread()
#     while getattr(t, "do_run", True):
#         schedule.run_pending()
#         time.sleep(30)

# def RunMysql():
#     temp_thread = threading.Thread(target=setMysqlServer)
#     temp_thread.start()

# def RunScheduleNow():
#     RunSchedule(runUpdate,str(datetime.today().hour)+ ":" + str(datetime.today().minute + 1))
#     RunSchedule(RunUpdate_sp500,str(datetime.today().hour)+ ":" + str(datetime.today().minute + 1))

# def setMysqlServer():
#     global MySql_server
#     server_flask = Flask(__name__)#初始化server
#     #設定mysql DB
#     server_flask.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#     server_flask.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://" + "demo" + ":" + "demo123" + "@" + "122.116.102.141" + ":"+ "3307" +"/"+"demo"
#     #連線mysql DB
#     MySql_server = SQLAlchemy(server_flask)
    

# def runUpdate():
#     print("Update all stocks start!")
#     df = pd.DataFrame()
#     for key,value in ts.codes.items():
#         if value.market == "上市" and len(value.code) >= 4 and len(value.code) <= 5 and check_ETF_stock(value.code):
#             try:
#                 deleteStockDayTable(str(value.code+".TW"))
#             except:
#                 print("SQL No Table:" + str(value.code+".TW"))
            
#             #SQL沒資料抓取一整包
#             yf.pdr_override()
#             start_date = datetime(2005,1,1)
#             end_date = datetime.today()#設定資料起訖日期
#             df = data.get_data_yahoo([value.code+".TW"], start_date, end_date,index_col=0)
#             if df.empty:
#                 print("yahoo no data:" + str(value.code+".TW"))
#                 continue
#             df.to_sql(name=value.code+".TW",con=MySql_server.engine)
#             print("Update stocks " + value.code+".TW" + " OK!")
    
#     #dataframe = pd.read_sql(sql = "2330.TW",con=MySql_server.engine,index_col='Date')
#     #print(dataframe)
#     print("Update all stocks end!")

# def RunUpdate_sp500():
#     print("Update all stocks start!")
#     sp500 = get_SP500_list()
#     for temp in sp500:
#         try:
#             deleteStockDayTable(temp)
#         except:
#             print("SQL No Table:" + str(temp))
            
#         #SQL沒資料抓取一整包
#         yf.pdr_override()
#         start_date = datetime(2005,1,1)
#         end_date = datetime.today()#設定資料起訖日期
#         df = data.get_data_yahoo([temp], start_date, end_date,index_col=0)
#         if df.empty:
#             print("yahoo no data:" + str(temp))
#             continue
#         df.to_sql(name=temp,con=MySql_server.engine)
#         print("Update stocks " + temp + " OK!")
#     print("Update all stocks end!")

# def stopThreadSchedule():
#     for thread in threads:
#         thread.do_run = False
#     print("thread all stop")

# def readStockDay(name):
#     dataframe = pd.DataFrame()
#     try:
#         dataframe = pd.read_sql(sql = name,con=MySql_server.engine,index_col='Date')
#         return dataframe
#     except Exception as e:
#         print('SQL Error {}'.format(e.args))
#         return dataframe

# def deleteStockDayTable(name):
#     DynamicBase = declarative_base(class_registry=dict())
#     class StockDayInfo(DynamicBase,MySql_server.Model):
#         __tablename__ = ""
#         Date = MySql_server.Column(MySql_server.DateTime, primary_key=True)
#         Open = MySql_server.Column(MySql_server.Float)
#         High = MySql_server.Column(MySql_server.Float)
#         Low = MySql_server.Column(MySql_server.Float)
#         Close = MySql_server.Column(MySql_server.Float)
#         AdjClose = MySql_server.Column(MySql_server.Float)
#         Volume = MySql_server.Column(MySql_server.Integer)
#         def __init__(self,name,Date,Open,High,Low,Close,AdjClose,Volume):
#             self.__tablename__ = name
#             self.Date = Date
#             self.Open = Open
#             self.High = High
#             self.Low = Low
#             self.Close = Close
#             self.AdjClose = AdjClose
#             self.Volume = Volume
    
#     temp_table = StockDayInfo.__table__
#     temp_table.name = name
#     StockDayInfo.__table__ = temp_table
#     StockDayInfo.__table__.drop(MySql_server.session.bind)
