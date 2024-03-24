import requests
from datetime import datetime
import pandas as pd
import StockInfos
import os
import numpy as np
from io import StringIO
import time
import tools
import update_stock_info
import Infomation_type as info
import sys
from abc import ABC , abstractmethod
import ReadLoadSystem as RLsys
import tools

class IGetExternalData(ABC):
    @abstractmethod
    def get_allstock_financial_statement(self, start:datetime,type:info.FS_type):
        '''#爬某季所有股票歷史財報'''
        pass
    @abstractmethod
    def get_allstock_monthly_report(self,start:datetime):
        '''爬某月所有股票月營收'''
        pass
    @abstractmethod
    def get_allstock_yield(self,start:datetime):
        '''#爬某天所有股票殖利率'''
        pass
    @abstractmethod
    def get_stock_history(self,number:str,start = datetime.strptime('2005-1-1',"%Y-%m-%d")) -> pd.DataFrame:   
        '''#爬某個股票的歷史紀錄'''
        pass
    @abstractmethod 
    def get_stock_AD_index(self,date:datetime,getNew = False):
        '''#取得上漲和下跌家數'''
        pass
class TGetExternalData(IGetExternalData):
    '''讀取外部資料'''
    def __init__(self) -> None:
        self.fileName_monthRP:str = "monthRP"
        self.fileName_stockInfo = "stockInfo"
        self.fileName_yield = "yieldInfo"
        self.fileName_season = "seasonInfo"
        self.fileName_index = "indexInfo"
        self.filePath = os.getcwd()#取得目錄路徑
    def get_allstock_financial_statement(self,start:datetime,type:info.FS_type):
        '''#爬某季所有股票歷史財報'''
        print(''.join(["{}:取得".format(sys._getframe().f_code.co_name)]),str(type),"的季財報的資料:",str(start))
        if tools.Have_DayRP(start) == False:
            return pd.DataFrame()
        season = int(((start.month - 1)/3)+1)
        Temp_data = pd.DataFrame()
        if tools.CheckFS_season(start) == False:
            print('Season rp is no data yet!')
            return pd.DataFrame()
        file = str(start.year) + "-season" + str(season) + "-" + type.value
        fileName = self.filePath + '/' + self.fileName_season + '/' + file
        Temp_data = RLsys.load_month_file(fileName,file) #去資料庫抓資料

        if Temp_data.empty == True:
            if os.path.isfile(fileName + '.csv') == True:
                print("已經有" + str(start.month)+ "月財務報告")
            self.financial_statement(start.year,season,type)
            print("下載" + str(start.month)+ "月財務報告ＯＫ")
        
            stock = pd.read_csv(fileName + '.csv')
            #整理一下資料
            stock.rename(columns = {"公司代號":"code"},inplace = True)
            stock.set_index("code",inplace = True)
            if info.FS_type.SCF == type:
                if stock["投資活動之淨現金流入（流出）"].dtype == object: 
                    stock["投資活動之淨現金流入（流出）"] = pd.to_numeric(stock["投資活動之淨現金流入（流出）"].str.replace('--', '0'))
                if stock["營業活動之淨現金流入（流出）"].dtype == object: 
                    stock["營業活動之淨現金流入（流出）"] = pd.to_numeric(stock["營業活動之淨現金流入（流出）"].str.replace('--', '0'))
                if stock["籌資活動之淨現金流入（流出）"].dtype == object: 
                    stock["籌資活動之淨現金流入（流出）"] = pd.to_numeric(stock["籌資活動之淨現金流入（流出）"].str.replace('--', '0'))
            update_stock_info.saveTable(file,stock)
        else:
            stock = Temp_data
        RLsys.load_memery[fileName] = stock
        return stock
    def get_allstock_monthly_report(self,start:datetime):
        '''爬某月所有股票月營收'''
        print(''.join(["{}:取得".format(sys._getframe().f_code.co_name)]),"月營收的資料:",str(start))
        if tools.Have_MonthRP(start) == False:
            return pd.DataFrame()
        m_data = pd.DataFrame()
        year = start.year
        file = 'monthly_report_'+ str(start.year) + '_' + str(start.month)
        fileName = self.filePath + '/' + self.fileName_monthRP + '/' + file
        m_data = RLsys.load_month_file(fileName,file) #去資料庫抓資料
        
        if m_data.empty == True:
            if os.path.isfile(fileName + '.csv') == False:
                # 假如是西元，轉成民國
                if year > 1990:
                    year -= 1911
                url = 'https://mops.twse.com.tw/nas/t21/sii/t21sc03_'+str(year)+'_'+str(start.month)+'_0.html'
                if year <= 98:
                    url = 'https://mops.twse.com.tw/nas/t21/sii/t21sc03_'+str(year)+'_'+str(start.month)+'.html'
                
                # 下載該年月的網站，並用pandas轉換成 dataframe
                r = requests.get(url, headers = tools.get_random_Header())
                r.encoding = 'big5-hkscs'
                
                try:
                    dfs = pd.read_html(StringIO(r.text), encoding='big-5')
                except:
                    return pd.DataFrame()
                

                df = pd.concat([df for df in dfs if df.shape[1] <= 11 and df.shape[1] > 5])
                
                if 'levels' in dir(df.columns):
                    df.columns = df.columns.get_level_values(1)
                else:
                    df = df[list(range(0,10))]
                    column_index = df.index[(df[0] == '公司代號')][0]
                    df.columns = df.iloc[column_index]
                
                df['當月營收'] = pd.to_numeric(df['當月營收'], 'coerce')
                df = df[~df['當月營收'].isnull()]
                df = df[df['公司代號'] != '合計']
                
                df.to_csv(fileName,index = False)
                # 偽停頓
                time.sleep(1.5)
                
            m_data = pd.read_csv(fileName)
            m_data.drop(m_data.tail(1).index,inplace=True)
            #整理一下資料
            m_data.rename(columns = {"公司代號":"code"},inplace = True)
            m_data[["code"]] = m_data[["code"]].astype(int)
            m_data.set_index("code",inplace = True)
            #存到資料庫
            update_stock_info.saveTable(file,m_data)
        RLsys.load_memery[fileName] = m_data
        return m_data  
    def get_allstock_yield(self,start:datetime):
        '''#爬某天所有股票殖利率'''
        print(''.join(["{}:取得".format(sys._getframe().f_code.co_name)]),"殖利率的資料:",str(start))
        file = 'dividend_yield_'+ str(start.year) + '_' + str(start.month) + '_' + str(start.day)
        fileName = self.filePath + '/' + self.fileName_yield + '/' + file
        m_yield = pd.DataFrame()
        #去資料庫抓資料
        m_yield = RLsys.load_month_file(fileName,file)

        if m_yield.empty == True and (start in self.get_stock_history('2330', start)) :
            if os.path.isfile(fileName + '.csv') == False:
                url = 'https://www.twse.com.tw/exchangeReport/BWIBBU_d?response=csv&date=' + str(start.year)+str(start.month).zfill(2)+str(start.day).zfill(2)+ '&selectType=ALL'
                response = requests.get(url,tools.get_random_Header())
                RLsys.save_stock_file(fileName,response,1,2)
                # 偽停頓
                time.sleep(3)
            try:
                m_yield = pd.read_csv(fileName + '.csv')
            except:
                m_yield = pd.read_csv(fileName + '.csv',encoding = 'ANSI')
            #整理一下資料
            m_yield.rename(columns = {"證券代號":"code"},inplace = True)
            m_yield.set_index("code",inplace = True)
            #存到資料庫
            update_stock_info.saveTable(file,m_yield)
        RLsys.load_memery[fileName] = m_yield
        return m_yield
    def get_stock_history(self,number:str,start = datetime.strptime('2005-1-1',"%Y-%m-%d")) -> pd.DataFrame:
        '''#爬某個股票的歷史紀錄'''
        print(''.join(["取得" , str(number) , "的資料從" , str(start) ,"到今天:{}".format(sys._getframe().f_code.co_name)]))
        start_time = start
        if type(start_time) == str:
            start_time  = datetime.strptime(start_time,"%Y-%m-%d")
        if type(number) != str:
            number = str(number)
        data_time = datetime.strptime('2005-1-1',"%Y-%m-%d")
        result = pd.DataFrame()

        if StockInfos.ts.codes.__contains__(number) == False:
            print("無此檔股票")
            return result
        if start_time < data_time:
            print('日期請大於西元2005年')
            return result
        file = str(number)
        filename = self.filePath +'/' + self.fileName_stockInfo  + '/' + file
        m_history = RLsys.load_stock_file(filename,file)
        if m_history.empty == True:
            # 去ＹＦ讀取資料
            update_stock_info.yf_info(str(number) + info.local_type.Taiwan)
            # 偽停頓
            time.sleep(1.5)
            m_history = RLsys.load_stock_file(filename,file)       
        mask = m_history.index >= start_time
        result = m_history[mask]
        result = result.dropna(axis = 0,how = 'any')
        return result
    def get_stock_AD_index(self,date:datetime,getNew = False):
        '''#取得上漲和下跌家數'''
        print('get_stock_AD_index')
        ADindex_result = pd.DataFrame(columns=['Date','上漲','下跌']).set_index('Date')
        if type(date) == str:
            date = datetime.strptime(date,"%Y-%m-%d")
        time = date 
        str_date = tools.DateTime2String(time)
        time_yesterday = tools.backWorkDays(time,1)

        while (self.get_stock_history('2330',time_yesterday)['Close'].empty == True):
            time_yesterday = tools.backWorkDays(time_yesterday,1)#加一天
        
        str_yesterday = tools.DateTime2String(time_yesterday)
        fileName = self.filePath +'/' + self.fileName_index + '/' + 'AD_index'
        
        ADindex_result = RLsys.load_other_file(fileName,'AD_index')
        if ADindex_result.empty == True:
            if os.path.isfile(fileName + '.csv') == True:
                ADindex_result = pd.read_csv(fileName + '.csv', index_col='Date', parse_dates=['Date'])
                RLsys.load_memery[fileName] = ADindex_result
            else:
                print('no AD_index csv file')
                
        up = 0
        down = 0
        if ADindex_result.empty == False and (ADindex_result.index == time).__contains__(True):
            return ADindex_result[ADindex_result.index == time]
        for key,value in StockInfos.ts.codes.items():
            if value.code == "1312":
                break
            if value.market == "上市" and len(value.code) == 4 and value.type == "股票":
                if tools.check_no_use_stock(value.code) == True:
                    print('get_stock_price: ' + str(value.code) + ' in no use')
                    continue
                m_history = self.get_stock_history(value.code,str_yesterday)['Close']
                try:
                    if m_history[str_yesterday] > m_history[str_date]:
                        down = down + 1
                    elif m_history[str_yesterday] < m_history[str_date]:
                        up = up + 1
                except:
                    print("get " + str(value.code) + " info fail!")
                    m_temp = self.get_stock_history('2330',str_yesterday)['Close']
                    if (m_temp.index == time).__contains__(True) != True:
                        return pd.DataFrame()
                    m_temp = self.get_stock_history('2330',str_date)['Close']
                    if (m_temp.index == time).__contains__(True) != True:
                        return pd.DataFrame()
        ADindex_result_new = pd.DataFrame({'Date':[time],'上漲':[up],'下跌':[down]}).set_index('Date')
        ADindex_result = pd.concat([ADindex_result,ADindex_result_new])
        ADindex_result = ADindex_result.sort_index()
        update_stock_info.saveTable('ad_index',ADindex_result)
        RLsys.load_memery[fileName] = ADindex_result
        df = ADindex_result[ADindex_result.index == time]
        return df
        
    def remove_td(self,column):
        remove_one = column.split('<')
        remove_two = remove_one[0].split('>')
        return remove_two[1].replace(",","")
    def translate_dataFrame(self,response):
        table_array = response.split('<table')
        tr_array = table_array[1].split('<tr')
        
        data = []
        index = []
        column = []
        for i in range(len(tr_array)):
            td_array = tr_array[i].split('<td')
            if(len(td_array)>1):
                code = self.remove_td(td_array[1])
                name = self.remove_td(td_array[2])
                revenue = self.remove_td(td_array[3])
                profitRatio = self.remove_td(td_array[4])
                profitMargin = self.remove_td(td_array[5])
                preTaxIncomeMargin = self.remove_td(td_array[6])
                afterTaxIncomeMargin = self.remove_td(td_array[7])
                if(revenue == '&nbsp;'):
                    continue
                if(revenue == ''):
                    continue
                if(i > 1):
                    if name == '公司名稱':
                        continue
                    data.append([name,code,revenue,profitRatio,profitMargin,preTaxIncomeMargin,afterTaxIncomeMargin])
                    #index.append(name)
                if(i == 1):
                    column.append('公司名稱')
                    column.append(code)
                    column.append(revenue)
                    column.append(profitRatio)
                    column.append(profitMargin)
                    column.append(preTaxIncomeMargin)
                    column.append(afterTaxIncomeMargin)
        return pd.DataFrame(data = data,columns=column)
    def translate_dataFrame2(self,response,type,year,season = 1):
        table_array = response.split('<table')
        tr_array_array = [table_array[2].split('<tr'),
                    table_array[3].split('<tr'),
                    table_array[4].split('<tr'),
                    table_array[5].split('<tr'),
                    table_array[6].split('<tr'),
                    table_array[7].split('<tr')]
        column_pos_array = np.array([[24,42,43,52,56],
                                    [5,8,9,18,22],
                                    [5,8,9,18,22],
                                    [25,44,45,53,57],
                                    [16,34,35,44,48],
                                    [5,8,9,17,21]])
        if(year <= 112):
            column_pos_array = np.array([[24,42,43,53,57],
                                    [5,8,9,19,23],
                                    [5,8,9,19,23],
                                    [25,44,45,53,57],
                                    [16,34,35,45,49],
                                    [5,8,9,18,22]])   
        if(year == 109):
            if (season == 1):
                column_pos_array = np.array([[24,42,43,52,56],
                                    [5,8,9,18,22],
                                    [5,8,9,18,22],
                                    [25,44,45,53,57],
                                    [16,34,35,44,48],
                                    [5,8,9,17,21]])    
            else:
                column_pos_array = np.array([[24,42,43,53,57],
                                    [5,8,9,19,23],
                                    [5,8,9,19,23],
                                    [25,44,45,53,57],
                                    [16,34,35,45,49],
                                    [5,8,9,18,22]])   
        if(year == 108):
            column_pos_array = np.array([[24,42,43,52,56],
                                    [5,8,9,18,22],
                                    [5,8,9,18,22],
                                    [25,44,45,53,57],
                                    [16,34,35,44,48],
                                    [5,8,9,17,21]])                      
        if(year == 107):
            column_pos_array = np.array([[25,42,43,52,56],
                                    [5,8,9,18,22],
                                    [5,8,9,18,22],
                                    [26,44,45,53,57],
                                    [14,32,33,42,46],
                                    [5,8,9,17,21]])
        if(year == 106):
            column_pos_array = np.array([[23,40,41,50,54],
                                    [5,8,9,17,21],
                                    [5,8,9,18,22],
                                    [23,41,42,50,54],
                                    [14,32,33,42,46],
                                    [5,8,9,17,21]])                            
        if(year < 106):
            column_pos_array = np.array([[22,39,40,49,53],
                                    [5,8,9,17,21],
                                    [5,8,9,18,22],
                                    [23,41,42,50,54],
                                    [14,32,33,42,46],
                                    [5,8,9,17,21]])
        if(year < 103):
            column_pos_array = np.array([[22,39,40,49,52],
                                    [5,8,9,17,20],
                                    [5,8,9,18,21],
                                    [23,41,42,50,53],
                                    [14,32,33,42,45],
                                    [5,8,9,17,20]])
        # if (year < 105):
        #     column_pos_array = np.array([[23,40,41,50,54],
        #                             [5,8,9,17,21],
        #                             [5,8,9,18,22],
        #                             [23,41,42,50,54],
        #                             [14,32,33,42,46],
        #                             [5,8,9,17,21]
        #                             ])
        if (type == info.FS_type.CPL):
            if(year < 108):
                column_pos_array = np.array([[14,21],
                                            [15,22],
                                            [23,30],
                                            [15,22],
                                            [16,23],
                                            [11,18]])
            if(year < 106):
                column_pos_array = np.array([[14,21],
                                            [15,22],
                                            [21,28],
                                            [15,22],
                                            [16,23],
                                            [11,18]])
            if(year < 104):
                column_pos_array = np.array([[15,22],
                                            [15,22],
                                            [21,28],
                                            [15,22],
                                            [16,23],
                                            [11,18]])
            if(year == 108):
                column_pos_array = np.array([[15,22],
                                            [15,22],
                                            [23,30],
                                            [15,22],
                                            [16,23],
                                            [11,18]])
            elif(year > 108):
                column_pos_array = np.array([[15,22],
                                            [15,22],
                                            [23,30],
                                            [15,22],
                                            [16,23],
                                            [11,18]])
        if (type == info.FS_type.SCF):
            column_pos_array = np.array([[3,4,5],
                                        [3,4,5],
                                        [3,4,5],
                                        [3,4,5],
                                        [3,4,5],
                                        [3,4,5]])
        data = []
        index = []
        column = []

        for k in range(len(tr_array_array)):
            tr_array = tr_array_array[k]
            for i in range(len(tr_array)):
                if i == 1:
                    td_array = tr_array[i].split('<th')
                else:    
                    td_array = tr_array[i].split('<td')

                if(len(td_array)>1):
                    code = self.remove_td(td_array[1])
                    name = self.remove_td(td_array[2])
                    revenue = self.remove_td(td_array[column_pos_array[k][0]])
                    profitRatio = self.remove_td(td_array[column_pos_array[k][1]])
                    if (type == info.FS_type.BS):
                        profitMargin = self.remove_td(td_array[column_pos_array[k][2]])
                        preTaxIncomeMargin = self.remove_td(td_array[column_pos_array[k][3]])
                        afterTaxIncomeMargin = self.remove_td(td_array[column_pos_array[k][4]])
                    if (type == info.FS_type.SCF):
                        profitMargin2 = self.remove_td(td_array[column_pos_array[k][2]])
                    if(i > 1):
                        if name == '公司名稱':
                            continue
                        if (type == info.FS_type.CPL):
                            data.append([name,code,revenue,profitRatio])
                        elif (type == info.FS_type.SCF):
                            data.append([name,code,revenue,profitRatio,profitMargin2])
                        else:
                            data.append([name,code,revenue,profitRatio,profitMargin,preTaxIncomeMargin,afterTaxIncomeMargin])
                        #index.append(name)
                    if(i == 1 and k == 0) :
                        column.append('公司名稱')
                        column.append('公司代號')
                        column.append(revenue)
                        column.append(profitRatio)
                        if (type == info.FS_type.BS):
                            column.append(profitMargin)
                            column.append(preTaxIncomeMargin)
                            column.append(afterTaxIncomeMargin)
                        if (type == info.FS_type.SCF):
                            column.append(profitMargin2)

        return pd.DataFrame(data = data,columns=column)
    def financial_statement(self,year:int, season:int, type:info.FS_type):#year = 年 season = 季 type = 財報種類
        myear = year
        if year>= 1000:
            myear -= 1911
        
        if type == info.FS_type.CPL:
            url = 'https://mops.twse.com.tw/mops/web/ajax_t163sb04'
        elif type == info.FS_type.BS:
            url = 'https://mops.twse.com.tw/mops/web/ajax_t163sb05'
        elif type == info.FS_type.PLA:
            url = 'https://mops.twse.com.tw/mops/web/ajax_t163sb06'
        elif type == info.FS_type.SCF:
            url = 'https://mops.twse.com.tw/mops/web/ajax_t163sb20'
        else:
            print('type does not match')

        # url = 'http://mops.twse.com.tw/mops/web/ajax_t163sb06'
        form_data = {
            'encodeURIComponent':1,
            'step':1,
            'firstin':1,
            'off':1,
            'TYPEK':'sii',
            'year': myear,
            'season': season,
        }
        response = requests.post(url,form_data,headers = tools.get_random_Header())
        #response.encoding = 'utf8'

        if type == info.FS_type.PLA:
            df = self.translate_dataFrame(response.text)
        else:
            df = self.translate_dataFrame2(response.text,type,myear,season)
        file = str(year) + "-season" + str(season) + "-" + type.value
        df.to_csv(self.filePath + "/" + self.fileName_season + "/" + file + ".csv",index=False)
        # 偽停頓
        time.sleep(5)
