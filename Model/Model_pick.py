from Controller.Controller import IController
from Model.Model import TModel
import tools
from datetime import timedelta,datetime
import get_stock_history as gsh
import Infomation_type as info
from IParameter import RecordPickParameter
import pandas as pd
from StockInfos import PickInfoDatas

class Model_pick(TModel):
    def __init__(self,_interactiveController: IController):
        super().__init__()
        self._InteractiveController = _interactiveController

    @property
    def InteractiveController(self):
        if self._InteractiveController == None:
            raise
        return self._InteractiveController
    @InteractiveController.setter
    def InteractiveController(self,_interactiveController:IController):
        self._InteractiveController = _interactiveController

    def GetInteractiveController(self) -> IController:
        return self.InteractiveController

    #全部篩選
    def monthRP_Up(self, RecordPickParameter: RecordPickParameter, endDate: datetime) -> pd.DataFrame:
        date = endDate#tools.QtDate2DateTime(self.Controller_main.View.FormUI.date_endDate.date())
        if date.isoweekday() == 6 or gsh.Stock_2330.get_PriceByDateAndType(date,info.Price_type.AdjClose) == None:
            date = date + timedelta(days=-1)
        elif date.isoweekday() == 7:
            date = date + timedelta(days=-2)
        else:
            pass
        try:
            GPM = RecordPickParameter.GPM
            OPR = RecordPickParameter.OPR
            EPS = RecordPickParameter.EPS
            RPS = RecordPickParameter.RPS 
            monthRP_smoothAVG = RecordPickParameter.monthRP_smoothAVG
            monthRP_UpMpnth = RecordPickParameter.monthRP_UpMpnth
            PBR_low = RecordPickParameter.PBR_low
            PBR_high = RecordPickParameter.PBR_high
            PER_low = RecordPickParameter.PER_low
            PER_high = RecordPickParameter.PER_high
            ROE_low = RecordPickParameter.ROE_low
            ROE_high = RecordPickParameter.ROE_high
            yiled_high = RecordPickParameter.yiled_high
            yiled_low = RecordPickParameter.yiled_low
            OMGR = RecordPickParameter.OMGR
            price_high = RecordPickParameter.price_high
            price_low = RecordPickParameter.price_low
            flash_Day = RecordPickParameter.flash_Day
            record_Day = RecordPickParameter.record_Day
            volum = RecordPickParameter.volum
            PEG_low = RecordPickParameter.PEG_low
            PEG_high = RecordPickParameter.PEG_high
            FCF = RecordPickParameter.FCF
            ROE_up = RecordPickParameter.ROE
            EPS_up = RecordPickParameter.EPS_up
            SRGR = RecordPickParameter.SRGR
            MRGR = RecordPickParameter.MRGR
            BerMA = RecordPickParameter.BetterMA
        except:
            print("Get value error")
            return
        FS_data = pd.DataFrame()
        pick_data = pd.DataFrame()
        result_data = pd.DataFrame()
        BOOK_data = pd.DataFrame()
        PER_data = pd.DataFrame()
        yield_data = pd.DataFrame()
        PEG_data = pd.DataFrame()
        FCF_data = pd.DataFrame()
        ROE_Up_data = pd.DataFrame()
        EPS_up_data = pd.DataFrame()

        FS_data = self.get_financial_statement(date,GPM,OPR,EPS,RPS)
        
        mainStockfun = gsh.All_Stock_Filters_fuc(date,FS_data)
        mainfun = gsh.All_fuc(date,gsh.Month_index)
        result_data = mainfun.get_Smooth_Up_Auto(monthRP_smoothAVG,monthRP_UpMpnth)
        
        mainfun.report = gsh.PBR_index
        BOOK_data = mainfun.get_Filter_Auto(PBR_high,PBR_low)
        
        mainfun.report = gsh.PER_index
        PER_data = mainfun.get_Filter_Auto(PER_high,PER_low)
        
        mainfun.report = gsh.ROE_index
        ROE_data = mainfun.get_Filter_Auto(ROE_high,ROE_low)
        ROE_Up_data = mainfun.get_Up_Auto(ROE_up)
        
        mainfun.report = gsh.Yield_index
        yield_data = mainfun.get_Filter_Auto(yiled_high,yiled_low)
        
        mainfun.report = gsh.OM_Growth_index
        OMGR_data = mainfun.get_Up_Auto(OMGR)
        
        mainfun.report = gsh.PEG_index
        PEG_data = mainfun.get_Filter_Auto(PEG_high,PEG_low)
        
        mainfun.report = gsh.FreeCF_index
        FCF_data = mainfun.get_Up_Auto(FCF)
        
        mainfun.report = gsh.EPS_index
        EPS_up_data = mainfun.get_Up_Auto(EPS_up)
        
        mainfun.report = gsh.SR_Growth_index
        SRGR_data = mainfun.get_Up_Auto(SRGR)
        
        mainfun.report = gsh.MR_Growth_index
        MRGR_data = mainfun.get_Up_Auto(MRGR)
        
        pick_data = FS_data
        if monthRP_smoothAVG > 0 or monthRP_UpMpnth > 0:            
            pick_data = pd.merge(pick_data,result_data,left_index=True,right_index=True,how='left')
            pick_data = pick_data.dropna(axis=0,how='any')
        if PBR_low > 0 or PBR_high > 0:
            pick_data = pd.merge(pick_data,BOOK_data,left_index=True,right_index=True,how='left')
            pick_data = pick_data.dropna(axis=0,how='any')
        if PER_low > 0 or PER_high > 0:
            pick_data = pd.merge(pick_data,PER_data,left_index=True,right_index=True,how='left')
            pick_data = pick_data.dropna(axis=0,how='any')
        if PEG_low > 0 or PEG_high > 0:
            pick_data = pd.merge(pick_data,PEG_data,left_index=True,right_index=True,how='left')
            pick_data = pick_data.dropna(axis=0,how='any')
        if ROE_low > 0 or ROE_high > 0:
            pick_data = pd.merge(pick_data,ROE_data,left_index=True,right_index=True,how='left')
            pick_data = pick_data.dropna(axis=0,how='any')
        if yiled_high > 0 or yiled_low > 0:
            pick_data = pd.merge(pick_data,yield_data,left_index=True,right_index=True,how='left')
            pick_data = pick_data.dropna(axis=0,how='any')
        if OMGR > 0:
            pick_data = pd.merge(pick_data,OMGR_data,left_index=True,right_index=True,how='left')
            pick_data = pick_data.dropna(axis=0,how='any')
        if SRGR > 0:
            pick_data = pd.merge(pick_data,SRGR_data,left_index=True,right_index=True,how='left')
            pick_data = pick_data.dropna(axis=0,how='any')
        if MRGR > 0:
            pick_data = pd.merge(pick_data,MRGR_data,left_index=True,right_index=True,how='left')
            pick_data = pick_data.dropna(axis=0,how='any')
        if FCF > 0:
            pick_data = pd.merge(pick_data,FCF_data,left_index=True,right_index=True,how='left')
            pick_data = pick_data.dropna(axis=0,how='any')
        if ROE_up > 0:
            pick_data = pd.merge(pick_data,ROE_Up_data,left_index=True,right_index=True,how='left')
            pick_data = pick_data.dropna(axis=0,how='any')
        if EPS_up > 0:
            pick_data = pd.merge(pick_data,EPS_up_data,left_index=True,right_index=True,how='left')
            pick_data = pick_data.dropna(axis=0,how='any')
        if price_high > 0 or price_low > 0:
            mainStockfun.Data = pick_data
            price_data = mainStockfun.get_Filter('price',price_high,price_low,info.Price_type.Close)
            pick_data = tools.MixDataFrames({'pick':pick_data,'price':price_data})
            pick_data = pick_data.dropna(axis=0,how='any')
        if flash_Day > 0 or record_Day > 0:
            mainStockfun.Data = pick_data
            record_data = mainStockfun.get_Filter_RecordHigh(flash_Day,record_Day,info.Price_type.High)
            pick_data = tools.MixDataFrames({'pick':pick_data,'recordHigh':record_data})
            pick_data = pick_data.dropna(axis=0,how='any')
        if BerMA > 0:
            mainStockfun.Data = pick_data
            BerMA_data = mainStockfun.get_Filter_BetterMA(BerMA,info.Price_type.Close)
            pick_data = tools.MixDataFrames({'pick':pick_data,'BerMA_data':BerMA_data})
            pick_data = pick_data.dropna(axis=0,how='any')
        if volum > 0:
            mainStockfun.Data = pick_data
            volume_data = mainStockfun.get_Filter_SMA('volume',volum * 100000000,volum * 10000,5,info.Price_type.Volume)
            pick_data = tools.MixDataFrames({'pick':pick_data,'volumeData':volume_data})
            pick_data = pick_data.dropna(axis=0,how='any')
        print("總挑選數量:" + str(len(pick_data)))
        return pick_data

    #取得各種財報數字篩選
    def get_financial_statement(slef, date, GPM:float = 0 ,OPR:float = 0 ,EPS:int = 0,RPS:float = 0) -> pd.DataFrame:
        resultAllFS1 = []
        resultAllFS2 = []
        resultAllFS3 = []
        this = pd.DataFrame()
        volume_date = date
        for i in range(12):
            try:
                this = gsh.PLA_RP.get_ALL_Report(volume_date)
                if this.empty:
                    volume_date = tools.changeDateMonth(volume_date,-1)
                    continue
                print(str(volume_date.month)+ "月財務報告ＯＫ")
                break
            except:
                print(str(volume_date.month)+ "月財務報告未出跳下一個月")
                volume_date = tools.changeDateMonth(volume_date,-1)
                continue
        this1 = this["毛利率(%)"] > float(GPM)
        this2 = this["營業利益率(%)"] > float(OPR)
        resultAllFS1 = this[this1 & this2]

        this = gsh.BS_RP.get_ALL_Report(volume_date)
        this1 = this["每股參考淨值"] > float(RPS)
        resultAllFS2 = this[this1]

        this = gsh.CPL_RP.get_ALL_Report(volume_date)
        this1 = this["基本每股盈餘（元）"] > float(EPS)
        resultAllFS3 = this[this1]

        resultAllFS_temp = tools.MixDataFrames({'resultAllFS1':resultAllFS1,'resultAllFS2':resultAllFS2})
        resultAllFS = tools.MixDataFrames({'resultAllFS3':resultAllFS3,'resultAllFS_temp':resultAllFS_temp})

        return resultAllFS