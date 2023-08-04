import pandas as pd
import numpy as np
from datetime import datetime,timedelta
#from backtesting import Backtest, Strategy #引入回測和交易策略功能
import talib
import get_stock_history as gsh
import tools
from tools import MixDataFrames,Count_Stock_Amount
from draw_figur import draw_backtest
import get_user_info
import Infomation_type as info

bool_check_monthRP_pick = False
bool_check_PER_pick = False
bool_check_volume_pick = False
bool_check_pickOneStock = False
bool_check_price_pick = False
bool_check_PBR_pick = False
bool_check_ROE_pick = False

class VirturlBackTestParameter():
    def __init__(self):
        self.date_start:datetime = None # tools.QtDate2DateTime(mybacktest.date_start.date())
        self.date_end:datetime = None # tools.QtDate2DateTime(mybacktest.date_end.date())
        self.money_start:int = None # int(mybacktest.input_startMoney.toPlainText())
        self.change_days:int = None # int(mybacktest.input_changeDays.toPlainText())
        self.smoothAVG:int = None # int(mybacktest.input_monthRP_smoothAVG.toPlainText())
        self.upMonth:int = None # int(mybacktest.input_monthRP_UpMpnth.toPlainText())
        self.PER_start:float = None # float(mybacktest.input_PER_start.toPlainText())
        self.PER_end:float = None # float(mybacktest.input_PER_end.toPlainText())
        self.volumeAVG:int = None # int(mybacktest.input_volume_money.toPlainText())
        self.volumeDays:int = None # int(mybacktest.input_volumeAVG_days.toPlainText())
        self.price_high:int = None # int(mybacktest.input_price_high.toPlainText())
        self.price_low:int = None # int(mybacktest.input_price_low.toPlainText())
        self.PBR_end:float = None # float(mybacktest.input_PBR_end.toPlainText())
        self.PBR_start:float = None # float(mybacktest.input_PBR_start.toPlainText())
        self.ROE_end:float = None # float(mybacktest.input_ROE_end.toPlainText())
        self.ROE_start:float = None # float(mybacktest.input_ROE_start.toPlainText())
        self.Pick_amount:int = None # int(mybacktest.input_StockAmount.toPlainText())
        self.buy_number:str = None # str(mybacktest.input_stockNumber.toPlainText())
        self.Dividend_yield_high:float = None # float(mybacktest.input_yield_start.toPlainText())
        self.Dividend_yield_low:float = None # float(mybacktest.input_yield_end.toPlainText())
        self.buy_day:int = None # int(mybacktest.input_buyDay.toPlainText())
        self.Record_high_day:int = None # int(mybacktest.input_RecordHigh.toPlainText())


def set_check(monthRP_pick,PER_pick,volume_pick,One_pick,price_pick,PBR_pick,ROE_pick):
    global bool_check_monthRP_pick
    bool_check_monthRP_pick = monthRP_pick
    global bool_check_PER_pick
    bool_check_PER_pick = PER_pick
    global bool_check_volume_pick
    bool_check_volume_pick = volume_pick
    global bool_check_pickOneStock
    bool_check_pickOneStock = One_pick
    global bool_check_price_pick
    bool_check_price_pick = price_pick
    global bool_check_PBR_pick
    bool_check_PBR_pick = PBR_pick
    global bool_check_ROE_pick
    bool_check_ROE_pick = ROE_pick

#平均股價 
def avg_stock_price(date,vData = pd.DataFrame()):
    All_price = 0 #
    Count = 0
    Result_avg_price = 0
    if(vData.empty == True):
        return 0,0
    for value in range(0,len(vData)):
        Nnumber = str(vData.iloc[value].name)
        Temp_stock_price = gsh.get_stock_price(Nnumber,tools.DateTime2String(date),
                                                            gsh.stock_data_kind.AdjClose)
        if Temp_stock_price != None:
            All_price = All_price + Temp_stock_price
            Count = Count + 1
    if All_price == 0 or Count == 0:
        return 0,0
    Result_avg_price = All_price / Count
    return Result_avg_price,Count
#////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#14年14倍 https://www.finlab.tw/%E6%AF%94%E7%AD%96%E7%95%A5%E7%8B%97%E9%82%84%E8%A6%81%E5%AE%89%E5%85%A8%E7%9A%84%E9%81%B8%E8%82%A1%E7%AD%96%E7%95%A5%EF%BC%81/
def backtest_PERandPBR(mainParament):
    Temp_reset = 0#休息日剩餘天數

    Temp_result_pick = pd.DataFrame(columns=['date','選股數量'])

    userInfo = get_user_info.data_user_info(mainParament.money_start,mainParament.date_start,mainParament.date_end)

    while userInfo.now_day <= userInfo.end_day:
        #週末直接跳過
        if userInfo.now_day.isoweekday() in [6,7]:
            print(str(userInfo.now_day) + 'is 星期' + str(userInfo.now_day.isoweekday()))
            if userInfo.add_one_day() == False:#加一天
                break
            continue

        #先看看台積有沒有資料，如果沒有表示這天是非週末假日跳過 
        if gsh.Stock_2330.get_PriceByDateAndType(userInfo.now_day,gsh.stock_data_kind.AdjClose) == None:
            print(str(userInfo.now_day) + "這天沒開市")
            if userInfo.add_one_day() == False:#加一天
                break
            continue

        #休息日直接跳過
        if Temp_reset > 0 and len(userInfo.handle_stock) == 0:
            print(str(userInfo.now_day) + ' is reset time:第' + str(Temp_reset) + '天')
            if userInfo.add_one_day() == False:#加一天
                break
            Temp_reset = Temp_reset - 1
            continue

        #開始篩選--------------------------------------
        Temp_result0 = {}
        Temp_result = pd.DataFrame()
        if bool_check_PER_pick:#PER pick
            Temp_result0['PER'] = gsh.get_PER_range(userInfo.now_day,mainParament.PER_start,mainParament.PER_end)
        if bool_check_PBR_pick:#PBR pick    
            Temp_result0['PBR'] = gsh.get_PBR_range(userInfo.now_day,mainParament.PBR_start,mainParament.PBR_end)
        Temp_result = tools.MixDataFrames(Temp_result0)

        #出場訊號篩選--------------------------------------
        if len(Temp_result) < mainParament.Pick_amount and len(userInfo.handle_stock) > 0:
            userInfo.sell_all_stock()
            Temp_reset = mainParament.change_days
        
        #入場訊號篩選--------------------------------------
        if len(Temp_result) > mainParament.Pick_amount and Temp_reset == 0 and len(userInfo.handle_stock) == 0:
            Temp_buy0 = {'result':Temp_result}
            if bool_check_price_pick:
                Temp_buy0['price'] = gsh.get_price_range(userInfo.now_day,mainParament.price_high,mainParament.price_low,Temp_result)
                Temp_buy0['price'] = Temp_buy0['price'].sort_values(by='price', ascending=False)
            if bool_check_volume_pick:
                Temp_buy0['volume'] = gsh.get_AVG_value(userInfo.now_day,mainParament.volumeAVG,mainParament.volumeDays,Temp_result)
                Temp_buy0['volume'] = Temp_buy0['volume'].sort_values(by='volume', ascending=False)
            Temp_buy = tools.MixDataFrames(Temp_buy0)
            if Temp_buy0['price'].empty == False:
                Temp_buy = Temp_buy.sort_values(by='price', ascending=False)
            if Temp_buy0['volume'].empty == False:
                Temp_buy = Temp_buy.sort_values(by='volume', ascending=False)
            userInfo.buy_all_stock(Temp_buy)
            Temp_reset = mainParament.change_days

        #更新資訊--------------------------------------
        userInfo.Record_userInfo()
        userInfo.Recod_tradeInfo()
        Temp_result_pick = pd.concat([Temp_result_pick,{'date':userInfo.now_day,
                                                '選股數量':len(Temp_result)}],ignore_index = True)
        #加一天----------------------------
        if userInfo.add_one_day() == False:
            break

    #最後總結算----------------------------
    Temp_result_pick.set_index('date',inplace=True)
    Temp_alldata = tools.MixDataFrames({'draw':userInfo.Temp_result_draw,'pick':Temp_result_pick},'date')
    
    Temp_alldata = tools.MixDataFrames({'all':Temp_alldata,'userinfo':userInfo.Temp_result_All},'date')
    
    userInfo.Temp_result_draw.to_csv('backtestdata.csv')
    userInfo.Temp_trade_info.to_csv('backtesttrade.csv')
    Temp_alldata.to_csv('backtestAll.csv')
    draw_backtest(userInfo.Temp_result_draw)
#月營收增高 https://www.finlab.tw/%e4%b8%89%e7%a8%ae%e6%9c%88%e7%87%9f%e6%94%b6%e9%80%b2%e9%9a%8e%e7%9c%8b%e6%b3%95/#ji_ji_xuan_gu_cheng_zhang_fa
def backtest_monthRP_Up(mainParament):
    Temp_change = 0#換股剩餘天數
    userInfo = get_user_info.data_user_info(mainParament.money_start,mainParament.date_start,mainParament.date_end)
    Temp_result_pick = pd.DataFrame(columns=['date','選股數量'])
    while userInfo.now_day <= userInfo.end_day:

        #週末直接跳過
        if userInfo.now_day.isoweekday() in [6,7]:
            print(str(userInfo.now_day) + 'is 星期' + str(userInfo.now_day.isoweekday()))
            if userInfo.add_one_day() == False:#加一天
                break
            continue
        #先看看台積有沒有資料，如果沒有表示這天是非週末假日跳過 
        if gsh.Stock_2330.get_PriceByDateAndType(userInfo.now_day,gsh.stock_data_kind.AdjClose) == None:
            print(str(userInfo.now_day) + "這天沒開市")
            if userInfo.add_one_day() == False:#加一天
                break
            continue
        
        #出場訊號篩選--------------------------------------
        if Temp_change <= 0 and len(userInfo.handle_stock) > 0:
            userInfo.sell_all_stock()

        #開始篩選--------------------------------------
        Temp_result0 = {}
        Temp_result = pd.DataFrame()
        if Temp_change <= 0:
            if bool_check_monthRP_pick:#月營收升高篩選(月為單位)
                Temp_result0['month'] = gsh.get_monthRP_up(userInfo.now_day,mainParament.smoothAVG,mainParament.upMonth)
            if bool_check_ROE_pick:#ROE
                Temp_result0['ROE'] = gsh.get_ROE_range(userInfo.now_day,mainParament.ROE_start,mainParament.ROE_end)
            if bool_check_PBR_pick:#PBR
                Temp_result0['PBR'] = gsh.get_PBR_range(userInfo.now_day,mainParament.PBR_start,mainParament.PBR_end)
            if bool_check_PER_pick:#PER
                Temp_result0['PER'] = gsh.get_PER_range(userInfo.now_day,mainParament.PER_start,mainParament.PER_end)
            Temp_result = tools.MixDataFrames(Temp_result0)

        #入場訊號篩選--------------------------------------
        if Temp_change <= 0 and len(userInfo.handle_stock) <= 0 and len(Temp_result) > mainParament.Pick_amount:
            Temp_buy0 = {'result':Temp_result}
            if bool_check_price_pick:
                Temp_buy0['price'] = gsh.get_price_range(userInfo.now_day,mainParament.price_high,mainParament.price_low,Temp_result)
                Temp_buy0['price'] = Temp_buy0['price'].sort_values(by='price', ascending=False)
            if bool_check_volume_pick:
                Temp_buy0['volume'] = gsh.get_AVG_value(userInfo.now_day,mainParament.volumeAVG,mainParament.volumeDays,Temp_result)
                Temp_buy0['volume'] = Temp_buy0['volume'].sort_values(by='volume', ascending=False)
            Temp_buy = tools.MixDataFrames(Temp_buy0)
            if Temp_buy0.__contains__('price') and Temp_buy0['price'].empty == False:
               Temp_buy = Temp_buy.sort_values(by='price', ascending=False)
            if Temp_buy0.__contains__('volume') and Temp_buy0['volume'].empty == False:
               Temp_buy = Temp_buy.sort_values(by='volume', ascending=False)
            userInfo.buy_all_stock(Temp_buy)

        #更新資訊--------------------------------------
        if Temp_change <= 0 and len(userInfo.handle_stock) > 0:
            Temp_change = mainParament.change_days
        userInfo.Record_userInfo()
        userInfo.Recod_tradeInfo()
        Temp_result_pick = pd.concat([Temp_result_pick,{'date':userInfo.now_day,
                                                '選股數量':len(Temp_result)}],ignore_index = True)
        #加一天----------------------------
        if userInfo.add_one_day() == False:
            break
        else:
            Temp_change = Temp_change - 1

    #最後總結算----------------------------
    Temp_result_pick.set_index('date',inplace=True)
    Temp_alldata = tools.MixDataFrames({'draw':userInfo.Temp_result_draw,'pick':Temp_result_pick},'date')
    draw_backtest(userInfo.Temp_result_draw)
    Temp_alldata = tools.MixDataFrames({'all':Temp_alldata,'userinfo':userInfo.Temp_result_All},'date')
    
    userInfo.Temp_result_draw.to_csv('backtestdata.csv')
    userInfo.Temp_trade_info.to_csv('backtesttrade.csv')
    Temp_alldata.to_csv('backtestAll.csv')
#定期定額非常詳細版，要跑很久暫時不使用
def backtest_Regular_quota(mainParament):
    userInfo = get_user_info.data_user_info(0,mainParament.date_start,mainParament.date_end)
    buy_month = mainParament.date_start
    Temp_result_pick = pd.DataFrame(columns=['date','選股數量'])
    while userInfo.now_day <= userInfo.end_day:        
        #週末直接跳過
        if userInfo.now_day.isoweekday() in [6,7]:
            print(str(userInfo.now_day) + 'is 星期' + str(userInfo.now_day.isoweekday()))
            if userInfo.add_one_day() == False:#加一天
                break
            continue
        #先看看台積有沒有資料，如果沒有表示這天是非週末假日跳過 
        if gsh.Stock_2330.get_PriceByDateAndType(userInfo.now_day,gsh.stock_data_kind.AdjClose) == None:
            print(str(userInfo.now_day) + "這天沒開市")
            if userInfo.add_one_day() == False:#加一天
                break
            continue

        #開始篩選--------------------------------------
        Temp_result = pd.DataFrame()
        Temp_result = pd.concat([Temp_result,{'date':userInfo.now_day,
                                                'number':mainParament.buy_number}],ignore_index = True)

        #入場訊號篩選--------------------------------------
        if userInfo.now_day.month != buy_month.month and userInfo.now_day.day >= mainParament.buy_day:
            Temp_price = gsh.get_stock_price(mainParament.buy_number,userInfo.now_day,gsh.stock_data_kind.AdjClose)
            userInfo.now_money = userInfo.now_money + mainParament.money_start
            userInfo.start_money = userInfo.start_money + mainParament.money_start
            Temp_stockNumber = tools.Count_Stock_Amount(mainParament.money_start,Temp_price)
            userInfo.buy_stock(mainParament.buy_number,Temp_stockNumber)
            buy_month = userInfo.now_day

        #更新資訊--------------------------------------   
        if userInfo.start_money > 0:
            userInfo.Record_userInfo()
            userInfo.Recod_tradeInfo()
        Temp_result_pick = pd.concat([Temp_result_pick,{'date':userInfo.now_day,
                                                '選股數量':len(Temp_result)}],ignore_index = True)

        #加一天----------------------------
        if userInfo.add_one_day() == False:
            break
    
    #最後總結算----------------------------
    Temp_result_pick.set_index('date',inplace=True)
    Temp_alldata = tools.MixDataFrames({'draw':userInfo.Temp_result_draw,'pick':Temp_result_pick},'date')
    #draw_backtest(userInfo.Temp_result_draw)
    Temp_alldata = tools.MixDataFrames({'all':Temp_alldata,'userinfo':userInfo.Temp_result_All},'date')
    
    userInfo.Temp_result_draw.to_csv('backtestdata.csv')
    userInfo.Temp_trade_info.to_csv('backtesttrade.csv')
    Temp_alldata.to_csv('backtestAll.csv')
    return userInfo.Temp_result_draw
#創新高 https://www.finlab.tw/break-new-high-roe-stock/
def backtest_Record_high(mainParament):
    Temp_reset = 0#休息日剩餘天數
    userInfo = get_user_info.data_user_info(mainParament.money_start,mainParament.date_start,mainParament.date_end)
    Temp_result_pick = pd.DataFrame(columns=['date','選股數量'])
    
    
    while userInfo.now_day <= userInfo.end_day:
        #週末直接跳過
        if userInfo.now_day.isoweekday() in [6,7]:
            print(str(userInfo.now_day) + 'is 星期' + str(userInfo.now_day.isoweekday()))
            if userInfo.add_one_day() == False:#加一天
                break
            continue
        #先看看台積有沒有資料，如果沒有表示這天是非週末假日跳過 
        if gsh.Stock_2330.get_PriceByDateAndType(userInfo.now_day,gsh.stock_data_kind.AdjClose) == None:
            print(str(userInfo.now_day) + "這天沒開市")
            if userInfo.add_one_day() == False:#加一天
                break
            continue
        #休息日直接跳過
        if Temp_reset > 0 and len(userInfo.handle_stock) == 0:
            print(str(userInfo.now_day) + ' is reset time:第' + str(Temp_reset) + '天')
            if userInfo.add_one_day() == False:#加一天
                break
            Temp_reset = Temp_reset - 1
            continue
        #出場訊號篩選--------------------------------------
        if len(userInfo.handle_stock) > 0:
            Temp_data = userInfo.handle_stock
            for key,value in list(Temp_data.items()):
                if gsh.get_stock_price(key,userInfo.now_day,gsh.stock_data_kind.AdjClose) < gsh.get_stock_MA(key,userInfo.now_day,20):
                    userInfo.sell_stock(key,value.amount)
        #開始篩選--------------------------------------
        Temp_result = pd.DataFrame()
        Temp_result0 = {}
        if Temp_reset <= 0:
            if bool_check_ROE_pick == True:
                Temp_result0['ROE'] = gsh.get_ROE_range(userInfo.now_day,mainParament.ROE_start,mainParament.ROE_end)
            if bool_check_ROE_pick == True:
                Temp_result0['ROE_last_seson'] = gsh.get_ROE_range(userInfo.now_day - timedelta(weeks = 4),1,10000)
            Temp_result = tools.MixDataFrames(Temp_result0)
            
        #入場訊號篩選--------------------------------------
        if Temp_reset <= 0 and len(Temp_result) > 0:
            Temp_buy0 = {'result':Temp_result}
            if bool_check_PBR_pick:
                Temp_buy0['PBR'] = gsh.get_PBR_range(userInfo.now_day,mainParament.PBR_start,mainParament.PBR_end)
            if bool_check_price_pick:
                Temp_buy0['price'] = gsh.get_price_range(userInfo.now_day,mainParament.price_high,mainParament.price_low,Temp_result)
            if bool_check_volume_pick:
                Temp_buy0['volume'] = gsh.get_AVG_value(userInfo.now_day,mainParament.volumeAVG,mainParament.volumeDays,Temp_result)
            
            Temp_buy0['point'] = pd.DataFrame(columns=['公司代號','point'])
            for index,row in Temp_result.iterrows():
                try:
                    temp = Temp_buy0['PBR'].at[index,'PBR']
                except:
                    continue
                if gsh.check_no_use_stock(index):
                    continue
                Temp_point = (row['ROE_x'] / row['ROE_y']) / Temp_buy0['PBR'].at[index,'PBR']
                Temp_buy0['point'] = Temp_buy0['point'].append({'公司代號':index,'point':Temp_point},ignore_index=True)
            Temp_buy0['point'] = Temp_buy0['point'].astype({'公司代號':'int','point':'float'})
            Temp_buy0['point'] = Temp_buy0['point'].set_index('公司代號')
            Temp_buy = tools.MixDataFrames(Temp_buy0)

            Temp_buy1 = {'result':Temp_buy}
            Temp_buy1['high'] = gsh.get_RecordHigh_range(userInfo.now_day,mainParament.change_days,mainParament.Record_high_day,Temp_buy)
            Temp_buy = tools.MixDataFrames(Temp_buy1)

            if Temp_buy.empty == False:
                Temp_buy = Temp_buy.sort_values(by='point', ascending=False)
                Temp_buy = Temp_buy.head(3)
                userInfo.buy_all_stock(Temp_buy)
        #更新資訊--------------------------------------
        if Temp_reset <= 0:
            Temp_reset = mainParament.change_days
        userInfo.Record_userInfo()
        userInfo.Recod_tradeInfo()
        Temp_result_pick = pd.concat([Temp_result_pick,{'date':userInfo.now_day,
                                                '選股數量':len(Temp_result)}],ignore_index = True)
        #加一天----------------------------
        if userInfo.add_one_day() == False:
            break
        else:
            Temp_reset = Temp_reset - 1

    #最後總結算----------------------------
    Temp_result_pick.set_index('date',inplace=True)
    Temp_alldata = tools.MixDataFrames({'draw':userInfo.Temp_result_draw,'pick':Temp_result_pick},'date')
    draw_backtest(userInfo.Temp_result_draw)
    Temp_alldata = tools.MixDataFrames({'all':Temp_alldata,'userinfo':userInfo.Temp_result_All},'date')
    
    userInfo.Temp_result_draw.to_csv('backtestdata.csv')
    userInfo.Temp_trade_info.to_csv('backtesttrade.csv')
    Temp_alldata.to_csv('backtestAll.csv')
#////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#KD值選股 https://www.finlab.tw/%e7%94%a8kd%e5%80%bc%e9%81%b8%e8%82%a1%ef%bc%9a%e9%82%84%e9%9c%80%e6%90%ad%e9%85%8d%e9%80%99%e4%b8%89%e7%a8%ae%e6%8c%87%e6%a8%99/
def backtest_KD_pick(mainParament):
    userInfo = get_user_info.data_user_info(mainParament.money_start,mainParament.date_start,mainParament.date_end)
    Temp_result_pick = pd.DataFrame(columns=['date','選股數量'])
    Temp_table = gsh.gsh(2330,"2005-01-01",reGetInfo = False,UpdateInfo = False)
    All_stock_signal = dict()
      
    ROE_record_day = datetime.strptime("2000-01-01","%Y-%m-%d")
    buy_data = pd.DataFrame(columns = ['Date','code']).set_index('Date')
    sell_data = pd.DataFrame(columns = ['Date','code']).set_index('Date')
    ROE_data = {}
    add_one_day = userInfo.add_one_day
    changeDateMonth = tools.changeDateMonth
    get_ROE_range = gsh.get_ROE_range
    MixDataFrames = tools.MixDataFrames
    sell_stock = userInfo.sell_stock
    buy_all_stock = userInfo.buy_all_stock
    for index,row in Temp_table.iterrows():
        if index < userInfo.now_day:
            continue
        while userInfo.now_day != index:
            if add_one_day() == False:
                break
        has_trade = False
        #ROE篩選
        if ROE_record_day <= index:
            ROE_data = {}
            ROE_record_day = changeDateMonth(index,1)
            ROE_data["ROE_data_1"] = pd.DataFrame(get_ROE_range(changeDateMonth(index,-3),0,999))
            ROE_data["ROE_data_1"].rename(columns={'ROE':'ROE_data_1'},inplace=True)
            ROE_data["ROE_data_2"] = pd.DataFrame(get_ROE_range(changeDateMonth(index,-6),0,999))
            ROE_data["ROE_data_2"].rename(columns={'ROE':'ROE_data_2'},inplace=True)
            ROE_data["ROE_data_3"] = pd.DataFrame(get_ROE_range(changeDateMonth(index,-9),0,999))
            ROE_data["ROE_data_3"].rename(columns={'ROE':'ROE_data_3'},inplace=True)
            ROE_data["ROE_data_4"] = pd.DataFrame(get_ROE_range(changeDateMonth(index,-12),0,999))
            ROE_data["ROE_data_4"].rename(columns={'ROE':'ROE_data_4'},inplace=True)
            mask = MixDataFrames(ROE_data)
            
            ROE_data_result =(mask["ROE_data_1"]+mask["ROE_data_2"]+mask["ROE_data_3"]+mask["ROE_data_4"])/4
            ROE_data_result = ROE_data_result.dropna()
            ROE_data_mask = mask["ROE_data_1"]> ROE_data_result
            ROE_data = ROE_data_mask[ROE_data_mask]
            
            for key,value in ROE_data.iteritems():#先算出股票的買賣訊號
                if gsh.check_no_use_stock(key) == True:
                    print('get_stock_price: ' + str(key) + ' in no use')
                    continue
                if All_stock_signal.__contains__(key):
                    continue
                table = gsh.gsh(key,"2005-01-01",reGetInfo = False,UpdateInfo = False)
                table_K,table_D = talib.STOCH(table['High'],table['Low'],table['Close'],fastk_period=50, slowk_period=20, slowk_matype=0, slowd_period=20, slowd_matype=0)
                table_sma10 = talib.SMA(np.array(table['Close']), 10)
                table_sma240 = talib.SMA(np.array(table['Close']), 240)
                signal_buy = (table_K > table_D)
                signal_sell = (table_K < table_D)
                signal_sma10 = table.Close < table_sma10
                signal_sma240 = table.Close > table_sma240
                signal = signal_buy.copy()
                signal = (signal_sma10 & signal_sma240 & signal_buy)
                signal[signal_sell] = -1
                All_stock_signal[key] = signal
        
        
        #找出買入訊號跟賣出訊號-------------------------
        buy_numbers = []
        sell_numbers = []
        for i,value in All_stock_signal.items():
            try:
                if value[index] == True:
                    if ROE_data.index.__contains__(int(i)):
                        if ROE_data[int(i)] == True:
                            buy_numbers.append(i)
                elif value[index] < 0 :
                    sell_numbers.append(i)
            except:
                #print('error:' + str(index) + ' at ' + str(i))
                continue
        #出場訊號篩選--------------------------------------
        if len(userInfo.handle_stock) > 0:
            Temp_data = userInfo.handle_stock
            for key,value in list(Temp_data.items()):
                if sell_numbers.__contains__(int(key)):
                    sell_stock(key,value.amount)
                    has_trade = True
        #入場訊號篩選--------------------------------------
        if len(buy_numbers) > 0 :
            Temp_buy = pd.DataFrame(columns={'code','volume'})
            for number in buy_numbers:
                volume = gsh.get_stock_price(number,tools.DateTime2String(userInfo.now_day),gsh.stock_data_kind.Volume)
                Temp_buy = pd.concat([Temp_buy,{'code':str(number),'volume':volume}],ignore_index = True)
            Temp_buy = Temp_buy.sort_values(by='volume', ascending=False).set_index('code')
            buy_all_stock(Temp_buy)
            has_trade = True
            
        #更新資訊--------------------------------------
        if has_trade:
            if len(buy_numbers) != 0:
                buy_data = pd.concat([buy_data,{'Date':index,'code':buy_numbers}],ignore_index = True)
            if len(sell_numbers) != 0:
                sell_data = pd.concat([sell_data,{'Date':index,'code':sell_numbers}],ignore_index = True)
            userInfo.Record_userInfo()
            userInfo.Recod_tradeInfo()
            Temp_result_pick = pd.concat([Temp_result_pick,{'date':userInfo.now_day,
                                                '選股數量':len(buy_numbers)}],ignore_index = True)
    
    buy_data = buy_data.set_index('Date')
    buy_data.to_csv('buy.csv')
    sell_data = sell_data.set_index('Date')
    sell_data.to_csv('sell.csv')
    #最後總結算----------------------------
    Temp_result_pick.set_index('date',inplace=True)
    Temp_alldata = tools.MixDataFrames({'draw':userInfo.Temp_result_draw,'pick':Temp_result_pick},'date')
    
    Temp_alldata = tools.MixDataFrames({'all':Temp_alldata,'userinfo':userInfo.Temp_result_All},'date')
    
    userInfo.Temp_result_draw.set_index('date').to_csv('backtestdata.csv')
    userInfo.Temp_trade_info.set_index('date').to_csv('backtesttrade.csv')
    Temp_alldata.set_index('date').to_csv('backtestAll.csv')   
    return userInfo.Temp_result_draw.set_index('date')

#PEG選股外加月營收增高 https://www.finlab.tw/finlab-tw-stock-peg-strategy/#PEG_ding_yi 
def backtest_PEG_pick_Fast(mainParament):
    userInfo = get_user_info.data_user_info(mainParament.money_start,mainParament.date_start,mainParament.date_end)
    buy_month = mainParament.date_start
    Temp_result_pick = pd.DataFrame(columns=['date','選股數量'])
    All_data = gsh.get_stock_history(mainParament.buy_number,mainParament.date_start)
    add_one_day = userInfo.add_one_day
    Record_userInfo = userInfo.Record_userInfo
    Recod_tradeInfo = userInfo.Recod_tradeInfo
    sell_stock = userInfo.sell_stock
    buy_all_stock = userInfo.buy_all_stock
    for index,row in All_data.iterrows():
        has_trade = False
        while(userInfo.now_day != index):
            #加一天----------------------------
            if add_one_day() == False:
                break
        #出場訊號篩選-----------------------------------
        if len(userInfo.handle_stock) > 0:
            Temp_data = userInfo.handle_stock
            for key,value in list(Temp_data.items()):
                if gsh.get_stock_price(key,userInfo.now_day,info.Price_type.Close) < gsh.get_stock_MA(key,userInfo.now_day,20):
                    sell_stock(key,value.amount)
                    has_trade = True
        #開始篩選--------------------------------------
        #入場訊號篩選--------------------------------------
        Temp_buy = pd.DataFrame()
        if userInfo.now_day.day >= mainParament.buy_day:
            if userInfo.now_day.month != buy_month.month or userInfo.now_day.year != buy_month.year:
                
                Temp_result0 = {}
                if bool_check_monthRP_pick:
                    Temp_result0['month'] = gsh.get_monthRP_up(userInfo.now_day,mainParament.smoothAVG,mainParament.upMonth)
                    Temp_result0['PEG'] = gsh.get_PEG_range(userInfo.now_day,0.66,1)
                    Temp_result0['result'] = MixDataFrames(Temp_result0)
                Temp_buy = Temp_result0['result']
                if Temp_buy.empty == False:
                    Temp_buy = Temp_buy.sort_values(by='PEG')
                    Temp_buy = Temp_buy.head(10)
                    buy_all_stock(Temp_buy)
                    has_trade = True
                buy_month = userInfo.now_day
        #更新資訊--------------------------------------
        if len(userInfo.handle_stock) > 0 or has_trade:
            Record_userInfo()
            Recod_tradeInfo()
            Temp_result_pick = pd.concat([Temp_result_pick,{'date':userInfo.now_day,
                                                '選股數量':len(Temp_buy)}],ignore_index = True)
        #加一天----------------------------
        if userInfo.add_one_day() == False:
            break
        else:
            continue
    #最後總結算----------------------------
    Temp_result_pick.set_index('date',inplace=True)
    Temp_alldata = MixDataFrames({'draw':userInfo.Temp_result_draw,'pick':Temp_result_pick},'date')
    Temp_alldata = MixDataFrames({'all':Temp_alldata,'userinfo':userInfo.Temp_result_All},'date')
    
    userInfo.Temp_result_draw.to_csv('backtestdata.csv')
    userInfo.Temp_trade_info.to_csv('backtesttrade.csv')
    Temp_alldata.to_csv('backtestAll.csv')
    return userInfo.Temp_result_draw

#定期定額
def backtest_Regular_quota_Fast(mainParament:VirturlBackTestParameter):
    userInfo = get_user_info.data_user_info(0,mainParament.date_start,mainParament.date_end)
    buy_month = mainParament.date_start
    Temp_result_pick = pd.DataFrame(columns=['date','選股數量'])
    
    All_data = gsh.get_stock_history(mainParament.buy_number,mainParament.date_start)
    add_one_day = userInfo.add_one_day
    Record_userInfo = userInfo.Record_userInfo
    Recod_tradeInfo = userInfo.Recod_tradeInfo
    buy_stock = userInfo.buy_stock
    for index,row in All_data.iterrows():
        while(userInfo.now_day != index):#消掉假日的誤差用的
            #加一天----------------------------
            if add_one_day() == False:
                break
        #開始篩選--------------------------------------
        #定期定額不用篩選--------------------------------------
        #入場訊號篩選--------------------------------------
        if userInfo.now_day.month != buy_month.month and userInfo.now_day.day >= mainParament.buy_day:
            Temp_price = row['Adj Close']
            userInfo.now_money = userInfo.now_money + mainParament.money_start
            userInfo.start_money = userInfo.start_money + mainParament.money_start
            Temp_stockNumber = Count_Stock_Amount(mainParament.money_start,Temp_price)
            buy_stock(mainParament.buy_number,Temp_stockNumber)
            buy_month = userInfo.now_day
            #更新資訊--------------------------------------   
            Record_userInfo()
            Recod_tradeInfo()
            Temp_result_pick = pd.concat([Temp_result_pick,{'date':userInfo.now_day,
                                                '選股數量':1}],ignore_index = True)
        #加一天----------------------------
        if add_one_day() == False:
            break
    
    #最後總結算----------------------------
    Temp_result_pick.set_index('date',inplace=True)
    Temp_alldata = MixDataFrames({'draw':userInfo.Temp_result_draw,'pick':Temp_result_pick},'date')
    Temp_alldata = MixDataFrames({'all':Temp_alldata,'userinfo':userInfo.Temp_result_All},'date')
    
    userInfo.Temp_result_draw.to_csv('backtestdata.csv')
    userInfo.Temp_trade_info.to_csv('backtesttrade.csv')
    Temp_alldata.to_csv('backtestAll.csv')
    return userInfo.Temp_result_draw

#創新高 https://www.finlab.tw/break-new-high-roe-stock/
def backtest_Record_high_Fast(mainParament):
    Temp_reset = 0#休息日剩餘天數
    userInfo = get_user_info.data_user_info(mainParament.money_start,mainParament.date_start,mainParament.date_end)
    Temp_result_pick = pd.DataFrame(columns=['date','選股數量'])
    All_data = gsh.get_stock_history(mainParament.buy_number,mainParament.date_start)
    add_one_day = userInfo.add_one_day
    Record_userInfo = userInfo.Record_userInfo
    Recod_tradeInfo = userInfo.Recod_tradeInfo
    sell_stock = userInfo.sell_stock
    buy_all_stock = userInfo.buy_all_stock
    for index,row in All_data.iterrows():
        has_trade = False
        while(userInfo.now_day != index):
            #加一天----------------------------
            if add_one_day() == False:
                break
        #出場訊號篩選--------------------------------------
        if len(userInfo.handle_stock) > 0:
            Temp_data = userInfo.handle_stock
            for key,value in list(Temp_data.items()):
                if gsh.get_stock_price(key,userInfo.now_day,gsh.stock_data_kind.AdjClose) < gsh.get_stock_MA(key,userInfo.now_day,20):
                    sell_stock(key,value.amount)
                    has_trade = True
        #開始篩選--------------------------------------
        Temp_result = pd.DataFrame()
        Temp_result0 = {}
        if Temp_reset <= 0:
            if bool_check_ROE_pick:
                Temp_result0['ROE'] = gsh.get_ROE_range(userInfo.now_day,mainParament.ROE_end,mainParament.ROE_start)
            if bool_check_ROE_pick:
                Temp_result0['ROE_last_seson'] = gsh.get_ROE_range(userInfo.now_day - timedelta(weeks = 12),10000,1)
            if bool_check_PBR_pick:
                Temp_result0['PBR'] = gsh.get_PBR_range(userInfo.now_day,mainParament.PBR_end,mainParament.PBR_start)
            Temp_result = MixDataFrames(Temp_result0)
            
        #入場訊號篩選--------------------------------------
        if Temp_reset <= 0 and len(Temp_result) > 0:
            Temp_buy0 = {'result':Temp_result}
            Temp_buy0['result']['point'] = (Temp_result['ROE'] / Temp_result['ROE_R']) / Temp_result['PBR']
            if bool_check_price_pick:
                Temp_buy0['price'] = gsh.get_price_range(userInfo.now_day,mainParament.price_high,mainParament.price_low,Temp_result)
                Temp_buy0['result'] = MixDataFrames(Temp_buy0)
            if bool_check_volume_pick:
                Temp_buy0['volume'] = gsh.get_AVG_value(userInfo.now_day,mainParament.volumeAVG,mainParament.volumeDays,Temp_result)
                Temp_buy0['result'] = MixDataFrames(Temp_buy0)
            
            # for index,row in Temp_result.iterrows():
            #     try:
            #         temp = Temp_buy0['PBR'].at[index,'PBR']
            #     except:
            #         continue
            #     if gsh.check_no_use_stock(index):
            #         continue
            #     Temp_point = (row['ROE'] / row['ROE_R']) / Temp_buy0['PBR'].at[index,'PBR']
            #     Temp_buy0['point'] = Temp_buy0['point'].append({'code':index,'point':Temp_point},ignore_index=True)
            # Temp_buy0['point'] = Temp_buy0['point'].astype({'code':'int','point':'float'})
            # Temp_buy0['point'] = Temp_buy0['point'].set_index('code')
            Temp_buy = MixDataFrames(Temp_buy0)

            Temp_buy = Temp_buy.sort_values(by='point', ascending=False)
            
            Temp_buy1 = {'result':Temp_buy}
            Temp_buy1['high'] = gsh.get_RecordHigh_range(userInfo.now_day,mainParament.change_days,mainParament.Record_high_day,Temp_buy)
            Temp_buy = MixDataFrames(Temp_buy1)

            if Temp_buy.empty == False:
                Temp_buy = Temp_buy.sort_values(by='point', ascending=False)
                Temp_buy = Temp_buy.head(3)
                buy_all_stock(Temp_buy)
                has_trade = True
        #更新資訊--------------------------------------
        if Temp_reset <= 0:
            Temp_reset = mainParament.change_days
        if len(userInfo.handle_stock) > 0 or has_trade:
            Record_userInfo()
            Recod_tradeInfo()
            Temp_result_pick = pd.concat([Temp_result_pick,{'date':userInfo.now_day,
                                                '選股數量':len(Temp_result)}],ignore_index = True)
        #加一天----------------------------
        if add_one_day() == False:
            break
        else:
            Temp_reset = Temp_reset - 1

    #最後總結算----------------------------
    Temp_result_pick.set_index('date',inplace=True)
    Temp_alldata = MixDataFrames({'draw':userInfo.Temp_result_draw,'pick':Temp_result_pick},'date')
    
    Temp_alldata = MixDataFrames({'all':Temp_alldata,'userinfo':userInfo.Temp_result_All},'date')
    
    userInfo.Temp_result_draw.to_csv('backtestdata.csv')
    userInfo.Temp_trade_info.to_csv('backtesttrade.csv')
    Temp_alldata.to_csv('backtestAll.csv')
    return userInfo.Temp_result_draw

#14年14倍 https://www.finlab.tw/%E6%AF%94%E7%AD%96%E7%95%A5%E7%8B%97%E9%82%84%E8%A6%81%E5%AE%89%E5%85%A8%E7%9A%84%E9%81%B8%E8%82%A1%E7%AD%96%E7%95%A5%EF%BC%81/
def backtest_PERandPBR_Fast(mainParament):
    Temp_reset = 0#休息日剩餘天數
    Temp_changeDays = 0#換股剩餘天數
    Temp_result_pick = pd.DataFrame(columns=['date','選股數量'])

    userInfo = get_user_info.data_user_info(mainParament.money_start,mainParament.date_start,mainParament.date_end)

    All_data = gsh.get_stock_history(mainParament.buy_number,mainParament.date_start)
    
    add_one_day = userInfo.add_one_day
    sell_all_stock = userInfo.sell_all_stock
    buy_all_stock = userInfo.buy_all_stock
    for index,row in All_data.iterrows():
        has_trade = False
        while(userInfo.now_day != index):
            #加一天----------------------------
            if add_one_day() == False:
                break
        
        #休息日直接跳過
        if Temp_reset > 0 and len(userInfo.handle_stock) == 0:
            print(str(userInfo.now_day) + ' is reset time:第' + str(Temp_reset) + '天')
            if add_one_day() == False:#加一天
                break
            Temp_reset = Temp_reset - 1
            continue
        
        #開始篩選--------------------------------------
        Temp_result0 = {}
        Temp_result = pd.DataFrame()
        if bool_check_PER_pick:#PER pick
            Temp_result0['PER'] = gsh.get_PER_range(userInfo.now_day,mainParament.PER_end,mainParament.PER_start)
        if bool_check_PBR_pick:#PBR pick    
            Temp_result0['PBR'] = gsh.get_PBR_range(userInfo.now_day,mainParament.PBR_end,mainParament.PBR_start)
        Temp_result = tools.MixDataFrames(Temp_result0)

        #出場訊號篩選--------------------------------------
        if len(Temp_result) < mainParament.Pick_amount and len(userInfo.handle_stock) > 0:
            sell_all_stock()
            Temp_reset = 120
            has_trade = True
        #出場訊號篩選--------------------------------------
        if Temp_changeDays <= 0 and len(userInfo.handle_stock) > 0:
            sell_all_stock()
            has_trade = True
        
        #入場訊號篩選--------------------------------------
        if len(Temp_result) >= mainParament.Pick_amount and Temp_reset == 0 and len(userInfo.handle_stock) == 0:
            Temp_buy0 = {'result':Temp_result}
            if bool_check_price_pick:
                Temp_buy0['price'] = gsh.get_price_range(userInfo.now_day,mainParament.price_high,mainParament.price_low,Temp_result)
                Temp_buy0['price'] = Temp_buy0['price'].sort_values(by='price', ascending=False)
            if bool_check_volume_pick:
                Temp_buy0['volume'] = gsh.get_AVG_value(userInfo.now_day,mainParament.volumeAVG,mainParament.volumeDays,Temp_result)
                Temp_buy0['volume'] = Temp_buy0['volume'].sort_values(by='volume', ascending=False)
            Temp_buy = tools.MixDataFrames(Temp_buy0)
            if Temp_buy0.__contains__('price') and Temp_buy0['price'].empty == False:
                Temp_buy = Temp_buy.sort_values(by='price', ascending=False)
            if Temp_buy0.__contains__('volume') and Temp_buy0['volume'].empty == False:
                Temp_buy = Temp_buy.sort_values(by='volume', ascending=False)
            buy_all_stock(Temp_buy)
            Temp_changeDays = mainParament.change_days
            has_trade = True
        #更新資訊--------------------------------------
        if len(userInfo.handle_stock) > 0 or has_trade == True:
            userInfo.Record_userInfo()
            userInfo.Recod_tradeInfo()
            Temp_result_pick = pd.concat([Temp_result_pick,{'date':userInfo.now_day,
                                                '選股數量':len(Temp_result)}],ignore_index = True)
        #加一天----------------------------
        if add_one_day() == False:
            break
        else:
            Temp_changeDays = Temp_changeDays - 1
    
    #最後總結算----------------------------
    Temp_result_pick.set_index('date',inplace=True)
    Temp_alldata = tools.MixDataFrames({'draw':userInfo.Temp_result_draw,'pick':Temp_result_pick},'date')
    
    Temp_alldata = tools.MixDataFrames({'all':Temp_alldata,'userinfo':userInfo.Temp_result_All},'date')
    
    userInfo.Temp_result_draw.to_csv('backtestdata.csv')
    userInfo.Temp_trade_info.to_csv('backtesttrade.csv')
    Temp_alldata.to_csv('backtestAll.csv')
    return userInfo.Temp_result_draw

#月營收增高 https://www.finlab.tw/%e4%b8%89%e7%a8%ae%e6%9c%88%e7%87%9f%e6%94%b6%e9%80%b2%e9%9a%8e%e7%9c%8b%e6%b3%95/#ji_ji_xuan_gu_cheng_zhang_fa
def backtest_monthRP_Up_Fast(mainParament:VirturlBackTestParameter):
    Temp_change = 0#換股剩餘天數
    userInfo = get_user_info.data_user_info(mainParament.money_start,mainParament.date_start,mainParament.date_end)
    Temp_result_pick = pd.DataFrame(columns=['date','選股數量'])
    All_data = gsh.get_stock_history(mainParament.buy_number,mainParament.date_start)
    add_one_day = userInfo.add_one_day
    sell_all_stock = userInfo.sell_all_stock
    buy_all_stock = userInfo.buy_all_stock
    for index,row in All_data.iterrows():
        has_trade = False
        while(userInfo.now_day != index):
            #加一天----------------------------
            if add_one_day() == False:
                break
        #出場訊號篩選--------------------------------------
        if Temp_change <= 0 and len(userInfo.handle_stock) > 0:
            sell_all_stock()
            has_trade = True
        #開始篩選--------------------------------------
        Temp_result0 = {}
        Temp_result = pd.DataFrame()
        if Temp_change <= 0:
            if bool_check_monthRP_pick:#月營收升高篩選(月為單位)
                Temp_result0['month'] = gsh.get_monthRP_up(userInfo.now_day,mainParament.smoothAVG,mainParament.upMonth)
            if bool_check_ROE_pick:#ROE
                Temp_result0['ROE'] = gsh.get_ROE_range(userInfo.now_day,mainParament.ROE_start,mainParament.ROE_end)
            if bool_check_PBR_pick:#PBR
                Temp_result0['PBR'] = gsh.get_PBR_range(userInfo.now_day,mainParament.PBR_start,mainParament.PBR_end)
            if bool_check_PER_pick:#PER
                Temp_result0['PER'] = gsh.get_PER_range(userInfo.now_day,mainParament.PER_start,mainParament.PER_end)
            Temp_result = tools.MixDataFrames(Temp_result0)
        #入場訊號篩選--------------------------------------
        if Temp_change <= 0 and len(userInfo.handle_stock) <= 0 and len(Temp_result) > mainParament.Pick_amount:
            Temp_buy0 = {'result':Temp_result}
            if bool_check_price_pick:
                Temp_buy0['price'] = gsh.get_price_range(userInfo.now_day,mainParament.price_high,mainParament.price_low,Temp_result)
                Temp_buy0['price'] = Temp_buy0['price'].sort_values(by='price', ascending=False)
            if bool_check_volume_pick:
                Temp_buy0['volume'] = gsh.get_AVG_value(userInfo.now_day,mainParament.volumeAVG,mainParament.volumeDays,Temp_result)
                Temp_buy0['volume'] = Temp_buy0['volume'].sort_values(by='volume', ascending=False)
            Temp_buy = tools.MixDataFrames(Temp_buy0)
            if Temp_buy0.__contains__('price') and Temp_buy0['price'].empty == False:
               Temp_buy = Temp_buy.sort_values(by='price', ascending=False)
            if Temp_buy0.__contains__('volume') and Temp_buy0['volume'].empty == False:
               Temp_buy = Temp_buy.sort_values(by='volume', ascending=False)
            buy_all_stock(Temp_buy)
            has_trade = True
        #更新資訊--------------------------------------
        if Temp_change <= 0:
            Temp_change = mainParament.change_days
        if has_trade or len(userInfo.handle_stock) > 0:
            userInfo.Record_userInfo()
            userInfo.Recod_tradeInfo()
            Temp_result_pick = pd.concat([Temp_result_pick,{'date':userInfo.now_day,
                                                '選股數量':len(Temp_result)}],ignore_index = True)
        #加一天----------------------------
        if add_one_day() == False:
            break
        else:
            Temp_change = Temp_change - 1
    #最後總結算----------------------------
    Temp_result_pick.set_index('date',inplace=True)
    Temp_alldata = tools.MixDataFrames({'draw':userInfo.Temp_result_draw,'pick':Temp_result_pick},'date')
    
    Temp_alldata = tools.MixDataFrames({'all':Temp_alldata,'userinfo':userInfo.Temp_result_All},'date')
    
    userInfo.Temp_result_draw.to_csv('backtestdata.csv')
    userInfo.Temp_trade_info.to_csv('backtesttrade.csv')
    Temp_alldata.to_csv('backtestAll.csv')
    return userInfo.Temp_result_draw
