import Common.Globals as Globals
from BackTestService.BackTestStock import BackTestStock
from DrawFigur import DrawFigur
from Model.Model import TModel
from Common.Parameter import RecordBackTestParameter
import os


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

    def _run_backtest(self, func, folder_prefix: str, _recordBackTestParameter: RecordBackTestParameter, set_check: bool = True):
        filePath = f"{folder_prefix}_{str(_recordBackTestParameter.date_start.date())}_{str(_recordBackTestParameter.date_end.date())}/"
        if not os.path.exists(filePath):
            os.makedirs(filePath)
        if set_check:
            self.Set_BackTestCheck(_recordBackTestParameter)
        Globals.THREADPOOL.submit_task(
            func,
            lambda data: self.df.draw_BackTestResult(data, outputFolder=filePath),
            mainParament=_recordBackTestParameter,
            folderName=filePath,
        )

    # 第3頁的UI
    def backtest(
        self, _recordBackTestParameter: RecordBackTestParameter
    ):
        self._run_backtest(self.backtestFunc.backtest_monthRP_Up, "monthRP_Up", _recordBackTestParameter, set_check=False)

    def backtest2(self, _recordBackTestParameter: RecordBackTestParameter):
        self._run_backtest(self.backtestFunc.backtest_PERandPBR, "PERandPBR", _recordBackTestParameter)

    def backtest3(self, _recordBackTestParameter: RecordBackTestParameter):
        self._run_backtest(self.backtestFunc.backtest_Regular_quota, "Regular_quota", _recordBackTestParameter)

    def backtest4(self, _recordBackTestParameter: RecordBackTestParameter):
        self._run_backtest(self.backtestFunc.backtest_Record_high, "Record_high", _recordBackTestParameter)

    def backtest5(self, _recordBackTestParameter: RecordBackTestParameter):
        self._run_backtest(self.backtestFunc.backtest_KD_pick, "KD_pick", _recordBackTestParameter)

    def backtest6(self, _recordBackTestParameter: RecordBackTestParameter):  # PEG篩選
        self._run_backtest(self.backtestFunc.backtest_PEG_pick, "PEG_pick", _recordBackTestParameter)
