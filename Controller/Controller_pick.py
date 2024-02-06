from Controller.Controller import TController
from Model.Model import IModel
from View.View import IWindow
from View.View_pick import Pick_Window
import Controller.Controller as Controller

import tools
from datetime import timedelta
import Infomation_type as info
import get_stock_history as gsh
import pandas as pd

class Controller_pick(TController):
    def __init__(self, _view: IWindow = None, _model: IModel = None) -> None:
        super().__init__(_view, _model)
        self.Init_Window()
    
    def __GetView(self) -> Pick_Window:
        return self.View

    def Init_Window(self):
        UI_form = self.__GetView().GetFormUI()
        UI_form.button_openBackWindow.clicked.connect(self.button_openBackWindow_click)#設定button功能
        UI_form.button_moveToInput.clicked.connect(self.button_moveToInputFromPick_click)#設定button功能
        UI_form.button_pick_2.clicked.connect(self.button_monthRP_Up_click)#設定button功能
        UI_form.treeView_pick.setModel(Controller.creat_treeView_model(UI_form.treeView_pick,Controller.pick_titalList))#設定treeView功能
        UI_form.button_inputNum.clicked.connect(self.button_inuptNumber_click)#設定button功能
        UI_form.input_EPS.setValue(0)
        UI_form.input_GPM.setValue(0)
        UI_form.input_OPR.setValue(0)
        UI_form.input_RPS.setValue(0)
        UI_form.input_OMGR.setValue(0)
        UI_form.input_monthRP_smoothAVG.setValue(0)
        UI_form.input_monthRP_UpMpnth.setValue(0)
        UI_form.input_volum.setValue(0)
        UI_form.input_price_high.setValue(0)
        UI_form.input_price_low.setValue(0)
        UI_form.input_PBR_high.setValue(0)
        UI_form.input_PBR_low.setValue(0)
        UI_form.input_PER_high.setValue(0)
        UI_form.input_PER_low.setValue(0)
        UI_form.input_ROE_high.setValue(0)
        UI_form.input_ROE_low.setValue(0)
        UI_form.input_yiled_high.setValue(0)
        UI_form.input_yiled_low.setValue(0)
        UI_form.input_flash_Day.setValue(0)
        UI_form.input_record_Day.setValue(0)
        UI_form.input_PEG_high.setValue(0)
        UI_form.input_PEG_low.setValue(0)
        UI_form.input_FCF.setValue(0)
        UI_form.input_ROE.setValue(0)
        UI_form.input_EPS_up.setValue(0)
        UI_form.input_SRGR.setValue(0)
        UI_form.input_MRGR.setValue(0)

    def button_openBackWindow_click(self):
        self.Model.GetInteractiveController().ShowWindow()

    def button_moveToInputFromPick_click(self):
        Index = self.__GetView().GetFormUI().treeView_pick.currentIndex()
        mModel = self.__GetView().GetFormUI().treeView_pick.model()
        try:
            data = mModel.item(Index.row(),0).text()
            text = str(data)
            self.Controller_main.GetView().GetFormUI().input_stockNumber.setPlainText(text)
        except:
            print("")
    #全部篩選
    def button_monthRP_Up_click(self):
        UI_form = self.__GetView().GetFormUI()
        date = tools.QtDate2DateTime(self.Controller_main.View.FormUI.date_endDate.date())
        if date.isoweekday() == 6 or gsh.Stock_2330.get_PriceByDateAndType(date,info.Price_type.AdjClose) == None:
            date = date + timedelta(days=-1)
        elif date.isoweekday() == 7:
            date = date + timedelta(days=-2)
        else:
            pass
        try:
            GPM = UI_form.input_GPM.value()
            OPR = UI_form.input_OPR.value()
            EPS = UI_form.input_EPS.value()
            RPS = UI_form.input_RPS.value() 
            monthRP_smoothAVG = UI_form.input_monthRP_smoothAVG.value()
            monthRP_UpMpnth = UI_form.input_monthRP_UpMpnth.value()
            PBR_low = UI_form.input_PBR_low.value()
            PBR_high = UI_form.input_PBR_high.value()
            PER_low = UI_form.input_PER_low.value()
            PER_high = UI_form.input_PER_high.value()
            ROE_low = UI_form.input_ROE_low.value()
            ROE_high = UI_form.input_ROE_high.value()
            yiled_high = UI_form.input_yiled_high.value()
            yiled_low = UI_form.input_yiled_low.value()
            OMGR = UI_form.input_OMGR.value()
            price_high = UI_form.input_price_high.value()
            price_low = UI_form.input_price_low.value()
            flash_Day = UI_form.input_flash_Day.value()
            record_Day = UI_form.input_record_Day.value()
            volum = UI_form.input_volum.value()
            PEG_low = UI_form.input_PEG_low.value()
            PEG_high = UI_form.input_PEG_high.value()
            FCF = UI_form.input_FCF.value()
            ROE_up = UI_form.input_ROE.value()
            EPS_up = UI_form.input_EPS_up.value()
            SRGR = UI_form.input_SRGR.value()
            MRGR = UI_form.input_MRGR.value()
            BerMA = UI_form.input_BetterMA.value()
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
        UI_form.treeView_pick.setModel(Controller.creat_treeView_model(UI_form.treeView_pick,Controller.pick_titalList))#設定treeView功能
        Controller.set_treeView2(UI_form.treeView_pick.model(),pick_data) 
    def button_inuptNumber_click(self):# 帶入數值
        UI_form = self.__GetView().GetFormUI()
        UI_form.input_PER_high.setValue(15)#本益比
        UI_form.input_PBR_high.setValue(2)#股價淨值比
        UI_form.input_yiled_high.setValue(999)#殖利率
        UI_form.input_yiled_low.setValue(4)#殖利率
        UI_form.input_EPS_up.setValue(4)#EPS
        UI_form.input_monthRP_UpMpnth.setValue(12)#月營收
        UI_form.input_monthRP_smoothAVG.setValue(4)#月營收
        UI_form.input_volum.setValue(200)#成交量    
    #取得各種財報數字篩選
    def get_financial_statement(date,GPM = '0' ,OPR ='0' ,EPS ='0',RPS ='0'):
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