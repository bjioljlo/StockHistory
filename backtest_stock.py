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

        #開始篩選--------------------------------------
        Temp_result0 = {}
        Temp_result = pd.DataFrame()
        if bool_check_PER_pick:#PER pick
            Temp_result0['PER'] = get_stock_history.get_PER_range(userInfo.now_day,mainParament.PER_start,mainParament.PER_end)
        if bool_check_PBR_pick:#PBR pick    
            Temp_result0['PBR'] = get_stock_history.get_PBR_range(userInfo.now_day,mainParament.PBR_start,mainParament.PBR_end)
        Temp_result = tools.MixDataFrames(Temp_result0)

        #出場訊號篩選--------------------------------------
        if len(Temp_result) < mainParament.Pick_amount and len(userInfo.handle_stock) > 0:
            userInfo.sell_all_stock()
            Temp_reset = mainParament.change_days
        
        #入場訊號篩選--------------------------------------
        if len(Temp_result) > mainParament.Pick_amount and Temp_reset == 0 and len(userInfo.handle_stock) == 0:
            Temp_buy0 = {'result':Temp_result}
            if bool_check_price_pick:
                Temp_buy0['price'] = get_stock_history.get_price_range(userInfo.now_day,mainParament.price_high,mainParament.price_low,Temp_result)
                Temp_buy0['price'] = Temp_buy0['price'].sort_values(by='price', ascending=False)
            if bool_check_volume_pick:
                Temp_buy0['volume'] = get_stock_history.get_AVG_value(userInfo.now_day,mainParament.volumeAVG,mainParament.volumeDays,Temp_result)
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
                Temp_result0['month'] = get_stock_history.get_monthRP_up(userInfo.now_day,mainParament.smoothAVG,mainParament.upMonth)
            if bool_check_ROE_pick:#ROE
                Temp_result0['ROE'] = get_stock_history.get_ROE_range(userInfo.now_day,mainParament.ROE_start,mainParament.ROE_end)
            if bool_check_PBR_pick:#PBR
                Temp_result0['PBR'] = get_stock_history.get_PBR_range(userInfo.now_day,mainParament.PBR_start,mainParament.PBR_end)
            if bool_check_PER_pick:#PER
                Temp_result0['PER'] = get_stock_history.get_PER_range(userInfo.now_day,mainParament.PER_start,mainParament.PER_end)
            Temp_result = tools.MixDataFrames(Temp_result0)

        #入場訊號篩選--------------------------------------
        if Temp_change <= 0 and len(userInfo.handle_stock) <= 0 and len(Temp_result) > mainParament.Pick_amount:
            Temp_buy0 = {'result':Temp_result}
            if bool_check_price_pick:
                Temp_buy0['price'] = get_stock_history.get_price_range(userInfo.now_day,mainParament.price_high,mainParament.price_low,Temp_result)
                Temp_buy0['price'] = Temp_buy0['price'].sort_values(by='price', ascending=False)
            if bool_check_volume_pick:
                Temp_buy0['volume'] = get_stock_history.get_AVG_value(userInfo.now_day,mainParament.volumeAVG,mainParament.volumeDays,Temp_result)
                Temp_buy0['volume'] = Temp_buy0['volume'].sort_values(by='volume', ascending=False)
            Temp_buy = tools.MixDataFrames(Temp_buy0)
            #if Temp_buy0['price'].empty == False:
            #    Temp_buy = Temp_buy.sort_values(by='price', ascending=False)
            if Temp_buy0['volume'].empty == False:
                Temp_buy = Temp_buy.sort_values(by='volume', ascending=False)
            userInfo.buy_all_stock(Temp_buy)

        #更新資訊--------------------------------------
        if Temp_change <= 0 and len(userInfo.handle_stock) > 0:
            Temp_change = mainParament.change_days
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
#定期定額 
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
        if get_stock_history.get_stock_price(2330,userInfo.now_day,get_stock_history.stock_data_kind.AdjClose) == None:
            print(str(userInfo.now_day) + "這天沒開市")
            if userInfo.add_one_day() == False:#加一天
                break
            continue

        #開始篩選--------------------------------------
        Temp_result = pd.DataFrame()
        Temp_result = Temp_result.append({'date':userInfo.now_day,
                                                'number':mainParament.buy_number},ignore_index = True)

        #入場訊號篩選--------------------------------------
        if userInfo.now_day.month != buy_month.month and userInfo.now_day.day >= mainParament.buy_day:
            Temp_price = get_stock_history.get_stock_price(mainParament.buy_number,userInfo.now_day,get_stock_history.stock_data_kind.AdjClose)
            userInfo.now_money = userInfo.now_money + mainParament.money_start
            userInfo.start_money = userInfo.start_money + mainParament.money_start
            Temp_stockNumber = tools.Count_Stock_Amount(mainParament.money_start,Temp_price)
            userInfo.buy_stock(mainParament.buy_number,Temp_stockNumber)
            buy_month = userInfo.now_day

        #更新資訊--------------------------------------   
        if userInfo.start_money > 0:
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
        #出場訊號篩選--------------------------------------
        if len(userInfo.handle_stock) > 0:
            Temp_data = userInfo.handle_stock
            for key,value in list(Temp_data.items()):
                if get_stock_history.get_stock_price(key,userInfo.now_day,get_stock_history.stock_data_kind.AdjClose) < get_stock_history.get_stock_MA(key,userInfo.now_day,20):
                    userInfo.sell_stock(key,value.amount)
        #開始篩選--------------------------------------
        Temp_result = pd.DataFrame()
        Temp_result0 = {}
        if Temp_reset <= 0:
            if bool_check_ROE_pick == True:
                Temp_result0['ROE'] = get_stock_history.get_ROE_range(userInfo.now_day,mainParament.ROE_start,mainParament.ROE_end)
            if bool_check_ROE_pick == True:
                Temp_result0['ROE_last_seson'] = get_stock_history.get_ROE_range(userInfo.now_day - datetime.timedelta(weeks = 4),1,10000)
            Temp_result = tools.MixDataFrames(Temp_result0)
            
        #入場訊號篩選--------------------------------------
        if Temp_reset <= 0 and len(Temp_result) > 0:
            Temp_buy0 = {'result':Temp_result}
            if bool_check_PBR_pick:
                Temp_buy0['PBR'] = get_stock_history.get_PBR_range(userInfo.now_day,mainParament.PBR_start,mainParament.PBR_end)
            if bool_check_price_pick:
                Temp_buy0['price'] = get_stock_history.get_price_range(userInfo.now_day,mainParament.price_high,mainParament.price_low,Temp_result)
            if bool_check_volume_pick:
                Temp_buy0['volume'] = get_stock_history.get_AVG_value(userInfo.now_day,mainParament.volumeAVG,mainParament.volumeDays,Temp_result)
            
            Temp_buy0['point'] = pd.DataFrame(columns=['公司代號','point'])
            for index,row in Temp_result.iterrows():
                try:
                    temp = Temp_buy0['PBR'].at[index,'PBR']
                except:
                    continue
                if get_stock_history.check_no_use_stock(index):
                    continue
                Temp_point = (row['ROE_x'] / row['ROE_y']) / Temp_buy0['PBR'].at[index,'PBR']
                Temp_buy0['point'] = Temp_buy0['point'].append({'公司代號':index,'point':Temp_point},ignore_index=True)
            Temp_buy0['point'] = Temp_buy0['point'].astype({'公司代號':'int','point':'float'})
            Temp_buy0['point'] = Temp_buy0['point'].set_index('公司代號')
            Temp_buy = tools.MixDataFrames(Temp_buy0)

            Temp_buy1 = {'result':Temp_buy}
            Temp_buy1['high'] = get_stock_history.get_RecordHigh_range(userInfo.now_day,mainParament.change_days,mainParament.Record_high_day,Temp_buy)
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
        Temp_result_pick = Temp_result_pick.append({'date':userInfo.now_day,
                                                '選股數量':len(Temp_result)},ignore_index = True)
        #加一天----------------------------
        if userInfo.add_one_day() == False:
            break
        else:
            Temp_reset = Temp_reset - 1

    #最後總結算----------------------------
    Temp_result_pick.set_index('date',inplace=True)
    Temp_alldata = tools.MixDataFrames({'draw':userInfo.Temp_result_draw,'pick':Temp_result_pick},'date')
    draw_figur.draw_backtest(userInfo.Temp_result_draw)
    Temp_alldata = tools.MixDataFrames({'all':Temp_alldata,'userinfo':userInfo.Temp_result_All},'date')
    
    userInfo.Temp_result_draw.to_csv('backtestdata.csv')
    userInfo.Temp_trade_info.to_csv('backtesttrade.csv')
    Temp_alldata.to_csv('backtestAll.csv')