import pandas as pd
import numpy as np
import datetime
import get_stock_history
import tools
import draw_figur

bool_check_monthRP_pick = False
bool_check_PER_pick = False
bool_check_volume_pick = False

def set_check(monthRP_pick,PER_pick,volume_pick):
    global bool_check_monthRP_pick
    bool_check_monthRP_pick = monthRP_pick
    global bool_check_PER_pick
    bool_check_PER_pick = PER_pick
    global bool_check_volume_pick
    bool_check_volume_pick = volume_pick
    return


def backtest_monthRP_Up(change,AvgMon,UpMon,Start_date,End_date,start_money,PER_start,PER_end,
                        VolumeAVG,VolumeAVG_days):
    Temp_date = Start_date#模擬到的日期
    Temp_change = 0#換股剩餘天數
    Temp_result = None#選出的股票
    Temp_stock_avg_price = 0#選出股價的平均
    Temp_result_draw = pd.DataFrame(columns = ['date','price'])#最後輸出的結果
    Temp_result_picNumber = pd.DataFrame(columns = ['date','number'])#最後輸出選擇數量的結果
    Temp_result_pickStock = pd.DataFrame(columns = ['date','stock'])#最後輸出選擇股票的結果
    Temp_stock_Count = 0#選出之後有效股票數量
    Temp_money = start_money#當下現金
    Temp_stock_avg_money = 0 #手持股票張數

    while Temp_date <= End_date:
        Temp_stock_avg_price = 0
        Temp_stock_Count = 0

        if Temp_date.isoweekday() in [6,7]:#週末直接跳過
            print('星期' + str(Temp_date.isoweekday()))
            Temp_date = Temp_date + datetime.timedelta(days=1)#加一天
            continue

        if Temp_change == 0:#檢查換股天數,賣出股票
            if Temp_stock_avg_money != 0:#檢查手持股票張數是否為0
                for value in range(0,len(Temp_result)):#平均股價
                    Nnumber = str(Temp_result.iloc[value].name)
                    Temp_stock_price = get_stock_history.get_stock_price(Nnumber,tools.DateTime2String(Temp_date),
                                                                        get_stock_history.stock_data_kind.AdjClose)
                    if Temp_stock_price != None:
                        Temp_stock_avg_price = Temp_stock_avg_price + Temp_stock_price
                        Temp_stock_Count = Temp_stock_Count + 1

                if Temp_stock_avg_price == 0:
                    Temp_date = Temp_date + datetime.timedelta(days=1)#加一天
                    continue

                Temp_stock_avg_price = Temp_stock_avg_price / Temp_stock_Count
                Temp_stock_Count = 0
                
                Temp_money = Temp_stock_avg_money * Temp_stock_avg_price#出清股票
                Temp_stock_avg_price = 0
            
            Temp_result = pd.DataFrame()
            
            if bool_check_monthRP_pick:#月營收升高篩選
                Temp_result = get_stock_history.get_monthRP_up(Temp_date,AvgMon,UpMon)
                if Temp_result.empty == True:#沒篩出來直接換下個月
                    Temp_date = Temp_date + datetime.timedelta(weeks=4)#加一月
                    Temp_date = datetime.datetime(Temp_date.year,Temp_date.month,1)
                    continue

            if bool_check_PER_pick:#PER篩選
                Temp_result = pd.merge(Temp_result,get_stock_history.get_PER_range(tools.DateTime2String(Temp_date),PER_start,PER_end),on='公司代號',how='inner')

            if bool_check_volume_pick:#交易量篩選
                Temp_result = get_stock_history.get_AVG_value(Temp_date,VolumeAVG,VolumeAVG_days,Temp_result)            

        for value in range(0,len(Temp_result)):#平均股價
            Nnumber = str(Temp_result.iloc[value].name)
            Temp_stock_price = get_stock_history.get_stock_price(Nnumber,tools.DateTime2String(Temp_date),
                                                                get_stock_history.stock_data_kind.AdjClose)
            if Temp_stock_price != None:
                Temp_stock_avg_price = Temp_stock_avg_price + Temp_stock_price
                Temp_stock_Count = Temp_stock_Count + 1

        if Temp_stock_avg_price == 0:
            Temp_date = Temp_date + datetime.timedelta(days=1)#加一天
            continue

        Temp_stock_avg_price = Temp_stock_avg_price / Temp_stock_Count


        if Temp_change == 0:#檢查換股天數,更新資訊
            Temp_stock_avg_money = Temp_money / Temp_stock_avg_price#買入股票
            Temp_change = change

        Temp_result_draw.loc[(len(Temp_result_draw)+1)] = {'date':Temp_date,'price':(Temp_stock_avg_money * Temp_stock_avg_price)/start_money}
        Temp_result_picNumber.loc[(len(Temp_result_picNumber)+1)] = {'date':Temp_date,'number':len(Temp_result)}
        Temp_result_pickStock.loc[(len(Temp_result_pickStock)+1)] = {'date':Temp_date,'stock':Temp_result}

        print('---------------------------')
        print('date:' + tools.DateTime2String(Temp_date))
        print('換股剩餘天數:' + str(Temp_change))
        print('目前資產:' + str(Temp_stock_avg_money * Temp_stock_avg_price))
        print('平均股價:' + str(Temp_stock_avg_price))
        print('股票張數:' + str(Temp_stock_avg_money))
        print('挑出張數:' + str(len(Temp_result)))
        print('---------------------------')

        Temp_date = Temp_date + datetime.timedelta(days=1)#加一天
        Temp_change = Temp_change - 1#計算天數減一天

    Temp_result_draw.set_index('date',inplace=True)
    Temp_result_picNumber.set_index('date',inplace=True)
    Temp_result_pickStock.set_index('date',inplace=True)
    Temp_alldata = pd.merge(Temp_result_draw,Temp_result_picNumber,left_on='date',right_on='date')
    print(Temp_alldata)
    draw_figur.draw_backtest(Temp_result_draw)
    Temp_alldata = pd.merge(Temp_alldata,Temp_result_pickStock,left_on='date',right_on='date')
    Temp_result_draw.to_csv('backtestdata.csv')
    Temp_result_picNumber.to_csv('backtestdatanumber.csv')
    Temp_result_pickStock.to_csv('backtestdatastock.csv')
    Temp_alldata.to_csv('backtestAll.csv')

     
            
     