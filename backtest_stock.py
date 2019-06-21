import pandas as pd
import numpy as np
import datetime
import get_stock_history
import tools
import draw_figur


def backtest_monthRP_Up(change,UpMon,AvgMon,Start_date,End_date,start_money):
    Temp_date = Start_date
    Temp_change = 0
    Temp_result = None
    Temp_stock_avg_price = 0
    Start_price = None
    Temp_result_draw = pd.DataFrame(columns = ['date','price'])
    Temp_stock_Count = 0
    Temp_money = start_money#當下現金
    Temp_stock_avg_money = 0 #手持股票張數

    while Temp_date < End_date:
        Temp_stock_avg_price = 0

        if Temp_change == 0:#檢查換股天數
            if Temp_stock_avg_money != 0:#檢查手持股票張數是否為0
                for value in range(0,len(Temp_result)):#平均股價
                    Nnumber = str(Temp_result.iloc[value].name)
                    #print(Nnumber)
                    if get_stock_history.get_stock_price(Nnumber,tools.DateTime2String(Temp_date)) != None:
                        Temp_stock_avg_price = Temp_stock_avg_price + get_stock_history.get_stock_price(Nnumber,tools.DateTime2String(Temp_date))
                        Temp_stock_Count = Temp_stock_Count + 1

                if Temp_stock_avg_price == 0:
                    Temp_date = Temp_date + datetime.timedelta(days=1)#加一天
                    Temp_stock_Count = 0
                    continue

                Temp_stock_avg_price = Temp_stock_avg_price / Temp_stock_Count
                Temp_stock_Count = 0
                
                Temp_money = Temp_stock_avg_money * Temp_stock_avg_price
                Temp_stock_avg_price = 0
            Temp_result = get_stock_history.get_monthRP_up(tools.changeDateMonth(Temp_date,-1),AvgMon,UpMon)
            

        for value in range(0,len(Temp_result)):#平均股價
            Nnumber = str(Temp_result.iloc[value].name)
            #print(Nnumber)
            if get_stock_history.get_stock_price(Nnumber,tools.DateTime2String(Temp_date)) != None:
                Temp_stock_avg_price = Temp_stock_avg_price + get_stock_history.get_stock_price(Nnumber,tools.DateTime2String(Temp_date))
                Temp_stock_Count = Temp_stock_Count + 1

        if Temp_stock_avg_price == 0:
            Temp_date = Temp_date + datetime.timedelta(days=1)#加一天
            Temp_stock_Count = 0
            continue

        Temp_stock_avg_price = Temp_stock_avg_price / Temp_stock_Count
        Temp_stock_Count = 0
        if Temp_change == 0:#檢查換股天數
            Temp_stock_avg_money = Temp_money / Temp_stock_avg_price
            Temp_change = change

       

        if Start_price == None:#紀錄第一天的股價
            Start_price = Temp_stock_avg_price

        Temp_result_draw.loc[(len(Temp_result_draw)+1)] = {'date':Temp_date,'price':Temp_stock_avg_price/Start_price}

        print('date:' + tools.DateTime2String(Temp_date))
        print('換股剩餘天數:' + str(Temp_change))
        print('目前資金:' + str(Temp_money))
        print('平均股價:' + str(Temp_stock_avg_price))
        print('股票張數:' + str(Temp_stock_avg_money//1000))
        print('挑出張數:' + str(len(Temp_result)))

        Temp_date = Temp_date + datetime.timedelta(days=1)#加一天
        Temp_change = Temp_change - 1#計算天數減一天
    Temp_result_draw.set_index('date',inplace=True)
    print(Temp_result_draw)
    draw_figur.draw_backtest(Temp_result_draw)
        

     
            
     