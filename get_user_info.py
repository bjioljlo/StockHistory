import datetime
import pandas as pd
import get_stock_history
import get_stock_info
import twstock as ts #抓取台灣股票資料套件

class data_user_stock():#手持股票資訊
    def __init__(self,stock_info,amount,price):
        self.stock_info = stock_info
        self.amount = amount
        self.price = price
    def add_amount(self,amount,price):
        self.price = ((self.price * self.amount) + (price * amount)) / (self.amount + amount)
        self.amount = self.amount + amount
    def minus_amount(self,amount):
        if self.amount > amount:
            self.amount = self.amount - amount
            return True
        elif self.amount < amount:
            print(str(self.stock_info.number) + '數量不足!')
        self.amount = 0
        return False
        

class data_user_info():#使用者資訊
    
    def __init__(self,start_money,start_day,end_day):
        self.start_money = start_money #起始現金
        self.now_money = start_money #剩餘現金
        self.handle_stock = {}#手持股票
        self.start_day = start_day #開始日期
        self.now_day = start_day #現在日期
        self.end_day = end_day  #結束日期

        self.Temp_result_draw = pd.DataFrame(columns=['date','資產比例'])
        self.Temp_result_All = pd.DataFrame(columns=['date','股票資產','剩餘現金','總資產'])
        self.Temp_trade_info = pd.DataFrame(columns=['date','號碼','數量','均價'])

    def add_one_day(self):#過一天
        if self.now_day >= self.end_day:
            self.Temp_result_All = self.Temp_result_All.set_index('date')
            self.Temp_result_draw = self.Temp_result_draw.set_index('date')
            self.Temp_trade_info = self.Temp_trade_info.set_index('date')
            return False
        else:
            self.now_day = self.now_day + datetime.timedelta(days=1)#加一天
            return True
    def get_handle_stock(self):#手中股票總資料
        Temp = pd.DataFrame(columns = ['stock','number'])
        for key,value in self.handle_stock.items():
            Temp = Temp.append({'stock':key,'number':value.amount},ignore_index=True)
            Temp.set_index('stock')
        return Temp
    def get_user_all_asset(self):#總資產
        Temp_money = self.get_user_stock_asset()
        return Temp_money + self.now_money
    def get_user_stock_asset(self):#股票資產
        Temp_money = 0
        for key,value in self.handle_stock.items():
            Temp = get_stock_history.get_stock_price(key,self.now_day,get_stock_history.stock_data_kind.AdjClose)
            Temp_money = Temp_money + (Temp * value.amount)
        return Temp_money
    def sell_all_stock(self):#賣出所有股票
        for key,value in list(self.handle_stock.items()):
            self.sell_stock(key,value.amount)
    def buy_all_stock(self,data = pd.DataFrame()):#買入所有股票
        while len(data) > 0:
            for index,row in data.iterrows():
                if self.buy_stock(index,1000) == False:
                    data = data.drop(index=index)
    def buy_stock(self,number,amount):#買股票
        stock_price = get_stock_history.get_stock_price(number,self.now_day,get_stock_history.stock_data_kind.AdjClose)
        if (stock_price * amount) > self.now_money:
            print('錢不夠：')
            return False
        else:
            m_stock = ts.codes[str(number)]
            m_info = get_stock_info.data_stock_info(m_stock.code,m_stock.name,m_stock.type,m_stock.start,m_stock.market,m_stock.group)
            if self.handle_stock.__contains__(number) == False:
                self.handle_stock[number] = data_user_stock(m_info,amount,stock_price)
            else:
                self.handle_stock[number].add_amount(amount,stock_price)
            self.now_money = self.now_money - (stock_price * amount)
            return True
    def sell_stock(self,number,amount):#賣股票
        if self.handle_stock.__contains__(number) == False:
            print('手上無此股票')
            return False    
        elif self.handle_stock[number].amount < amount:
            print('股票數量不足')
            return False
        else:
            stock_price = get_stock_history.get_stock_price(number,self.now_day,get_stock_history.stock_data_kind.AdjClose)
            self.now_money = self.now_money + (stock_price * amount)
            if self.handle_stock[number].minus_amount(amount) == False:
                self.handle_stock.pop(number,None)
            return True
    def Record_userInfo(self,data = pd.DataFrame()):
        self.Temp_result_draw = self.Temp_result_draw.append({'date':self.now_day,
                                        '資產比例':self.get_user_all_asset()/self.start_money},ignore_index=True)
        self.Temp_result_All = self.Temp_result_All.append({'date':self.now_day,
                                                '股票資產':self.get_user_stock_asset(),
                                                '剩餘現金':self.now_money,
                                                '總資產':self.get_user_all_asset()},ignore_index=True)
    def Recod_tradeInfo(self):
        temp_numbers = ''
        temp_amount = ''
        temp_price = ''
        for key,value in self.handle_stock.items():
            temp_amount = temp_amount + str(value.amount) + '/' 
            temp_price = temp_price + str(value.price)+ '/' 
            temp_numbers = temp_numbers + str(key)+ '/' 
        self.Temp_trade_info = self.Temp_trade_info.append({'date':self.now_day,
                                                '號碼':temp_numbers,
                                                '數量':temp_amount,
                                                '均價':temp_price},ignore_index=True)

    
    