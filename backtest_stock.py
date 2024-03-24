import pandas as pd
import numpy as np
from datetime import datetime,timedelta
#from backtesting import Backtest, Strategy #引入回測和交易策略功能
import talib as talib
from GetExternalData import TGetExternalData 
import GetStockData
import tools
from tools import MixDataFrames,Count_Stock_Amount
from StockInfosInBackTest import StockInfoDatasInBackTestPriceByToday
import Infomation_type as info
from Infomation_type import stock_data_kind
from IParameter import RecordBackTestParameter
from StockInfoData import BaseInfoData

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
 
def backtest_KD_pick(mainParament:RecordBackTestParameter):
    '''KD值選股 https://www.finlab.tw/%e7%94%a8kd%e5%80%bc%e9%81%b8%e8%82%a1%ef%bc%9a%e9%82%84%e9%9c%80%e6%90%ad%e9%85%8d%e9%80%99%e4%b8%89%e7%a8%ae%e6%8c%87%e6%a8%99/'''
    userInfo = StockInfoDatasInBackTestPriceByToday(BaseInfoData(mainParament.money_start,mainParament.date_start,mainParament.date_end))
    Temp_result_pick = pd.DataFrame(columns=['date','選股數量'])
    Temp_table = TGetExternalData().get_stock_history(mainParament.buy_number,mainParament.date_start)
    All_stock_signal = dict()
      
    ROE_record_day = datetime.strptime("2000-01-01","%Y-%m-%d")
    buy_data = pd.DataFrame(columns = ['Date','code']).set_index('Date')
    sell_data = pd.DataFrame(columns = ['Date','code']).set_index('Date')
    ROE_data = {}
    add_one_day = userInfo.AddOneDay
    changeDateMonth = tools.changeDateMonth
    get_ROE_range = GetStockData.get_ROE_range
    MixDataFrames = tools.MixDataFrames
    sell_stock = userInfo.SellStock
    buy_all_stock = userInfo.BuyAllStock
    for index,row in Temp_table.iterrows():
        if index < userInfo.BaseInfoData.now_day:
            continue
        while userInfo.BaseInfoData.now_day != index:
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
                if tools.check_no_use_stock(key) == True:
                    print('get_stock_price: ' + str(key) + ' in no use')
                    continue
                if All_stock_signal.__contains__(key):
                    continue
                table = TGetExternalData().get_stock_history(key,"2005-01-01")
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
        if len(userInfo.HandleStock) > 0:
            Temp_data = userInfo.HandleStock
            for key,value in list(Temp_data.items()):
                if sell_numbers.__contains__(int(key)):
                    sell_stock(key,value.Amount)
                    has_trade = True
        #入場訊號篩選--------------------------------------
        if len(buy_numbers) > 0 :
            Temp_buy = pd.DataFrame(columns={'code','volume'})
            for number in buy_numbers:
                volume = GetStockData.get_stock_price(number,tools.DateTime2String(userInfo.BaseInfoData.now_day),stock_data_kind.Volume)
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
            userInfo.RecordUserInfo()
            userInfo.RecodTradeInfo()
            Temp_result_pick = Temp_result_pick.append({'date':userInfo.BaseInfoData.now_day,
                                                '選股數量':len(buy_numbers)},ignore_index = True)
    
    buy_data = buy_data.set_index('Date')
    buy_data.to_csv('buy.csv')
    sell_data = sell_data.set_index('Date')
    sell_data.to_csv('sell.csv')
    #最後總結算----------------------------
    Temp_result_pick.set_index('date',inplace=True)
    userInfo.RunFinish()
    Temp_alldata = tools.MixDataFrames({'draw':userInfo._TempResultDraw,'pick':Temp_result_pick},'date')
    
    Temp_alldata = tools.MixDataFrames({'all':Temp_alldata,'userinfo':userInfo._TempResultAll},'date')
    
    userInfo._TempResultDraw.set_index('date').to_csv('backtestdata.csv')
    userInfo._TempTradeInfo.set_index('date').to_csv('backtesttrade.csv')
    Temp_alldata.set_index('date').to_csv('backtestAll.csv')   
    return userInfo._TempResultDraw.set_index('date')
def backtest_PEG_pick_Fast(mainParament:RecordBackTestParameter):
    ''' PEG選股外加月營收增高 https://www.finlab.tw/finlab-tw-stock-peg-strategy/#PEG_ding_yi '''
    userInfo = StockInfoDatasInBackTestPriceByToday(BaseInfoData(mainParament.money_start,mainParament.date_start,mainParament.date_end))
    buy_month = mainParament.date_start
    Temp_result_pick = pd.DataFrame(columns=['date','選股數量'])
    All_data = TGetExternalData().get_stock_history(mainParament.buy_number,mainParament.date_start)
    add_one_day = userInfo.AddOneDay
    Record_userInfo = userInfo.RecordUserInfo
    Recod_tradeInfo = userInfo.RecodTradeInfo
    sell_stock = userInfo.SellStock
    buy_all_stock = userInfo.BuyAllStock
    for index,row in All_data.iterrows():
        has_trade = False
        while(userInfo.BaseInfoData.now_day != index):
            #加一天----------------------------
            if add_one_day() == False:
                break
        #出場訊號篩選-----------------------------------
        if len(userInfo.HandleStock) > 0:
            Temp_data = userInfo.HandleStock
            for key,value in list(Temp_data.items()):
                if GetStockData.get_stock_price(key,userInfo.BaseInfoData.now_day,info.Price_type.Close) < GetStockData.get_stock_MA(key,userInfo.BaseInfoData.now_day,20):
                    sell_stock(key,value.Amount)
                    has_trade = True
        #開始篩選--------------------------------------
        #入場訊號篩選--------------------------------------
        Temp_buy = pd.DataFrame()
        if userInfo.BaseInfoData.now_day.day >= mainParament.buy_day:
            if userInfo.BaseInfoData.now_day.month != buy_month.month or userInfo.BaseInfoData.now_day.year != buy_month.year:
                
                Temp_result0 = {}
                if bool_check_monthRP_pick:
                    Temp_result0['month'] = GetStockData.get_monthRP_up(userInfo.BaseInfoData.now_day,mainParament.smoothAVG,mainParament.upMonth)
                    Temp_result0['PEG'] = GetStockData.get_PEG_range(userInfo.BaseInfoData.now_day,0.66,1)
                    Temp_result0['result'] = MixDataFrames(Temp_result0)
                Temp_buy = Temp_result0['result']
                if Temp_buy.empty == False:
                    Temp_buy = Temp_buy.sort_values(by='PEG')
                    Temp_buy = Temp_buy.head(10)
                    buy_all_stock(Temp_buy)
                    has_trade = True
                buy_month = userInfo.BaseInfoData.now_day
        #更新資訊--------------------------------------
        if len(userInfo.HandleStock) > 0 or has_trade:
            Record_userInfo()
            Recod_tradeInfo()
            Temp_result_pick = pd.concat(Temp_result_pick, pd.DataFrame({'date':[userInfo.BaseInfoData.now_day],
                                                                        '選股數量':[len(Temp_buy)]}),
                                                                        ignore_index = True)
        #加一天----------------------------
        if userInfo.AddOneDay() == False:
            break
        else:
            continue
    #最後總結算----------------------------
    Temp_result_pick.set_index('date',inplace=True)
    userInfo.RunFinish()
    Temp_alldata = MixDataFrames({'draw':userInfo._TempResultDraw,'pick':Temp_result_pick},'date')
    Temp_alldata = MixDataFrames({'all':Temp_alldata,'userinfo':userInfo._TempResultAll},'date')
    
    userInfo._TempResultDraw.to_csv('backtestdata.csv')
    userInfo._TempTradeInfo.to_csv('backtesttrade.csv')
    Temp_alldata.to_csv('backtestAll.csv')
    return userInfo._TempResultDraw
def backtest_Regular_quota_Fast(mainParament:RecordBackTestParameter):
    '''定期定額'''
    userInfo = StockInfoDatasInBackTestPriceByToday(BaseInfoData(0,mainParament.date_start,mainParament.date_end))
    buy_month = mainParament.date_start
    Temp_result_pick = pd.DataFrame(columns=['date','選股數量'])
    
    All_data = TGetExternalData().get_stock_history(mainParament.buy_number,mainParament.date_start)
    add_one_day = userInfo.AddOneDay
    Record_userInfo = userInfo.RecordUserInfo
    Recod_tradeInfo = userInfo.RecodTradeInfo
    buy_stock = userInfo.BuyStock
    for index,row in All_data.iterrows():
        while(userInfo.BaseInfoData.now_day != index):#消掉假日的誤差用的
            #加一天----------------------------
            if add_one_day() == False:
                break
        #開始篩選--------------------------------------
        #定期定額不用篩選--------------------------------------
        #入場訊號篩選--------------------------------------
        if userInfo.BaseInfoData.now_day.month != buy_month.month and userInfo.BaseInfoData.now_day.day >= mainParament.buy_day:
            Temp_price = row['Adj Close']
            userInfo.BaseInfoData.now_money = userInfo.BaseInfoData.now_money + mainParament.money_start
            userInfo.BaseInfoData.start_money = userInfo.BaseInfoData.start_money + mainParament.money_start
            Temp_stockNumber = Count_Stock_Amount(mainParament.money_start,Temp_price)
            buy_stock(mainParament.buy_number,Temp_stockNumber)
            buy_month = userInfo.BaseInfoData.now_day
            #更新資訊--------------------------------------   
            Record_userInfo()
            Recod_tradeInfo()
            Temp_result_pick = pd.concat([Temp_result_pick, pd.DataFrame({'date':[userInfo.BaseInfoData.now_day],
                                                                        '選股數量':[1]})],
                                                                        ignore_index = True)
        #加一天----------------------------
        if add_one_day() == False:
            break
    
    #最後總結算----------------------------
    Temp_result_pick.set_index('date',inplace=True)
    userInfo.RunFinish()
    Temp_alldata = MixDataFrames({'draw':userInfo._TempResultDraw,'pick':Temp_result_pick},'date')
    Temp_alldata = MixDataFrames({'all':Temp_alldata,'userinfo':userInfo._TempResultAll},'date')
    
    userInfo._TempResultDraw.to_csv('backtestdata.csv')
    userInfo._TempTradeInfo.to_csv('backtesttrade.csv')
    Temp_alldata.to_csv('backtestAll.csv')
    return userInfo._TempResultDraw
def backtest_Record_high_Fast(mainParament:RecordBackTestParameter):
    '''#創新高 https://www.finlab.tw/break-new-high-roe-stock/'''
    Temp_reset = 0#休息日剩餘天數
    userInfo = StockInfoDatasInBackTestPriceByToday(BaseInfoData(mainParament.money_start,mainParament.date_start,mainParament.date_end))
    Temp_result_pick = pd.DataFrame(columns=['date','選股數量'])
    All_data = TGetExternalData().get_stock_history(mainParament.buy_number,mainParament.date_start)
    add_one_day = userInfo.AddOneDay
    Record_userInfo = userInfo.RecordUserInfo
    Recod_tradeInfo = userInfo.RecodTradeInfo
    sell_stock = userInfo.SellStock
    buy_all_stock = userInfo.BuyAllStock
    for index,row in All_data.iterrows():
        has_trade = False
        while(userInfo.BaseInfoData.now_day != index):
            #加一天----------------------------
            if add_one_day() == False:
                break
        #出場訊號篩選--------------------------------------
        if len(userInfo.HandleStock) > 0:
            Temp_data = userInfo.HandleStock
            for key,value in list(Temp_data.items()):
                if TGetExternalData().get_stock_price(key,userInfo.BaseInfoData.now_day,stock_data_kind.AdjClose) < GetStockData.get_stock_MA(key,userInfo.BaseInfoData.now_day,20):
                    sell_stock(key,value.Amount)
                    has_trade = True
        #開始篩選--------------------------------------
        Temp_result = pd.DataFrame()
        Temp_result0 = {}
        if Temp_reset <= 0:
            if bool_check_ROE_pick:
                Temp_result0['ROE'] = GetStockData.get_ROE_range(userInfo.BaseInfoData.now_day,mainParament.ROE_end,mainParament.ROE_start)
            if bool_check_ROE_pick:
                Temp_result0['ROE_last_seson'] = GetStockData.get_ROE_range(userInfo.BaseInfoData.now_day - timedelta(weeks = 12),10000,1)
            if bool_check_PBR_pick:
                Temp_result0['PBR'] = GetStockData.get_PBR_range(userInfo.BaseInfoData.now_day,mainParament.PBR_end,mainParament.PBR_start)
            Temp_result = MixDataFrames(Temp_result0)
            
        #入場訊號篩選--------------------------------------
        if Temp_reset <= 0 and len(Temp_result) > 0:
            Temp_buy0 = {'result':Temp_result}
            Temp_buy0['result']['point'] = (Temp_result['ROE'] / Temp_result['ROE_R']) / Temp_result['PBR']
            if bool_check_price_pick:
                Temp_buy0['price'] = GetStockData.All_Stock_Filters_fuc(userInfo.BaseInfoData.now_day,Temp_result).get_Filter('price',mainParament.price_high,mainParament.price_low,info.Price_type.Close)
                Temp_buy0['result'] = MixDataFrames(Temp_buy0)
            if bool_check_volume_pick:
                Temp_buy0['volume'] = GetStockData.get_AVG_value(userInfo.BaseInfoData.now_day,mainParament.volumeAVG,mainParament.volumeDays,Temp_result)
                Temp_buy0['result'] = MixDataFrames(Temp_buy0)

            Temp_buy = MixDataFrames(Temp_buy0)

            Temp_buy = Temp_buy.sort_values(by='point', ascending=False)
            
            Temp_buy1 = {'result':Temp_buy}
            #Temp_buy1['high'] = gsh.get_RecordHigh_range(userInfo.BaseInfoData.now_day,mainParament.change_days,mainParament.Record_high_day,Temp_buy)
            Temp_buy1['high'] = GetStockData.All_Stock_Filters_fuc(userInfo.BaseInfoData.now_day,Temp_buy).get_Filter_RecordHigh(mainParament.change_days,mainParament.Record_high_day,info.Price_type.High)
            Temp_buy = MixDataFrames(Temp_buy1)

            if Temp_buy.empty == False:
                Temp_buy = Temp_buy.sort_values(by='point', ascending=False)
                Temp_buy = Temp_buy.head(3)
                buy_all_stock(Temp_buy)
                has_trade = True
        #更新資訊--------------------------------------
        if Temp_reset <= 0:
            Temp_reset = mainParament.change_days
        if len(userInfo.HandleStock) > 0 or has_trade:
            Record_userInfo()
            Recod_tradeInfo()
            Temp_result_pick = pd.concat([Temp_result_pick, pd.DataFrame({'date':[userInfo.BaseInfoData.now_day],
                                                                        '選股數量':[len(Temp_result)]})],
                                                                        ignore_index = True)
        #加一天----------------------------
        if add_one_day() == False:
            break
        else:
            Temp_reset = Temp_reset - 1

    #最後總結算----------------------------
    Temp_result_pick.set_index('date',inplace=True)
    userInfo.RunFinish()
    Temp_alldata = MixDataFrames({'draw':userInfo._TempResultDraw,'pick':Temp_result_pick},'date')
    Temp_alldata = MixDataFrames({'all':Temp_alldata,'userinfo':userInfo._TempResultAll},'date')
    userInfo._TempResultDraw.to_csv('backtestdata.csv')
    userInfo._TempTradeInfo.to_csv('backtesttrade.csv')
    Temp_alldata.to_csv('backtestAll.csv')
    return userInfo._TempResultDraw
def backtest_PERandPBR_Fast(mainParament:RecordBackTestParameter):
    '''#14年14倍 https://www.finlab.tw/%E6%AF%94%E7%AD%96%E7%95%A5%E7%8B%97%E9%82%84%E8%A6%81%E5%AE%89%E5%85%A8%E7%9A%84%E9%81%B8%E8%82%A1%E7%AD%96%E7%95%A5%EF%BC%81/'''
    Temp_reset = 0#休息日剩餘天數
    Temp_changeDays = 0#換股剩餘天數
    Temp_result_pick = pd.DataFrame(columns=['date','選股數量'])

    userInfo = StockInfoDatasInBackTestPriceByToday(BaseInfoData(mainParament.money_start,mainParament.date_start,mainParament.date_end))

    All_data = TGetExternalData().get_stock_history(mainParament.buy_number,mainParament.date_start)
    
    add_one_day = userInfo.AddOneDay
    sell_all_stock = userInfo.SellAllStock
    buy_all_stock = userInfo.BuyAllStock
    for index,row in All_data.iterrows():
        has_trade = False
        while(userInfo.BaseInfoData.now_day != index):
            #加一天----------------------------
            if add_one_day() == False:
                break
        
        #休息日直接跳過
        if Temp_reset > 0 and len(userInfo.HandleStock) == 0:
            print(str(userInfo.BaseInfoData.now_day) + ' is reset time:第' + str(Temp_reset) + '天')
            if add_one_day() == False:#加一天
                break
            Temp_reset = Temp_reset - 1
            continue
        
        #開始篩選--------------------------------------
        Temp_result0 = {}
        Temp_result = pd.DataFrame()
        if bool_check_PER_pick:#PER pick
            Temp_result0['PER'] = GetStockData.get_PER_range(userInfo.BaseInfoData.now_day,mainParament.PER_end,mainParament.PER_start)
        if bool_check_PBR_pick:#PBR pick    
            Temp_result0['PBR'] = GetStockData.get_PBR_range(userInfo.BaseInfoData.now_day,mainParament.PBR_end,mainParament.PBR_start)
        Temp_result = tools.MixDataFrames(Temp_result0)

        #出場訊號篩選--------------------------------------
        if len(Temp_result) < mainParament.Pick_amount and len(userInfo.HandleStock) > 0:
            sell_all_stock()
            Temp_reset = 120
            has_trade = True
        #出場訊號篩選--------------------------------------
        if Temp_changeDays <= 0 and len(userInfo.HandleStock) > 0:
            sell_all_stock()
            has_trade = True
        
        #入場訊號篩選--------------------------------------
        if len(Temp_result) >= mainParament.Pick_amount and Temp_reset == 0 and len(userInfo.HandleStock) == 0:
            Temp_buy0 = {'result':Temp_result}
            if bool_check_price_pick:
                Temp_buy0['price'] = GetStockData.All_Stock_Filters_fuc(userInfo.BaseInfoData.now_day,Temp_result).get_Filter('price',mainParament.price_high,mainParament.price_low,info.Price_type.Close)
                Temp_buy0['price'] = Temp_buy0['price'].sort_values(by='price', ascending=False)
            if bool_check_volume_pick:
                Temp_buy0['volume'] = GetStockData.get_AVG_value(userInfo.BaseInfoData.now_day,mainParament.volumeAVG,mainParament.volumeDays,Temp_result)
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
        if len(userInfo.HandleStock) > 0 or has_trade == True:
            userInfo.RecordUserInfo()
            userInfo.RecodTradeInfo()
            Temp_result_pick = pd.concat([Temp_result_pick, pd.DataFrame({'date':[userInfo.BaseInfoData.now_day],
                                                            '選股數量':[len(Temp_result)]})],
                                                            ignore_index = True)
        #加一天----------------------------
        if add_one_day() == False:
            break
        else:
            Temp_changeDays = Temp_changeDays - 1
    
    #最後總結算----------------------------
    Temp_result_pick.set_index('date',inplace=True)
    userInfo.RunFinish()
    Temp_alldata = tools.MixDataFrames({'draw':userInfo._TempResultDraw,'pick':Temp_result_pick},'date')
    
    Temp_alldata = tools.MixDataFrames({'all':Temp_alldata,'userinfo':userInfo._TempResultAll},'date')
    
    userInfo._TempResultDraw.to_csv('backtestdata.csv')
    userInfo._TempTradeInfo.to_csv('backtesttrade.csv')
    Temp_alldata.to_csv('backtestAll.csv')
    return userInfo._TempResultDraw
def backtest_monthRP_Up_Fast(mainParament:RecordBackTestParameter):
    '''#月營收增高 https://www.finlab.tw/%e4%b8%89%e7%a8%ae%e6%9c%88%e7%87%9f%e6%94%b6%e9%80%b2%e9%9a%8e%e7%9c%8b%e6%b3%95/#ji_ji_xuan_gu_cheng_zhang_fa'''
    Temp_change = 0 #換股剩餘天數
    userInfo = StockInfoDatasInBackTestPriceByToday(BaseInfoData(mainParament.money_start,mainParament.date_start,mainParament.date_end))
    Temp_result_pick = pd.DataFrame(columns=['date','選股數量'])
    All_data = TGetExternalData().get_stock_history(mainParament.buy_number,mainParament.date_start)
    add_one_day = userInfo.AddOneDay
    sell_all_stock = userInfo.SellAllStock
    buy_all_stock = userInfo.BuyAllStock
    for index,row in All_data.iterrows():
        has_trade = False
        while(userInfo.BaseInfoData.now_day != index):
            #加一天----------------------------
            if add_one_day() == False:
                break
        #出場訊號篩選--------------------------------------
        if Temp_change <= 0 and len(userInfo.HandleStock) > 0:
            sell_all_stock()
            has_trade = True
        #開始篩選--------------------------------------
        Temp_result0 = {}
        Temp_result = pd.DataFrame()
        if Temp_change <= 0:
            if bool_check_monthRP_pick:#月營收升高篩選(月為單位)
                Temp_result0['month'] = GetStockData.get_monthRP_up(userInfo.BaseInfoData.now_day,mainParament.smoothAVG,mainParament.upMonth)
            if bool_check_ROE_pick:#ROE
                Temp_result0['ROE'] = GetStockData.get_ROE_range(userInfo.BaseInfoData.now_day,mainParament.ROE_start,mainParament.ROE_end)
            if bool_check_PBR_pick:#PBR
                Temp_result0['PBR'] = GetStockData.get_PBR_range(userInfo.BaseInfoData.now_day,mainParament.PBR_start,mainParament.PBR_end)
            if bool_check_PER_pick:#PER
                Temp_result0['PER'] = GetStockData.get_PER_range(userInfo.BaseInfoData.now_day,mainParament.PER_start,mainParament.PER_end)
            Temp_result = tools.MixDataFrames(Temp_result0)
        #入場訊號篩選--------------------------------------
        if Temp_change <= 0 and len(userInfo.HandleStock) <= 0 and len(Temp_result) > mainParament.Pick_amount:
            Temp_buy0 = {'result':Temp_result}
            if bool_check_price_pick:
                Temp_buy0['price'] = GetStockData.All_Stock_Filters_fuc(userInfo.BaseInfoData.now_day,Temp_result).get_Filter('price',mainParament.price_high,mainParament.price_low,info.Price_type.Close)
                Temp_buy0['price'] = Temp_buy0['price'].sort_values(by='price', ascending=False)
            if bool_check_volume_pick:
                Temp_buy0['volume'] = GetStockData.get_AVG_value(userInfo.BaseInfoData.now_day,mainParament.volumeAVG,mainParament.volumeDays,Temp_result)
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
        if has_trade or len(userInfo.HandleStock) > 0:
            userInfo.RecordUserInfo()
            userInfo.RecodTradeInfo()
            Temp_result_pick = pd.concat([Temp_result_pick, pd.DataFrame({'date':[userInfo.BaseInfoData.now_day],
                                                                        '選股數量':[len(Temp_result)]})],
                                                                        ignore_index = True)
        #加一天----------------------------
        if add_one_day() == False:
            break
        else:
            Temp_change = Temp_change - 1
    #最後總結算----------------------------
    Temp_result_pick.set_index('date',inplace=True)
    userInfo.RunFinish()
    Temp_alldata = tools.MixDataFrames({'draw':userInfo._TempResultDraw,'pick':Temp_result_pick},'date')
    
    Temp_alldata = tools.MixDataFrames({'all':Temp_alldata,'userinfo':userInfo._TempResultAll},'date')
    
    userInfo._TempResultDraw.to_csv('backtestdata.csv')
    userInfo._TempTradeInfo.to_csv('backtesttrade.csv')
    Temp_alldata.to_csv('backtestAll.csv')
    return userInfo._TempResultDraw
