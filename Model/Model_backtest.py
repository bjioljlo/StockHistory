import Globals
from BackTestService import BackTestStock
from DrawFigur import DrawFigur
from Model.Model import TModel
from Parameter import RecordBackTestParameter


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
        if (
            _recordBackTestParameter.check_monthRP_pick
            == _recordBackTestParameter.check_PER_pick
            == _recordBackTestParameter.check_volume_pick
            is False
        ):
            print("都沒選是要回測個毛線！")
            return
        elif _recordBackTestParameter.volumeDays < 2:
            print("測均線給1天是怎樣!")
            return
        else:
            self.Set_BackTestCheck(_recordBackTestParameter)
        _data = self.backtestFunc.backtest_monthRP_Up_Fast(_recordBackTestParameter)
        self.df.draw_BackTestResult(_data)

    def backtest2(self, _recordBackTestParameter: RecordBackTestParameter):  # PER PBR
        self.Set_BackTestCheck(_recordBackTestParameter)
        Globals.THREADPOOL.submit_task(
            self.backtestFunc.backtest_PERandPBR_Fast,
            self.df.draw_BackTestResult,
            mainParament=_recordBackTestParameter,
        )

    def backtest3(self, _recordBackTestParameter: RecordBackTestParameter):  # 定期定額
        self.Set_BackTestCheck(_recordBackTestParameter)
        Globals.THREADPOOL.submit_task(
            self.backtestFunc.backtest_Regular_quota,
            self.df.draw_BackTestResult,
            mainParament=_recordBackTestParameter,
        )

    def backtest4(self, _recordBackTestParameter: RecordBackTestParameter):  # 創新高
        self.Set_BackTestCheck(_recordBackTestParameter)
        Globals.THREADPOOL.submit_task(
            self.backtestFunc.backtest_Record_high,
            self.df.draw_BackTestResult,
            mainParament=_recordBackTestParameter,
        )

    def backtest5(self, _recordBackTestParameter: RecordBackTestParameter):  # KD篩選
        self.Set_BackTestCheck(_recordBackTestParameter)
        Globals.THREADPOOL.submit_task(
            self.backtestFunc.backtest_KD_pick,
            self.df.draw_BackTestResult,
            mainParament=_recordBackTestParameter,
        )

    def backtest6(self, _recordBackTestParameter: RecordBackTestParameter):  # PEG篩選
        self.Set_BackTestCheck(_recordBackTestParameter)
        Globals.THREADPOOL.submit_task(
            self.backtestFunc.backtest_PEG_pick,
            self.df.draw_BackTestResult,
            mainParament=_recordBackTestParameter,
        )
