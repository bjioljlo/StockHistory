from enum import Enum

from src.ExternalService.TGetExternalData import TGetExternalData
from src.ExternalService.GetExternalDataTest import GetExternalDataTest
from src.ExternalService.IGetExternalData import IGetExternalData
from src.ExternalService.MockGetExternalData import MockGetExternalData
from src.MongoService import MongoService
from src.ReadLoadSystem import ReadLoadSystem
from src.SqlService import SqlService
from src.Common.CacheService import HybridCacheService


class ExternalDataTypeEnum(Enum):
    Normal = 0
    Test = 1

class ExternalDataFactory(IGetExternalData):
    """
    外部資料工廠 + 轉送器
    同時扮演工廠角色與 IGetExternalData 介面實作，內部自動管理實例生命週期
    解決整個系統到處把 Factory 當成 IGetExternalData 注入的架構問題
    """
    def __init__(self,
        sql_service: SqlService,
        mongo_service: MongoService,
        read_load_system: ReadLoadSystem,
        cache_service: HybridCacheService):
        self._sql_service = sql_service
        self._mongo_service = mongo_service
        self._read_load_system = read_load_system
        self._cache_service = cache_service
        # 內部快取實例，避免重複建立
        self._instance = None

    def Get_instance(self,
        type: ExternalDataTypeEnum = ExternalDataTypeEnum.Normal,
    ) -> IGetExternalData:
        if self._instance is None:
            # 直接回傳 TGetExternalData 實例，不要使用 Interface 轉型，避免 debug 符號遺失
            self._instance = TGetExternalData(
                sql_service=self._sql_service,
                mongo_service=self._mongo_service,
                read_load_system=self._read_load_system,
                cache_service=self._cache_service
            )
        return self._instance

    # ==================================================
    # IGetExternalData 介面轉送實作
    # 所有方法直接轉送到內部真正的實例
    # ==================================================

    def get_stock_history(self, symbol: str, start_date=None, end_date=None):
        # TODO: 此方法已過時，將在下個版本移除，請直接呼叫 Get_instance() 取得實例
        return self.Get_instance().get_stock_history(symbol, start_date, end_date)

    def get_allstock_daily_data(self, start_date, end_date):
        return self.Get_instance().get_allstock_daily_data(start_date, end_date)

    def get_allstock_financial_statement(self, date, fs_type):
        return self.Get_instance().get_allstock_financial_statement(date, fs_type)

    def get_allstock_monthly_report(self, date):
        return self.Get_instance().get_allstock_monthly_report(date)

    def get_allstock_dividend_yield(self):
        return self.Get_instance().get_allstock_dividend_yield()

    def get_full_ad_index(self):
        return self.Get_instance().get_full_ad_index()

    def get_full_adl(self):
        return self.Get_instance().get_full_adl()

    def get_stock_AD_index(self, date, getNew=False):
        return self.Get_instance().get_stock_AD_index(date, getNew)

    def get_allstock_yield(self, start):
        return self.Get_instance().get_allstock_yield(start)

    # 自動轉送所有其他 IGetExternalData 介面方法
    def __getattr__(self, name):
        return getattr(self.Get_instance(), name)

