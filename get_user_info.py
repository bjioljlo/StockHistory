from datetime import timedelta, datetime
import pandas as pd
from pandas import DataFrame
from get_stock_history import get_stock_price,stock_data_kind
from StockInfos import StockInfoData
import tools
import twstock as ts #抓取台灣股票資料套件

class data_user_stock():#手持股票資訊
    def __init__(self,stock_info: StockInfoData,amount:int,price:float):
        self.stock_info:StockInfoData = stock_info
        self.amount:int = amount
        self.price:float = price
    def add_amount(self,amount:int,price:float):
        self.price = ((self.price * self.amount) + (price * amount)) / (self.amount + amount)
        self.amount = self.amount + amount
    def minus_amount(self,amount:int) -> bool:
        if self.amount > amount:
            self.amount = self.amount - amount
            return True
        elif self.amount < amount:
            print(str(self.stock_info.number) + '數量不足!')
        self.amount = 0
        return False
        

class data_user_info():#使用者資訊 
    def __init__(self,start_money:int,start_day:datetime,end_day:datetime):
        self.start_money:int = start_money #起始現金
        self.now_money:int = start_money #剩餘現金
        self.handle_stock = {}#手持股票
        self.start_day:datetime = start_day #開始日期
        self.now_day:datetime = start_day #現在日期
        self.end_day:datetime = end_day  #結束日期

        self.Temp_result_draw:pd.DataFrame = pd.DataFrame(columns=['date','資產比例'])
        self.Temp_result_All:pd.DataFrame = pd.DataFrame(columns=['date','股票資產','剩餘現金','總資產'])
        self.Temp_trade_info:pd.DataFrame = pd.DataFrame(columns=['date','號碼','數量','均價'])

    def Run_Finish(self):
        self.Temp_result_All['date'] = pd.to_datetime(self.Temp_result_All['date'])
        self.Temp_result_draw['date'] = pd.to_datetime(self.Temp_result_draw['date'])
        self.Temp_trade_info['date'] = pd.to_datetime(self.Temp_trade_info['date'])
        if self.Temp_result_All.index.name != 'date':
            self.Temp_result_All = self.Temp_result_All.set_index('date')
            self.Temp_result_draw = self.Temp_result_draw.set_index('date')
            self.Temp_trade_info = self.Temp_trade_info.set_index('date')

    def add_one_day(self):#過一天
        if self.now_day >= self.end_day:
            if self.Temp_result_All.index.name != 'date':
                self.Temp_result_All = self.Temp_result_All.set_index('date')
                self.Temp_result_draw = self.Temp_result_draw.set_index('date')
                self.Temp_trade_info = self.Temp_trade_info.set_index('date')
            return False
        else:
            self.now_day = self.now_day + timedelta(days=1)#加一天
            return True
    def get_handle_stock(self):#手中股票總資料
        Temp = pd.DataFrame(columns = ['stock','number'])
        for key,value in self.handle_stock.items():
            Temp = pd.concat([Temp,{'stock':key,'number':value.amount}],ignore_index=True)
            Temp.set_index('stock')
        return Temp
    def get_user_all_asset(self):#總資產
        Temp_money = self.get_user_stock_asset()
        return Temp_money + self.now_money
    def get_user_stock_asset(self):#股票資產
        Temp_money = 0
        for key,value in self.handle_stock.items():
            Temp = get_stock_price(key,self.now_day,stock_data_kind.AdjClose)
            if Temp == None:
                print('no use stock')
                return 0
            Temp_money = Temp_money + (Temp * value.amount)
        return Temp_money
    def sell_all_stock(self):#賣出所有股票
        for key,value in list(self.handle_stock.items()):
            self.sell_stock(key,value.amount)
    def buy_all_stock(self,data:DataFrame):#買入所有股票
        while len(data) > 0:
            for index,row in data.iterrows():
                if self.buy_stock(index,1000) == False:
                    data = data.drop(index=index)
    def buy_stock(self,number:str,amount:int):#買股票
        stock_price = get_stock_price(number,self.now_day,stock_data_kind.AdjClose)
        if stock_price == None:
            print(str(number) + ' no use stock')
            return False
        elif tools.Total_with_Handling_fee_and_Tax(stock_price,amount) > self.now_money:
            print('錢不夠：')
            return False
        else:
            m_stock = ts.codes[str(number)]
            m_info = StockInfoData(m_stock.code,m_stock.name,m_stock.type,m_stock.start,m_stock.market,m_stock.group)
            if self.handle_stock.__contains__(number) == False:
                self.handle_stock[number] = data_user_stock(m_info,amount,stock_price)
            else:
                self.handle_stock[number].add_amount(amount,stock_price)
            self.now_money = self.now_money - tools.Total_with_Handling_fee_and_Tax(stock_price,amount)
            return True
    def sell_stock(self,number:str,amount:int):#賣股票
        if self.handle_stock.__contains__(number) == False:
            print('手上無此股票')
            return False    
        elif self.handle_stock[number].amount < amount:
            print('股票數量不足')
            return False
        else:
            stock_price = get_stock_price(number,self.now_day,stock_data_kind.AdjClose)
            self.now_money = self.now_money + tools.Total_with_Handling_fee_and_Tax(stock_price,amount,False)
            if self.handle_stock[number].minus_amount(amount) == False:
                self.handle_stock.pop(number,None)
            return True
    def Record_userInfo(self,data:DataFrame):
        self.Temp_result_draw = self.Temp_result_draw.append({'date':self.now_day,
                                                            '資產比例':self.get_user_all_asset()/self.start_money},
                                                            ignore_index=True)
        self.Temp_result_All = self.Temp_result_All.append({'date':self.now_day,
                                                            '股票資產':self.get_user_stock_asset(),
                                                            '剩餘現金':self.now_money,
                                                            '總資產':self.get_user_all_asset()},
                                                            ignore_index=True)
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
                                                '均價':temp_price}
                                                ,ignore_index=True)