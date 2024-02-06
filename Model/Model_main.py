from Controller.Controller import IController
from Model.Model import TModel

from PyQt5.QtCore import QDate
from datetime import datetime
import get_stock_history as gsh
import tools
import draw_figur as df

class Model_main(TModel):
    def __init__(self, _interactiveController: IController):
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


    def monthRP(self, number: str, startdate: QDate, enddate: QDate):#某股票月營收曲線
        if (number == ''):
            print('請輸入股票號碼')
            return
        if (int(enddate.day()) == int(datetime.today().day)):
            print("今天還沒過完無資資訊")
            return
        if (int(enddate.month()) == int(datetime.today().month)):
            print("本月還沒過完無資資訊")
            return
        if int(enddate.month()) == int(tools.changeDateMonth(datetime.today(),-1).month) and (int(datetime.today().day)) < 15 :
            print("還沒15號沒有上個月的資料")
            return
        main_imge = gsh.All_imge(tools.QtDate2DateTime(startdate),
                                    tools.QtDate2DateTime(enddate),
                                    gsh.Month_index)
        data_result = main_imge.get_Chart(int(number))
        df.draw_RP(data_result,
                number,
                main_imge._report._name,
                main_imge._report._name,
                'Monthly Revenue(UNIT-->NTD:1000,000)')
        
    def Dividend_yield(self, number: str, startdate: QDate, enddate: QDate):#某股票殖利率曲線
        if (number == ''):
            print('請輸入股票號碼')
            return
        if (int(enddate.day()) == int(datetime.today().day)):
            print("今天還沒過完無資資訊")
            return
        main_imge = gsh.All_imge(tools.QtDate2DateTime(startdate),
                                    tools.QtDate2DateTime(enddate),
                                    gsh.Yield_index)
        data_result = main_imge.get_Chart(int(number))
        df.draw_RP(data_result,
                number,
                main_imge._report._name,
                main_imge._report._name,
                'Dividend yield')   