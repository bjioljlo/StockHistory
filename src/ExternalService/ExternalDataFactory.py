from enum import Enum

from src.ExternalService.TGetExternalData import TGetExternalData
from src.ExternalService.GetExternalDataTest import GetExternalDataTest
from src.ExternalService.IGetExternalData import IGetExternalData
from src.MongoService import MongoService
from src.ReadLoadSystem import ReadLoadSystem
from src.SqlService import SqlService


class ExternalDataTypeEnum(Enum):
    Normal = (0,)
    Test = 1

class ExternalDataFactory:
    def __init__(self,
        sql_service: SqlService,
        mongo_service: MongoService,
        read_load_system: ReadLoadSystem,
        cache_service=None):
        self._sql_service = sql_service
        self._mongo_service = mongo_service
        self._read_load_system = read_load_system
        self._cache_service = cache_service
    def Get_instance(self,
        type: ExternalDataTypeEnum = ExternalDataTypeEnum.Normal,
    ) -> IGetExternalData:
        if type == ExternalDataTypeEnum.Test:
            return GetExternalDataTest(sql_service=self._sql_service, mongo_service=self._mongo_service,
                                    read_load_system=self._read_load_system)
        else:
            return TGetExternalData(sql_service=self._sql_service, mongo_service=self._mongo_service,
                                    read_load_system=self._read_load_system, cache_service=self._cache_service)
