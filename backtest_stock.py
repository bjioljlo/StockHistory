import pandas as pd
import numpy as np
import datetime
import get_stock_history
import tools
import draw_figur
import get_user_info

bool_check_monthRP_pick = False
bool_check_PER_pick = False
bool_check_volume_pick = False
bool_check_pickOneStock = False
bool_check_price_pick = False
bool_check_PBR_pick = False
bool_check_ROE_pick = False

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
        Temp_stock_price = get_stock_history.get_stock_price(Nnumber,tools.DateTime2String(date),
                                                            get_stock_history.stock_data_kind.AdjClose)
        if Temp_stock_price != None:
            All_price = All_price + Temp_stock_price
            Count = Count + 1
    if All_price == 0 or Count == 0:
        return 0,0
    Result_avg_price = All_price / Count
    return Result_avg_price,Count
    
def backtest_PERandPBR(reset,Start_date,End_date,start_money,PER_start,PER_end,PBR_start,PBR_end,pick_amount):
    Temp_reset = 0#休息日剩餘天數

    Temp_result_pick = pd.DataFrame(columns=['date','選股數量'])

    userInfo = get_user_info.data_user_info(start_money,Start_date,End_date)

    while userInfo.now_day <= userInfo.end_day:
        #週末直接跳過
        if userInfo.now_day.isoweekday() in [6,7]:
            print(str(userInfo.now_day) + 'is 星期' + str(userInfo.now_day.isoweekday()))
            if userInfo.add_one_day() == False:#加一天
                break
            continue

        #先看看台積有沒有資料，如果沒有表示這天是非週末假日跳過 
        if get_stock_history.get_stock_price(2330,userInfo.now_day,get_stock_history.stock_data_kind.AdjClose) == None:
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

        #開始篩選
        Temp_result0 = {}
        Temp_result = pd.DataFrame()
        if bool_check_PER_pick:#PER pick
            Temp_result0['PER'] = get_stock_history.get_PER_range(userInfo.now_day,PER_start,PER_end)
        if bool_check_PBR_pick:#PBR pick    
            Temp_result0['PBR'] = get_stock_history.get_PBR_range(userInfo.now_day,PBR_start,PBR_end)
        Temp_result = tools.MixDataFrames(Temp_result0)

        #出場訊號篩選--------------------------------------
        if len(Temp_result) < pick_amount and len(userInfo.handle_stock) > 0:
            userInfo.sell_all_stock()
            Temp_reset = reset
        
        #入場訊號篩選--------------------------------------
        if len(Temp_result) >= pick_amount and Temp_reset == 0 and len(userInfo.handle_stock) == 0:
            Temp_buy = get_stock_history.get_AVG_value(userInfo.now_day,5000000,1,Temp_result)
            Temp_buy = Temp_buy.sort_values(by='Volume', ascending=False)
            userInfo.buy_all_stock(Temp_buy)
            Temp_reset = reset

        #更新資訊--------------------------------------
        userInfo.Record_userInfo()
        userInfo.Recod_tradeInfo()
        Temp_result_pick = Temp_result_pick.append({'date':userInfo.now_day,
                                                '選股數量':len(Temp_result)},ignore_index = True)
        #加一天----------------------------
        if userInfo.add_one_day() == False:
            break

    #最後總結算----------------------------
    Temp_result_pick.set_index('date',inplace=True)
    Temp_alldata = tools.MixDataFrames({'draw':userInfo.Temp_result_draw,'pick':Temp_result_pick},'date')
    draw_figur.draw_backtest(userInfo.Temp_result_draw)
    Temp_alldata = tools.MixDataFrames({'all':Temp_alldata,'userinfo':userInfo.Temp_result_All},'date')
    
    userInfo.Temp_result_draw.to_csv('backtestdata.csv')
    userInfo.Temp_trade_info.to_csv('backtesttrade.csv')
    Temp_alldata.to_csv('backtestAll.csv')

def backtest_monthRP_Up(change,AvgMon,UpMon,Start_date,End_date,start_money,PER_start,PER_end,
                        VolumeAVG,VolumeAVG_days,price_high,price_low,PBR_start,PBR_end,
                        ROE_start,ROE_end):
    Temp_change = 0#換股剩餘天數
    userInfo = get_user_info.data_user_info(start_money,Start_date,End_date)
    Temp_result_pick = pd.DataFrame(columns=['date','選股數量'])
    while userInfo.now_day <= userInfo.end_day:

        #週末直接跳過
        if userInfo.now_day.isoweekday() in [6,7]:
            print(str(userInfo.now_day) + 'is 星期' + str(userInfo.now_day.isoweekday()))
            if userInfo.add_one_day() == False:#加一天
                break
            continue
        #先看看台積有沒有資料，如果沒有表示這天是非週末假日跳過 
        if get_stock_history.get_stock_price(2330,userInfo.now_day,get_stock_history.stock_data_kind.AdjClose) == None:
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
                Temp_result0['month'] = get_stock_history.get_monthRP_up(userInfo.now_day,AvgMon,UpMon)
            if bool_check_ROE_pick:#ROE
                Temp_result0['ROE'] = get_stock_history.get_ROE_range(userInfo.now_day,ROE_start,ROE_end)
            if bool_check_PBR_pick:#PBR
                Temp_result0['PBR'] = get_stock_history.get_PBR_range(userInfo.now_day,PBR_start,PBR_end)
            if bool_check_PER_pick:#PER
                Temp_result0['PER'] = get_stock_history.get_PER_range(userInfo.now_day,PER_start,PER_end)
            Temp_result = tools.MixDataFrames(Temp_result0)

        #入場訊號篩選--------------------------------------
        if Temp_change <= 0 and len(userInfo.handle_stock) <= 0:
            Temp_buy0 = {'result':Temp_result}
            if bool_check_volume_pick:
                Temp_buy0['volume'] = get_stock_history.get_AVG_value(userInfo.now_day,VolumeAVG,VolumeAVG_days,Temp_result)
                Temp_buy0['volume'] = Temp_buy0['volume'].sort_values(by='volume', ascending=False)
            if bool_check_price_pick:
                Temp_buy0['price'] = get_stock_history.get_price_range(userInfo.now_day,price_high,price_low,Temp_result)
                Temp_buy0['price'] = Temp_buy0['price'].sort_values(by='price', ascending=False)
            Temp_buy = tools.MixDataFrames(Temp_buy0)
            userInfo.buy_all_stock(Temp_buy)

        #更新資訊--------------------------------------
        if Temp_change <= 0 and len(userInfo.handle_stock) >= 0:
            Temp_change = change
        userInfo.Record_userInfo()
        userInfo.Recod_tradeInfo()
        Temp_result_pick = Temp_result_pick.append({'date':userInfo.now_day,
                                                '選股數量':len(Temp_result)},ignore_index = True)
        #加一天----------------------------
        if userInfo.add_one_day() == False:
            break
        else:
            Temp_change = Temp_change - 1

    #最後總結算----------------------------
    Temp_result_pick.set_index('date',inplace=True)
    Temp_alldata = tools.MixDataFrames({'draw':userInfo.Temp_result_draw,'pick':Temp_result_pick},'date')
    draw_figur.draw_backtest(userInfo.Temp_result_draw)
    Temp_alldata = tools.MixDataFrames({'all':Temp_alldata,'userinfo':userInfo.Temp_result_All},'date')
    
    userInfo.Temp_result_draw.to_csv('backtestdata.csv')
    userInfo.Temp_trade_info.to_csv('backtesttrade.csv')
    Temp_alldata.to_csv('backtestAll.csv')
