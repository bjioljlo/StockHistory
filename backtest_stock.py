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

def backtest_monthRP_Up(change,AvgMon,UpMon,Start_date,End_date,start_money,PER_start,PER_end,
                        VolumeAVG,VolumeAVG_days,price_high,price_low,PBR_start,PBR_end,
                        ROE_start,ROE_end):
    Temp_date = Start_date#模擬到的日期
    Temp_change = 0#換股剩餘天數
    Temp_result = None#選出的股票
    Temp_stock_avg_price = 0#選出股價的平均
    Temp_result_draw = pd.DataFrame(columns = ['date','price'])#最後輸出的結果
    Temp_result_All = pd.DataFrame(columns=['date','資產比例','買了幾張','平均股價','股票資產','剩餘現金'])
    Temp_result_picNumber = pd.DataFrame(columns = ['date','number'])#最後輸出選擇數量的結果
    Temp_result_pickStock = pd.DataFrame(columns = ['date','stock'])#最後輸出選擇股票的結果
    Temp_stock_Count = 0#選出之後有效股票數量
    Temp_money = start_money#當下現金
    Temp_stock_money = 0#股票資產
    Temp_stock_avg_money = 0 #手持股票張數

    while Temp_date <= End_date:
        Temp_stock_avg_price = 0
        Temp_stock_Count = 0

        if Temp_date.isoweekday() in [6,7]:#週末直接跳過
            print('星期' + str(Temp_date.isoweekday()))
            Temp_date = Temp_date + datetime.timedelta(days=1)#加一天
            continue

        if Temp_change == 0:#檢查換股天數,賣出股票,換股天數到了-------start
            if Temp_stock_avg_money != 0:#檢查手持股票張數是否為0,手中持有股票賣出
                
                Sell_stock_avg_price,Sell_stock_Count = avg_stock_price(Temp_date,Temp_result)#平均股價
                if Sell_stock_avg_price == 0:
                    Temp_date = Temp_date + datetime.timedelta(days=1)#加一天
                    continue
                Temp_money = Temp_money + (Temp_stock_avg_money * Sell_stock_avg_price) #出清股票
                Temp_stock_avg_price = 0
                Temp_stock_avg_money = 0
                Temp_result = pd.DataFrame()
            
            #取得要的表然後集合起來------------------start
            Temp_result = pd.DataFrame()
            Temp_result0 = {}

            Temp_GetInfoDate = tools.changeDateMonth(Temp_date,-1)
            
            if bool_check_monthRP_pick:#月營收升高篩選(月為單位)
                Temp_result0['month'] = get_stock_history.get_monthRP_up(Temp_GetInfoDate,AvgMon,UpMon)
                if Temp_result0['month'].empty == True:#沒篩出來直接換下個月
                    Temp_date = Temp_date + datetime.timedelta(weeks=4)#加一月
                    Temp_date = datetime.datetime(Temp_date.year,Temp_date.month,1)
                    continue
            if bool_check_PER_pick:#PER篩選
                Temp_result0['PER'] = get_stock_history.get_PER_range(tools.DateTime2String(Temp_date),PER_start,PER_end)
                if Temp_result0['PER'].empty == True:#沒篩出來直接換明天 
                    Temp_date = Temp_date + datetime.timedelta(days=1)#加一天
                    Temp_date = datetime.datetime(Temp_date.year,Temp_date.month,Temp_date.day)
                    continue
            if bool_check_PBR_pick:#PBR篩選
                Temp_result0['PBR'] = get_stock_history.get_PBR_rang(tools.DateTime2String(Temp_date),PBR_start,PBR_end)
                if Temp_result0['PBR'].empty == True:#沒篩出來直接換明天 
                    Temp_date = Temp_date + datetime.timedelta(days=1)#加一天
                    Temp_date = datetime.datetime(Temp_date.year,Temp_date.month,Temp_date.day)
                    continue
            if bool_check_ROE_pick:#PBR篩選
                Temp_result0['ROE'] = get_stock_history.get_ROE_rang(tools.DateTime2String(Temp_date),ROE_start,ROE_end)
                if Temp_result0['ROE'].empty == True:#沒篩出來直接換明天
                    Temp_date = Temp_date + datetime.timedelta(days=1)#加一天
                    Temp_date = datetime.datetime(Temp_date.year,Temp_date.month,Temp_date.day)
                    continue
            if bool_check_volume_pick:#交易量篩選
                Temp_result0['volume'] = get_stock_history.get_AVG_value(Temp_date,VolumeAVG,VolumeAVG_days,Temp_result)            
                if Temp_result0['volume'].empty == True:#沒篩出來直接換明天   
                    Temp_date = Temp_date + datetime.timedelta(days=1)#加一天
                    Temp_date = datetime.datetime(Temp_date.year,Temp_date.month,Temp_date.day)
                    continue
            for key,value in Temp_result0.items():
                if Temp_result.empty == True:
                    Temp_result = value
                else:
                    Temp_result = pd.merge(Temp_result,value,on='公司代號',how='inner')
                if Temp_result.empty == True:
                    break
            #取得要的表然後集合起來------------------end

            if bool_check_price_pick:#挑股價範圍
                for index,row in Temp_result.iterrows():
                    Temp_price = get_stock_history.get_stock_price(str(index),tools.DateTime2String(Temp_date),
                                                        get_stock_history.stock_data_kind.AdjClose)
                    if Temp_price != None and Temp_price >= price_low and Temp_price <= price_high:
                        print("")
                    else:
                        Temp_result = Temp_result.drop(index = index)
            

            if bool_check_pickOneStock:#只挑選一支股票來買
                if bool_check_volume_pick:#量最大
                    Temp_result.sort_values("Volume",ascending=False,inplace=True)
                    Temp_result = Temp_result.iloc[0:1]
                elif bool_check_PER_pick:#PER最低
                    Temp_result.sort_values("PER",ascending=True,inplace=True)
                    Temp_result = Temp_result.iloc[0:1]

        #檢查換股天數,賣出股票,換股天數到了-------end

        Temp_stock_avg_price,Temp_stock_Count = avg_stock_price(Temp_date,Temp_result)#平均股價每天跑
        if Temp_stock_avg_price == 0:
            Temp_date = Temp_date + datetime.timedelta(days=1)#加一天
            continue

        if Temp_change == 0:#檢查換股天數,更新資訊--------
            Temp_stock_avg_money = Temp_money // Temp_stock_avg_price#買入股票(1000為整數)
            Temp_stock_avg_money = Temp_stock_avg_money//1000
            Temp_stock_avg_money = Temp_stock_avg_money * 1000
            Temp_stock_money = Temp_stock_avg_money * Temp_stock_avg_price
            Temp_money = Temp_money - Temp_stock_money
            Temp_change = change

        Temp_result_draw.loc[(len(Temp_result_draw)+1)] = {'date':Temp_date,
                                                        'price':((Temp_stock_avg_money * Temp_stock_avg_price) + Temp_money)/start_money}
        Temp_result_picNumber.loc[(len(Temp_result_picNumber)+1)] = {'date':Temp_date,'number':len(Temp_result)}
        Temp_result_pickStock.loc[(len(Temp_result_pickStock)+1)] = {'date':Temp_date,'stock':Temp_result}

        Temp_result_All.loc[(len(Temp_result_All)+1)] = {'date':Temp_date,
                                                '資產比例':(Temp_money + Temp_stock_money)/start_money,
                                                '買了幾張':Temp_stock_avg_money,
                                                '平均股價':Temp_stock_avg_price,
                                                '股票資產':(Temp_stock_money),
                                                '剩餘現金':Temp_money}

        print('---------------------------')
        print('date:' + tools.DateTime2String(Temp_date))
        print('換股剩餘天數:' + str(Temp_change))
        print('目前資產:' + str(Temp_stock_avg_money * Temp_stock_avg_price))
        print('平均股價:' + str(Temp_stock_avg_price))
        print('股票張數:' + str(Temp_stock_avg_money))
        print('挑出張數:' + str(Temp_stock_Count))
        print('手中現金:' + str(Temp_money))
        print('---------------------------')

        Temp_date = Temp_date + datetime.timedelta(days=1)#加一天
        Temp_change = Temp_change - 1#計算天數減一天

    Temp_result_draw.set_index('date',inplace=True)
    Temp_result_All.set_index('date',inplace = True)
    Temp_result_picNumber.set_index('date',inplace=True)
    Temp_result_pickStock.set_index('date',inplace=True)
    Temp_alldata = pd.merge(Temp_result_draw,Temp_result_picNumber,left_on='date',right_on='date')
    
    draw_figur.draw_backtest(Temp_result_draw)
    Temp_alldata = pd.merge(Temp_alldata,Temp_result_pickStock,left_on='date',right_on='date')
    Temp_alldata = pd.merge(Temp_alldata,Temp_result_All,left_on='date',right_on='date')
    Temp_result_draw.to_csv('backtestdata.csv')
    Temp_result_picNumber.to_csv('backtestdatanumber.csv')
    Temp_result_pickStock.to_csv('backtestdatastock.csv')
    Temp_alldata.to_csv('backtestAll.csv')

     
def backtest_PERandPBR(reset,Start_date,End_date,start_money,PER_start,PER_end,PBR_start,PBR_end,pick_amount):
    Temp_reset = 0#休息日剩餘天數
    Temp_result_draw = pd.DataFrame(columns = ['date','price'])#最後輸出的結果
    Temp_result_All = pd.DataFrame(columns=['date','資產比例','買了幾張','挑出股票數量','股票資產','剩餘現金'])
    Temp_result_picNumber = pd.DataFrame(columns = ['date','number'])#最後輸出選擇數量的結果
    Temp_result_pickStock = pd.DataFrame(columns = ['date','stock'])#最後輸出選擇股票的結果

    userInfo = get_user_info.data_user_info(start_money,Start_date,End_date)

    while userInfo.now_day <= userInfo.end_day:
        #週末直接跳過
        if userInfo.now_day.isoweekday() in [6,7]:
            print('星期' + str(userInfo.now_day.isoweekday()))
            if userInfo.add_one_day() == False:#加一天
                break
            continue

        #先看看台積有沒有資料，如果沒有表示這天是非週末假日跳過 
        if get_stock_history.get_stock_price(2330,userInfo.now_day,get_stock_history.stock_data_kind.AdjClose) == None:
            print("今天沒開市跳過")
            if userInfo.add_one_day() == False:#加一天
                break
            continue

        #休息日直接跳過
        if Temp_reset > 0 and len(userInfo.handle_stock) == 0:
            print('reset time:day ' + str(Temp_reset))
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
            Temp_result0['PBR'] = get_stock_history.get_PBR_rang(userInfo.now_day,PBR_start,PBR_end)
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
        Temp_result_draw.loc[(len(Temp_result_draw)+1)] = {'date':userInfo.now_day,
                                                        'price':userInfo.get_user_all_asset()/userInfo.start_money}
        Temp_result_picNumber.loc[(len(Temp_result_picNumber)+1)] = {'date':userInfo.now_day,'number':len(userInfo.handle_stock)}
        Temp_result_pickStock.loc[(len(Temp_result_pickStock)+1)] = {'date':userInfo.now_day,'stock':userInfo.get_handle_stock()}

        Temp_result_All.loc[(len(Temp_result_All)+1)] = {'date':userInfo.now_day,
                                                '資產比例':userInfo.get_user_all_asset()/userInfo.start_money,
                                                '買了幾張':len(userInfo.handle_stock),
                                                '挑出股票數量':str(len(Temp_result)),
                                                '股票資產':userInfo.get_user_stock_asset(),
                                                '剩餘現金':userInfo.now_money}

        print('---------------------------')
        print('date:' + tools.DateTime2String(userInfo.now_day))
        print('換股剩餘天數:' + str(Temp_reset))
        print('目前資產:' + str(userInfo.get_user_all_asset()))
        print('股票張數:' + str(len(userInfo.handle_stock)))
        print('挑出股票數量:' + str(len(Temp_result)))
        print('手中現金:' + str(userInfo.now_money))
        print('---------------------------')

        if userInfo.add_one_day() == False:
            break


    Temp_result_draw.set_index('date',inplace=True)
    Temp_result_All.set_index('date',inplace = True)
    Temp_result_picNumber.set_index('date',inplace=True)
    Temp_result_pickStock.set_index('date',inplace=True)
    Temp_alldata = pd.merge(Temp_result_draw,Temp_result_picNumber,left_on='date',right_on='date')
    
    draw_figur.draw_backtest(Temp_result_draw)
    Temp_alldata = pd.merge(Temp_alldata,Temp_result_pickStock,left_on='date',right_on='date')
    Temp_alldata = pd.merge(Temp_alldata,Temp_result_All,left_on='date',right_on='date')
    Temp_result_draw.to_csv('backtestdata.csv')
    Temp_result_picNumber.to_csv('backtestdatanumber.csv')
    Temp_result_pickStock.to_csv('backtestdatastock.csv')
    Temp_alldata.to_csv('backtestAll.csv')

    