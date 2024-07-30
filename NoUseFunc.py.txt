#////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#14年14倍 https://www.finlab.tw/%E6%AF%94%E7%AD%96%E7%95%A5%E7%8B%97%E9%82%84%E8%A6%81%E5%AE%89%E5%85%A8%E7%9A%84%E9%81%B8%E8%82%A1%E7%AD%96%E7%95%A5%EF%BC%81/
def backtest_PERandPBR(mainParament):
    Temp_reset = 0#休息日剩餘天數
    Temp_result_pick = pd.DataFrame(columns=['date','選股數量'])
    userInfo = StockInfoDatasInBackTestPriceByToday(BaseInfoData(mainParament.money_start,mainParament.date_start,mainParament.date_end))
    while userInfo.now_day <= userInfo.end_day:
        #週末直接跳過
        if userInfo.now_day.isoweekday() in [6,7]:
            print(str(userInfo.now_day) + 'is 星期' + str(userInfo.now_day.isoweekday()))
            if userInfo.AddOneDay() == False:#加一天
                break
            continue

        #先看看台積有沒有資料，如果沒有表示這天是非週末假日跳過 
        if gsh.Stock_2330.get_PriceByDateAndType(userInfo.now_day,gsh.stock_data_kind.AdjClose) == None:
            print(str(userInfo.now_day) + "這天沒開市")
            if userInfo.AddOneDay() == False:#加一天
                break
            continue

        #休息日直接跳過
        if Temp_reset > 0 and len(userInfo._Handle_stock) == 0:
            print(str(userInfo.now_day) + ' is reset time:第' + str(Temp_reset) + '天')
            if userInfo.AddOneDay() == False:#加一天
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
        if len(Temp_result) < mainParament.Pick_amount and len(userInfo._Handle_stock) > 0:
            userInfo.SellAllStock()
            Temp_reset = mainParament.change_days
        
        #入場訊號篩選--------------------------------------
        if len(Temp_result) > mainParament.Pick_amount and Temp_reset == 0 and len(userInfo._Handle_stock) == 0:
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
            userInfo.BuyAllStock(Temp_buy)
            Temp_reset = mainParament.change_days

        #更新資訊--------------------------------------
        userInfo.RecordUserInfo()
        userInfo.RecodTradeInfo()
        Temp_result_pick = pd.concat([Temp_result_pick,{'date':userInfo.now_day,
                                                '選股數量':len(Temp_result)}],ignore_index = True)
        #加一天----------------------------
        if userInfo.AddOneDay() == False:
            break

    #最後總結算----------------------------
    Temp_result_pick.set_index('date',inplace=True)
    Temp_alldata = tools.MixDataFrames({'draw':userInfo._TempResultDraw,'pick':Temp_result_pick},'date')
    
    Temp_alldata = tools.MixDataFrames({'all':Temp_alldata,'userinfo':userInfo._TempResultAll},'date')
    
    userInfo._TempResultDraw.to_csv('backtestdata.csv')
    userInfo._TempTradeInfo.to_csv('backtesttrade.csv')
    Temp_alldata.to_csv('backtestAll.csv')
    draw_backtest(userInfo._TempResultDraw)
#月營收增高 https://www.finlab.tw/%e4%b8%89%e7%a8%ae%e6%9c%88%e7%87%9f%e6%94%b6%e9%80%b2%e9%9a%8e%e7%9c%8b%e6%b3%95/#ji_ji_xuan_gu_cheng_zhang_fa
def backtest_monthRP_Up(mainParament):
    Temp_change = 0#換股剩餘天數
    userInfo = StockInfoDatasInBackTestPriceByToday(BaseInfoData(mainParament.money_start,mainParament.date_start,mainParament.date_end))
    Temp_result_pick = pd.DataFrame(columns=['date','選股數量'])
    while userInfo.now_day <= userInfo.end_day:

        #週末直接跳過
        if userInfo.now_day.isoweekday() in [6,7]:
            print(str(userInfo.now_day) + 'is 星期' + str(userInfo.now_day.isoweekday()))
            if userInfo.AddOneDay() == False:#加一天
                break
            continue
        #先看看台積有沒有資料，如果沒有表示這天是非週末假日跳過 
        if gsh.Stock_2330.get_PriceByDateAndType(userInfo.now_day,gsh.stock_data_kind.AdjClose) == None:
            print(str(userInfo.now_day) + "這天沒開市")
            if userInfo.AddOneDay() == False:#加一天
                break
            continue
        
        #出場訊號篩選--------------------------------------
        if Temp_change <= 0 and len(userInfo._Handle_stock) > 0:
            userInfo.SellAllStock()

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
        if Temp_change <= 0 and len(userInfo._Handle_stock) <= 0 and len(Temp_result) > mainParament.Pick_amount:
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
            userInfo.BuyAllStock(Temp_buy)

        #更新資訊--------------------------------------
        if Temp_change <= 0 and len(userInfo._Handle_stock) > 0:
            Temp_change = mainParament.change_days
        userInfo.RecordUserInfo()
        userInfo.RecodTradeInfo()
        Temp_result_pick = pd.concat([Temp_result_pick,{'date':userInfo.now_day,
                                                '選股數量':len(Temp_result)}],ignore_index = True)
        #加一天----------------------------
        if userInfo.AddOneDay() == False:
            break
        else:
            Temp_change = Temp_change - 1

    #最後總結算----------------------------
    Temp_result_pick.set_index('date',inplace=True)
    Temp_alldata = tools.MixDataFrames({'draw':userInfo._TempResultDraw,'pick':Temp_result_pick},'date')
    draw_backtest(userInfo._TempResultDraw)
    Temp_alldata = tools.MixDataFrames({'all':Temp_alldata,'userinfo':userInfo._TempResultAll},'date')
    
    userInfo._TempResultDraw.to_csv('backtestdata.csv')
    userInfo._TempTradeInfo.to_csv('backtesttrade.csv')
    Temp_alldata.to_csv('backtestAll.csv')
#定期定額非常詳細版，要跑很久暫時不使用
def backtest_Regular_quota(mainParament):
    userInfo = StockInfoDatasInBackTestPriceByToday(BaseInfoData(0,mainParament.date_start,mainParament.date_end))
    buy_month = mainParament.date_start
    Temp_result_pick = pd.DataFrame(columns=['date','選股數量'])
    while userInfo.now_day <= userInfo.end_day:        
        #週末直接跳過
        if userInfo.now_day.isoweekday() in [6,7]:
            print(str(userInfo.now_day) + 'is 星期' + str(userInfo.now_day.isoweekday()))
            if userInfo.AddOneDay() == False:#加一天
                break
            continue
        #先看看台積有沒有資料，如果沒有表示這天是非週末假日跳過 
        if gsh.Stock_2330.get_PriceByDateAndType(userInfo.now_day,gsh.stock_data_kind.AdjClose) == None:
            print(str(userInfo.now_day) + "這天沒開市")
            if userInfo.AddOneDay() == False:#加一天
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
            userInfo.BuyStock(mainParament.buy_number,Temp_stockNumber)
            buy_month = userInfo.now_day

        #更新資訊--------------------------------------   
        if userInfo.start_money > 0:
            userInfo.RecordUserInfo()
            userInfo.RecodTradeInfo()
        Temp_result_pick = pd.concat([Temp_result_pick,{'date':userInfo.now_day,
                                                '選股數量':len(Temp_result)}],ignore_index = True)

        #加一天----------------------------
        if userInfo.AddOneDay() == False:
            break
    
    #最後總結算----------------------------
    Temp_result_pick.set_index('date',inplace=True)
    Temp_alldata = tools.MixDataFrames({'draw':userInfo._TempResultDraw,'pick':Temp_result_pick},'date')
    #draw_backtest(userInfo.Temp_result_draw)
    Temp_alldata = tools.MixDataFrames({'all':Temp_alldata,'userinfo':userInfo._TempResultAll},'date')
    
    userInfo._TempResultDraw.to_csv('backtestdata.csv')
    userInfo._TempTradeInfo.to_csv('backtesttrade.csv')
    Temp_alldata.to_csv('backtestAll.csv')
    return userInfo._TempResultDraw
#創新高 https://www.finlab.tw/break-new-high-roe-stock/
def backtest_Record_high(mainParament):
    Temp_reset = 0#休息日剩餘天數
    userInfo = StockInfoDatasInBackTestPriceByToday(BaseInfoData(mainParament.money_start,mainParament.date_start,mainParament.date_end))
    Temp_result_pick = pd.DataFrame(columns=['date','選股數量'])
    
    
    while userInfo.now_day <= userInfo.end_day:
        #週末直接跳過
        if userInfo.now_day.isoweekday() in [6,7]:
            print(str(userInfo.now_day) + 'is 星期' + str(userInfo.now_day.isoweekday()))
            if userInfo.AddOneDay() == False:#加一天
                break
            continue
        #先看看台積有沒有資料，如果沒有表示這天是非週末假日跳過 
        if gsh.Stock_2330.get_PriceByDateAndType(userInfo.now_day,gsh.stock_data_kind.AdjClose) == None:
            print(str(userInfo.now_day) + "這天沒開市")
            if userInfo.AddOneDay() == False:#加一天
                break
            continue
        #休息日直接跳過
        if Temp_reset > 0 and len(userInfo._Handle_stock) == 0:
            print(str(userInfo.now_day) + ' is reset time:第' + str(Temp_reset) + '天')
            if userInfo.AddOneDay() == False:#加一天
                break
            Temp_reset = Temp_reset - 1
            continue
        #出場訊號篩選--------------------------------------
        if len(userInfo._Handle_stock) > 0:
            Temp_data = userInfo._Handle_stock
            for key,value in list(Temp_data.items()):
                if gsh.get_stock_price(key,userInfo.now_day,gsh.stock_data_kind.AdjClose) < gsh.get_stock_MA(key,userInfo.now_day,20):
                    userInfo.SellStock(key,value.amount)
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
                userInfo.BuyAllStock(Temp_buy)
        #更新資訊--------------------------------------
        if Temp_reset <= 0:
            Temp_reset = mainParament.change_days
        userInfo.RecordUserInfo()
        userInfo.RecodTradeInfo()
        Temp_result_pick = pd.concat([Temp_result_pick,{'date':userInfo.now_day,
                                                '選股數量':len(Temp_result)}],ignore_index = True)
        #加一天----------------------------
        if userInfo.AddOneDay() == False:
            break
        else:
            Temp_reset = Temp_reset - 1

    #最後總結算----------------------------
    Temp_result_pick.set_index('date',inplace=True)
    Temp_alldata = tools.MixDataFrames({'draw':userInfo._TempResultDraw,'pick':Temp_result_pick},'date')
    draw_backtest(userInfo._TempResultDraw)
    Temp_alldata = tools.MixDataFrames({'all':Temp_alldata,'userinfo':userInfo._TempResultAll},'date')
    
    userInfo._TempResultDraw.to_csv('backtestdata.csv')
    userInfo._TempTradeInfo.to_csv('backtesttrade.csv')
    Temp_alldata.to_csv('backtestAll.csv')
#////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////