import Common.Globals as Globals
from BackTestService.BackTestStock import BackTestStock
from DrawFigur import DrawFigur
from Model.Model import TModel
from Common.Parameter import RecordBackTestParameter


class Model_backtest(TModel):
    def __init__(self):
        super().__init__()
        self.df: DrawFigur = Globals.DRAWFIGUR
        self.backtestFunc: BackTestStock = BackTestStock()

    def Set_BackTestCheck(self, _recordBackTestParameter: RecordBackTestParameter):
        self.backtestFunc.set_check(
            _recordBackTestParameter.check_monthRP_pick,
            _recordBackTestParameter.check_PER_pick,
            _recordBackTestParameter.check_volume_pick,
            _recordBackTestParameter.check_pickOneStock,
            _recordBackTestParameter.check_price_pick,
            _recordBackTestParameter.check_PBR_pick,
            _recordBackTestParameter.check_ROE_pick,
        )

    # 第3頁的UI
    def backtest(
        self, _recordBackTestParameter: RecordBackTestParameter
    ):  # 月營收回測開始紐
        Globals.THREADPOOL.submit_task(
            self.backtestFunc.backtest_monthRP_Up,
            lambda data: self.df.draw_BackTestResult(data, outputFolder="monthRP_Up/"),
            mainParament=_recordBackTestParameter,
        )
        
    def backtest2(self, _recordBackTestParameter: RecordBackTestParameter):  # PER PBR
        self.Set_BackTestCheck(_recordBackTestParameter)
        Globals.THREADPOOL.submit_task(
            self.backtestFunc.backtest_PERandPBR,
            lambda data: self.df.draw_BackTestResult(data, outputFolder="PERandPBR/"),
            mainParament=_recordBackTestParameter,
        )

    def backtest3(self, _recordBackTestParameter: RecordBackTestParameter):  # 定期定額
        self.Set_BackTestCheck(_recordBackTestParameter)
        Globals.THREADPOOL.submit_task(
            self.backtestFunc.backtest_Regular_quota,
            lambda data: self.df.draw_BackTestResult(data, outputFolder="Regular_quota/"),
            mainParament=_recordBackTestParameter,
        )

    def backtest4(self, _recordBackTestParameter: RecordBackTestParameter):  # 創新高
        self.Set_BackTestCheck(_recordBackTestParameter)
        Globals.THREADPOOL.submit_task(
            self.backtestFunc.backtest_Record_high,
            lambda data: self.df.draw_BackTestResult(data, outputFolder="Record_high/"),
            mainParament=_recordBackTestParameter,
        )

    def backtest5(self, _recordBackTestParameter: RecordBackTestParameter):  # KD篩選
        self.Set_BackTestCheck(_recordBackTestParameter)
        Globals.THREADPOOL.submit_task(
            self.backtestFunc.backtest_KD_pick,
            lambda data: self.df.draw_BackTestResult(data, outputFolder="KD_pick/"),
            mainParament=_recordBackTestParameter,
        )

    def backtest6(self, _recordBackTestParameter: RecordBackTestParameter):  # PEG篩選
        self.Set_BackTestCheck(_recordBackTestParameter)
        Globals.THREADPOOL.submit_task(
            self.backtestFunc.backtest_PEG_pick,
            lambda data: self.df.draw_BackTestResult(data, outputFolder="PEG_pick/"),
            mainParament=_recordBackTestParameter,
        )
