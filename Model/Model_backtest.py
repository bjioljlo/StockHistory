from Model.Model import TModel
from IParameter import RecordBackTestParameter
import backtest_stock
import draw_figur as df

class Model_backtest(TModel):
    def __init__(self):
        super().__init__()
    
    def GetInteractiveController(self):
        return super().GetInteractiveController()
    
    def Set_BackTestCheck(self, _recordBackTestParameter: RecordBackTestParameter):
        backtest_stock.set_check(_recordBackTestParameter.check_monthRP_pick,
                                _recordBackTestParameter.check_PER_pick,
                                _recordBackTestParameter.check_volume_pick,
                                _recordBackTestParameter.check_pickOneStock,
                                _recordBackTestParameter.check_price_pick,
                                _recordBackTestParameter.check_PBR_pick,
                                _recordBackTestParameter.check_ROE_pick) 

    #第3頁的UI
    def backtest(self, _recordBackTestParameter: RecordBackTestParameter):#月營收回測開始紐
        if _recordBackTestParameter.check_monthRP_pick == _recordBackTestParameter.check_PER_pick == _recordBackTestParameter.check_volume_pick == False:
            print("都沒選是要回測個毛線！")
            return
        else:
            self.Set_BackTestCheck(_recordBackTestParameter)
        _data = backtest_stock.backtest_monthRP_Up_Fast(_recordBackTestParameter)
        df.draw_backtest(_data)

    def backtest2(self, _recordBackTestParameter: RecordBackTestParameter):#PER PBR 回測開始紐
        self.Set_BackTestCheck(_recordBackTestParameter)
        _data = backtest_stock.backtest_PERandPBR_Fast(_recordBackTestParameter)
        df.draw_backtest(_data)

    def backtest3(self, _recordBackTestParameter: RecordBackTestParameter):#定期定額
        _data = backtest_stock.backtest_Regular_quota_Fast(_recordBackTestParameter)
        df.draw_backtest(_data)

    def backtest4(self, _recordBackTestParameter: RecordBackTestParameter):#創新高
        self.Set_BackTestCheck(_recordBackTestParameter)
        _data = backtest_stock.backtest_Record_high_Fast(_recordBackTestParameter)
        df.draw_backtest(_data)

    def backtest5(self, _recordBackTestParameter: RecordBackTestParameter):#KD篩選
        self.Set_BackTestCheck(_recordBackTestParameter)
        _data = backtest_stock.backtest_KD_pick(_recordBackTestParameter)
        df.draw_backtest(_data)

    def backtest6(self, _recordBackTestParameter: RecordBackTestParameter):#PEG篩選
        self.Set_BackTestCheck(_recordBackTestParameter)
        _data = backtest_stock.backtest_PEG_pick_Fast(_recordBackTestParameter)
        df.draw_backtest(_data)