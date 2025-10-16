from BackTestService.BackTestStock import BackTestStock
from DrawFigur import DrawFigur
from Model.Model import TModel
from Common.Parameter import RecordBackTestParameter
import os
import pandas as pd
from ExternalService.IGetExternalData import IGetExternalData
from MongoService import MongoService
from SqlService import SqlService
from ThreadPool import ThreadPool


class Model_backtest(TModel):
    def __init__(self, sql_service: SqlService, mongo_service: MongoService, external_data_service: IGetExternalData, draw_figur_service: DrawFigur, thread_pool: ThreadPool):
        super().__init__()
        self._sql_service = sql_service
        self._mongo_service = mongo_service
        self._external_data_service = external_data_service
        self._draw_figur_service = draw_figur_service
        self._thread_pool = thread_pool
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

    def _run_backtest(self, func, folder_prefix: str, _recordBackTestParameter: RecordBackTestParameter, resultID:int, set_check: bool = True):
        backTestResultFolderName = "Datafiles"
        filePath = f"{backTestResultFolderName}/{folder_prefix}_{str(_recordBackTestParameter.date_start.date())}_{str(_recordBackTestParameter.date_end.date())}/"
        if not os.path.exists(filePath):
            os.makedirs(filePath)
        if set_check:
            self.Set_BackTestCheck(_recordBackTestParameter)
        self._thread_pool.submit_task(
            func,
            lambda data: _run_backTestcallBack(folder_prefix, data, outputFolder=filePath),
            mainParament=_recordBackTestParameter,
            folderName=filePath,
        )
        def _run_backTestcallBack(username, data, outputFolder):
            print("回測結束!")
            filterdate = data._TempTradeInfo.Data.tail(1).index[0]
            filterData = data._TempTradeInfo.Data.index == filterdate
            tempData = data._TempTradeInfo.Data[filterData]
            
            new_user_data = {
                'id': [resultID],
                'username': [username],
                'password': ['1234'], 
                'stocks': [(tempData['號碼'] + '.tw').to_json(orient='records')] 
            }
            user_df = pd.DataFrame(new_user_data).reset_index()
            self._sql_service.upsert_data("user_infos", user_df, key_columns=['username']);  # 回測完後重新連線
            self._draw_figur_service.draw_BackTestResult(data._TempResultDraw.Data, outputFolder),


    # 第3頁的UI
    def backtest(
        self, _recordBackTestParameter: RecordBackTestParameter
    ):
        self._run_backtest(self.backtestFunc.backtest_monthRP_Up, "monthRP_Up", _recordBackTestParameter, 5, set_check=False)

    def backtest2(self, _recordBackTestParameter: RecordBackTestParameter):
        self._run_backtest(self.backtestFunc.backtest_PERandPBR, "PERandPBR", _recordBackTestParameter, 6)

    def backtest3(self, _recordBackTestParameter: RecordBackTestParameter):
        self._run_backtest(self.backtestFunc.backtest_Regular_quota, "Regular_quota", _recordBackTestParameter, 7)

    def backtest4(self, _recordBackTestParameter: RecordBackTestParameter):
        self._run_backtest(self.backtestFunc.backtest_Record_high, "Record_high", _recordBackTestParameter, 8)

    def backtest5(self, _recordBackTestParameter: RecordBackTestParameter):
        self._run_backtest(self.backtestFunc.backtest_KD_pick, "KD_pick", _recordBackTestParameter, 9)

    def backtest6(self, _recordBackTestParameter: RecordBackTestParameter):  # PEG篩選
        self._run_backtest(self.backtestFunc.backtest_PEG_pick, "PEG_pick", _recordBackTestParameter, 10)