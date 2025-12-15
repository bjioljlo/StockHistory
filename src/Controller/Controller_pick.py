from datetime import datetime

from src.Model.Model import IModel
from src.Model.Model_pick import Model_pick
from src.View.View import IWindow
from src.View.View_pick import Pick_Window

from . import Controller
from .Controller import TController, controllers


class Controller_pick(TController):
    def __init__(self, _view: IWindow = None, _model: IModel = None) -> None:
        super().__init__(_view, _model)
        self.Init_Window()

    def __GetView(self) -> Pick_Window:
        return self.View

    def __GetModel(self) -> Model_pick:
        return self.Model

    def Init_Window(self):
        UI_form = self.__GetView().GetFormUI()
        UI_form.button_openBackWindow.clicked.connect(
            self.button_openBackWindow_click
        )  # 設定button功能
        UI_form.button_moveToInput.clicked.connect(
            self.button_moveToInputFromPick_click
        )  # 設定button功能
        UI_form.button_pick_2.clicked.connect(
            self.button_Filter_click
        )  # 設定button功能
        UI_form.treeView_pick.setModel(
            Controller.creat_treeView_model(
                UI_form.treeView_pick, Controller.PICK__TITALLIST
            )
        )  # 設定treeView功能
        UI_form.button_inputNum.clicked.connect(
            self.button_inuptNumber_click
        )  # 設定button功能
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
        UI_form.input_kind.addItem("無")
        UI_form.input_kind.addItems(self.__GetModel().Groups)
        UI_form.input_AvgVolume.setValue(0)

    def GetEndDate(self) -> datetime:
        pass

    def GetStockNumber(self) -> str:
        pass

    def SetStockNumber(self, stockNumber: str):
        pass

    def button_openBackWindow_click(self):
        self.GetController(controllers.BackTest).ShowWindow()

    def button_moveToInputFromPick_click(self):
        Index = self.__GetView().GetFormUI().treeView_pick.currentIndex()
        mModel = self.__GetView().GetFormUI().treeView_pick.model()
        try:
            data = mModel.item(Index.row(), 0).text()
            text = str(data)
            self.GetController(controllers.Main).SetStockNumber(text)
        except IndexError:
            print("")

    # 全部篩選
    def button_Filter_click(self):
        UI_form = self.__GetView().GetFormUI()
        endDate = self.GetController(controllers.Main).GetEndDate()
        pick_data = self.__GetModel().RunFilte(self.__GetView().Parament, endDate)
        UI_form.treeView_pick.setModel(
            Controller.creat_treeView_model(
                UI_form.treeView_pick, Controller.PICK__TITALLIST
            )
        )  # 設定treeView功能
        Controller.set_treeView2(UI_form.treeView_pick.model(), pick_data)

    def button_inuptNumber_click(self):  # 帶入數值
        UI_form = self.__GetView().GetFormUI()
        UI_form.input_PER_high.setValue(15)  # 本益比
        UI_form.input_PBR_high.setValue(2)  # 股價淨值比
        UI_form.input_yiled_high.setValue(999)  # 殖利率
        UI_form.input_yiled_low.setValue(4)  # 殖利率
        UI_form.input_EPS_up.setValue(4)  # EPS
        UI_form.input_monthRP_UpMpnth.setValue(12)  # 月營收
        UI_form.input_monthRP_smoothAVG.setValue(4)  # 月營收
        UI_form.input_volum.setValue(200)  # 成交量
